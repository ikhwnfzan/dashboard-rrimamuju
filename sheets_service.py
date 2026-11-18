import os
import json
import time
import threading
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
    "LPU": {"info_board": "view"},
    "Berita": {"info_board": "view"},
    "Keuangan": {"info_board": "view"},
    "Pimpinan": {"info_board": "view", "data_pegawai": "view", "dialog": "view", "jadwal_siaran": "view", "program_siaran": "view"},
    "Kasubag TU": {"info_board": "view", "data_pegawai": "view", "master_barang": "view", "master_persediaan": "view"},
}

APP_CONFIG_DEFAULTS = {
    "timezone": "Asia/Makassar",
    "language": "id",
    "default_theme": "light",
}

APP_CONFIG_DESCRIPTIONS = {
    "timezone": "Zona waktu untuk waktu sinkronisasi aplikasi.",
    "language": "Preferensi bahasa untuk dukungan lokalisasi mendatang.",
    "default_theme": "Tema dashboard yang digunakan untuk semua pengguna.",
}

# Unified Database (`DB_*`) & Configuration (`CFG_*`) Schemas with standardized Title Case Headers
TAB_SCHEMAS = {
    "CFG_Users": ["NIP", "Password", "Role"],
    "CFG_Role_Modules": ["Role"] + [m["key"] for m in ALL_MODULES],
    "CFG_App": ["Key", "Value", "Description"],
    "DB_Timeline": ["Kegiatan", "Tahapan", "Tanggal Mulai", "Tanggal Selesai", "Keterangan", "Tanggal"],
    "DB_Dialog": ["No", "Tanggal", "Program", "Topik", "Narasumber", "Foto Narasumber", "Jabatan", "Kehadiran", "PIC Narasumber", "Flyer", "Bestcut", "Keterlaksanaan", "Kendala"],
    "DB_Siaran": ["Tanggal", "Shift", "Programa", "Penyiar", "Operator", "Status"],
    "DB_Program": ["Kode Program", "Programa", "Nama Program", "Hari", "Jam", "Format", "Produser", "Status"],
    "DB_Konten": ["ID", "Tanggal Tayang", "Platform", "Akun", "Judul Konten", "Jenis", "Divisi", "PIC", "Status", "Link Asset"],
    "DB_Jadwal_TMB": ["Tanggal", "Shift", "Lokasi Pemancar", "Teknisi TMB", "Tugas", "Status"],
    "DB_Pegawai": ["No", "Nama Pegawai", "NIP", "Pangkat Golongan", "Jabatan", "Status", "Posisi"],
    "DB_Arsip_SDM": ["Nomor Dokumen", "Nama Dokumen", "Tanggal", "Jenis", "Link"],
    "DB_Info_Board": ["Tanggal", "Prioritas", "Judul", "Isi", "Target Divisi", "Lampiran"],
    "DB_Ruangan": ["Nomor Ruangan", "Nama Ruangan", "Lokasi", "NIP Penanggung Jawab"],
    "DB_Aset": ["Nomor Kode Barang", "Kode Ruang", "Nama Barang", "Merk Model", "Tahun", "NUP", "Kondisi", "Tindak Lanjut", "Keterangan"],
    "DB_Stok_Master": ["Kode Barang", "Nama Barang", "Unit", "Stok Awal", "Keterangan"],
    "DB_Stok_Masuk": ["Tanggal", "Penanggung Jawab", "Nama Barang", "Jumlah Masuk", "Unit", "Pcs", "Keterangan"],
    "DB_Stok_Keluar": ["Tanggal", "Nama Barang", "Bidang", "Penerima Barang", "Jumlah Keluar", "Unit", "Pcs", "Keterangan"],
}

AUTO_ID_FIELDS = {
    "DB_Pegawai": ("No", ""),
    "DB_Dialog": ("No", ""),
    "DB_Konten": ("ID", "CNT-"),
}
AUTO_ID_LOCK = threading.Lock()

# Maps legacy tab titles -> new standardized tab titles for automatic migration on Initial Data
LEGACY_TAB_RENAMES = {
    "sheet1": "DB_Timeline",
    "agenda setting": "DB_Dialog",
    "siaran": "DB_Siaran",
    "jadwal_tmb": "DB_Jadwal_TMB",
    "arsip_sdm": "DB_Arsip_SDM",
    "info_board": "DB_Info_Board",
    "users": "CFG_Users",
    "role_modules": "CFG_Role_Modules",
}

# Maps legacy column header aliases -> standardized Title Case header
HEADER_ALIASES = {
    "start date": "Tanggal Mulai",
    "end date": "Tanggal Selesai",
    "topik/ isu": "Topik",
    "jabatan/ instansi": "Jabatan",
    "ket. kehadiran": "Kehadiran",
    "tanggal_tayang": "Tanggal Tayang",
    "judul_konten": "Judul Konten",
    "link_asset": "Link Asset",
    "jam_tayang": "Jam",
    "kode_program": "Kode Program",
    "nama_program": "Nama Program",
    "lokasi_pemancar": "Lokasi Pemancar",
    "teknisi_tmb": "Teknisi TMB",
    "nip / nippk": "NIP",
    "nip / nippk": "NIP",
    "pangkat/ golongan": "Pangkat Golongan",
    "target_divisi": "Target Divisi",
    "penanggungjawab ruangan": "NIP Penanggung Jawab",
    "merk/ model": "Merk Model",
}

