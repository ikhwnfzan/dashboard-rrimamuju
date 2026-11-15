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
CACHE_TTL = 45  # seconds
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


DEMO_DATA = {
    "Timeline": [
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pendaftaran dibuka", "Start Date": "08/01/2026", "End Date": "08/01/2026", "Keterangan": "Online & Kantor LPP RRI Mamuju", "Tanggal": "01 Aug 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/19/2026", "End Date": "08/19/2026", "Keterangan": "SMAN 2 Mamuju", "Tanggal": "19 Aug 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/20/2026", "End Date": "08/20/2026", "Keterangan": "SMAN 3 Mamuju", "Tanggal": "20 Aug 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/24/2026", "End Date": "08/24/2026", "Keterangan": "SMKN Rangas & SMKN 1", "Tanggal": "24 Aug 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Bersih-Bersih Lingkungan", "Start Date": "08/28/2026", "End Date": "08/28/2026", "Keterangan": "Pantai Manakarra", "Tanggal": "28 Aug 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Rangkaian Kegiatan RRI Fest", "Start Date": "08/30/2026", "End Date": "08/30/2026", "Keterangan": "Senam, CKG, Bazaar", "Tanggal": "30 Aug 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Olahraga Keluarga", "Start Date": "09/05/2026", "End Date": "09/06/2026", "Keterangan": "Acara Internal & Lomba", "Tanggal": "06 Sep 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Upacara dan Penyuluhan Obor", "Start Date": "09/11/2026", "End Date": "09/11/2026", "Keterangan": "Auditorium LPP RRI Mamuju", "Tanggal": "11 Sep 2026"},
        {"Kegiatan": "Lomba Pidato", "Tahapan": "Pelaksanaan Lomba Pidato", "Start Date": "09/13/2026", "End Date": "09/13/2026", "Keterangan": "Aula Lt. 2 RRI Mamuju", "Tanggal": "13 Sep 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Tahap I tingkat Korwil", "Start Date": "09/28/2026", "End Date": "09/28/2026", "Keterangan": "", "Tanggal": "28 Sep 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Tahap II tingkat Korwil", "Start Date": "10/01/2026", "End Date": "10/01/2026", "Keterangan": "", "Tanggal": "01 Oct 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pengumuman lolos nasional", "Start Date": "10/05/2026", "End Date": "10/05/2026", "Keterangan": "", "Tanggal": "05 Oct 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Seleksi antar korwil", "Start Date": "10/12/2026", "End Date": "10/12/2026", "Keterangan": "", "Tanggal": "12 Oct 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Final tingkat nasional", "Start Date": "10/28/2026", "End Date": "10/28/2026", "Keterangan": "", "Tanggal": "28 Oct 2026"}
    ],
    "Agenda_Setting": [
        {
            "No": "1",
            "Tanggal": "Tuesday, 01 September 2026",
            "Program": "Dialog Interaktif Pro 1",
            "Topik/ Isu": "Kesiapan Pelaksanaan RRI Fest & Bintang Radio Mamuju 2026",
            "Narasumber": "Ketua Panitia RRI Fest Mamuju",
            "Foto Narasumber": "",
            "Jabatan/ Instansi": "Koordinator LPU LPP RRI Mamuju",
            "KET. Kehadiran": "Hadir di Studio",
            "PIC Narasumber": "Tim Siaran Pro 1",
            "Flyer": "https://www.instagram.com/rri_mamuju/",
            "Keterlaksanaan": "Terlaksana",
            "Kendala": "-"
        },
        {
            "No": "1",
            "Tanggal": "Tuesday, 01 September 2026",
            "Program": "Pro 2 Music Live Chat",
            "Topik/ Isu": "Ruang Kreatif Musisi Muda Sulawesi Barat",
            "Narasumber": "AELEA Band",
            "Foto Narasumber": "",
            "Jabatan/ Instansi": "Musisi Lokal Mamuju",
            "KET. Kehadiran": "Hadir di Studio",
            "PIC Narasumber": "Tim KMB / Pro 2",
            "Flyer": "https://www.youtube.com/@LPPRRIMamuju",
            "Keterlaksanaan": "Terlaksana",
            "Kendala": "-"
        },
        {
            "No": "2",
            "Tanggal": "Wednesday, 02 September 2026",
            "Program": "Dialog Tematik Pemberitaan",
            "Topik/ Isu": "Literasi Digital & Pencegahan Hoax di Sulawesi Barat",
            "Narasumber": "Koordinator Wilayah Mafindo Sulbar",
            "Foto Narasumber": "",
            "Jabatan/ Instansi": "Mafindo Sulawesi Barat",
            "KET. Kehadiran": "Konfirmasi Hadir",
            "PIC Narasumber": "Redaksi Pemberitaan",
            "Flyer": "",
            "Keterlaksanaan": "Terjadwal",
            "Kendala": "-"
        }
    ],
    "Planner": [
        {
            "ID": "CNT-01",
            "Tanggal_Tayang": "2026-11-16",
            "Platform": "Instagram & TikTok",
            "Akun": "@pro2_mamuju",
            "Judul_Konten": "Teaser Reels Pro 2 Music Live Chat Edisi Minggu Ini",
            "Jenis": "Reels / Short Video",
            "Divisi": "KMB / Pro 2",
            "PIC": "Tim Kreatif Pro 2",
            "Status": "Review",
            "Link_Asset": "https://drive.google.com"
        },
        {
            "ID": "CNT-02",
            "Tanggal_Tayang": "2026-11-16",
            "Platform": "Portal Web & IG",
            "Akun": "rri.co.id/mamuju",
            "Judul_Konten": "Liputan Khusus Infrastruktur & Pelayanan Publik Mamuju",
            "Jenis": "Artikel Berita + Infografis",
            "Divisi": "Pemberitaan",
            "PIC": "Redaksi Pemberitaan",
            "Status": "Tayang",
            "Link_Asset": "https://rri.co.id/mamuju"
        }
    ],
    "Siaran": [
        {
            "Tanggal": "2026-11-16",
            "Shift": "Pagi (05:00 - 12:00 WITA)",
            "Programa": "Pro 1 (96.0 FM)",
            "Penyiar": "Penyiar Shift Pagi A",
            "Operator": "Operator TMB 1",
            "Status": "On Duty"
        },
        {
            "Tanggal": "2026-11-16",
            "Shift": "Pagi - Siang (06:00 - 15:00 WITA)",
            "Programa": "Pro 2 (89.3 FM)",
            "Penyiar": "Host Pro 2 Pagi",
            "Operator": "Operator Pro 2 A",
            "Status": "On Duty"
        }
    ],
    "Arsip": [
        {
            "Kode_Arsip": "PPID-RRI/129/2026",
            "Tanggal": "2026-08-31",
            "Kategori": "PPID - Acara Siaran",
            "Judul": "Rekaman & Naskah Mimbar Agama Hindu (Berkala)",
            "Divisi": "Siaran / PPID",
            "Link": "https://mamuju.ppid.rri.go.id/"
        },
        {
            "Kode_Arsip": "YT-PRO2-2026-08",
            "Tanggal": "2026-08-28",
            "Kategori": "Video Siaran",
            "Judul": "Pro 2 Music Live Chat - AELEA (Full Session)",
            "Divisi": "Pro 2 / KMB",
            "Link": "https://www.youtube.com/@LPPRRIMamuju"
        }
    ],
    "Info_Pegawai": [
        {
            "ID": "INF-01",
            "Tanggal": "2026-11-15",
            "Prioritas": "Urgent",
            "Judul": "Sinkronisasi Input Rencana Anggaran & Realisasi Triwulan IV",
            "Isi": "Seluruh koordinator bidang (Perencanaan, KMB, Pemberitaan, LPU, Keuangan) dimohon memperbarui matriks kegiatan pada Google Sheet master sebelum rapat evaluasi Senin pukul 09.00 WITA.",
            "Target_Divisi": "Semua Divisi",
            "Lampiran": "https://sakti.kemenkeu.go.id"
        }
    ],
    "Users": [
        {"Username": "admin", "Nama": "Admin Portal RRI Mamuju", "Divisi": "Perencanaan & IT", "Role": "Admin", "PIN": "2026"},
        {"Username": "siaran", "Nama": "Koordinator Siaran & Penyiar", "Divisi": "Siaran", "Role": "Staff", "PIN": "1234"},
        {"Username": "kmb", "Nama": "Tim KMB & Konten Digital", "Divisi": "KMB", "Role": "Staff", "PIN": "1234"},
        {"Username": "lpu", "Nama": "Tim LPU & Event", "Divisi": "LPU", "Role": "Staff", "PIN": "1234"}
    ]
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


def _format_gspread_error(err, client_email="", sheet_id=""):
    err_type = type(err).__name__
    err_str = str(err)
    if "SpreadsheetNotFound" in err_type or "404" in err_str:
        return (
            f"Spreadsheet tidak ditemukan / belum di-Share ke Service Account. "
            f"Pastikan Google Sheet ({sheet_id}) sudah di-Share sebagai Editor ke: {client_email}"
        )
    if "PERMISSION_DENIED" in err_str or "403" in err_str:
        return (
            f"Akses ditolak (403). Aktifkan Google Sheets API & Google Drive API di Google Cloud, "
            f"lalu Share sheet ke: {client_email}"
        )
    if "FAILED_PRECONDITION" in err_str or "not supported for this document" in err_str:
        return "File di Drive masih format Excel (.xlsx). Buka di Google Sheets -> File -> Save as Google Sheets."
    return f"{err_type}: {err_str}"


class SheetsDB:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        if "/spreadsheets/d/" in self.sheet_id:
            self.sheet_id = self.sheet_id.split("/spreadsheets/d/")[1].split("/")[0]

        self.creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
        self.timeline_tab = os.getenv("TIMELINE_TAB_NAME", "Sheet1").strip()
        self.dialog_tab = os.getenv("DIALOG_TAB_NAME", "Agenda Setting").strip()
        self.client = None
        self.spreadsheet = None
        self.connected = False
        self.last_error = None
        self.service_email = ""
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
            self.last_error = "GOOGLE_SHEET_ID belum diisi di file .env (Mode Demo)."
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
                self.last_error = "File service_account.json tidak ditemukan di folder app.py (Mode Demo)."
                return

            if not self.service_email or info.get("type") != "service_account":
                self.last_error = "JSON bukan Service Account (pastikan 'type': 'service_account', bukan OAuth client_id)."
                return

            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.connected = True
            self.last_error = None
            print(f"[SheetsDB] Connected to '{self.spreadsheet.title}' via {self.service_email}")
        except Exception as e:
            self.connected = False
            self.last_error = _format_gspread_error(e, self.service_email, self.sheet_id)
            print("[SheetsDB] Connection Error:", self.last_error)
            traceback.print_exc()

    def clear_cache(self, tab_name=None):
        if tab_name:
            _CACHE.pop(tab_name, None)
        else:
            _CACHE.clear()
        if not self.connected:
            self._connect()

    def _find_worksheet(self, candidates):
        ws_map = {ws.title.strip().lower(): ws for ws in self.spreadsheet.worksheets()}
        for name in candidates:
            key = name.strip().lower()
            if key in ws_map:
                return ws_map[key]
        return None

    def get_timeline(self):
        cache_key = "timeline"
        now = time.time()
        if cache_key in _CACHE and now - _CACHE[cache_key][0] < CACHE_TTL:
            return _CACHE[cache_key][1]

        if not self.connected:
            return DEMO_DATA["Timeline"]

        try:
            ws = self._find_worksheet([self.timeline_tab, "Sheet1", "Events", "Timeline"])
            if not ws:
                return DEMO_DATA["Timeline"]
            rows = ws.get_all_records()
            cleaned = [r for r in rows if any(str(v).strip() for v in r.values())]
            _CACHE[cache_key] = (now, cleaned)
            return cleaned
        except Exception as e:
            self.last_error = f"Error Timeline: {e}"
            return DEMO_DATA["Timeline"]

    def get_agenda_setting(self):
        cache_key = "agenda_setting"
        now = time.time()
        if cache_key in _CACHE and now - _CACHE[cache_key][0] < CACHE_TTL:
            return _CACHE[cache_key][1]

        if not self.connected:
            return DEMO_DATA["Agenda_Setting"]

        try:
            ws = self._find_worksheet([self.dialog_tab, "Agenda Setting", "Dialog"])
            if not ws:
                return DEMO_DATA["Agenda_Setting"]

            all_values = ws.get_all_values()
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

            for raw_row in all_values[header_idx + 1:]:
                padded = raw_row + [""] * (len(headers) - len(raw_row))
                item = {headers[i]: padded[i].strip() for i in range(len(headers)) if headers[i]}

                if item.get("No"):
                    last_no = item["No"]
                else:
                    item["No"] = last_no

                if item.get("Tanggal"):
                    last_tanggal = item["Tanggal"]
                else:
                    item["Tanggal"] = last_tanggal

                has_content = any([
                    item.get("Program", ""),
                    item.get("Topik/ Isu", ""),
                    item.get("Topik", ""),
                    item.get("Narasumber", "")
                ])
                if has_content:
                    parsed_rows.append(item)

            _CACHE[cache_key] = (now, parsed_rows)
            return parsed_rows
        except Exception as e:
            self.last_error = f"Error Agenda Setting: {e}"
            return DEMO_DATA["Agenda_Setting"]

    def get_records(self, tab_name):
        now = time.time()
        if tab_name in _CACHE and now - _CACHE[tab_name][0] < CACHE_TTL:
            return _CACHE[tab_name][1]

        if not self.connected:
            return DEMO_DATA.get(tab_name, [])

        try:
            ws = self._find_worksheet([tab_name])
            if not ws:
                return DEMO_DATA.get(tab_name, [])
            rows = ws.get_all_records()
            _CACHE[tab_name] = (now, rows)
            return rows
        except Exception as e:
            self.last_error = f"Error tab '{tab_name}': {e}"
            return DEMO_DATA.get(tab_name, [])

    def append_record(self, target_key, row_dict):
        if not self.connected:
            DEMO_DATA.setdefault(target_key, []).append(row_dict)
            self.clear_cache()
            return True, "Disimpan sementara (Mode Demo)."

        try:
            if target_key == "Timeline":
                ws = self._find_worksheet([self.timeline_tab, "Sheet1", "Events"])
                headers = ws.row_values(1)
                row_values = [str(row_dict.get(h.strip(), "")) for h in headers]
                ws.append_row(row_values, value_input_option="USER_ENTERED")
            elif target_key == "Agenda_Setting":
                ws = self._find_worksheet([self.dialog_tab, "Agenda Setting", "Dialog"])
                all_values = ws.get_all_values()
                header_idx = 0
                for idx, r in enumerate(all_values[:10]):
                    lowered = [c.strip().lower() for c in r]
                    if "tanggal" in lowered and "program" in lowered:
                        header_idx = idx
                        break
                headers = [h.strip() for h in all_values[header_idx]]
                row_values = [str(row_dict.get(h, "")) for h in headers]
                ws.append_row(row_values, value_input_option="USER_ENTERED")
            else:
                ws = self._find_worksheet([target_key])
                if not ws:
                    return False, f"Tab '{target_key}' belum ada di Google Sheet."
                headers = ws.row_values(1)
                row_values = [str(row_dict.get(h.strip(), "")) for h in headers]
                ws.append_row(row_values, value_input_option="USER_ENTERED")

            self.clear_cache()
            return True, "Data berhasil disimpan ke Google Sheets!"
        except Exception as e:
            return False, f"Gagal menyimpan: {e}"

    def init_missing_tabs(self):
        if not self.connected:
            return False, "Google Sheet belum terhubung."

        existing = [ws.title.strip().lower() for ws in self.spreadsheet.worksheets()]
        created = []
        for tab_name in ["Planner", "Siaran", "Arsip", "Info_Pegawai", "Users"]:
            if tab_name.lower() not in existing:
                sample_rows = DEMO_DATA[tab_name]
                headers = list(sample_rows[0].keys())
                ws = self.spreadsheet.add_worksheet(title=tab_name, rows=200, cols=len(headers) + 2)
                ws.append_row(headers)
                for row in sample_rows:
                    ws.append_row([str(row.get(h, "")) for h in headers])
                created.append(tab_name)
        self.clear_cache()
        if created:
            return True, f"Tab baru berhasil dibuat: {', '.join(created)}"
        return True, "Semua tab pendukung sudah tersedia."