# RRI Mamuju — Digital Board & Employee Portal (v2 — Kompatibel dengan Sheet Eksisting)

Versi ini sudah disesuaikan 100% dengan struktur tab Google Sheet Anda yang sudah berjalan:
1. **`Sheet1` (Timeline):** Membaca langsung kolom `Kegiatan`, `Tahapan`, `Start Date`, `End Date`, `Keterangan`, dan `Tanggal` lengkap dengan tombol filter otomatis per kegiatan (*Bintang Radio*, *Lomba Pidato*, *RRI Fest*, *Hari Radio*).
2. **`Agenda Setting` (Dialog):** Mendeteksi header di baris ke-3 secara otomatis, meneruskan nilai sel gabungan (*merged cells*) pada kolom `No` dan `Tanggal`, menyaring baris kosong, dan menampilkan `Program`, `Topik/ Isu`, `Narasumber`, `Jabatan/ Instansi`, `KET. Kehadiran`, `PIC Narasumber`, `Flyer`, `Keterlaksanaan`, dan `Kendala`.
3. **Tab Pendukung Baru (`Planner`, `Siaran`, `Arsip`, `Info_Pegawai`, `Users`):** Dapat dibuat otomatis hanya dengan 1 klik tombol **⚙ Init Tab Baru** (setelah login sebagai `admin` / PIN `2026`) tanpa menyentuh atau mengubah tab `Sheet1` dan `Agenda Setting` Anda.

## Cara Deploy ke Render (Docker)
1. Ekstrak ZIP ini dan upload ke repository **GitHub**.
2. Buat **Web Service** baru di **Render** dengan Runtime **Docker**.
3. Isi Environment Variables di Render:
   - `FLASK_SECRET_KEY`: teks acak rahasia
   - `GOOGLE_SHEET_ID`: ID Google Spreadsheet master Anda (yang berisi `Sheet1` dan `Agenda Setting`)
   - `GOOGLE_CREDENTIALS_JSON`: isi file JSON Service Account Google Cloud Anda (pastikan email Service Account sudah di-Share sebagai **Editor** di Spreadsheet tersebut).
