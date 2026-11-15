import os
import json
import time
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_CACHE = {}
CACHE_TTL = 45  # seconds


DEMO_DATA = {
    "Timeline": [
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pendaftaran dibuka", "Start Date": "08/01/2026", "End Date": "08/01/2026", "Keterangan": "", "Tanggal": "1 Agustus 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/19/2026", "End Date": "08/19/2026", "Keterangan": "SMAN 2 Mamuju", "Tanggal": "19 Agustus 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/20/2026", "End Date": "08/20/2026", "Keterangan": "SMAN 3 Mamuju", "Tanggal": "20 Agustus 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/22/2026", "End Date": "08/22/2026", "Keterangan": "SMAN 1 Mamuju", "Tanggal": "22 Agustus 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Audisi offline", "Start Date": "08/24/2026", "End Date": "08/24/2026", "Keterangan": "SMKN Rangas & SMKN 1", "Tanggal": "24 Agustus 2026"},
        {"Kegiatan": "Lomba Pidato", "Tahapan": "Pendaftaran dibuka", "Start Date": "08/26/2026", "End Date": "08/26/2026", "Keterangan": "Publikasi", "Tanggal": "26 Agustus 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Bersih-Bersih Lingkungan", "Start Date": "08/28/2026", "End Date": "08/28/2026", "Keterangan": "Pantai Manakarra", "Tanggal": "28 Agustus 2026"},
        {"Kegiatan": "RRI Fest", "Tahapan": "Rangkaian Kegiatan RRI Fest", "Start Date": "08/30/2026", "End Date": "08/30/2026", "Keterangan": "Senam, CKG, Bazaar", "Tanggal": "30 Agustus 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Olahraga Keluarga", "Start Date": "09/05/2026", "End Date": "09/06/2026", "Keterangan": "Acara Internal & Lomba", "Tanggal": "6 September 2026"},
        {"Kegiatan": "Hari Radio", "Tahapan": "Upacara dan Penyuluhan Obor", "Start Date": "09/11/2026", "End Date": "09/11/2026", "Keterangan": "", "Tanggal": "11 September 2026"},
        {"Kegiatan": "Lomba Pidato", "Tahapan": "Pelaksanaan Lomba Pidato", "Start Date": "09/13/2026", "End Date": "09/13/2026", "Keterangan": "", "Tanggal": "13 September 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Putaran I", "Start Date": "09/17/2026", "End Date": "09/17/2026", "Keterangan": "Pop indonesia", "Tanggal": "17 September 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Putaran II", "Start Date": "09/18/2026", "End Date": "09/18/2026", "Keterangan": "Pop daerah", "Tanggal": "18 September 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Pengumuman", "Start Date": "09/18/2026", "End Date": "09/18/2026", "Keterangan": "Hasil penilaian juri + voting", "Tanggal": "Pengumuman juara"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Tahap I tingkat Korwil", "Start Date": "09/28/2026", "End Date": "09/28/2026", "Keterangan": "", "Tanggal": "28 September 2026"},
        {"Kegiatan": "Bintang Radio", "Tahapan": "Seleksi antar korwil", "Start Date": "10/12/2026", "End Date": "10/12/2026", "Keterangan": "", "Tanggal": "12 October 2026"}
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
        },
        {
            "ID": "CNT-03",
            "Tanggal_Tayang": "2026-11-17",
            "Platform": "Instagram & Facebook",
            "Akun": "@rri_mamuju",
            "Judul_Konten": "Flyer Jadwal Agenda Setting & Dialog Interaktif Mingguan",
            "Jenis": "Flyer Desain",
            "Divisi": "LPU & Siaran",
            "PIC": "Desainer Grafis",
            "Status": "Desain",
            "Link_Asset": "https://drive.google.com"
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
            "Shift": "Siang (12:00 - 18:00 WITA)",
            "Programa": "Pro 1 (96.0 FM)",
            "Penyiar": "Penyiar Shift Siang B",
            "Operator": "Operator TMB 2",
            "Status": "Terjadwal"
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
        },
        {
            "Kode_Arsip": "LAP-BR-2026",
            "Tanggal": "2026-09-05",
            "Kategori": "Dokumentasi Event",
            "Judul": "Laporan & Galeri Bintang Radio & RRI Fest Mamuju 2026",
            "Divisi": "LPU",
            "Link": "https://linktr.ee/rri_mamuju"
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
        },
        {
            "ID": "INF-02",
            "Tanggal": "2026-11-14",
            "Prioritas": "Info",
            "Judul": "Pembaruan SOP Metadata & Upload Arsip Siaran ke Portal PPID",
            "Isi": "Setiap program dialog tematik dan mimbar agama wajib diarsipkan maksimal H+1 beserta tautan YouTube/rekaman audio untuk pelaporan berkala PPID.",
            "Target_Divisi": "Siaran, Pemberitaan, KMB",
            "Lampiran": "https://mamuju.ppid.rri.go.id/"
        }
    ],
    "Users": [
        {"Username": "admin", "Nama": "Admin Portal RRI Mamuju", "Divisi": "Perencanaan & IT", "Role": "Admin", "PIN": "2026"},
        {"Username": "siaran", "Nama": "Koordinator Siaran & Penyiar", "Divisi": "Siaran", "Role": "Staff", "PIN": "1234"},
        {"Username": "kmb", "Nama": "Tim KMB & Konten Digital", "Divisi": "KMB", "Role": "Staff", "PIN": "1234"},
        {"Username": "lpu", "Nama": "Tim LPU & Event", "Divisi": "LPU", "Role": "Staff", "PIN": "1234"}
    ]
}


