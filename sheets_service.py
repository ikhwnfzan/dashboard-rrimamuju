import os
import json
import time
import traceback
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_CACHE = {}
CACHE_TTL = 180
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _extract_sheet_id(val):
    val = str(val or "").strip()
    if "/spreadsheets/d/" in val:
        return val.split("/spreadsheets/d/")[1].split("/")[0]
    return val


def _normalize_nip(val):
    return "".join(str(val or "").split())


def _parse_num(val):
    s = str(val or "").strip().replace(",", "")
    if not s:
        return 0
    try:
        f = float(s)
        return int(f) if f.is_integer() else round(f, 2)
    except ValueError:
        return 0


def parse_roles(role_str):
    raw = str(role_str or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace(",", ";").split(";") if p.strip()]
    seen = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return seen


def _rows_to_dicts(all_values, include_row_num=False):
    if not all_values or len(all_values) < 2:
        return []
    headers = [str(h).strip() for h in all_values[0]]
    records = []
    for idx, row in enumerate(all_values[1:], start=2):
        padded = row + [""] * (len(headers) - len(row))
        item = {headers[i]: str(padded[i]).strip() for i in range(len(headers)) if headers[i]}
        if any(v for v in item.values()):
            if include_row_num:
                item["_row_num"] = idx
            records.append(item)
    return records


ALL_MODULES = [
    {"key": "info_board", "label": "Info Board", "group": "Publik & Internal"},
    {"key": "data_pegawai", "label": "Data Pegawai", "group": "SDM"},
    {"key": "arsip_sdm", "label": "Arsip SDM", "group": "SDM"},
    {"key": "dialog", "label": "Dialog", "group": "Siaran & Perencanaan"},
    {"key": "jadwal_siaran", "label": "Jadwal Siaran", "group": "Siaran & Perencanaan"},
    {"key": "program_siaran", "label": "Program Siaran", "group": "Siaran & Perencanaan"},
    {"key": "konten", "label": "Content Planner", "group": "KMB"},
    {"key": "jadwal_tmb", "label": "Jadwal TMB", "group": "TMB"},
    {"key": "master_barang", "label": "Master Barang", "group": "BMN"},
    {"key": "master_persediaan", "label": "Master Persediaan", "group": "BMN"},
    {"key": "persediaan_masuk", "label": "Persediaan Masuk", "group": "BMN"},
    {"key": "persediaan_keluar", "label": "Persediaan Keluar", "group": "BMN"},
    {"key": "master_ruangan", "label": "Master Ruangan", "group": "BMN"},
    {"key": "bmn_area", "label": "BMN AREA", "group": "BMN"},
    {"key": "manage_users", "label": "Manage User", "group": "Admin"},
    {"key": "manage_modules", "label": "Manage Module", "group": "Admin"},
]

ALL_ROLES = [
    "Admin",
    "SDM",
    "Perencanaan",
    "KMB",
    "BMN",
    "Operator BMN",
    "TMB",
    "LPU",
    "Berita",
    "Siaran",
    "Keuangan",
    "Pimpinan",
    "Kasubag TU",
]

DEFAULT_ROLE_PERMISSIONS = {
    "Admin": {m["key"]: "full" for m in ALL_MODULES},
    "SDM": {
        "data_pegawai": "full",
        "arsip_sdm": "full",
        "info_board": "full",
    },
    "Perencanaan": {
        "info_board": "view",
        "dialog": "full",
        "jadwal_siaran": "full",
        "program_siaran": "full",
    },
    "KMB": {
        "info_board": "view",
        "konten": "full",
    },
    "Siaran": {
        "info_board": "view",
        "jadwal_siaran": "view",
        "dialog": "update",
        "program_siaran": "view",
    },
    "TMB": {
        "info_board": "view",
        "jadwal_tmb": "view",
    },
    "BMN": {
        "info_board": "view",
        "master_barang": "full",
        "master_persediaan": "full",
        "persediaan_masuk": "full",
        "persediaan_keluar": "full",
        "master_ruangan": "full",
        "bmn_area": "full",
    },
    "Operator BMN": {
        "info_board": "view",
        "master_barang": "full",
        "master_persediaan": "full",
        "persediaan_masuk": "full",
        "persediaan_keluar": "full",
        "master_ruangan": "full",
        "bmn_area": "full",
    },
    "LPU": {"info_board": "view"},
    "Berita": {"info_board": "view"},
    "Keuangan": {"info_board": "view"},
    "Pimpinan": {"info_board": "view", "data_pegawai": "view", "dialog": "view", "jadwal_siaran": "view", "program_siaran": "view"},
    "Kasubag TU": {"info_board": "view", "data_pegawai": "view", "master_barang": "view", "master_persediaan": "view"},
}

