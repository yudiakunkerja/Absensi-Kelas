# 🎒 Panduan Deploy Absensi Ceria ke Streamlit Cloud

## Langkah 1 — Persiapan Google Sheets

1. Buka spreadsheet kamu: https://docs.google.com/spreadsheets/d/1bjrCAF1WSQORDhgCE8yT2RMP7sydzGmbbTXddW1uO_Q
2. Pastikan ada 2 sheet:
   - **DaftarSiswa** → kolom A: header "Nama Siswa", lalu nama-nama siswa di bawahnya
   - **Sheet1** → akan diisi otomatis oleh aplikasi (kolom: Tanggal, Jam, Nama, Status, Keterangan)

## Langkah 2 — Setup Google Service Account

1. Buka https://console.cloud.google.com
2. Buat/pilih project
3. Aktifkan API: **Google Sheets API** dan **Google Drive API**
4. Buat **Service Account**: IAM & Admin > Service Accounts > Create
5. Download file JSON kredensial
6. Share spreadsheet kamu dengan email service account (misal: `nama@project.iam.gserviceaccount.com`) dengan akses **Editor**

## Langkah 3 — Upload ke GitHub

1. Upload semua file ini ke repository GitHub (public atau private)
2. **JANGAN** upload file `secrets.toml` — itu hanya contoh!

## Langkah 4 — Deploy di Streamlit Cloud

1. Buka https://share.streamlit.io dan login
2. Klik **New app** > pilih repo GitHub kamu
3. Set **Main file path**: `app.py`
4. Klik **Advanced settings > Secrets**

## Langkah 5 — Isi Secrets di Streamlit Cloud

Copy-paste format ini ke kotak Secrets (ganti nilainya dengan dari file JSON kamu):

```toml
guru_password = "password_guru_kamu"

[gcp_service_account]
type = "service_account"
project_id = "nama-project-kamu"
private_key_id = "xxxx"
private_key = '''-----BEGIN RSA PRIVATE KEY-----
ISI_PRIVATE_KEY_DARI_FILE_JSON_DISINI
-----END RSA PRIVATE KEY-----
'''
client_email = "nama-akun@project.iam.gserviceaccount.com"
client_id = "000000000000000"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/1/certs/nama-akun%40project.iam.gserviceaccount.com"
```

⚠️ **PENTING untuk private_key**: Gunakan tanda petik tiga (''') agar format TOML tidak error.

## Fitur Aplikasi

### 🎒 Halaman Utama (Siswa)
- Pilih nama dari daftar
- Pilih status: Hadir / Izin / Sakit
- Tambahkan keterangan opsional
- Klik tombol absen

### 🔒 Menu Guru (password protected)
- **Tab Data Siswa**: Lihat, tambah, dan hapus siswa
- **Tab Rekap Absensi**: Filter berdasarkan tanggal, cari nama, lihat statistik
- **Tab Rekap Mingguan**: Rekap per siswa dalam satu minggu, identifikasi siswa hadir penuh

## Troubleshooting

| Error | Solusi |
|-------|--------|
| `Malformed JSON` | Pastikan private_key menggunakan `'''` (triple quote) |
| `Invalid padding` | Pastikan tidak ada spasi ekstra di private_key |
| `Spreadsheet not found` | Pastikan service account sudah di-share ke spreadsheet |
| `Worksheet not found` | Sheet akan dibuat otomatis saat pertama kali diakses |
