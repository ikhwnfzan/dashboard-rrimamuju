import os
import json
import time
import threading
import traceback
import io
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from werkzeug.security import generate_password_hash, check_password_hash

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


def _format_rupiah(val):
    try:
        number = int(float(str(val).replace(",", "").replace(".", "").split(".")[0]))
    except (ValueError, AttributeError):
        number = 0
    return f"Rp {number:,}".replace(",", ".")


def _indonesian_day_words(day):
    words = [
        "", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan",
        "sepuluh", "sebelas", "dua belas", "tiga belas", "empat belas", "lima belas",
        "enam belas", "tujuh belas", "delapan belas", "sembilan belas", "dua puluh",
    ]
    day = int(day)
    if day <= 20:
        return words[day]
    return f"dua puluh {words[day - 20]}"


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
    {"key": "info_board", "label": "Info Board", "group": "SDM"},
    {"key": "data_pegawai", "label": "Employee", "group": "SDM"},
    {"key": "arsip_sdm", "label": "Archive SDM", "group": "SDM"},
    {"key": "jadwal_siaran", "label": "Jadwal Penyiar", "group": "Siaran"},
    {"key": "produksi_paket", "label": "Produksi Paket", "group": "Perencanaan"},
    {"key": "dialog", "label": "Jadwal Dialog", "group": "Perencanaan"},
    {"key": "program_siaran", "label": "Program Siaran", "group": "Perencanaan"},
    {"key": "arsip_program", "label": "Arsip Program", "group": "Perencanaan"},
    {"key": "konten", "label": "Content Planner", "group": "KMB"},
    {"key": "bestcut_monitoring", "label": "Bestcut Monitoring", "group": "KMB"},
    {"key": "socmed_analytics", "label": "Social Media Analytics", "group": "KMB"},
    {"key": "jadwal_tmb", "label": "Jadwal TMB", "group": "TMB"},
    {"key": "tmb_working_progresss", "label": "TMB Working Progress", "group": "TMB"},
    {"key": "master_barang", "label": "Kartu Inventaris Ruangan", "group": "BMN • ASET"},
    {"key": "master_ruangan", "label": "Daftar Barang Ruangan", "group": "BMN • ASET"},
    {"key": "bast_otomatis", "label": "BAST Otomatis", "group": "BMN • ASET"},
    {"key": "aset_tutup_buku", "label": "Tutup Buku", "group": "BMN • ASET"},
    {"key": "aset_calbmn", "label": "CALBMN", "group": "BMN • ASET"},
    {"key": "aset_wasdal", "label": "WASDAL", "group": "BMN • ASET"},
    {"key": "aset_rkbmn", "label": "RKBMN", "group": "BMN • ASET"},
    {"key": "aset_manajemen_risiko", "label": "Manajemen Risiko", "group": "BMN • ASET"},
    {"key": "aset_sisporja", "label": "SISPORJA", "group": "BMN • ASET"},
    {"key": "bmn_arsip", "label": "Dokumen BMN", "group": "BMN • ASET"},
    {"key": "pemeliharaan_aset", "label": "Monitoring Pemeliharaan Aset", "group": "BMN • ASET"},
    {"key": "master_persediaan", "label": "Monitoring Persediaan", "group": "BMN • Persediaan"},
    {"key": "persediaan_tutup_buku", "label": "Tutup Buku", "group": "BMN • Persediaan"},
    {"key": "persediaan_form_pengajuan", "label": "Form Pengajuan", "group": "BMN • Persediaan"},
    {"key": "persediaan_pipk", "label": "PIPK", "group": "BMN • Persediaan"},
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
    "SDM": {"data_pegawai": "full", "arsip_sdm": "full", "info_board": "full"},
    "Perencanaan": {"info_board": "view", "produksi_paket": "full", "dialog": "full", "jadwal_siaran": "full", "program_siaran": "full", "arsip_program": "full"},
    "KMB": {"info_board": "view", "konten": "full", "bestcut_monitoring": "full", "socmed_analytics": "full", "dialog": "update"},
    "Siaran": {"info_board": "view", "jadwal_siaran": "view", "produksi_paket": "view", "dialog": "update", "program_siaran": "view", "arsip_program": "view"},
    "TMB": {"info_board": "view", "jadwal_tmb": "full", "tmb_working_progresss": "full"},
    "BMN": {
        "info_board": "view",
        "master_barang": "full", "master_ruangan": "full", "bast_otomatis": "full",
        "aset_tutup_buku": "full", "aset_calbmn": "full", "aset_wasdal": "full",
        "aset_rkbmn": "full", "aset_manajemen_risiko": "full", "aset_sisporja": "full",
        "bmn_arsip": "full", "pemeliharaan_aset": "full",
        "master_persediaan": "full", "persediaan_tutup_buku": "full",
        "persediaan_form_pengajuan": "full", "persediaan_pipk": "full"
    },
    "LPU": {"info_board": "view"},
    "Berita": {"info_board": "view", "produksi_paket": "view"},
    "Keuangan": {"info_board": "view", "master_barang": "view", "master_persediaan": "view"},
    "Pimpinan": {"info_board": "view", "data_pegawai": "view", "produksi_paket": "view", "dialog": "view", "jadwal_siaran": "view", "program_siaran": "view", "arsip_program": "view", "socmed_analytics": "view", "master_barang": "view", "master_persediaan": "view"},
    "Kasubag TU": {"info_board": "view", "data_pegawai": "view", "arsip_sdm": "view", "master_barang": "view", "master_persediaan": "view", "pemeliharaan_aset": "view"},
}

APP_CONFIG_DEFAULTS = {
    "timezone": "WITA",
    "language": "id",
    "default_theme": "light",
    "active_year": str(time.localtime().tm_year),
    "station_info": "",
}

APP_CONFIG_DESCRIPTIONS = {
    "timezone": "Zona waktu untuk waktu sinkronisasi aplikasi.",
    "language": "Preferensi bahasa untuk dukungan lokalisasi mendatang.",
    "default_theme": "Tema dashboard yang digunakan untuk semua pengguna.",
    "active_year": "Tahun aktif untuk data dan laporan.",
    "station_info": "Informasi stasiun mengikuti struktur STATION_INFO.",
}