TAB_SCHEMAS = {
    "Users": ["NIP", "Password", "Role"],
    "Role_Modules": ["Role"] + [m["key"] for m in ALL_MODULES],
    "DB_Pegawai": ["No", "Nama Pegawai", "NIP / NIPPK", "Pangkat/ Golongan", "Jabatan", "Status", "Posisi"],
    "Arsip_SDM": ["Nomor Dokumen", "Nama Dokumen", "Tanggal", "Jenis", "Link"],
    "Info_Board": ["Tanggal", "Prioritas", "Judul", "Isi", "Target_Divisi", "Lampiran"],
    "Planner": ["Tanggal_Tayang", "Platform", "Akun", "Judul_Konten", "Jenis", "Divisi", "PIC", "Status", "Link_Asset"],
    "Siaran": ["Tanggal", "Shift", "Programa", "Penyiar", "Operator", "Status"],
    "Program_Siaran": ["Kode_Program", "Programa", "Nama_Program", "Hari", "Jam_Tayang", "Format", "Produser", "Status"],
    "Jadwal_TMB": ["Tanggal", "Shift", "Lokasi_Pemancar", "Teknisi_TMB", "Tugas", "Status"],
    "DB_Ruangan": ["Nomor Ruangan", "Nama Ruangan", "Lokasi", "Penanggungjawab Ruangan", "Nama", "NIP/ NIPPPK"],
    "DB_Aset": ["Kode Ruang", "Nomor Kode Barang", "Nama Barang", "Merk/ Model", "Tahun", "NUP", "Kondisi", "Tindak Lanjut", "Keterangan"],
    "DB_Stok_Master": ["Kode Barang", "Nama Barang", "Unit", "Stok Awal", "Keterangan"],
    "DB_Stok_Masuk": ["Tanggal", "Penanggung Jawab", "Nama Barang", "Jumlah Masuk", "Unit", "Pcs", "Keterangan"],
    "DB_Stok_Keluar": ["Tanggal", "Nama Barang", "Bidang", "Penerima Barang", "Jumlah Keluar", "Unit", "Pcs", "Keterangan"],
    "Arsip": ["Kode_Arsip", "Tanggal", "Kategori", "Judul", "Divisi", "Link"],
}