class SheetsDB:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
        self.timeline_tab = os.getenv("TIMELINE_TAB_NAME", "Sheet1").strip()
        self.dialog_tab = os.getenv("DIALOG_TAB_NAME", "Agenda Setting").strip()
        self.client = None
        self.spreadsheet = None
        self.connected = False
        self.last_error = None
        self._connect()

    def _connect(self):
        if not self.sheet_id:
            self.last_error = "GOOGLE_SHEET_ID belum diatur (berjalan dalam Mode Demo)."
            return

        try:
            if self.creds_json:
                creds_dict = json.loads(self.creds_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                self.client = gspread.authorize(creds)
            elif os.path.exists("service_account.json"):
                creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
                self.client = gspread.authorize(creds)
            else:
                self.last_error = "Kredensial Service Account tidak ditemukan (berjalan dalam Mode Demo)."
                return

            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.connected = True
            self.last_error = None
        except Exception as e:
            self.connected = False
            self.last_error = str(e)

    def clear_cache(self, tab_name=None):
        if tab_name:
            _CACHE.pop(tab_name, None)
        else:
            _CACHE.clear()

    def _find_worksheet(self, candidates):
        """Find the first matching worksheet name (case-insensitive)."""
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
            self.last_error = f"Error membaca Timeline: {e}"
            return DEMO_DATA["Timeline"]

    def get_agenda_setting(self):
        """
        Reads the 'Agenda Setting' sheet where:
        - Header row is located dynamically (usually Row 3: No, Tanggal, Program, Topik/ Isu, Narasumber, ...)
        - Columns 'No' and 'Tanggal' are merged across 6 rows per day, so empty cells inherit the previous date.
        - Blank placeholder rows (where Program, Topik/ Isu, and Narasumber are all empty) are filtered out.
        """
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

            # Locate the header row containing 'Tanggal' and 'Program'
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
                # Pad row length to match headers
                padded = raw_row + [""] * (len(headers) - len(raw_row))
                item = {headers[i]: padded[i].strip() for i in range(len(headers)) if headers[i]}

                # Forward-fill merged cells for No and Tanggal
                if item.get("No"):
                    last_no = item["No"]
                else:
                    item["No"] = last_no

                if item.get("Tanggal"):
                    last_tanggal = item["Tanggal"]
                else:
                    item["Tanggal"] = last_tanggal

                # Keep only rows that have actual content in Program, Topik/ Isu, or Narasumber
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
            self.last_error = f"Error membaca Agenda Setting: {e}"
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
            self.last_error = f"Error membaca tab '{tab_name}': {e}"
            return DEMO_DATA.get(tab_name, [])

    def append_record(self, target_key, row_dict):
        if not self.connected:
            DEMO_DATA.setdefault(target_key, []).append(row_dict)
            self.clear_cache()
            return True, "Disimpan sementara (Mode Demo - hubungkan Google Sheet untuk penyimpanan permanen)."

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
                    return False, f"Tab '{target_key}' belum ada di Google Sheet. Klik tombol 'Init Sheet' terlebih dahulu."
                headers = ws.row_values(1)
                row_values = [str(row_dict.get(h.strip(), "")) for h in headers]
                ws.append_row(row_values, value_input_option="USER_ENTERED")

            self.clear_cache()
            return True, "Data berhasil disimpan ke Google Sheets!"
        except Exception as e:
            return False, f"Gagal menyimpan ke Google Sheets: {e}"

    def init_missing_tabs(self):
        """Creates only the new employee/archive tabs without touching your existing Sheet1 and Agenda Setting."""
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
            return True, f"Tab baru berhasil dibuat: {', '.join(created)} (Tab existing Anda tetap aman)."
        return True, "Semua tab pendukung sudah tersedia di Google Sheet Anda."