# Unified Database (`DB_*`) & Configuration (`CFG_*`) Schemas with standardized Title Case Headers
DB_SCHEMAS = {
    "CFG_App": ["key", "value", "description"],
    "CFG_Users": ["NIP", "Password_Hash", "Role"],
    "CFG_Role_Modules": ["Role"] + [m["key"] for m in ALL_MODULES],
    "DB_Pegawai": ["No", "Nama Pegawai", "NIP", "Pangkat Golongan", "Jabatan", "Status", "Posisi"],
    "DB_SDM_Arsip": ["Nomor Dokumen", "Nama Dokumen", "Tanggal", "Jenis", "Link"],
    "DB_Info_Board": ["Tanggal", "Prioritas", "Judul", "Isi", "Target Divisi", "Lampiran"],
    "DB_Timeline": ["ID Kegiatan", "Kegiatan", "Tahapan", "Tanggal Mulai", "Tanggal Selesai", "Keterangan"],
    "DB_Jadwal_Operasional": ["ID Jadwal", "Tanggal", "Shift", "Bidang", "Pegawai", "Status"],
    "DB_Program": ["Kode Program", "Programa", "Nama Program", "Hari", "Jam", "Kategori", "Status"],
    "DB_Dialog": [
        "ID Dialog", "Tanggal Surat", "Program", "Topik", "Narasumber", "Kehadiran",
        "PIC Narasumber", "Flyer", "Bestcut", "Status", "Catatan", "Tanggal Dialog",
        "Instansi", "Link Live", "Operator", "Penyiar"
    ],
    "DB_Flyer": ["ID File", "ID Dialog", "Nama File", "Link Flyer"],
    "DB_Konten": ["ID Konten", "Tanggal Tayang", "Platform", "Akun", "Judul Konten", "Jenis", "Keterangan", "PIC", "Status", "Link Asset", "Catatan"],
    "DB_Ruangan": ["Nomor Ruangan", "Nama Ruangan", "Lokasi", "NIP Penanggung Jawab"],
    "DB_Aset": ["Kode Barang", "Kode Ruang", "Nama Barang", "Merk Model", "Tipe", "Tahun", "NUP", "Kondisi", "Tindak Lanjut", "Keterangan"],
    "DB_BAST": ["Nomor BAST", "Tanggal Dokumen", "NIP", "Nomor Barang", "NUP", "Nilai", "Jumlah", "Letak", "Status", "Link PDF"],
    "DB_Pemeliharaan_Header": ["Kode Jadwal", "Tanggal", "Judul Pemeliharaan", "Lokasi", "Teknisi Vendor", "Status", "Keterangan"],
    "DB_Pemeliharaan_Detail": ["Kode Detail Pemeliharaan", "Kode Jadwal", "Nomor Kode Barang", "Nama Barang", "NUP", "Kondisi Sebelum", "Tindakan", "Kondisi Sesudah", "Biaya"],
    "DB_BMN_Arsip": ["Nomor Dokumen", "Jenis", "Judul Dokumen", "Tanggal", "Keterangan", "Link"],
    "DB_BMN_Dokumen": ["ID Dokumen", "Group", "Sub Menu", "Periode", "Kategori Item", "Judul Dokumen", "Tanggal Buat", "Link File", "Keterangan"],
    "DB_Stok_Master": ["Kode Barang", "Nama Barang", "Unit", "Stok Awal", "Keterangan"],
    "DB_Stok_Detail": ["ID Transaksi", "Tanggal", "Jenis", "Bidang", "Penanggung Jawab", "Kode Barang", "Jumlah", "Unit", "Pcs", "Keterangan"],
    "DB_Socmed_Analytics": ["ID Socmed", "Periode", "Platform", "Akun", "Followers", "Reach", "Engagement", "Top Konten", "Catatan"],
    "DB_TMB_Working_Progress": [
        "ID Produksi", "Judul", "Jenis", "Tanggal Record", "Record", "Editing", "PIC TMB", "PIC Penyiaran",
        "Progress", "Deadline", "Catatan", "Link File", "Status", "Tanggal Tayang",
        "Keterangan", "Deskripsi"
    ],
    "DB_Arsip_Program": ["ID Dokumen", "Kategori", "Jenis", "Tanggal Upload", "Nama Dokumen", "Keterangan", "Link"],
}