DEMO_DATA = {
    "Users": [
        {"NIP": "199806212025041001", "Password": "rri2026", "Role": "Admin"},
        {"NIP": "200112082025042004", "Password": "bmn2026", "Role": "TMB; Operator BMN"},
        {"NIP": "199203252024212001", "Password": "sdm2026", "Role": "SDM"},
        {"NIP": "199210252025042002", "Password": "ren2026", "Role": "Siaran; Perencanaan"},
        {"NIP": "199010302022211010", "Password": "kmb2026", "Role": "KMB; Siaran"},
    ],
    "DB_Pegawai": [
        {"No": "1", "Nama Pegawai": "Rina Irfantini, S.H., M.Si.", "NIP / NIPPK": "197312051999032007", "Pangkat/ Golongan": "Pembina Tk.I IV/b", "Posisi": "Kepala Stasiun LPP RRI Mamuju", "Status": "Aktif", "Jabatan": "Kepala Stasiun"},
        {"No": "2", "Nama Pegawai": "Muhamad Dirsan, S.E.", "NIP / NIPPK": "197506231998031002", "Pangkat/ Golongan": "Penata Tk.I III/d", "Posisi": "Kepala Sub Bagian Tata Usaha", "Status": "Aktif", "Jabatan": "Kepala Sub Bagian Tata Usaha"},
        {"No": "3", "Nama Pegawai": "Jamil Ma'ruf, S.E.", "NIP / NIPPK": "199208152022021002", "Pangkat/ Golongan": "Penata Muda III/a", "Posisi": "Bendahara", "Status": "Aktif", "Jabatan": "Bendahara"},
        {"No": "4", "Nama Pegawai": "Dwita Ardiyana", "NIP / NIPPK": "199210252025042002", "Pangkat/ Golongan": "Penata Muda III/a", "Posisi": "Staf", "Status": "Aktif", "Jabatan": "Pranata Siaran Ahli Pertama"},
        {"No": "5", "Nama Pegawai": "Ikhwan Fauzan, A.Md.T", "NIP / NIPPK": "199806212025041001", "Pangkat/ Golongan": "Pengatur II/c", "Posisi": "Staf", "Status": "Aktif", "Jabatan": "Asisten Teknisi Siaran Terampil"},
        {"No": "6", "Nama Pegawai": "Muthiah Azizah Ijsam, A.Md.T", "NIP / NIPPK": "200112082025042004", "Pangkat/ Golongan": "Pengatur II/c", "Posisi": "Staf", "Status": "Aktif", "Jabatan": "Asisten Teknisi Siaran Terampil"},
        {"No": "7", "Nama Pegawai": "A. Mirwan Syam", "NIP / NIPPK": "199006082022211012", "Pangkat/ Golongan": "Pengatur Muda V", "Posisi": "Ketua Tim TMB", "Status": "Aktif", "Jabatan": "Ketua Tim TMB"},
        {"No": "8", "Nama Pegawai": "Nurul Qodriyah, S.E.", "NIP / NIPPK": "199203252024212001", "Pangkat/ Golongan": "Penata Muda IX", "Posisi": "Staf", "Status": "Aktif", "Jabatan": "Analis SDM"},
        {"No": "9", "Nama Pegawai": "Sugiyanto", "NIP / NIPPK": "199010302022211010", "Pangkat/ Golongan": "Pengatur Muda V", "Posisi": "Ketua Tim KMB", "Status": "Aktif", "Jabatan": "Ketua Tim KMB"},
    ],
    "Arsip_SDM": [
        {"Nomor Dokumen": "SK-014/RRI-MMJ/SDM/2026", "Nama Dokumen": "SK Tim Pengelola BMN & Persediaan 2026", "Tanggal": "2026-01-10", "Jenis": "Surat Keputusan", "Link": "https://drive.google.com"},
        {"Nomor Dokumen": "ST-088/RRI-MMJ/SDM/2026", "Nama Dokumen": "Surat Tugas Liputan RRI Fest Mamuju", "Tanggal": "2026-08-25", "Jenis": "Surat Tugas", "Link": "https://drive.google.com"},
    ],
    "Info_Board": [
        {"Tanggal": "2026-11-17", "Prioritas": "Urgent", "Judul": "Pemutakhiran Data Kepegawaian & SK Jabatan", "Isi": "Seluruh pegawai dimohon mengecek kesesuaian NIP, Pangkat/Golongan, dan Jabatan pada modul Data Pegawai.", "Target_Divisi": "Semua Pegawai", "Lampiran": ""}
    ],
    "Timeline": [
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pendaftaran dibuka", "Start Date": "08/01/2026", "End Date": "08/01/2026", "Keterangan": "Online & Kantor LPP RRI Mamuju", "Tanggal": "01 Aug 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Bersih-Bersih Lingkungan", "Start Date": "08/28/2026", "End Date": "08/28/2026", "Keterangan": "Pantai Manakarra", "Tanggal": "28 Aug 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Upacara dan Penyuluhan Obor", "Start Date": "09/11/2026", "End Date": "09/11/2026", "Keterangan": "Auditorium LPP RRI Mamuju", "Tanggal": "11 Sep 2026"},
    ],
    "Agenda_Setting": [
        {"No": "1", "Tanggal": "Tuesday, 01 September 2026", "Program": "Dialog Interaktif Pro 1", "Topik/ Isu": "Kesiapan Pelaksanaan RRI Fest & Bintang Radio Mamuju 2026", "Narasumber": "Ketua Panitia RRI Fest Mamuju", "Jabatan/ Instansi": "Koordinator LPU LPP RRI Mamuju", "KET. Kehadiran": "Hadir di Studio", "PIC Narasumber": "Tim Siaran Pro 1", "Flyer": "https://www.instagram.com/rri_mamuju/", "Bestcut": "https://www.youtube.com/@LPPRRIMamuju", "Keterlaksanaan": "Terlaksana", "Kendala": "-"}
    ],
    "Planner": [
        {"Tanggal_Tayang": "2026-11-17", "Platform": "Instagram & TikTok", "Akun": "@pro2_mamuju", "Judul_Konten": "Teaser Reels Pro 2 Music Live Chat", "Jenis": "Reels / Short Video", "Divisi": "KMB / Pro 2", "PIC": "Tim Kreatif Pro 2", "Status": "Review", "Link_Asset": "https://drive.google.com"}
    ],
    "Siaran": [
        {"Tanggal": "2026-11-17", "Shift": "Pagi (05:00 - 12:00 WITA)", "Programa": "Pro 1 (96.0 FM)", "Penyiar": "Penyiar Shift Pagi A", "Operator": "Operator TMB 1", "Status": "On Duty"}
    ],
    "Program_Siaran": [
        {"Kode_Program": "PRG-P1-01", "Programa": "Pro 1 (96.0 FM)", "Nama_Program": "Mamuju Pagi Ini (Dialog Interaktif)", "Hari": "Senin - Jumat", "Jam_Tayang": "08:00 - 09:00 WITA", "Format": "Dialog & Informasi", "Produser": "Tim Perencanaan & Siaran", "Status": "Aktif"},
        {"Kode_Program": "PRG-P2-01", "Programa": "Pro 2 (89.3 FM)", "Nama_Program": "Pro 2 Music Live Chat", "Hari": "Sabtu", "Jam_Tayang": "16:00 - 17:30 WITA", "Format": "Musik & Talkshow Kreatif", "Produser": "Tim Pro 2 & KMB", "Status": "Aktif"},
    ],
    "Jadwal_TMB": [
        {"Tanggal": "2026-11-17", "Shift": "Pagi (06:00 - 14:00 WITA)", "Lokasi_Pemancar": "Studio & MCR Kantor", "Teknisi_TMB": "A. Mirwan Syam", "Tugas": "Monitoring Tx & Audio Stream", "Status": "On Duty"},
    ],
    "DB_Ruangan": [
        {"Nomor Ruangan": "1.0", "Nama Ruangan": "Lantai 1", "Lokasi": "Kantor RRI Mamuju", "Penanggungjawab Ruangan": "Operator BMN", "Nama": "Muthiah Azizah Ijsam, A.Md.T.", "NIP/ NIPPPK": "NIP. 20011208 202504 2 004"},
        {"Nomor Ruangan": "1.13", "Nama Ruangan": "Gudang TMB", "Lokasi": "Lantai 1", "Penanggungjawab Ruangan": "Ketua Tim Teknologi dan Media Baru", "Nama": "A. Mirwan Syam", "NIP/ NIPPPK": "NIPPPK. 19900608 202221 1 012"},
    ],
    "DB_Aset": [
        {"Kode Ruang": "1.13", "Nomor Kode Barang": "3030205002", "Nama Barang": "Tool Kit Box", "Merk/ Model": "Hand Toolset", "Tahun": "2026", "NUP": "1", "Kondisi": "Baik", "Tindak Lanjut": "", "Keterangan": ""},
    ],
    "DB_Stok_Master": [
        {"Kode Barang": "ATK-001", "Nama Barang": "Kertas HVS F4", "Unit": "Rim", "Stok Awal": 10, "Keterangan": "Kertas F4 70gsm"},
    ],
    "DB_Stok_Masuk": [
        {"Tanggal": "14 Januari 2026", "Penanggung Jawab": "Operator Barang Persediaan", "Nama Barang": "Kertas HVS F4", "Jumlah Masuk": 5, "Unit": "Rim", "Pcs": 5, "Keterangan": "Pengadaan Triwulan I"},
    ],
    "DB_Stok_Keluar": [
        {"Tanggal": "15 Januari 2026", "Nama Barang": "Kertas HVS F4", "Bidang": "Tim Penyiaran", "Penerima Barang": "Meydiana Indah", "Jumlah Keluar": 2, "Unit": "Rim", "Pcs": 2, "Keterangan": "Kebutuhan Naskah Siaran"},
    ],
    "Arsip": [
        {"Kode_Arsip": "PPID-RRI/129/2026", "Tanggal": "2026-08-31", "Kategori": "PPID - Acara Siaran", "Judul": "Rekaman & Naskah Mimbar Agama Hindu (Berkala)", "Divisi": "Siaran / PPID", "Link": "https://mamuju.ppid.rri.go.id/"}
    ],
}