DEMO_DATA = {
    "CFG_Users": [
        {"NIP": "199806212025041001", "Password": "rri2026", "Role": "Admin; TMB"},
        {"NIP": "200112082025042004", "Password": "bmn2026", "Role": "TMB; BMN"},
        {"NIP": "199203252024212001", "Password": "sdm2026", "Role": "SDM"},
        {"NIP": "199210252025042002", "Password": "ren2026", "Role": "Siaran; Perencanaan"},
        {"NIP": "199010302022211010", "Password": "kmb2026", "Role": "KMB; Siaran"},
    ],
    "DB_Timeline": [
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pendaftaran dibuka", "Tanggal Mulai": "08/01/2026", "Tanggal Selesai": "08/01/2026", "Keterangan": "Online & Kantor LPP RRI Mamuju", "Tanggal": "1 Agustus 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Bersih-Bersih Lingkungan", "Tanggal Mulai": "08/28/2026", "Tanggal Selesai": "08/28/2026", "Keterangan": "Pantai Manakarra", "Tanggal": "28 Agustus 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Upacara dan Penyuluhan Obor", "Tanggal Mulai": "09/11/2026", "Tanggal Selesai": "09/11/2026", "Keterangan": "Auditorium LPP RRI Mamuju", "Tanggal": "11 September 2026"},
    ],
    "DB_Dialog": [
        {"No": "1", "Tanggal": "Tuesday, 01 September 2026", "Program": "Dialog Interaktif Pro 1", "Topik": "Kesiapan Pelaksanaan RRI Fest & Bintang Radio Mamuju 2026", "Narasumber": "Ketua Panitia RRI Fest Mamuju", "Foto Narasumber": "", "Jabatan": "Koordinator LPU LPP RRI Mamuju", "Kehadiran": "Hadir di Studio", "PIC Narasumber": "Tim Siaran Pro 1", "Flyer": "https://www.instagram.com/rri_mamuju/", "Bestcut": "https://www.youtube.com/@LPPRRIMamuju", "Keterlaksanaan": "Terlaksana", "Kendala": "-"}
    ],
    "DB_Siaran": [
        {"Tanggal": "2026-11-17", "Shift": "Pagi (05:00 - 12:00 WITA)", "Programa": "Pro 1 (96.0 FM)", "Penyiar": "Penyiar Shift Pagi A", "Operator": "Operator TMB 1", "Status": "On Duty"}
    ],
    "DB_Program": [
        {"Kode Program": "PRG-P1-01", "Programa": "Pro 1", "Nama Program": "Halo Sulbar", "Hari": "Setiap Hari", "Jam": "09:00 - 10:00 WITA", "Format": "Dialog", "Produser": "Pengelola Pro 1", "Status": "Aktif"},
        {"Kode Program": "PRG-P2-03", "Programa": "Pro 2", "Nama Program": "Music Live Chat", "Hari": "Sabtu", "Jam": "19:00 - 20:00 WITA", "Format": "Dialog & Live Music", "Produser": "Sugiyanto", "Status": "Aktif"},
    ],
    "DB_Konten": [
        {"ID": "CNT-01", "Tanggal Tayang": "2026-11-17", "Platform": "Instagram & TikTok", "Akun": "@pro2_mamuju", "Judul Konten": "Teaser Reels Pro 2 Music Live Chat", "Jenis": "Reels / Short Video", "Divisi": "KMB / Pro 2", "PIC": "Tim Kreatif Pro 2", "Status": "Review", "Link Asset": "https://drive.google.com"}
    ],
    "DB_Jadwal_TMB": [
        {"Tanggal": "2026-11-17", "Shift": "Pagi (06:00 - 14:00 WITA)", "Lokasi Pemancar": "Studio & MCR Kantor", "Teknisi TMB": "A. Mirwan Syam", "Tugas": "Monitoring Tx & Audio Stream", "Status": "On Duty"},
    ],
    "DB_Pegawai": [
        {"No": "1", "Nama Pegawai": "Rina Irfantini, S.H., M.Si.", "NIP": "197312051999032007", "Pangkat Golongan": "Pembina Tk.I IV/b", "Jabatan": "Kepala Stasiun", "Status": "Aktif", "Posisi": "Kepala Stasiun LPP RRI Mamuju"},
        {"No": "2", "Nama Pegawai": "Muhamad Dirsan, S.E.", "NIP": "197506231998031002", "Pangkat Golongan": "Penata Tk.I III/d", "Jabatan": "Kepala Sub Bagian Tata Usaha", "Status": "Aktif", "Posisi": "Kepala Sub Bagian Tata Usaha"},
        {"No": "9", "Nama Pegawai": "Ikhwan Fauzan, A.Md.T", "NIP": "199806212025041001", "Pangkat Golongan": "Pengatur II/c", "Jabatan": "Asisten Teknisi Siaran Terampil", "Status": "Aktif", "Posisi": "Staf"},
        {"No": "14", "Nama Pegawai": "Muthiah Azizah Ijsam, A.Md.T", "NIP": "200112082025042004", "Pangkat Golongan": "Pengatur II/c", "Jabatan": "Asisten Teknisi Siaran Terampil", "Status": "Aktif", "Posisi": "Staf"},
    ],
    "DB_Arsip_SDM": [
        {"Nomor Dokumen": "SK-014/RRI-MMJ/SDM/2026", "Nama Dokumen": "SK Tim Pengelola BMN & Persediaan 2026", "Tanggal": "2026-01-10", "Jenis": "Surat Keputusan", "Link": "https://drive.google.com"},
    ],
    "DB_Info_Board": [
        {"Tanggal": "2026-11-17", "Prioritas": "Urgent", "Judul": "Pemutakhiran Data Kepegawaian & SK Jabatan", "Isi": "Seluruh pegawai dimohon mengecek kesesuaian NIP, Pangkat/Golongan, dan Jabatan pada modul Data Pegawai.", "Target Divisi": "Semua Pegawai", "Lampiran": ""}
    ],
    "DB_Ruangan": [
        {"Nomor Ruangan": "1", "Nama Ruangan": "Lantai 1", "Lokasi": "Kantor RRI Mamuju", "NIP Penanggung Jawab": "200112082025042004"},
        {"Nomor Ruangan": "1.13", "Nama Ruangan": "Gudang TMB", "Lokasi": "Lantai 1", "NIP Penanggung Jawab": "199006082022211012"},
    ],
    "DB_Aset": [
        {"Nomor Kode Barang": "3030205002", "Kode Ruang": "1.13", "Nama Barang": "Tool Kit Box", "Merk Model": "Hand Toolset", "Tahun": "2026", "NUP": "1", "Kondisi": "Baik", "Tindak Lanjut": "", "Keterangan": ""},
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
        self.timeline_tab = os.getenv("TIMELINE_TAB_NAME", "DB_Timeline").strip()
        self.dialog_tab = os.getenv("DIALOG_TAB_NAME", "DB_Dialog").strip()

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
    # ADMIN INITIAL DATA (REFACTOR + NON-DESTRUCTIVE MIGRATION):
    # 1. Renames legacy tabs (`Sheet1` -> `DB_Timeline`, `Agenda Setting` -> `DB_Dialog`, etc.) if target `DB_*`/`CFG_*` doesn't exist yet.
    # 2. Normalizes Row 1 headers across all `DB_*` & `CFG_*` tabs to clean Title Case (keeping all existing data rows intact!).
    # 3. Resets ONLY `CFG_Users` to default accounts (never touches `DB_Pegawai` or any `DB_*` data).
    # 4. Syncs `CFG_Role_Modules` columns (`program_siaran`, `persediaan_masuk`, `persediaan_keluar`).
    # ---------------------------------------------------------
    def init_database_tabs(self, include_sample_rows=True):
        if not self.connected or not self.spreadsheet:
            return False, "Google Sheet utama belum terhubung."

        self._sync_snapshot(force=True)
        migrated = []
        created = []
        reset_tabs = []

        # Step 1: Migrate legacy tab names to standardized `DB_*` / `CFG_*` names
        for old_lower, new_title in LEGACY_TAB_RENAMES.items():
            new_lower = new_title.lower()
            if old_lower in self._ws_cache and new_lower not in self._ws_cache:
                try:
                    ws = self._ws_cache[old_lower]
                    ws.update_title(new_title)
                    del self._ws_cache[old_lower]
                    self._ws_cache[new_lower] = ws
                    migrated.append(f"{old_lower}→{new_title}")
                except Exception as e:
                    print(f"[InitData] Rename warning ({old_lower} -> {new_title}):", e)

        self._sync_snapshot(force=True)

        # Step 2: Ensure every standardized tab exists and has clean Title Case Row 1 headers
        for tab_name, target_headers in TAB_SCHEMAS.items():
            key = tab_name.lower()

            # Reset ONLY CFG_Users
            if key == "cfg_users":
                if key in self._ws_cache:
                    ws = self._ws_cache[key]
                    ws.clear()
                else:
                    ws = self.spreadsheet.add_worksheet(title=tab_name, rows=200, cols=len(target_headers) + 2)
                ws.append_row(target_headers, value_input_option="USER_ENTERED")
                default_users = [[str(u.get(h, "")) for h in target_headers] for u in DEMO_DATA["CFG_Users"]]
                if default_users:
                    ws.append_rows(default_users, value_input_option="USER_ENTERED")
                reset_tabs.append(tab_name)
                continue

            if key == "cfg_app":
                default_rows = [
                    [setting_key, value, APP_CONFIG_DESCRIPTIONS[setting_key]]
                    for setting_key, value in APP_CONFIG_DEFAULTS.items()
                ]
                if key not in self._ws_cache:
                    ws = self.spreadsheet.add_worksheet(title=tab_name, rows=50, cols=len(target_headers) + 2)
                    ws.append_row(target_headers, value_input_option="USER_ENTERED")
                    ws.append_rows(default_rows, value_input_option="USER_ENTERED")
                    created.append(tab_name)
                else:
                    ws = self._ws_cache[key]
                    cur_vals = self._snapshot.get(key) or ws.get_all_values()
                    if not cur_vals:
                        ws.append_row(target_headers, value_input_option="USER_ENTERED")
                        ws.append_rows(default_rows, value_input_option="USER_ENTERED")
                        created.append(tab_name)
                continue

            # Ensure CFG_Role_Modules has exact 17 standardized module columns (migrating existing permissions + splitting persediaan_mutasi)
            if key == "cfg_role_modules":
                if key not in self._ws_cache:
                    ws = self.spreadsheet.add_worksheet(title=tab_name, rows=50, cols=len(target_headers) + 4)
                    ws.append_row(target_headers, value_input_option="USER_ENTERED")
                    perm_rows = []
                    for r_name in ALL_ROLES:
                        perms = DEFAULT_ROLE_PERMISSIONS.get(r_name, {})
                        perm_rows.append([r_name] + [perms.get(m["key"], "none") for m in ALL_MODULES])
                    ws.append_rows(perm_rows, value_input_option="USER_ENTERED")
                    created.append(tab_name)
                else:
                    ws = self._ws_cache[key]
                    cur_vals = self._snapshot.get(key) or ws.get_all_values()
                    existing_by_role = {}
                    if cur_vals and len(cur_vals) > 1:
                        old_hdrs = [h.strip() for h in cur_vals[0]]
                        for row in cur_vals[1:]:
                            if not row or not row[0].strip():
                                continue
                            r_name = row[0].strip()
                            row_dict = {old_hdrs[i]: row[i].strip().lower() for i in range(min(len(old_hdrs), len(row))) if old_hdrs[i]}
                            # Migrate legacy persediaan_mutasi -> persediaan_masuk & persediaan_keluar
                            if "persediaan_mutasi" in row_dict:
                                row_dict.setdefault("persediaan_masuk", row_dict["persediaan_mutasi"])
                                row_dict.setdefault("persediaan_keluar", row_dict["persediaan_mutasi"])
                            existing_by_role[r_name] = row_dict

                    # Ensure grid has enough columns before writing
                    if ws.col_count < len(target_headers):
                        ws.resize(rows=max(ws.row_count, 50), cols=len(target_headers) + 4)

                    rebuilt_matrix = [target_headers]
                    seen_roles = set()
                    for r_name in ALL_ROLES:
                        seen_roles.add(r_name.lower())
                        saved_map = existing_by_role.get(r_name, {})
                        def_map = DEFAULT_ROLE_PERMISSIONS.get(r_name, {})
                        rebuilt_matrix.append([
                            r_name
                        ] + [
                            saved_map.get(m["key"]) or def_map.get(m["key"], "none")
                            for m in ALL_MODULES
                        ])
                    # Preserve any custom roles that existed in the sheet
                    for r_name, saved_map in existing_by_role.items():
                        if r_name.lower() not in seen_roles:
                            rebuilt_matrix.append([r_name] + [saved_map.get(m["key"], "none") for m in ALL_MODULES])

                    ws.clear()
                    ws.update("A1", rebuilt_matrix, value_input_option="USER_ENTERED")
                continue

            # Existing DB_* tab: standardize Row 1 header names in-place without touching data rows!
            if key in self._ws_cache:
                ws = self._ws_cache[key]
                cur_vals = self._snapshot.get(key) or []
                if cur_vals:
                    cur_row1 = cur_vals[0]
                    updated_row1 = []
                    changed_hdr = False
                    for h in cur_row1:
                        h_clean = str(h).strip()
                        mapped = HEADER_ALIASES.get(h_clean.lower(), h_clean)
                        if mapped != h_clean:
                            changed_hdr = True
                        updated_row1.append(mapped)
                    if changed_hdr:
                        ws.update("1:1", [updated_row1], value_input_option="USER_ENTERED")
                continue

            # Create missing DB_* tab
            ws = self.spreadsheet.add_worksheet(title=tab_name, rows=300, cols=len(target_headers) + 2)
            ws.append_row(target_headers, value_input_option="USER_ENTERED")
            if include_sample_rows and tab_name in DEMO_DATA:
                rows_to_insert = [[str(sample.get(h, "")) for h in target_headers] for sample in DEMO_DATA[tab_name]]
                if rows_to_insert:
                    ws.append_rows(rows_to_insert, value_input_option="USER_ENTERED")
            created.append(tab_name)

        self.clear_cache()
        parts = []
        if reset_tabs:
            parts.append(f"Tabel {', '.join(reset_tabs)} di-reset")
        if migrated:
            parts.append(f"Tabel direfaktor: {', '.join(migrated)}")
        if created:
            parts.append(f"Tabel baru dibuat: {', '.join(created)}")
        if not parts:
            return True, "Tabel Users di-reset & header seluruh tabel sudah terstandarisasi"
        return True, " • ".join(parts) + "."

    # ---------------------------------------------------------
    # ROLE -> MODULE PERMISSIONS MATRIX
    # ---------------------------------------------------------
    def get_app_settings(self):
        values = self._get_values_from_snapshot(["CFG_App"])
        if values is None and self.connected:
            self._sync_snapshot(force=True)
            values = self._snapshot.get("cfg_app")

        stored = {}
        for row in _rows_to_dicts(values):
            key = str(row.get("key", "")).strip()
            if key:
                stored[key.lower()] = row

        settings = []
        for key, default_value in APP_CONFIG_DEFAULTS.items():
            saved = stored.pop(key.lower(), {})
            settings.append({
                "key": key,
                "value": str(saved.get("value", "")).strip() or default_value,
                "description": str(saved.get("description", "")).strip() or APP_CONFIG_DESCRIPTIONS[key],
            })
        settings.extend(
            {
                "key": str(row.get("key", "")).strip(),
                "value": str(row.get("value", "")).strip(),
                "description": str(row.get("description", "")).strip(),
            }
            for row in stored.values()
        )
        return settings

    def save_app_settings(self, settings):
        if not self.connected or not self.spreadsheet:
            return False, "Google Sheet utama belum terhubung; pengaturan tidak disimpan."
        if not isinstance(settings, dict) or set(settings) != set(APP_CONFIG_DEFAULTS):
            return False, "Data pengaturan aplikasi tidak lengkap atau tidak valid."

        ws = self._find_ws(["CFG_App"])
        if not ws:
            self._sync_snapshot(force=True)
            ws = self._find_ws(["CFG_App"])
        if not ws:
            return False, "Tab CFG_App tidak ditemukan. Jalankan Initial Data sebagai Admin terlebih dahulu."

        try:
            values = self._get_values_from_snapshot(["CFG_App"]) or ws.get_all_values()
            if not values:
                headers = list(TAB_SCHEMAS["CFG_App"])
                if ws.col_count < len(headers):
                    ws.resize(rows=max(ws.row_count, 50), cols=len(headers))
                ws.append_row(headers, value_input_option="USER_ENTERED")
                values = [headers]

            headers = [str(header).strip() for header in values[0]]
            columns = {header.lower(): index + 1 for index, header in enumerate(headers) if header}
            required_columns = {"key", "value", "description"}
            if not required_columns.issubset(columns):
                return False, "Header tabel harus memiliki kolom Key, Value, dan Description."
            if ws.col_count < len(headers):
                ws.resize(rows=max(ws.row_count, 50), cols=len(headers) + 2)

            row_by_key = {}
            for row_num, row in enumerate(values[1:], start=2):
                key_index = columns["key"] - 1
                key = row[key_index].strip().lower() if len(row) > key_index else ""
                if key:
                    row_by_key.setdefault(key, row_num)

            for key, value in settings.items():
                row_num = row_by_key.get(key.lower())
                if row_num:
                    ws.update_cell(row_num, columns["value"], value)
                    ws.update_cell(row_num, columns["description"], APP_CONFIG_DESCRIPTIONS[key])
                else:
                    new_row = [""] * len(headers)
                    new_row[columns["key"] - 1] = key
                    new_row[columns["value"] - 1] = value
                    new_row[columns["description"] - 1] = APP_CONFIG_DESCRIPTIONS[key]
                    ws.append_row(new_row, value_input_option="USER_ENTERED")

            self._sync_snapshot(force=True)
            return True, "Pengaturan aplikasi berhasil disimpan!"
        except Exception as e:
            return False, f"Gagal menyimpan pengaturan: {e}"

    def get_role_matrix(self):
        matrix = {r: dict(DEFAULT_ROLE_PERMISSIONS.get(r, {})) for r in ALL_ROLES}
        vals = self._get_values_from_snapshot(["CFG_Role_Modules", "Role_Modules"])
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
        ws = self._find_ws(["CFG_Role_Modules", "Role_Modules"])
        if not ws:
            return True, f"Akses {role_name} → {module_key} diubah ke '{level}' (Mode Demo)."

        try:
            all_vals = self._get_values_from_snapshot(["CFG_Role_Modules", "Role_Modules"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            if module_key not in headers:
                if ws.col_count < len(headers) + 1:
                    ws.resize(rows=max(ws.row_count, 50), cols=len(headers) + 4)
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
            return False, f"Gagal menyimpan ke CFG_Role_Modules: {e}"

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
    # TIMELINE & DIALOG (SUPPORTS BOTH REFACTORED & LEGACY HEADERS)
    # ---------------------------------------------------------
    def get_timeline(self):
        vals = self._get_values_from_snapshot(["DB_Timeline", self.timeline_tab, "Sheet1", "Timeline"])
        if vals is None:
            return [dict(row, _row_num=idx) for idx, row in enumerate(DEMO_DATA["DB_Timeline"], start=2)]
        rows = _rows_to_dicts(vals, include_row_num=True)
        for r in rows:
            r.setdefault("Tanggal Mulai", r.get("Start Date", ""))
            r.setdefault("Tanggal Selesai", r.get("End Date", ""))
        return rows

    def update_timeline_row(self, row_num, updates_dict):
        try:
            target_row = int(row_num)
            if target_row < 2:
                return False, "Nomor baris timeline tidak valid."
        except (TypeError, ValueError):
            return False, "Nomor baris timeline tidak valid."

        if not self._find_ws(["DB_Timeline", self.timeline_tab, "Sheet1", "Timeline"]):
            rows = DEMO_DATA["DB_Timeline"]
            idx = target_row - 2
            if idx < 0 or idx >= len(rows):
                return False, "Baris timeline tidak ditemukan."
            rows[idx].update(updates_dict)
            return True, "Timeline diperbarui (Mode Demo)."

        ws = self._find_ws(["DB_Timeline", self.timeline_tab, "Sheet1", "Timeline"])
        try:
            all_values = self._get_values_from_snapshot(
                ["DB_Timeline", self.timeline_tab, "Sheet1", "Timeline"]
            ) or ws.get_all_values()
            headers = [header.strip() for header in all_values[0]] if all_values else []
            col_fallbacks = {
                "Tanggal Mulai": ["Tanggal Mulai", "Start Date"],
                "Tanggal Selesai": ["Tanggal Selesai", "End Date"],
            }
            updated_columns = 0
            for col_name, new_val in updates_dict.items():
                for candidate in col_fallbacks.get(col_name, [col_name]):
                    if candidate in headers:
                        ws.update_cell(target_row, headers.index(candidate) + 1, str(new_val))
                        updated_columns += 1
                        break
            if not updated_columns:
                return False, "Kolom timeline yang akan diperbarui tidak ditemukan."
            self._sync_snapshot(force=True)
            return True, "Data timeline berhasil diperbarui."
        except Exception as e:
            return False, f"Gagal memperbarui timeline: {e}"

    def get_agenda_setting(self):
        all_values = self._get_values_from_snapshot(["DB_Dialog", self.dialog_tab, "Agenda Setting", "Dialog"])
        if all_values is None:
            return DEMO_DATA["DB_Dialog"]
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
            # Normalize keys so frontend works seamlessly before and after header rename
            item["Topik"] = item.get("Topik") or item.get("Topik/ Isu") or ""
            item["Jabatan"] = item.get("Jabatan") or item.get("Jabatan/ Instansi") or ""
            item["Kehadiran"] = item.get("Kehadiran") or item.get("KET. Kehadiran") or ""
            item.setdefault("Bestcut", "")
            if item.get("No"):
                last_no = item["No"]
            else:
                item["No"] = last_no
            if item.get("Tanggal"):
                last_tanggal = item["Tanggal"]
            else:
                item["Tanggal"] = last_tanggal
            if any([item.get("Program", ""), item.get("Topik", ""), item.get("Narasumber", "")]):
                parsed_rows.append(item)
        return parsed_rows

    def update_dialog_row(self, row_num, updates_dict):
        ws = self._find_ws(["DB_Dialog", self.dialog_tab, "Agenda Setting", "Dialog"])
        if not ws:
            for d in DEMO_DATA["DB_Dialog"]:
                d.update(updates_dict)
            return True, "Dialog diperbarui (Mode Demo)."
        try:
            all_values = self._get_values_from_snapshot(["DB_Dialog", self.dialog_tab, "Agenda Setting", "Dialog"]) or ws.get_all_values()
            header_idx = 0
            for idx, row in enumerate(all_values[:10]):
                lowered = [c.strip().lower() for c in row]
                if "tanggal" in lowered and ("program" in lowered or "narasumber" in lowered):
                    header_idx = idx
                    break
            headers = [h.strip() for h in all_values[header_idx]]

            if "Bestcut" in updates_dict and "Bestcut" not in headers:
                new_col = len(headers) + 1
                ws.update_cell(header_idx + 1, new_col, "Bestcut")
                headers.append("Bestcut")

            # Map normalized keys to whichever header is currently in the sheet
            col_fallbacks = {
                "Topik": ["Topik", "Topik/ Isu"],
                "Kehadiran": ["Kehadiran", "KET. Kehadiran"],
                "Jabatan": ["Jabatan", "Jabatan/ Instansi"],
            }
            for col_name, new_val in updates_dict.items():
                candidates = col_fallbacks.get(col_name, [col_name])
                for cand in candidates:
                    if cand in headers:
                        col_idx = headers.index(cand) + 1
                        ws.update_cell(int(row_num), col_idx, str(new_val))
                        break
            self._sync_snapshot(force=True)
            return True, "Data Dialog berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui Dialog: {e}"

    def get_tab_records(self, candidates, include_row_num=False):
        if isinstance(candidates, str):
            candidates = [candidates]
        vals = self._get_values_from_snapshot(candidates)
        if vals is None:
            rows = DEMO_DATA.get(candidates[0], [])
            if include_row_num:
                return [dict(r, _row_num=idx) for idx, r in enumerate(rows, start=2)]
            return rows
        return _rows_to_dicts(vals, include_row_num=include_row_num)

    # ---------------------------------------------------------
    # BMN: MASTER ASSET, ROOM & STOCK
    # ---------------------------------------------------------
    def get_rooms(self):
        rooms = self.get_tab_records(["DB_Ruangan"], include_row_num=True)
        emp_map = {e["nip_clean"]: e for e in self.get_employees() if e.get("nip_clean")}
        enriched = []
        for r in rooms:
            item = dict(r)
            raw_pj = str(item.get("NIP Penanggung Jawab", "") or item.get("Penanggungjawab Ruangan", "")).strip()
            nip_clean = _normalize_nip(raw_pj.replace("NIPPPK.", "").replace("NIP.", ""))
            emp = emp_map.get(nip_clean)
            item["NIP Penanggung Jawab"] = raw_pj
            if emp:
                item["pj_nip"] = emp.get("NIP") or raw_pj
                item["pj_nama"] = emp.get("Nama Pegawai") or "-"
                item["pj_jabatan"] = emp.get("Jabatan") or emp.get("Posisi") or "-"
                item["pj_posisi"] = emp.get("Posisi") or "-"
            else:
                item["pj_nip"] = raw_pj or "-"
                item["pj_nama"] = "-"
                item["pj_jabatan"] = "-"
                item["pj_posisi"] = "-"
            item["nip_clean"] = nip_clean
            enriched.append(item)
        return enriched

    def get_assets(self):
        assets = self.get_tab_records(["DB_Aset"])
        rooms = self.get_rooms()
        room_lookup = {str(rm.get("Nomor Ruangan", "")).strip(): rm.get("Nama Ruangan", "") for rm in rooms}
        enriched = []
        for a in assets:
            item = dict(a)
            item["Merk Model"] = item.get("Merk Model") or item.get("Merk/ Model") or ""
            kr = str(item.get("Kode Ruang", "")).strip()
            item["Nama Ruangan"] = room_lookup.get(kr, kr or "-")
            enriched.append(item)
        return enriched

    def get_stock_bundle(self):
        master_rows = self.get_tab_records(["DB_Stok_Master"])
        in_rows = self.get_tab_records(["DB_Stok_Masuk"])
        out_rows = self.get_tab_records(["DB_Stok_Keluar"])

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
    # EMPLOYEES & CFG_USERS
    # ---------------------------------------------------------
    def get_employees(self):
        rows = self.get_tab_records(["DB_Pegawai"], include_row_num=True)
        result = []
        for idx, r in enumerate(rows, start=2):
            nip = str(r.get("NIP") or r.get("NIP / NIPPK") or "").strip()
            pangkat = str(r.get("Pangkat Golongan") or r.get("Pangkat/ Golongan") or "").strip()
            item = dict(r)
            item["NIP"] = nip
            item["Pangkat Golongan"] = pangkat
            item["_row_num"] = r.get("_row_num") or idx
            item["nip_clean"] = _normalize_nip(nip)
            result.append(item)
        return result

    def update_employee_row(self, row_num, updates_dict):
        if "No" in updates_dict:
            return False, "Kolom No adalah ID otomatis dan tidak dapat diubah."
        ws = self._find_ws(["DB_Pegawai"])
        if not ws:
            for idx, e in enumerate(DEMO_DATA["DB_Pegawai"], start=2):
                if idx == int(row_num or 0) or _normalize_nip(e.get("NIP")) == _normalize_nip(updates_dict.get("NIP")):
                    e.update(updates_dict)
            return True, "Data pegawai diperbarui (Mode Demo)."
        try:
            all_vals = self._get_values_from_snapshot(["DB_Pegawai"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            target_row = int(row_num) if row_num else None

            col_fallbacks = {
                "NIP": ["NIP", "NIP / NIPPK"],
                "Pangkat Golongan": ["Pangkat Golongan", "Pangkat/ Golongan"],
            }
            for col_name, new_val in updates_dict.items():
                for cand in col_fallbacks.get(col_name, [col_name]):
                    if cand in headers:
                        col_idx = headers.index(cand) + 1
                        ws.update_cell(target_row, col_idx, str(new_val))
                        break
            self._sync_snapshot(force=True)
            return True, "Data pegawai berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui data pegawai: {e}"

    def get_users_list(self):
        rows = self.get_tab_records(["CFG_Users", "Users"])
        emp_map = {e["nip_clean"]: e for e in self.get_employees() if e.get("nip_clean")}
        out = []
        for idx, u in enumerate(rows, start=2):
            nip = str(u.get("NIP", "")).strip()
            nip_clean = _normalize_nip(nip)
            role_raw = str(u.get("Role", "")).strip()
            emp = emp_map.get(nip_clean)
            out.append({
                "row_num": idx,
                "NIP": nip,
                "nip_clean": nip_clean,
                "Nama": emp.get("Nama Pegawai") if emp else "(Belum di DB_Pegawai)",
                "Pangkat": emp.get("Pangkat Golongan") if emp else "-",
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

        users = self.get_tab_records(["CFG_Users", "Users"])
        matched_user = None
        for u in users:
            u_nip = _normalize_nip(u.get("NIP", ""))
            if u_nip == clean_id and str(u.get("Password", "")).strip() == pwd:
                matched_user = u
                break

        if not matched_user:
            return None

        emp_profile = next((e for e in self.get_employees() if e.get("nip_clean") == clean_id), None)
        combined_roles = parse_roles(matched_user.get("Role", "")) or ["Pegawai"]
        permissions = self.compute_effective_permissions(combined_roles)

        return {
            "nip": (emp_profile.get("NIP") if emp_profile else matched_user.get("NIP", "")),
            "nip_clean": clean_id,
            "nama": (emp_profile.get("Nama Pegawai") if emp_profile else f"Pegawai ({clean_id})"),
            "pangkat": emp_profile.get("Pangkat Golongan", "-") if emp_profile else "-",
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

        ws_usr = self._find_ws(["CFG_Users", "Users"])
        if not ws_usr:
            existing = next((u for u in DEMO_DATA["CFG_Users"] if _normalize_nip(u.get("NIP", "")) == nip_clean), None)
            if existing:
                if password_input:
                    existing["Password"] = password_input
                existing["Role"] = role_str
            else:
                DEMO_DATA["CFG_Users"].append({"NIP": nip_clean, "Password": password_input or "rri2026", "Role": role_str})
        else:
            try:
                all_vals = self._get_values_from_snapshot(["CFG_Users", "Users"]) or ws_usr.get_all_values()
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
                return False, f"Gagal menyimpan User: {e}"

        self._sync_snapshot(force=True)
        return True, f"Akun user ({nip_clean}) dengan role [{role_str}] berhasil disimpan."

    # ---------------------------------------------------------
    # GENERIC APPEND & DELETE
    # ---------------------------------------------------------
    @staticmethod
    def _next_auto_id(target_key, existing_rows):
        field, prefix = AUTO_ID_FIELDS[target_key]
        existing_values = set()
        numbers = []
        for row in existing_rows:
            value = str(row.get(field) or "").strip()
            if not value:
                continue
            existing_values.add(value)
            if prefix:
                if not value.startswith(prefix):
                    continue
                number_text = value[len(prefix):]
            else:
                number_text = value
            if number_text.isdecimal():
                numbers.append(int(number_text))

        next_number = max(numbers, default=0) + 1
        while True:
            value = f"{prefix}{next_number:02d}" if prefix else str(next_number)
            if value not in existing_values:
                return value
            next_number += 1

    def append_record(self, target_key, row_dict):
        if target_key in AUTO_ID_FIELDS:
            with AUTO_ID_LOCK:
                return self._append_record(target_key, row_dict)
        return self._append_record(target_key, row_dict)

    def _append_record(self, target_key, row_dict):
        if not isinstance(row_dict, dict):
            return False, "Format data harus berupa objek."
        row_dict = dict(row_dict)
        tab_lookup = {
            "DB_Timeline": ["DB_Timeline", self.timeline_tab, "Sheet1"],
            "DB_Dialog": ["DB_Dialog", self.dialog_tab, "Agenda Setting"],
            "DB_Siaran": ["DB_Siaran", "Siaran"],
            "DB_Jadwal_TMB": ["DB_Jadwal_TMB", "Jadwal_TMB"],
            "DB_Arsip_SDM": ["DB_Arsip_SDM", "Arsip_SDM"],
            "DB_Info_Board": ["DB_Info_Board", "Info_Board"],
        }
        candidates = tab_lookup.get(target_key, [target_key])
        ws = self._find_ws(candidates)

        if not ws:
            if target_key in AUTO_ID_FIELDS:
                field, _ = AUTO_ID_FIELDS[target_key]
                row_dict[field] = self._next_auto_id(target_key, DEMO_DATA.get(target_key, []))
            DEMO_DATA.setdefault(target_key, []).append(row_dict)
            return True, f"Disimpan sementara ke {target_key} (Klik 'Initial Data' sebagai Admin untuk sinkronisasi tab)."

        try:
            snap_vals = ws.get_all_values() if target_key in AUTO_ID_FIELDS else self._get_values_from_snapshot(candidates)
            headers = [h.strip() for h in snap_vals[0]] if (snap_vals and snap_vals[0]) else [h.strip() for h in ws.row_values(1)]
            if target_key in AUTO_ID_FIELDS:
                field, _ = AUTO_ID_FIELDS[target_key]
                if field not in headers:
                    return False, f"Kolom ID otomatis '{field}' tidak ditemukan di tab '{ws.title}'."
                row_dict[field] = self._next_auto_id(target_key, _rows_to_dicts(snap_vals or []))

            if target_key == "DB_Ruangan":
                raw_nip = str(row_dict.get("NIP Penanggung Jawab", "") or row_dict.get("Penanggungjawab Ruangan", "")).replace("NIPPPK.", "").replace("NIP.", "").strip()
                nip_clean = _normalize_nip(raw_nip)
                row_dict["NIP Penanggung Jawab"] = nip_clean
                row_dict["Penanggungjawab Ruangan"] = nip_clean

            timeline_fallbacks = {
                "Start Date": "Tanggal Mulai",
                "End Date": "Tanggal Selesai",
            } if target_key == "DB_Timeline" else {}
            row_values = [
                str(row_dict.get(header, row_dict.get(timeline_fallbacks.get(header, ""), "")))
                for header in headers
            ]
            ws.append_row(row_values, value_input_option="USER_ENTERED")
            self._sync_snapshot(force=True)
            return True, f"Data berhasil disimpan!"
        except Exception as e:
            return False, f"Gagal menyimpan data!': {e}"

    def delete_record(self, target_key, row_num):
        tab_lookup = {
            "DB_Timeline": ["DB_Timeline", self.timeline_tab, "Sheet1", "Timeline"],
            "DB_Dialog": ["DB_Dialog", self.dialog_tab, "Agenda Setting"],
            "DB_Info_Board": ["DB_Info_Board", "Info_Board"],
            "DB_Arsip_SDM": ["DB_Arsip_SDM", "Arsip_SDM"],
            "DB_Jadwal_TMB": ["DB_Jadwal_TMB", "Jadwal_TMB"],
            "DB_Siaran": ["DB_Siaran", "Siaran"],
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
            return True, f"Data berhasil dihapus!"
        except Exception as e:
            return False, f"Gagal menghapus baris: {e}"