AUTO_ID_FIELDS = {
    "DB_Pegawai": ("No", ""),
    "DB_Timeline": ("ID Kegiatan", "RRI-TL-"),
    "DB_Dialog": ("ID Dialog", "RRI-DS"),
    "DB_Konten": ("ID Konten", "CNT-"),
    "DB_Pemeliharaan_Header": ("Kode Jadwal", "BMN-PML-"),
    "DB_Pemeliharaan_Detail": ("Kode Detail Pemeliharaan", "PML-DT-"),
    "DB_BMN_Dokumen": ("ID Dokumen", "DOK-BMN-"),
    "DB_Stok_Master": ("Kode Barang", "STK-"),
    # "DB_Stok_Detail": ("ID Transaksi", "STK-DT-"),
    "DB_Socmed_Analytics": ("ID Socmed", "SOC-"),
    "DB_Flyer": ("ID File", "FLY-"),
    "DB_Arsip_Program": ("ID Dokumen", "DOK-PRC-"),
}
AUTO_ID_LOCK = threading.Lock()


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
            self.last_error = "GOOGLE_SHEET_ID belum diisi di konfigurasi."
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
                self.last_error = "service_account.json belum ditemukan."
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
    # ADMIN INITIAL DATA: create missing standardized tabs and their initial data.
    # ---------------------------------------------------------
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
        if not isinstance(settings, dict) or not settings or not set(settings).issubset(set(APP_CONFIG_DEFAULTS)):
            return False, "Data pengaturan aplikasi tidak lengkap atau tidak valid."

        ws = self._find_ws(["CFG_App"])
        if not ws:
            self._sync_snapshot(force=True)
            ws = self._find_ws(["CFG_App"])
        if not ws:
            return False, "Tabel config tidak ditemukan. Jalankan Initial Data sebagai Admin terlebih dahulu."

        try:
            values = self._get_values_from_snapshot(["CFG_App"]) or ws.get_all_values()
            if not values:
                headers = list(DB_SCHEMAS["CFG_App"])
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
            return False, "Tabel Modul tidak ditemukan."

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
        vals = self._get_values_from_snapshot(["DB_Timeline"])
        if vals is None:
             return False, "Tidak ada tahapan kegiatan ditemukan"
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

        if not self._find_ws(["DB_Timeline"]):
            return False, "Tab DB_Timeline tidak ditemukan."

        ws = self._find_ws(["DB_Timeline"])
        try:
            all_values = self._get_values_from_snapshot(
                ["DB_Timeline"]
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

    def update_tab_row(self, tab_name, row_num, updates_dict):
        """Generic row update helper for a named Google Sheet tab."""
        try:
            target_row = int(row_num)
            if target_row < 2:
                return False, "Nomor baris tidak valid."
        except (TypeError, ValueError):
            return False, "Nomor baris tidak valid."

        ws = self._find_ws([tab_name])
        if not ws:
            return False, f"Tab {tab_name} tidak ditemukan."
        try:
            all_values = self._get_values_from_snapshot([tab_name]) or ws.get_all_values()
            headers = [h.strip() for h in all_values[0]] if all_values else []
            updated = 0
            for col_name, new_val in (updates_dict or {}).items():
                if col_name in headers:
                    ws.update_cell(target_row, headers.index(col_name) + 1, str(new_val))
                    updated += 1
            if not updated:
                return False, "Kolom yang akan diperbarui tidak ditemukan."
            self._sync_snapshot(force=True)
            return True, "Data berhasil diperbarui."
        except Exception as e:
            return False, f"Gagal memperbarui data: {e}"

    def _employee_lookups(self):
        employees = self.get_employees()
        by_no = {}
        by_nip = {}
        by_nip15 = {}
        by_name = {}
        for emp in employees:
            no_val = str(emp.get("No", "")).strip()
            nip_clean = _normalize_nip(emp.get("NIP", ""))
            nm_clean = str(emp.get("Nama Pegawai", "")).strip().lower()
            if no_val:
                by_no[no_val] = emp
            if nip_clean:
                by_nip[nip_clean] = emp
                if len(nip_clean) >= 15:
                    by_nip15[nip_clean[:15]] = emp
            if nm_clean:
                by_name[nm_clean] = emp
        return employees, (by_no, by_nip, by_nip15, by_name)

    def _resolve_emp(self, raw_ref, lookups):
        by_no, by_nip, by_nip15, by_name = lookups
        s = str(raw_ref or "").strip()
        if not s:
            return {}
        if s in by_no:
            return by_no[s]
        digits = _normalize_nip(s)
        if digits:
            if digits in by_nip:
                return by_nip[digits]
            if len(digits) >= 15 and digits[:15] in by_nip15:
                return by_nip15[digits[:15]]
        low = s.lower()
        if low in by_name:
            return by_name[low]
        return {}

    def _resolve_emp_nip_for_write(self, raw_ref):
        s = str(raw_ref or "").strip()
        if not s:
            return ""
        _, lookups = self._employee_lookups()
        emp = self._resolve_emp(s, lookups)
        if emp and emp.get("NIP"):
            return _normalize_nip(emp.get("NIP"))
        digits = _normalize_nip(s)
        return digits if digits else s

    def get_agenda_setting(self):
        all_values = self._get_values_from_snapshot(["DB_Dialog"])
        if all_values is None:
            return []
        if not all_values:
            return []

        _, lookups = self._employee_lookups()
        flyers = self.get_tab_records(["DB_Flyer"])
        flyer_by_id = {str(fl.get("ID File", "")).strip(): fl for fl in flyers if str(fl.get("ID File", "")).strip()}
        flyer_by_dlg = {str(fl.get("ID Dialog", "")).strip(): fl for fl in flyers if str(fl.get("ID Dialog", "")).strip()}
        programs = {str(p.get("Kode Program", "")).strip(): p for p in self.get_tab_records(["DB_Program"])}

        header_idx = 0
        for idx, row in enumerate(all_values[:10]):
            lowered = [c.strip().lower() for c in row]
            if ("tanggal" in lowered or "tanggal dialog" in lowered or "tanggal surat" in lowered) and ("program" in lowered or "narasumber" in lowered):
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

            id_dlg = item.get("ID Dialog") or item.get("No") or ""
            if id_dlg:
                last_no = id_dlg
            else:
                id_dlg = last_no
            item["ID Dialog"] = id_dlg
            item["No"] = id_dlg

            tgl_dlg = item.get("Tanggal Dialog") or item.get("Tanggal") or item.get("Tanggal Surat") or ""
            if tgl_dlg:
                last_tanggal = tgl_dlg
            else:
                tgl_dlg = last_tanggal
            item["Tanggal Dialog"] = tgl_dlg
            item["Tanggal"] = tgl_dlg

            prog_code = str(item.get("Program", "")).strip()
            if prog_code in programs:
                item["Program Kode"] = prog_code
                item["Program"] = programs[prog_code].get("Nama Program") or prog_code

            item["Topik"] = item.get("Topik") or item.get("Topik/ Isu") or ""
            item["Instansi"] = item.get("Instansi") or item.get("Jabatan") or item.get("Jabatan/ Instansi") or ""
            item["Jabatan"] = item["Instansi"]
            item["Kehadiran"] = item.get("Kehadiran") or item.get("KET. Kehadiran") or ""
            item["Keterlaksanaan"] = item.get("Status") or item.get("Keterlaksanaan") or ""
            item["Status"] = item["Keterlaksanaan"]
            item["Kendala"] = item.get("Catatan") or item.get("Kendala") or ""
            item["Catatan"] = item["Kendala"]
            item.setdefault("Bestcut", "")

            for fk_col, label_key in [("PIC Narasumber", "PIC Narasumber Nama"), ("Operator", "Operator Nama"), ("Penyiar", "Penyiar Nama")]:
                raw_fk = item.get(fk_col, "")
                emp = self._resolve_emp(raw_fk, lookups)
                item[label_key] = emp.get("Nama Pegawai") or raw_fk or "-"

            flyer_ref = str(item.get("Flyer", "")).strip()
            fl_obj = flyer_by_id.get(flyer_ref) or flyer_by_dlg.get(str(id_dlg).strip())
            if fl_obj:
                item["Flyer URL"] = fl_obj.get("Link Flyer") or ""
                item["Flyer Nama"] = fl_obj.get("Nama File") or ""
                if not flyer_ref.startswith("http"):
                    item["Flyer"] = item["Flyer URL"] or flyer_ref
            else:
                item["Flyer URL"] = flyer_ref if flyer_ref.startswith("http") else ""

            if any([item.get("Program", ""), item.get("Topik", ""), item.get("Narasumber", "")]):
                parsed_rows.append(item)
        return parsed_rows

    def update_dialog_row(self, row_num, updates_dict):
        ws = self._find_ws(["DB_Dialog"])
        if not ws:
            return False, "Tabel Dialog tidak ditemukan."
        try:
            all_values = self._get_values_from_snapshot(["DB_Dialog"]) or ws.get_all_values()
            header_idx = 0
            for idx, row in enumerate(all_values[:10]):
                lowered = [c.strip().lower() for c in row]
                if ("tanggal" in lowered or "tanggal dialog" in lowered or "tanggal surat" in lowered) and ("program" in lowered or "narasumber" in lowered):
                    header_idx = idx
                    break
            headers = [h.strip() for h in all_values[header_idx]]

            if "Bestcut" in updates_dict and "Bestcut" not in headers:
                new_col = len(headers) + 1
                ws.update_cell(header_idx + 1, new_col, "Bestcut")
                headers.append("Bestcut")

            col_fallbacks = {
                "Topik": ["Topik", "Topik/ Isu"],
                "Kehadiran": ["Kehadiran", "KET. Kehadiran"],
                "Jabatan": ["Instansi", "Jabatan", "Jabatan/ Instansi"],
                "Instansi": ["Instansi", "Jabatan", "Jabatan/ Instansi"],
                "Keterlaksanaan": ["Status", "Keterlaksanaan"],
                "Status": ["Status", "Keterlaksanaan"],
                "Kendala": ["Catatan", "Kendala"],
                "Catatan": ["Catatan", "Kendala"],
                "Tanggal": ["Tanggal Dialog", "Tanggal"],
            }
            for col_name, new_val in updates_dict.items():
                val_to_write = str(new_val)
                if col_name in ("PIC Narasumber", "Operator", "Penyiar"):
                    val_to_write = self._resolve_emp_nip_for_write(val_to_write)
                candidates = col_fallbacks.get(col_name, [col_name])
                for cand in candidates:
                    if cand in headers:
                        col_idx = headers.index(cand) + 1
                        ws.update_cell(int(row_num), col_idx, val_to_write)
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
            return []
        return _rows_to_dicts(vals, include_row_num=include_row_num)

    # ---------------------------------------------------------
    # UNIFIED OPERATIONAL SCHEDULE & TMB WORKING PROGRESS
    # ---------------------------------------------------------
    def get_jadwal_operasional(self, mode="all"):
        _, lookups = self._employee_lookups()
        rows = self.get_tab_records(["DB_Jadwal_Operasional"], include_row_num=True)
        enriched = []
        for r in rows:
            item = dict(r)
            bidang = str(item.get("Bidang", "")).strip()
            is_tmb = "tmb" in bidang.lower()
            is_siaran = "pro" in bidang.lower()
            if mode == "siaran" and not is_siaran:
                continue
            if mode == "tmb" and not is_tmb:
                continue

            raw_pegawai = item.get("Pegawai") or item.get("Penyiar") or item.get("Teknisi TMB") or ""
            emp = self._resolve_emp(raw_pegawai, lookups)
            emp_name = emp.get("Nama Pegawai") or raw_pegawai or "-"
            emp_jab = emp.get("Jabatan") or emp.get("Posisi") or "-"

            item["Pegawai NIP"] = emp.get("NIP") or raw_pegawai
            item["Pegawai Nama"] = emp_name
            item["Pegawai Jabatan"] = emp_jab
            # Compatibility fields for Siaran & TMB views
            item["Programa"] = bidang
            item["Penyiar"] = emp_name
            item["Operator"] = emp_jab
            item["Lokasi Pemancar"] = bidang
            item["Teknisi TMB"] = emp_name
            item["Tugas"] = emp_jab
            enriched.append(item)
        return enriched

    def get_tmb_working_progress(self):
        _, lookups = self._employee_lookups()
        rows = self.get_tab_records(["DB_TMB_Working_Progress"], include_row_num=True)
        enriched = []
        for r in rows:
            item = dict(r)
            for col in ("Record", "Editing", "PIC TMB", "PIC Penyiaran"):
                emp = self._resolve_emp(item.get(col, ""), lookups)
                if emp:
                    item[col] = emp.get("Nama Pegawai") or item.get(col)
            item["Kendala"] = item.get("Catatan") or item.get("Kendala") or ""
            item["Link"] = item.get("Link File") or item.get("Link") or ""
            item["ID"] = item.get("ID Produksi") or item.get("ID") or ""
            item["Tanggal"] = item.get("Tanggal Tayang") or item.get("Tanggal Record") or ""
            item["Program"] = item.get("Keterangan") or item.get("Jenis") or ""
            item["Judul Paket"] = item.get("Judul") or ""
            item["Jenis Paket"] = item.get("Jenis") or ""
            item["Produser"] = item.get("PIC Penyiaran") or ""
            item["Link File"] = item["Link"]
            enriched.append(item)
        return enriched

    def get_arsip_sdm(self):
        rows = self.get_tab_records(["DB_SDM_Arsip", "DB_SDM_Arsip", "Arsip_SDM"], include_row_num=True)
        enriched = []
        for r in rows:
            item = dict(r)
            item["Nomor Dokumen"] = item.get("Nomor Dokumen") or f"SDM-{item.get('ID Dokumen', '')}"
            item["Nama Dokumen"] = item.get("Nama Dokumen") or "-"
            item["Tanggal"] = item.get("Tanggal") or item.get("Tanggal Upload") or "-"
            enriched.append(item)
        return enriched

    def get_arsip_program(self):
        rows = self.get_tab_records(["DB_Arsip_Program"], include_row_num=True)
        enriched = []
        for r in rows:
            item = dict(r)
            item["ID Dokumen"] = item.get("ID Dokumen") or "-"
            item["Tanggal Upload"] = item.get("Tanggal Upload") or item.get("Tanggal") or "-"
            enriched.append(item)
        return enriched

    # ---------------------------------------------------------
    # BMN: MASTER ASSET, ROOM & STOCK
    # ---------------------------------------------------------
    def get_rooms(self):
        rooms = self.get_tab_records(["DB_Ruangan"], include_row_num=True)
        _, lookups = self._employee_lookups()
        enriched = []
        for r in rooms:
            item = dict(r)
            raw_pj = str(item.get("NIP Penanggung Jawab", "") or item.get("Penanggungjawab Ruangan", "")).strip()
            emp = self._resolve_emp(raw_pj, lookups)
            item["NIP Penanggung Jawab"] = raw_pj
            if emp:
                item["pj_no"] = emp.get("No") or ""
                item["pj_nip"] = emp.get("NIP") or raw_pj
                item["pj_nama"] = emp.get("Nama Pegawai") or "-"
                item["pj_jabatan"] = emp.get("Jabatan") or emp.get("Posisi") or "-"
                item["pj_posisi"] = emp.get("Posisi") or "-"
            else:
                item["pj_no"] = ""
                item["pj_nip"] = raw_pj or "-"
                item["pj_nama"] = "-"
                item["pj_jabatan"] = "-"
                item["pj_posisi"] = "-"
            item["nip_clean"] = _normalize_nip(item["pj_nip"])
            enriched.append(item)
        return enriched

    def get_assets(self):
        assets = self.get_tab_records(["DB_Aset"], include_row_num=True)
        rooms = self.get_rooms()
        room_lookup = {str(rm.get("Nomor Ruangan", "")).strip(): rm.get("Nama Ruangan", "") for rm in rooms}
        enriched = []
        for idx, a in enumerate(assets, start=1):
            item = dict(a)
            # 1-based asset index (`1..N`, equal to `_row_num - 1`) used by `DB_BAST.Nomor Barang`
            item["ID Barang"] = str(idx)
            item["Merk Model"] = item.get("Merk Model") or item.get("Merk/ Model") or ""
            kr = str(item.get("Kode Ruang", "")).strip()
            item["Nama Ruangan"] = room_lookup.get(kr, kr or "-")
            enriched.append(item)
        return enriched

    def get_bast_records(self):
        records = self.get_tab_records(["DB_BAST"], include_row_num=True)
        _, lookups = self._employee_lookups()
        assets = self.get_assets()
        rooms = self.get_rooms()

        asset_by_id = {str(asset.get("ID Barang", "")).strip(): asset for asset in assets if str(asset.get("ID Barang", "")).strip()}
        asset_by_kode = {str(asset.get("Kode Barang", "")).strip(): asset for asset in assets if str(asset.get("Kode Barang", "")).strip()}
        room_lookup = {str(room.get("Nomor Ruangan", "")).strip(): room for room in rooms}

        enriched = []
        for record in records:
            item = dict(record)
            employee = self._resolve_emp(item.get("NIP"), lookups)
            asset_ref = str(item.get("Nomor Barang", "")).strip()
            asset = asset_by_id.get(asset_ref) or asset_by_kode.get(asset_ref) or {}
            room_code = str(item.get("Letak") or asset.get("Kode Ruang") or "").strip()
            room = room_lookup.get(room_code, {})

            item["NIP Display"] = employee.get("NIP") or item.get("NIP") or ""
            item["Nama"] = employee.get("Nama Pegawai") or ""
            item["Pangkat"] = employee.get("Pangkat Golongan") or ""
            item["Jabatan"] = employee.get("Jabatan") or employee.get("Posisi") or ""
            item["Kode Barang Display"] = asset.get("Kode Barang") or asset_ref
            item["Barang"] = asset.get("Nama Barang") or ""
            item["Merk"] = asset.get("Merk Model") or ""
            item["Tipe"] = asset.get("Tipe") or ""
            item["Letak"] = room.get("Nama Ruangan") or asset.get("Nama Ruangan") or room_code or ""
            item["Letak Kode"] = room_code
            if not item.get("Nilai"):
                item["Nilai"] = ""
            enriched.append(item)
        return enriched

    def get_stock_bundle(self):
        master_rows = self.get_tab_records(["DB_Stok_Master"], include_row_num=True)
        detail_rows = self.get_tab_records(["DB_Stok_Detail"], include_row_num=True)

        kode_to_name = {}
        name_to_kode = {}
        for m in master_rows:
            kb = str(m.get("Kode Barang", "")).strip()
            nb = str(m.get("Nama Barang", "")).strip()
            if kb and nb:
                kode_to_name[kb.lower()] = nb
                name_to_kode[nb.lower()] = kb

        in_totals = {}
        out_totals = {}
        enriched_details = []
        for r in detail_rows:
            item = dict(r)
            kb = str(item.get("Kode Barang", "")).strip()
            nb = str(item.get("Nama Barang", "")).strip()
            if not nb and kb:
                nb = kode_to_name.get(kb.lower(), kb)
            if not kb and nb:
                kb = name_to_kode.get(nb.lower(), "")
            item["Kode Barang"] = kb
            item["Nama Barang"] = nb
            enriched_details.append(item)

            key = kb.lower() if kb else nb.lower()
            if not key:
                continue
            jns = str(item.get("Jenis", "")).strip().lower()
            qty = _parse_num(item.get("Pcs", item.get("Jumlah", 0)))
            if jns == "keluar":
                out_totals[key] = out_totals.get(key, 0) + qty
            else:
                in_totals[key] = in_totals.get(key, 0) + qty

        computed_master = []
        for m in master_rows:
            kb = str(m.get("Kode Barang", "")).strip()
            name = str(m.get("Nama Barang", "")).strip()
            if not name and not kb:
                continue
            key = kb.lower() if kb else name.lower()
            awal = _parse_num(m.get("Stok Awal", 0))
            masuk = in_totals.get(key, 0)
            keluar = out_totals.get(key, 0)
            akhir = awal + masuk - keluar
            computed_master.append({
                "_row_num": m.get("_row_num"),
                "Kode Barang": kb,
                "Nama Barang": name,
                "Unit": m.get("Unit", "Pcs"),
                "Stok Awal": awal,
                "Barang Masuk": masuk,
                "Barang Keluar": keluar,
                "Stok Akhir": akhir,
                "Keterangan": m.get("Keterangan", ""),
            })

        return {
            "master": computed_master,
            "details": enriched_details,
        }

    def update_stok_detail_row(self, row_num, updates_dict):
        ws = self._find_ws(["DB_Stok_Detail"])
        if not ws:
            return False, "Tabel Stok Detail tidak ditemukan."
        try:
            all_values = self._get_values_from_snapshot(["DB_Stok_Detail"]) or ws.get_all_values()
            headers = [h.strip() for h in all_values[0]]
            for col_name, new_val in updates_dict.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    ws.update_cell(int(row_num), col_idx, str(new_val))
            self._sync_snapshot(force=True)
            return True, "Transaksi persediaan berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui transaksi persediaan: {e}"

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

    def generate_bast_document(self, payload, template_doc_id=None):
        cfg_map = {item["key"]: item["value"] for item in self.get_app_settings()}
        resolved_template_id = (
            str(payload.get("template_doc_id") or "").strip()
            or str(template_doc_id or "").strip()
        )
        if not resolved_template_id:
            return False, {"message": "BAST_TEMPLATE_DOC_ID belum diatur di .env."}

        bridge_url = os.getenv("DRIVE_BRIDGE_URL", "").strip()
        root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID", "").strip()
        bridge_secret = os.getenv("DRIVE_BRIDGE_SECRET", "").strip()
        subfolder_name = str(payload.get("subfolder_name") or "Tutup Buku").strip()

        from datetime import datetime
        try:
            tanggal = datetime.strptime(str(payload["tanggal"]), "%Y-%m-%d")
        except ValueError:
            return False, {"message": "Format tanggal BAST harus YYYY-MM-DD."}

        month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        tanggal_terbilang = f"{_indonesian_day_words(tanggal.day)} bulan {month_names[tanggal.month]} tahun {tanggal.year}"
        tanggal_ttd = f"{tanggal.day} {month_names[tanggal.month]} {tanggal.year}"
        tanggal_dokumen = tanggal.strftime("%Y-%m-%d")
        periode_dokumen = f"{month_names[tanggal.month]} {tanggal.year}"

        nomor_barang = str(payload.get("nomor_barang") or "").strip()
        asset = next(
            (
                item for item in self.get_assets()
                if str(item.get("ID Barang", "")).strip() == nomor_barang
                or str(item.get("Kode Barang", "")).strip() == nomor_barang
            ),
            {},
        )
        kode_barang_pdf = str(asset.get("Kode Barang") or nomor_barang).strip()
        room_code = str(asset.get("Kode Ruang") or payload.get("kode_ruang") or payload.get("letak") or "").strip()
        room = next(
            (item for item in self.get_rooms() if str(item.get("Nomor Ruangan", "")).strip() == room_code),
            {},
        )
        letak_name = room.get("Nama Ruangan") or asset.get("Nama Ruangan") or str(payload.get("letak") or "")

        replacements = {
            "{{nomor_bast}}": str(payload["nomor_bast"]),
            "{{tanggal_terbilang}}": tanggal_terbilang,
            "{{nama}}": str(payload["nama"]),
            "{{nip}}": str(payload["nip"]),
            "{{pangkat}}": str(payload["pangkat"]),
            "{{jabatan}}": str(payload["jabatan"]),
            "{{nomor_barang}}": kode_barang_pdf,
            "{{nup}}": str(payload["nup"]),
            "{{barang}}": str(payload["barang"]),
            "{{merk}}": str(payload.get("merk") or ""),
            "{{tipe}}": str(payload.get("tipe") or ""),
            "{{nilai}}": _format_rupiah(payload["nilai"]),
            "{{jumlah}}": str(payload["jumlah"]),
            "{{letak}}": str(letak_name),
            "{{tanggal_ttd}}": tanggal_ttd,
        }
        pdf_name = f"BAST {payload['nomor_bast']}.pdf".replace("/", "-")

        # 1. Preferred Path: Google Apps Script Bridge (uses owner Google Account Drive storage quota!)
        if bridge_url:
            try:
                import requests
                bridge_payload = {
                    "secret": bridge_secret,
                    "action": "generate_pdf",
                    "template_doc_id": resolved_template_id,
                    "root_folder_id": root_folder_id,
                    "subfolder_name": subfolder_name,
                    "output_name": pdf_name,
                    "replacements": replacements,
                }
                resp = requests.post(bridge_url, json=bridge_payload, timeout=60, allow_redirects=True)
                data = resp.json()
                if not data.get("ok"):
                    return False, {"message": data.get("message") or "Apps Script gagal membuat PDF."}

                pdf_url = data.get("pdf_url", "")
                pdf_id = data.get("pdf_id", "")
                self._mark_bast_row_done(
                    payload.get("sheet_row"),
                    pdf_url,
                    payload=payload,
                    document_date=tanggal_dokumen,
                    document_period=periode_dokumen,
                )
                self._sync_snapshot(force=True)
                return True, {
                    "message": f"Dokumen BAST berhasil dibuat!",
                    "pdf_url": pdf_url,
                    "pdf_id": pdf_id,
                }
            except Exception as exc:
                return False, {"message": f"Gagal menghubungi Google Apps Script Bridge: {exc}"}

        # 2. Fallback Path: Direct Service Account Drive/Docs API (requires Shared Drive or Service Account quota)
        creds = None
        try:
            sa_path = self._find_local_sa_file()
            if sa_path:
                info = json.load(open(sa_path, "r", encoding="utf-8"))
                creds = Credentials.from_service_account_info(info, scopes=SCOPES + ["https://www.googleapis.com/auth/documents"])
            elif self.creds_json:
                creds = Credentials.from_service_account_info(
                    _parse_service_account_env(self.creds_json),
                    scopes=SCOPES + ["https://www.googleapis.com/auth/documents"],
                )
        except Exception as exc:
            return False, {"message": f"Kredensial Google tidak valid: {exc}"}
        if not creds:
            return False, {"message": "service_account.json belum tersedia."}

        try:
            drive = build("drive", "v3", credentials=creds, cache_discovery=False)
            docs = build("docs", "v1", credentials=creds, cache_discovery=False)

            target_parent_id = root_folder_id
            if root_folder_id:
                for folder_name in ("Aset", subfolder_name):
                    q = (
                        f"'{target_parent_id}' in parents and "
                        f"mimeType = 'application/vnd.google-apps.folder' and "
                        f"name = '{folder_name}' and trashed = false"
                    )
                    folder_result = drive.files().list(
                        q=q,
                        fields="files(id,name)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    ).execute()
                    folders = folder_result.get("files", [])
                    if folders:
                        target_parent_id = folders[0]["id"]
                    else:
                        created_folder = drive.files().create(
                            body={
                                "name": folder_name,
                                "mimeType": "application/vnd.google-apps.folder",
                                "parents": [target_parent_id],
                            },
                            fields="id",
                            supportsAllDrives=True,
                        ).execute()
                        target_parent_id = created_folder["id"]

            copy_body = {"name": f"TEMP_{pdf_name}"}
            if target_parent_id:
                copy_body["parents"] = [target_parent_id]

            copied = drive.files().copy(
                fileId=resolved_template_id,
                body=copy_body,
                supportsAllDrives=True,
            ).execute()
            document_id = copied["id"]

            requests_body = [{
                "replaceAllText": {
                    "containsText": {"text": key, "matchCase": True},
                    "replaceText": value,
                }
            } for key, value in replacements.items()]
            docs.documents().batchUpdate(documentId=document_id, body={"requests": requests_body}).execute()

            pdf_bytes = drive.files().export_media(fileId=document_id, mimeType="application/pdf").execute()
            pdf_metadata = {"name": pdf_name, "mimeType": "application/pdf"}
            if target_parent_id:
                pdf_metadata["parents"] = [target_parent_id]
            media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype="application/pdf", resumable=False)
            pdf_file = drive.files().create(
                body=pdf_metadata,
                media_body=media,
                fields="id,webViewLink,webContentLink",
                supportsAllDrives=True,
            ).execute()

            try:
                drive.files().delete(fileId=document_id, supportsAllDrives=True).execute()
            except Exception:
                pass

            pdf_url = pdf_file.get("webViewLink") or f"https://drive.google.com/file/d/{pdf_file['id']}/view"
            self._mark_bast_row_done(
                payload.get("sheet_row"),
                pdf_url,
                payload=payload,
                document_date=tanggal_dokumen,
                document_period=periode_dokumen,
            )
            self._sync_snapshot(force=True)
            return True, {"message": "Dokumen BAST dan PDF berhasil dibuat.", "pdf_url": pdf_url, "pdf_id": pdf_file["id"]}
        except Exception as exc:
            err_msg = str(exc)
            if "storageQuotaExceeded" in err_msg:
                return False, {
                    "message": "Storage Service Account penuh (0 GB). Konfigurasikan DRIVE_BRIDGE_URL dan DRIVE_ROOT_FOLDER_ID melalui .env agar menggunakan Google Drive akun Anda."
                }
            return False, {"message": f"Gagal membuat dokumen BAST: {exc}"}

    def _mark_bast_row_done(self, sheet_row_raw, pdf_url, payload=None, document_date="", document_period=""):
        sheet_row = int(sheet_row_raw or 0)
        worksheet = self._find_ws(["DB_BAST"])
        if not worksheet:
            return False
        headers = [str(header).strip() for header in worksheet.row_values(1)]
        if "Tanggal Dokumen" not in headers:
            worksheet.update_cell(1, len(headers) + 1, "Tanggal Dokumen")
            headers.append("Tanggal Dokumen")
        if sheet_row >= 2:
            row_values = {
                "Status": "Done",
                "Link PDF": pdf_url,
                "Tanggal Dokumen": document_date,
            }
            for field, value in row_values.items():
                if field in headers:
                    worksheet.update_cell(sheet_row, headers.index(field) + 1, value)
        elif payload:
            asset_match = next(
                (
                    item for item in self.get_assets()
                    if str(item.get("ID Barang", "")).strip() == str(payload.get("nomor_barang", "")).strip()
                    or str(item.get("Kode Barang", "")).strip() == str(payload.get("nomor_barang", "")).strip()
                ),
                {},
            )
            row_map = {
                "Nomor BAST": str(payload.get("nomor_bast", "")).strip(),
                "Tanggal Dokumen": document_date,
                "NIP": self._resolve_emp_nip_for_write(payload.get("nip", "")),
                "Nomor Barang": str(asset_match.get("ID Barang") or payload.get("nomor_barang", "")).strip(),
                "NUP": str(payload.get("nup", "")).strip(),
                "Nilai": str(payload.get("nilai", "")).strip(),
                "Jumlah": str(payload.get("jumlah", "")).strip(),
                "Letak": str(asset_match.get("Kode Ruang") or payload.get("letak", "")).strip(),
                "Status": "Done",
                "Link PDF": pdf_url,
            }
            new_row = [row_map.get(h, "") for h in headers]
            worksheet.append_row(new_row, value_input_option="USER_ENTERED")

        if not self._find_ws(["DB_BMN_Dokumen"]):
            return False
        dokumen_ws = self._find_ws(["DB_BMN_Dokumen"])
        dokumen_headers = [str(header).strip() for header in dokumen_ws.row_values(1)]
        if not dokumen_headers:
            dokumen_headers = list(DB_SCHEMAS["DB_BMN_Dokumen"])
            dokumen_ws.append_row(dokumen_headers, value_input_option="USER_ENTERED")

        judul_dokumen = f"BAST {payload.get('nomor_bast', '')}.pdf".replace("/", "-") if payload else ""
        row_map = {
            "Group": "Aset",
            "Sub Menu": "Tutup Buku",
            "Periode": document_period,
            "Kategori Item": "BAST",
            "Judul Dokumen": judul_dokumen,
            "Tanggal Buat": document_date,
            "Link File": pdf_url,
            "Keterangan": "Done",
        }
        dokumen_ws.append_row(
            [row_map.get(header, "") for header in dokumen_headers],
            value_input_option="USER_ENTERED",
        )
        return True

    def update_bast_row(self, row_num, updates_dict):
        ws = self._find_ws(["DB_BAST"])
        if not ws:
            return False, "Tabel BAST tidak ditemukan."

        try:
            all_vals = self._get_values_from_snapshot(["DB_BAST"]) or ws.get_all_values()
            headers = [str(header).strip() for header in all_vals[0]]
            target_row = int(row_num)
            for col_name, new_val in updates_dict.items():
                if col_name in headers:
                    ws.update_cell(target_row, headers.index(col_name) + 1, str(new_val))
            self._sync_snapshot(force=True)
            return True, "Data BAST berhasil diperbarui!"
        except Exception as exc:
            return False, f"Gagal memperbarui data BAST: {exc}"

    def update_room_row(self, row_num, updates_dict):
        if "Nomor Ruangan" in updates_dict:
            return False, "Nomor Ruangan tidak dapat diubah."

        ws = self._find_ws(["DB_Ruangan"])
        if not ws:
            return False, "Baris Ruangan tidak ditemukan."

        try:
            all_vals = self._get_values_from_snapshot(["DB_Ruangan"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            target_row = int(row_num)
            for col_name, new_val in updates_dict.items():
                candidates = ["NIP Penanggung Jawab", "Penanggungjawab Ruangan"] if col_name == "NIP Penanggung Jawab" else [col_name]
                for cand in candidates:
                    if cand in headers:
                        col_idx = headers.index(cand) + 1
                        value = _normalize_nip(str(new_val).replace("NIPPPK.", "").replace("NIP.", "")) if col_name == "NIP Penanggung Jawab" else str(new_val)
                        ws.update_cell(target_row, col_idx, value)
                        break
            self._sync_snapshot(force=True)
            return True, "Data ruangan berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui data ruangan: {e}"

    def update_asset_row(self, row_num, updates_dict):
        if "Kode Barang" in updates_dict:
            return False, "Kode Barang tidak dapat diubah."

        ws = self._find_ws(["DB_Aset"])
        if not ws:
            return False, "Baris barang tidak ditemukan."

        try:
            all_vals = self._get_values_from_snapshot(["DB_Aset"]) or ws.get_all_values()
            headers = [h.strip() for h in all_vals[0]]
            target_row = int(row_num)
            col_fallbacks = {
                "Merk Model": ["Merk Model", "Merk/ Model"],
            }
            for col_name, new_val in updates_dict.items():
                found = False
                for cand in col_fallbacks.get(col_name, [col_name]):
                    if cand in headers:
                        col_idx = headers.index(cand) + 1
                        ws.update_cell(target_row, col_idx, str(new_val))
                        found = True
                        break
            self._sync_snapshot(force=True)
            return True, "Data barang berhasil diperbarui!"
        except Exception as e:
            return False, f"Gagal memperbarui data barang: {e}"

    def update_employee_row(self, row_num, updates_dict):
        if "No" in updates_dict:
            return False, "Kolom No adalah ID otomatis dan tidak dapat diubah."
        ws = self._find_ws(["DB_Pegawai"])
        if not ws:
            return False, "Data pegawai tidak ditemukan."
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
        rows = self.get_tab_records(["CFG_Users"])
        employees = self.get_employees()
        out = []
        for idx, u in enumerate(rows, start=2):
            nip = str(u.get("NIP", "")).strip()
            nip_clean = "".join(ch for ch in nip if ch.isdigit()) or _normalize_nip(nip)
            role_raw = str(u.get("Role", "")).strip()
            emp = next((e for e in employees if self._nip_matches(e.get("NIP", ""), nip_clean)), None)
            # Determine if the user has a hashed password already
            stored_pwd = str(u.get("Password_Hash", "") or u.get("Password", "")).strip()
            is_hashed = stored_pwd.startswith("pbkdf2:") or stored_pwd.startswith("scrypt:")
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
                "password_secured": is_hashed,  # True = hashed, False = still plain-text (needs migration)
            })
        return out

    @staticmethod
    def _nip_matches(sheet_nip_raw, input_nip_raw):
        s_clean = "".join(ch for ch in str(sheet_nip_raw or "") if ch.isdigit())
        i_clean = "".join(ch for ch in str(input_nip_raw or "") if ch.isdigit())
        if not s_clean or not i_clean:
            return _normalize_nip(sheet_nip_raw) == _normalize_nip(input_nip_raw) and bool(i_clean)
        if s_clean == i_clean:
            return True
        # Handle Excel 15-digit float precision rounding (e.g. 199806212025041001 -> 199806212025041000)
        if len(s_clean) >= 15 and len(i_clean) >= 15 and s_clean[:15] == i_clean[:15]:
            return True
        return False

    def authenticate_employee(self, employee_id_input, password_input):
        clean_id = "".join(ch for ch in str(employee_id_input or "") if ch.isdigit()) or _normalize_nip(employee_id_input)
        pwd = str(password_input or "").strip()
        if not clean_id or not pwd:
            return None

        # Force-sync if CFG_Users wasn't found yet (in case of stale cache)
        users = self.get_tab_records(["CFG_Users", "Users"])
        if not users and self.connected:
            self._sync_snapshot(force=True)
            users = self.get_tab_records(["CFG_Users", "Users"])

        matched_user = None
        needs_rehash = False
        for u in users:
            if not self._nip_matches(u.get("NIP", ""), clean_id):
                continue
            # Try new hashed field first, then legacy field names for migration
            stored_hash = str(u.get("Password_Hash", "") or u.get("Password", "")).strip()
            if not stored_hash:
                continue
            # werkzeug pbkdf2 hashes start with "pbkdf2:" or "scrypt:"
            if stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:"):
                if check_password_hash(stored_hash, pwd):
                    matched_user = u
                    break
            else:
                # Legacy plain-text comparison — still accepted but flagged for rehash
                if stored_hash == pwd:
                    matched_user = u
                    needs_rehash = True
                    break

        if not matched_user:
            return None

        # Upgrade plain-text password to hash transparently
        if needs_rehash:
            try:
                self._upgrade_password_hash(clean_id, pwd)
            except Exception:
                pass  # Non-critical; login still succeeds

        emp_profile = next((e for e in self.get_employees() if self._nip_matches(e.get("NIP", ""), clean_id)), None)
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

    def _upgrade_password_hash(self, nip_clean, plain_password):
        """Replace a legacy plain-text password with a secure bcrypt/pbkdf2 hash in the sheet."""
        ws_usr = self._find_ws(["CFG_Users"])
        if not ws_usr:
            return
        all_vals = self._get_values_from_snapshot(["CFG_Users"]) or ws_usr.get_all_values()
        if not all_vals:
            return
        headers = [h.strip() for h in all_vals[0]]
        # Support both old "Password" and new "Password_Hash" column names
        pwd_col_name = "Password_Hash" if "Password_Hash" in headers else ("Password" if "Password" in headers else None)
        if not pwd_col_name:
            return
        nip_idx = headers.index("NIP") if "NIP" in headers else 0
        pwd_idx = headers.index(pwd_col_name)
        for r_i, row in enumerate(all_vals[1:], start=2):
            if len(row) > nip_idx and self._nip_matches(row[nip_idx], nip_clean):
                new_hash = generate_password_hash(plain_password)
                ws_usr.update_cell(r_i, pwd_idx + 1, new_hash)
                self._sync_snapshot(force=True)
                break

    def save_user_account(self, nip_input, password_input, roles_list):
        nip_clean = _normalize_nip(nip_input)
        if not nip_clean:
            return False, "NIP wajib diisi."
        role_str = "; ".join(parse_roles("; ".join(roles_list))) if isinstance(roles_list, list) else str(roles_list).strip()
        if not role_str:
            role_str = "Pegawai"

        ws_usr = self._find_ws(["CFG_Users"])
        if not ws_usr:
            return False, "Tabel Users tidak ditemukan."
        else:
            try:
                all_vals = self._get_values_from_snapshot(["CFG_Users"]) or ws_usr.get_all_values()
                headers = [h.strip() for h in all_vals[0]] if all_vals else ["NIP", "Password_Hash", "Role"]
                nip_idx = headers.index("NIP") if "NIP" in headers else 0
                # Support both old "Password" and new "Password_Hash" column names
                pwd_col_name = "Password_Hash" if "Password_Hash" in headers else ("Password" if "Password" in headers else None)
                if pwd_col_name is None:
                    return False, "Kolom Password tidak ditemukan di CFG_Users."
                pwd_idx = headers.index(pwd_col_name)
                role_idx = headers.index("Role") if "Role" in headers else 2

                found_row = None
                for r_i, row in enumerate(all_vals[1:], start=2):
                    if len(row) > nip_idx and self._nip_matches(row[nip_idx], nip_clean):
                        found_row = r_i
                        break

                if found_row:
                    if password_input:
                        hashed = generate_password_hash(password_input)
                        ws_usr.update_cell(found_row, pwd_idx + 1, hashed)
                    ws_usr.update_cell(found_row, role_idx + 1, role_str)
                else:
                    # New user: always hash the password before saving
                    plain_pwd = password_input or "rri2026"
                    hashed = generate_password_hash(plain_pwd)
                    ws_usr.append_row([nip_clean, hashed, role_str], value_input_option="USER_ENTERED")
            except Exception as e:
                return False, f"Gagal menyimpan User: {e}"

        self._sync_snapshot(force=True)
        return True, f"Akun user ({nip_clean}) dengan role [{role_str}] berhasil disimpan."

    def change_own_password(self, nip_input, current_password, new_password):
        """Verify current password and update the user's password hash in CFG_Users."""
        clean_id = "".join(ch for ch in str(nip_input or "") if ch.isdigit()) or _normalize_nip(nip_input)
        cur_pwd = str(current_password or "").strip()
        new_pwd = str(new_password or "").strip()
        if not clean_id or not cur_pwd or not new_pwd:
            return False, "Semua kolom password wajib diisi."
        if len(new_pwd) < 8:
            return False, "Password baru minimal 8 karakter."

        ws_usr = self._find_ws(["CFG_Users"])
        if not ws_usr:
            return False, "Tabel Users tidak ditemukan."

        try:
            all_vals = ws_usr.get_all_values()
            if not all_vals:
                return False, "Data user kosong."
            headers = [h.strip() for h in all_vals[0]]
            nip_idx = headers.index("NIP") if "NIP" in headers else 0
            pwd_col_name = "Password_Hash" if "Password_Hash" in headers else ("Password" if "Password" in headers else None)
            if pwd_col_name is None:
                return False, "Kolom Password tidak ditemukan di CFG_Users."
            pwd_idx = headers.index(pwd_col_name)

            found_row = None
            stored_hash = ""
            for r_i, row in enumerate(all_vals[1:], start=2):
                if len(row) > nip_idx and self._nip_matches(row[nip_idx], clean_id):
                    found_row = r_i
                    stored_hash = str(row[pwd_idx]).strip() if len(row) > pwd_idx else ""
                    break

            if not found_row or not stored_hash:
                return False, "Akun user tidak ditemukan."

            if stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:"):
                valid = check_password_hash(stored_hash, cur_pwd)
            else:
                valid = (stored_hash == cur_pwd)

            if not valid:
                return False, "Password saat ini salah."

            ws_usr.update_cell(found_row, pwd_idx + 1, generate_password_hash(new_pwd))
            self._sync_snapshot(force=True)
            return True, "Password berhasil diubah. Gunakan password baru pada login berikutnya."
        except Exception as e:
            return False, f"Gagal mengubah password: {e}"

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
            "DB_Timeline": ["DB_Timeline"],
            "DB_Dialog": ["DB_Dialog"],
            "DB_SDM_Arsip": ["DB_SDM_Arsip"],
            "DB_Info_Board": ["DB_Info_Board"],
        }
        candidates = tab_lookup.get(target_key, [target_key])
        ws = self._find_ws(candidates)

        if not ws:
            return False, f"Tabel {target_key.replace('DB_', '').replace('_', ' ')} tidak ditemukan."

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
                resolved_nip = self._resolve_emp_nip_for_write(raw_nip)
                row_dict["NIP Penanggung Jawab"] = resolved_nip
                row_dict["Penanggungjawab Ruangan"] = resolved_nip
            elif target_key == "DB_Jadwal_Operasional":
                raw_peg = row_dict.get("Pegawai") or row_dict.get("Penyiar") or ""
                row_dict["Pegawai"] = self._resolve_emp_nip_for_write(raw_peg)
            elif target_key == "DB_TMB_Working_Progress":
                for emp_col in ("Record", "Editing", "PIC TMB", "PIC Penyiaran"):
                    if row_dict.get(emp_col):
                        row_dict[emp_col] = self._resolve_emp_nip_for_write(row_dict.get(emp_col))
            elif target_key == "DB_Dialog":
                for emp_col in ("PIC Narasumber", "Operator", "Penyiar"):
                    if row_dict.get(emp_col):
                        row_dict[emp_col] = self._resolve_emp_nip_for_write(row_dict.get(emp_col))

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

    def delete_bast_linked_record(self, target_key, row_num):
        if target_key not in {"DB_BAST", "DB_BMN_Dokumen"}:
            return False, "Jenis data BAST tidak valid."
        try:
            row_num = int(row_num)
        except (TypeError, ValueError):
            return False, "Nomor baris tidak valid."

        self._sync_snapshot(force=True)
        bast_rows = self.get_tab_records(["DB_BAST"], include_row_num=True)
        document_rows = self.get_tab_records(["DB_BMN_Dokumen"], include_row_num=True)
        source_rows = bast_rows if target_key == "DB_BAST" else document_rows
        source = next((row for row in source_rows if int(row.get("_row_num") or 0) == row_num), None)
        if not source:
            return False, "Dokumen BAST tidak ditemukan."

        def is_bast_document(row):
            return (
                str(row.get("Group", "")).strip().lower() == "aset"
                and str(row.get("Sub Menu", "")).strip().lower() == "tutup buku"
                and str(row.get("Kategori Item", "")).strip().lower() == "bast"
            )

        def matching_document(bast_row):
            pdf_link = str(bast_row.get("Link PDF", "")).strip()
            bast_number = str(bast_row.get("Nomor BAST", "")).strip()
            expected_title = f"BAST {bast_number}.pdf".lower()
            for document in document_rows:
                if not is_bast_document(document):
                    continue
                if pdf_link and str(document.get("Link File", "")).strip() == pdf_link:
                    return document
                if expected_title != "bast .pdf" and str(document.get("Judul Dokumen", "")).strip().lower() == expected_title:
                    return document
            return None

        def matching_bast(document_row):
            pdf_link = str(document_row.get("Link File", "")).strip()
            title = str(document_row.get("Judul Dokumen", "")).strip().lower()
            for bast_row in bast_rows:
                if pdf_link and str(bast_row.get("Link PDF", "")).strip() == pdf_link:
                    return bast_row
                bast_number = str(bast_row.get("Nomor BAST", "")).strip()
                if bast_number and title == f"bast {bast_number}.pdf".lower():
                    return bast_row
            return None

        if target_key == "DB_BAST":
            paired_row = matching_document(source)
            paired_key = "DB_BMN_Dokumen"
        elif is_bast_document(source):
            paired_row = matching_bast(source)
            paired_key = "DB_BAST"
        else:
            return self.delete_record(target_key, row_num)

        if paired_row:
            ok, message = self.delete_record(paired_key, paired_row["_row_num"])
            if not ok:
                return False, f"Gagal menghapus data BAST terkait: {message}"

        ok, message = self.delete_record(target_key, row_num)
        if not ok:
            if paired_row:
                return False, f"Baris terkait sudah dihapus, tetapi penghapusan baris ini gagal: {message}"
            return False, message

        return True, "Data BAST dan dokumen terkait berhasil dihapus." if paired_row else message

    def delete_record(self, target_key, row_num):
        tab_lookup = {
            "DB_Timeline": ["DB_Timeline"],
            "DB_Dialog": ["DB_Dialog"],
            "DB_SDM_Arsip": ["DB_SDM_Arsip"],
            "DB_Info_Board": ["DB_Info_Board"],
        }
        candidates = tab_lookup.get(target_key, [target_key])
        ws = self._find_ws(candidates)
        if not ws:
            return False, f"Tabel {target_key.replace('DB_', '').replace('_', ' ')} tidak ditemukan."
        try:
            ws.delete_rows(int(row_num))
            self._sync_snapshot(force=True)
            return True, f"Data berhasil dihapus!"
        except Exception as e:
            return False, f"Gagal menghapus baris: {e}"