def _parse_service_account_env(raw_val):
    text = raw_val.strip()
    if (text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"')):
        text = text[1:-1].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = text.replace("\\r\\n", "\\n").replace("\r\n", "\\n").replace("\n", "\\n")
        return json.loads(fixed)


class SheetsDB:
    def __init__(self):
        self.sheet_id = _extract_sheet_id(os.getenv("GOOGLE_SHEET_ID", ""))
        self.creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
        self.timeline_tab = os.getenv("TIMELINE_TAB_NAME", "Sheet1").strip()
        self.dialog_tab = os.getenv("DIALOG_TAB_NAME", "Agenda Setting").strip()

        self.client = None
        self.spreadsheet = None
        self.connected = False
        self.last_error = None
        self.service_email = ""
        self._ws_cache = {}
        self._sheet_titles = []
        self._snapshot = {}
        self._snapshot_time = 0
        self._connect()

    def _find_local_sa_file(self):
        for candidate in [
            os.path.join(BASE_DIR, "service_account.json"),
            os.path.join(BASE_DIR, "service_account.json.json"),
            "service_account.json",
        ]:
            if os.path.exists(candidate):
                return candidate
        return None

    def _connect(self):
        if not self.sheet_id:
            self.last_error = "GOOGLE_SHEET_ID belum diisi di .env (Mode Demo)."
            return

        sa_path = self._find_local_sa_file()
        try:
            if sa_path:
                with open(sa_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                self.service_email = info.get("client_email", "")
                creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                self.client = gspread.authorize(creds)
            elif self.creds_json:
                info = _parse_service_account_env(self.creds_json)
                self.service_email = info.get("client_email", "")
                creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                self.client = gspread.authorize(creds)
            else:
                self.last_error = "service_account.json belum ditemukan (Mode Demo)."
                return

            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.connected = True
            self.last_error = None
            self._sync_snapshot(force=True)
        except Exception as e:
            self.connected = False
            self.last_error = f"Gagal koneksi Google Sheet: {e}"
            traceback.print_exc()

    def _sync_snapshot(self, force=False):
        if not self.connected or not self.spreadsheet:
            return
        now = time.time()
        if not force and self._snapshot and (now - self._snapshot_time < CACHE_TTL):
            return

        try:
            worksheets = self.spreadsheet.worksheets()
            self._ws_cache = {ws.title.strip().lower(): ws for ws in worksheets}
            self._sheet_titles = [ws.title for ws in worksheets]

            if not self._sheet_titles:
                return

            ranges = [f"'{title}'" for title in self._sheet_titles]
            batch_res = self.spreadsheet.values_batch_get(ranges=ranges)
            value_ranges = batch_res.get("valueRanges", [])

            new_snap = {}
            for idx, title in enumerate(self._sheet_titles):
                vals = value_ranges[idx].get("values", []) if idx < len(value_ranges) else []
                new_snap[title.strip().lower()] = vals

            self._snapshot = new_snap
            self._snapshot_time = now
            self.last_error = None
        except Exception as e:
            if "429" in str(e):
                print("[SheetsDB] Rate limit 429 hit — serving cached snapshot.")
                self._snapshot_time = now
            else:
                self.last_error = f"Sync warning: {e}"
                traceback.print_exc()

    def clear_cache(self, key=None):
        _CACHE.clear()
        if not self.connected:
            self._connect()
        else:
            self._sync_snapshot(force=True)

    def get_existing_tab_names(self):
        self._sync_snapshot(force=False)
        return list(self._sheet_titles)

    def _find_ws(self, candidates):
        if not self.connected or not self.spreadsheet:
            return None
        if not self._ws_cache:
            self._sync_snapshot(force=True)
        for name in candidates:
            k = name.strip().lower()
            if k in self._ws_cache:
                return self._ws_cache[k]
        return None

    def _get_values_from_snapshot(self, candidates):
        self._sync_snapshot(force=False)
        for name in candidates:
            k = name.strip().lower()
            if k in self._snapshot:
                return self._snapshot[k]
        return None

    # ---------------------------------------------------------
    # ADMIN INITIAL DATA (Resets ONLY Users tab, creates missing tabs)
    # ---------------------------------------------------------
    def init_database_tabs(self, include_sample_rows=True):
        if not self.connected or not self.spreadsheet:
            return False, "Google Sheet utama belum terhubung."

        self._sync_snapshot(force=True)
        created = []
        reset_tabs = []

        for tab_name, headers in TAB_SCHEMAS.items():
            key = tab_name.lower()

            if key == "users":
                if key in self._ws_cache:
                    ws = self._ws_cache[key]
                    ws.clear()
                else:
                    ws = self.spreadsheet.add_worksheet(title=tab_name, rows=200, cols=len(headers) + 2)
                ws.append_row(headers, value_input_option="USER_ENTERED")
                default_users = [[str(u.get(h, "")) for h in headers] for u in DEMO_DATA["Users"]]
                if default_users:
                    ws.append_rows(default_users, value_input_option="USER_ENTERED")
                reset_tabs.append(tab_name)
                continue

            if key in self._ws_cache:
                continue

            ws = self.spreadsheet.add_worksheet(title=tab_name, rows=300, cols=len(headers) + 2)
            ws.append_row(headers, value_input_option="USER_ENTERED")

            if key == "role_modules":
                perm_rows = []
                for r_name in ALL_ROLES:
                    perms = DEFAULT_ROLE_PERMISSIONS.get(r_name, {})
                    perm_rows.append([r_name] + [perms.get(m["key"], "none") for m in ALL_MODULES])
                ws.append_rows(perm_rows, value_input_option="USER_ENTERED")
            elif include_sample_rows and tab_name in DEMO_DATA:
                rows_to_insert = [[str(sample.get(h, "")) for h in headers] for sample in DEMO_DATA[tab_name]]
                if rows_to_insert:
                    ws.append_rows(rows_to_insert, value_input_option="USER_ENTERED")

            created.append(tab_name)

        self.clear_cache()
        parts = []
        if reset_tabs:
            parts.append(f"Tab {', '.join(reset_tabs)} di-reset")
        if created:
            parts.append(f"Tab baru dibuat: {', '.join(created)}")
        if not parts:
            return True, "Tab Users berhasil di-reset. Semua tab master lainnya tetap aman."
        return True, " • ".join(parts) + "."

    # ---------------------------------------------------------
    # ROLE -> MODULE PERMISSIONS MATRIX
    # ---------------------------------------------------------
    def get_role_matrix(self):
        matrix = {r: dict(DEFAULT_ROLE_PERMISSIONS.get(r, {})) for r in ALL_ROLES}
        vals = self._get_values_from_snapshot(["Role_Modules"])
        if not vals:
            return matrix

        for r in _rows_to_dicts(vals):
            role_name = str(r.get("Role", "")).strip()
            if not role_name:
                continue
            matrix.setdefault(role_name, {})
            for m in ALL_MODULES:
                mk = m["key"]
                if mk in r and str(r[mk]).strip():
                    matrix[role_name][mk] = str(r[mk]).strip().lower()
        return matrix

    def update_role_module_permission(self, role_name, module_key, level):
        if level not in {"none", "view", "update", "full"}:
            return False, "Level akses tidak valid."

        DEFAULT_ROLE_PERMISSIONS.setdefault(role_name, {})[module_key] = level
        ws = self._find_ws(["Role_Modules"])
        if not ws:
            return True, f"Akses {role_name} → {module_key} diubah ke '{level}' (Mode Demo)."

        try:
            all_vals = self._get_values_from_snapshot(["Role_Modules"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            if module_key not in headers:
                ws.update_cell(1, len(headers) + 1, module_key)
                headers.append(module_key)
            col_idx = headers.index(module_key) + 1
            found_row = None
            for r_i, row in enumerate(all_vals[1:], start=2):
                if row and row[0].strip().lower() == role_name.strip().lower():
                    found_row = r_i
                    break
            if found_row:
                ws.update_cell(found_row, col_idx, level)
            else:
                new_row = [""] * len(headers)
                new_row[0] = role_name
                new_row[col_idx - 1] = level
                ws.append_row(new_row, value_input_option="USER_ENTERED")
            self._sync_snapshot(force=True)
            return True, f"Hak akses '{role_name}' untuk modul '{module_key}' diubah menjadi '{level}'."
        except Exception as e:
            return False, f"Gagal menyimpan ke Role_Modules: {e}"

    def compute_effective_permissions(self, roles_list):
        rank = {"none": 0, "view": 1, "update": 2, "full": 3}
        inv_rank = {0: "none", 1: "view", 2: "update", 3: "full"}
        matrix = self.get_role_matrix()

        effective = {m["key"]: ("view" if m["key"] == "info_board" else "none") for m in ALL_MODULES}
        for role in roles_list:
            if role.strip().lower() == "admin":
                return {m["key"]: "full" for m in ALL_MODULES}
            perms = matrix.get(role, {})
            for m in ALL_MODULES:
                mk = m["key"]
                cur_lvl = effective.get(mk, "none")
                new_lvl = perms.get(mk, "none")
                if rank.get(new_lvl, 0) > rank.get(cur_lvl, 0):
                    effective[mk] = inv_rank[rank[new_lvl]]
        return effective

    # ---------------------------------------------------------
    # TIMELINE & AGENDA SETTING (DIALOG WITH BESTCUT)
    # ---------------------------------------------------------
    def get_timeline(self):
        vals = self._get_values_from_snapshot([self.timeline_tab, "Sheet1", "Events", "Timeline"])
        if vals is None:
            return DEMO_DATA["Timeline"]
        return _rows_to_dicts(vals)

    def get_agenda_setting(self):
        all_values = self._get_values_from_snapshot([self.dialog_tab, "Agenda Setting", "Dialog"])
        if all_values is None:
            return DEMO_DATA["Agenda_Setting"]
        if not all_values:
            return []

        header_idx = 0
        for idx, row in enumerate(all_values[:10]):
            lowered = [c.strip().lower() for c in row]
            if "tanggal" in lowered and ("program" in lowered or "narasumber" in lowered):
                header_idx = idx
                break
        headers = [h.strip() for h in all_values[header_idx]]
        parsed_rows = []
        last_no = ""
        last_tanggal = ""
        for raw_row_idx, raw_row in enumerate(all_values[header_idx + 1:], start=header_idx + 2):
            padded = raw_row + [""] * (len(headers) - len(raw_row))
            item = {headers[i]: padded[i].strip() for i in range(len(headers)) if headers[i]}
            item["_row_num"] = raw_row_idx
            item.setdefault("Bestcut", "")
            if item.get("No"):
                last_no = item["No"]
            else:
                item["No"] = last_no
            if item.get("Tanggal"):
                last_tanggal = item["Tanggal"]
            else:
                item["Tanggal"] = last_tanggal
            if any([item.get("Program", ""), item.get("Topik/ Isu", ""), item.get("Topik", ""), item.get("Narasumber", "")]):
                parsed_rows.append(item)
        return parsed_rows

    def update_dialog_row(self, row_num, updates_dict):
        ws = self._find_ws([self.dialog_tab, "Agenda Setting", "Dialog"])
        if not ws:
            for d in DEMO_DATA["Agenda_Setting"]:
                d.update(updates_dict)
            return True, "Dialog diperbarui (Mode Demo)."
        try:
            all_values = self._get_values_from_snapshot([self.dialog_tab, "Agenda Setting", "Dialog"]) or ws.get_all_values()
            header_idx = 0
            for idx, row in enumerate(all_values[:10]):
                lowered = [c.strip().lower() for c in row]
                if "tanggal" in lowered and ("program" in lowered or "narasumber" in lowered):
                    header_idx = idx
                    break
            headers = [h.strip() for h in all_values[header_idx]]

            # Auto-create 'Bestcut' header column if not yet present in the Agenda Setting sheet
            if "Bestcut" in updates_dict and "Bestcut" not in headers:
                new_col = len(headers) + 1
                ws.update_cell(header_idx + 1, new_col, "Bestcut")
                headers.append("Bestcut")

            for col_name, new_val in updates_dict.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    ws.update_cell(int(row_num), col_idx, str(new_val))
            self._sync_snapshot(force=True)
            return True, "Data Dialog (termasuk Bestcut) berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui Dialog: {e}"

    def get_tab_records(self, tab_name, include_row_num=False):
        vals = self._get_values_from_snapshot([tab_name])
        if vals is None:
            rows = DEMO_DATA.get(tab_name, [])
            if include_row_num:
                return [dict(r, _row_num=idx) for idx, r in enumerate(rows, start=2)]
            return rows
        return _rows_to_dicts(vals, include_row_num=include_row_num)

    # ---------------------------------------------------------
    # BMN: MASTER ASSET, ROOM & STOCK
    # ---------------------------------------------------------
    def get_rooms(self):
        rooms = self.get_tab_records("DB_Ruangan", include_row_num=True)
        emp_map = {e["nip_clean"]: e for e in self.get_employees() if e.get("nip_clean")}
        enriched = []
        for r in rooms:
            item = dict(r)
            # In DB_Ruangan, `Penanggungjawab Ruangan` stores the NIP/NIPPPK (fallback to `NIP/ NIPPPK` if legacy)
            raw_pj = str(item.get("Penanggungjawab Ruangan", "")).strip()
            raw_legacy_nip = str(item.get("NIP/ NIPPPK", "")).strip()
            candidate = raw_pj if any(ch.isdigit() for ch in raw_pj) else (raw_legacy_nip or raw_pj)
            nip_clean = _normalize_nip(candidate.replace("NIPPPK.", "").replace("NIP.", ""))
            emp = emp_map.get(nip_clean)

            if emp:
                item["pj_nip"] = emp.get("NIP / NIPPK") or candidate
                item["pj_nama"] = emp.get("Nama Pegawai") or "-"
                item["pj_jabatan"] = emp.get("Jabatan") or emp.get("Posisi") or "-"
                item["pj_posisi"] = emp.get("Posisi") or "-"
                item["Nama"] = item["pj_nama"]
            else:
                item["pj_nip"] = candidate or "-"
                item["pj_nama"] = item.get("Nama") or "-"
                item["pj_jabatan"] = "-"
                item["pj_posisi"] = "-"
            item["nip_clean"] = nip_clean
            enriched.append(item)
        return enriched

    def get_assets(self):
        assets = self.get_tab_records("DB_Aset")
        rooms = self.get_rooms()
        room_lookup = {str(rm.get("Nomor Ruangan", "")).strip(): rm.get("Nama Ruangan", "") for rm in rooms}
        enriched = []
        for a in assets:
            item = dict(a)
            kr = str(item.get("Kode Ruang", "")).strip()
            item["Nama Ruangan"] = room_lookup.get(kr, kr or "-")
            enriched.append(item)
        return enriched

    def get_stock_bundle(self):
        master_rows = self.get_tab_records("DB_Stok_Master")
        in_rows = self.get_tab_records("DB_Stok_Masuk")
        out_rows = self.get_tab_records("DB_Stok_Keluar")

        in_totals = {}
        for r in in_rows:
            name = str(r.get("Nama Barang", "")).strip()
            if name:
                qty = _parse_num(r.get("Pcs", r.get("Jumlah Masuk", 0)))
                in_totals[name.lower()] = in_totals.get(name.lower(), 0) + qty

        out_totals = {}
        for r in out_rows:
            name = str(r.get("Nama Barang", "")).strip()
            if name:
                qty = _parse_num(r.get("Pcs", r.get("Jumlah Keluar", 0)))
                out_totals[name.lower()] = out_totals.get(name.lower(), 0) + qty

        computed_master = []
        seen_names = set()
        for m in master_rows:
            name = str(m.get("Nama Barang", "")).strip()
            if not name:
                continue
            key = name.lower()
            seen_names.add(key)
            awal = _parse_num(m.get("Stok Awal", 0))
            masuk = in_totals.get(key, 0)
            keluar = out_totals.get(key, 0)
            akhir = awal + masuk - keluar
            computed_master.append({
                "Kode Barang": m.get("Kode Barang", ""),
                "Nama Barang": name,
                "Unit": m.get("Unit", "Pcs"),
                "Stok Awal": awal,
                "Barang Masuk": masuk,
                "Barang Keluar": keluar,
                "Stok Akhir": akhir,
                "Keterangan": m.get("Keterangan", ""),
            })

        for tx in in_rows + out_rows:
            name = str(tx.get("Nama Barang", "")).strip()
            if name and name.lower() not in seen_names:
                key = name.lower()
                seen_names.add(key)
                masuk = in_totals.get(key, 0)
                keluar = out_totals.get(key, 0)
                computed_master.append({
                    "Kode Barang": "-",
                    "Nama Barang": name,
                    "Unit": tx.get("Unit", "Pcs"),
                    "Stok Awal": 0,
                    "Barang Masuk": masuk,
                    "Barang Keluar": keluar,
                    "Stok Akhir": masuk - keluar,
                    "Keterangan": "Otomatis dari mutasi",
                })

        return {
            "master": computed_master,
            "in_list": list(reversed(in_rows)),
            "out_list": list(reversed(out_rows)),
        }

    # ---------------------------------------------------------
    # EMPLOYEES (SDM EDIT) & USERS
    # ---------------------------------------------------------
    def get_employees(self):
        rows = self.get_tab_records("DB_Pegawai", include_row_num=True)
        result = []
        for idx, r in enumerate(rows, start=2):
            nip = str(r.get("NIP / NIPPK", "")).strip()
            item = dict(r)
            item["_row_num"] = r.get("_row_num") or idx
            item["nip_clean"] = _normalize_nip(nip)
            result.append(item)
        return result

    def update_employee_row(self, row_num, updates_dict):
        ws = self._find_ws(["DB_Pegawai"])
        if not ws:
            for idx, e in enumerate(DEMO_DATA["DB_Pegawai"], start=2):
                if idx == int(row_num or 0) or _normalize_nip(e.get("NIP / NIPPK")) == _normalize_nip(updates_dict.get("NIP / NIPPK")):
                    e.update(updates_dict)
            return True, "Data pegawai diperbarui (Mode Demo)."
        try:
            all_vals = self._get_values_from_snapshot(["DB_Pegawai"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            target_row = int(row_num) if row_num else None

            # Fallback lookup by NIP if row_num is missing
            if not target_row and "NIP / NIPPK" in headers:
                nip_idx = headers.index("NIP / NIPPK")
                target_nip = _normalize_nip(updates_dict.get("NIP / NIPPK", ""))
                for r_i, row in enumerate(all_vals[1:], start=2):
                    if len(row) > nip_idx and _normalize_nip(row[nip_idx]) == target_nip:
                        target_row = r_i
                        break

            if not target_row:
                return False, "Baris pegawai tidak ditemukan di tab DB_Pegawai."

            for col_name, new_val in updates_dict.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    ws.update_cell(target_row, col_idx, str(new_val))
            self._sync_snapshot(force=True)
            return True, "Data pegawai berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui data pegawai: {e}"

    def delete_record(self, target_key, row_num):
        tab_lookup = {
            "Agenda_Setting": [self.dialog_tab, "Agenda Setting", "Dialog"],
            "Info_Board": ["Info_Board", "Info_Pegawai"],
        }
        candidates = tab_lookup.get(target_key, [target_key])
        ws = self._find_ws(candidates)
        if not ws:
            rows = DEMO_DATA.get(target_key, [])
            idx = int(row_num) - 2
            if 0 <= idx < len(rows):
                rows.pop(idx)
            return True, f"Baris dihapus dari {target_key} (Mode Demo)."
        try:
            ws.delete_rows(int(row_num))
            self._sync_snapshot(force=True)
            return True, f"Data berhasil dihapus dari tab '{ws.title}'!"
        except Exception as e:
            return False, f"Gagal menghapus baris: {e}"

    def get_users_list(self):
        rows = self.get_tab_records("Users")
        emp_map = {e["nip_clean"]: e for e in self.get_employees() if e.get("nip_clean")}
        out = []
        for idx, u in enumerate(rows, start=2):
            nip = str(u.get("NIP", u.get("NIP / NIPPPK", ""))).strip()
            nip_clean = _normalize_nip(nip)
            role_raw = str(u.get("Role", "")).strip()
            emp = emp_map.get(nip_clean)
            out.append({
                "row_num": idx,
                "NIP": nip,
                "nip_clean": nip_clean,
                "Nama": emp.get("Nama Pegawai") if emp else "(Belum di DB_Pegawai)",
                "Pangkat": emp.get("Pangkat/ Golongan") if emp else "-",
                "Posisi": emp.get("Posisi") if emp else "-",
                "Jabatan": emp.get("Jabatan") if emp else "-",
                "Status": emp.get("Status") if emp else "Aktif",
                "Role": role_raw,
                "roles_list": parse_roles(role_raw),
            })
        return out

    def authenticate_employee(self, employee_id_input, password_input):
        clean_id = _normalize_nip(employee_id_input)
        pwd = str(password_input or "").strip()
        if not clean_id or not pwd:
            return None

        users = self.get_tab_records("Users")
        matched_user = None
        for u in users:
            u_nip = _normalize_nip(u.get("NIP", u.get("NIP / NIPPPK", "")))
            if u_nip == clean_id and str(u.get("Password", "")).strip() == pwd:
                matched_user = u
                break

        if not matched_user:
            return None

        emp_profile = next((e for e in self.get_employees() if e.get("nip_clean") == clean_id), None)
        combined_roles = parse_roles(matched_user.get("Role", "")) or ["Pegawai"]
        permissions = self.compute_effective_permissions(combined_roles)

        return {
            "nip": (emp_profile.get("NIP / NIPPK") if emp_profile else matched_user.get("NIP", "")),
            "nip_clean": clean_id,
            "nama": (emp_profile.get("Nama Pegawai") if emp_profile else f"Pegawai ({clean_id})"),
            "pangkat": emp_profile.get("Pangkat/ Golongan", "-") if emp_profile else "-",
            "jabatan": emp_profile.get("Jabatan", "Staf") if emp_profile else "Staf",
            "posisi": emp_profile.get("Posisi", "-") if emp_profile else "-",
            "status": emp_profile.get("Status", "Aktif") if emp_profile else "Aktif",
            "divisi": (emp_profile.get("Jabatan") if emp_profile else "Staf") or "Staf",
            "role": "; ".join(combined_roles),
            "roles": combined_roles,
            "permissions": permissions,
        }

    def save_user_account(self, nip_input, password_input, roles_list):
        nip_clean = _normalize_nip(nip_input)
        if not nip_clean:
            return False, "NIP wajib diisi."
        role_str = "; ".join(parse_roles("; ".join(roles_list))) if isinstance(roles_list, list) else str(roles_list).strip()
        if not role_str:
            role_str = "Pegawai"

        ws_usr = self._find_ws(["Users"])
        if not ws_usr:
            existing = next((u for u in DEMO_DATA["Users"] if _normalize_nip(u.get("NIP", "")) == nip_clean), None)
            if existing:
                if password_input:
                    existing["Password"] = password_input
                existing["Role"] = role_str
            else:
                DEMO_DATA["Users"].append({"NIP": nip_clean, "Password": password_input or "rri2026", "Role": role_str})
        else:
            try:
                all_vals = self._get_values_from_snapshot(["Users"]) or ws_usr.get_all_values()
                headers = [h.strip() for h in all_vals[0]] if all_vals else ["NIP", "Password", "Role"]
                nip_idx = headers.index("NIP") if "NIP" in headers else 0
                pwd_idx = headers.index("Password") if "Password" in headers else 1
                role_idx = headers.index("Role") if "Role" in headers else 2

                found_row = None
                for r_i, row in enumerate(all_vals[1:], start=2):
                    if len(row) > nip_idx and _normalize_nip(row[nip_idx]) == nip_clean:
                        found_row = r_i
                        break

                if found_row:
                    if password_input:
                        ws_usr.update_cell(found_row, pwd_idx + 1, password_input)
                    ws_usr.update_cell(found_row, role_idx + 1, role_str)
                else:
                    ws_usr.append_row([nip_clean, password_input or "rri2026", role_str], value_input_option="USER_ENTERED")
            except Exception as e:
                return False, f"Gagal menyimpan ke tab Users: {e}"

        self._sync_snapshot(force=True)
        return True, f"Akun user ({nip_clean}) dengan role [{role_str}] berhasil disimpan."

    # ---------------------------------------------------------
    # GENERIC APPEND FOR MODULES
    # ---------------------------------------------------------
    def append_record(self, target_key, row_dict):
        tab_lookup = {
            "Timeline": [self.timeline_tab, "Sheet1", "Events"],
            "Agenda_Setting": [self.dialog_tab, "Agenda Setting", "Dialog"],
            "Info_Board": ["Info_Board", "Info_Pegawai"],
        }
        candidates = tab_lookup.get(target_key, [target_key])
        ws = self._find_ws(candidates)

        if not ws:
            DEMO_DATA.setdefault(target_key, []).append(row_dict)
            return True, f"Disimpan sementara ke {target_key} (Klik 'Initial Data' sebagai Admin untuk membuat tab di Google Sheet)."

        try:
            snap_vals = self._get_values_from_snapshot(candidates)
            headers = [h.strip() for h in snap_vals[0]] if (snap_vals and snap_vals[0]) else [h.strip() for h in ws.row_values(1)]

            # Ensure Bestcut column exists if adding a new Agenda_Setting row with Bestcut
            if target_key == "Agenda_Setting" and "Bestcut" in row_dict and "Bestcut" not in headers:
                all_v = snap_vals or ws.get_all_values()
                h_idx = 0
                for idx, r in enumerate(all_v[:10]):
                    if "tanggal" in [c.strip().lower() for c in r]:
                        h_idx = idx
                        break
                headers = [h.strip() for h in all_v[h_idx]]
                if "Bestcut" not in headers:
                    ws.update_cell(h_idx + 1, len(headers) + 1, "Bestcut")
                    headers.append("Bestcut")

            if target_key == "DB_Ruangan":
                raw_nip = str(row_dict.get("Penanggungjawab Ruangan", "") or row_dict.get("NIP/ NIPPPK", "")).replace("NIPPPK.", "").replace("NIP.", "").strip()
                nip_clean = _normalize_nip(raw_nip)
                row_dict["Penanggungjawab Ruangan"] = nip_clean
                emp = next((e for e in self.get_employees() if e.get("nip_clean") == nip_clean), None)
                if emp:
                    row_dict["Nama"] = emp.get("Nama Pegawai", "")
                    row_dict["NIP/ NIPPPK"] = emp.get("NIP / NIPPK", nip_clean)

            row_values = [str(row_dict.get(h, "")) for h in headers]
            ws.append_row(row_values, value_input_option="USER_ENTERED")
            self._sync_snapshot(force=True)
            return True, f"Data berhasil disimpan ke tab '{ws.title}'!"
        except Exception as e:
            return False, f"Gagal menyimpan ke '{ws.title}': {e}"
