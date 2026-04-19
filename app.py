import streamlit as st
from datetime import datetime
import gspread
import pytz
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import math
import io
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Absensi Ceria - SD KARYABINANGKIT",
    page_icon="🎒",
    layout="centered"
)

SPREADSHEET_ID = "1bjrCAF1WSQORDhgCE8yT2RMP7sydzGmbbTXddW1uO_Q"
WIB = pytz.timezone('Asia/Jakarta')

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheet_conn():
    try:
        secret = st.secrets["gcp_service_account"]
        creds_dict = {
            "type": secret["type"],
            "project_id": secret["project_id"],
            "private_key_id": secret["private_key_id"],
            "private_key": secret["private_key"],
            "client_email": secret["client_email"],
            "client_id": secret["client_id"],
            "auth_uri": secret["auth_uri"],
            "token_uri": secret["token_uri"],
            "auth_provider_x509_cert_url": secret["auth_provider_x509_cert_url"],
            "client_x509_cert_url": secret["client_x509_cert_url"],
            "universe_domain": secret.get("universe_domain", "googleapis.com"),
        }
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return None

# --- 3. FUNGSI AMBIL DATA ---
@st.cache_data(ttl=60)
def get_data_siswa():
    try:
        client = get_sheet_conn()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet("DaftarSiswa")
        data = ws.col_values(1)
        return [v for v in data if v and v.strip() and v.strip() != "Nama Siswa"]
    except Exception as e:
        st.error(f"Gagal ambil data siswa: {e}")
        return []

@st.cache_data(ttl=60)
def get_data_absen():
    try:
        client = get_sheet_conn()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet("Sheet1")
        return ws.get_all_values()
    except Exception as e:
        st.error(f"Gagal ambil data absen: {e}")
        return []

@st.cache_data(ttl=300)
def get_pengaturan():
    try:
        client = get_sheet_conn()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet("Pengaturan")
        data = ws.get_all_values()
        pengaturan = {}
        for baris in data:
            if len(baris) >= 2:
                pengaturan[baris[0].strip()] = baris[1].strip()
        return pengaturan
    except Exception as e:
        st.error(f"Gagal ambil pengaturan: {e}")
        return {}

def simpan_pengaturan(key, value):
    try:
        client = get_sheet_conn()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet("Pengaturan")
        data = ws.get_all_values()
        for i, baris in enumerate(data):
            if len(baris) >= 1 and baris[0].strip() == key:
                ws.update_cell(i + 1, 2, value)
                get_pengaturan.clear()
                return True
        ws.append_row([key, value])
        get_pengaturan.clear()
        return True
    except Exception as e:
        st.error(f"Gagal simpan pengaturan: {e}")
        return False

def get_worksheet(name):
    client = get_sheet_conn()
    if client:
        sh = client.open_by_key(SPREADSHEET_ID)
        try:
            return sh.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=name, rows=1000, cols=10)
            return ws
    return None

def rapikan_baris(baris, jumlah_kolom=5):
    baris = list(baris)
    while len(baris) < jumlah_kolom:
        baris.append("")
    return baris[:jumlah_kolom]

def cek_sudah_absen(nama, tanggal_hari_ini):
    try:
        data = get_data_absen()
        for baris in data:
            if len(baris) >= 3:
                if baris[0] == tanggal_hari_ini and baris[2] == nama:
                    return True
        return False
    except:
        return False

def hitung_jarak(lat1, lon1, lat2, lon2):
    """Hitung jarak antara 2 koordinat dalam meter (Haversine)"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def cek_waktu_absen():
    """
    Cek apakah sekarang waktu absen siswa
    Return: (boleh_absen, pesan)
    """
    now = datetime.now(WIB)
    hari = now.weekday()  # 0=Senin, 6=Minggu
    jam = now.hour
    menit = now.minute

    if hari >= 5:  # Sabtu/Minggu
        return False, "🏖️ Hari ini Sabtu/Minggu, absen libur!"

    waktu_sekarang = jam * 60 + menit
    buka = 7 * 60       # 07.00
    tutup = 8 * 60      # 08.00

    if waktu_sekarang < buka:
        return False, "⏳ Absen belum dibuka. Dibuka jam 07.00 WIB"
    elif waktu_sekarang > tutup:
        return False, "🔒 Waktu absen sudah ditutup sejak jam 08.00 WIB"
    else:
        sisa = tutup - waktu_sekarang
        return True, f"✅ Absen dibuka! Sisa waktu: {sisa} menit"

def tambah_log(aksi, detail, pelaku="Guru"):
    try:
        client = get_sheet_conn()
        sh = client.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet("LogAktivitas")
        except:
            ws = sh.add_worksheet(title="LogAktivitas", rows=1000, cols=5)
            ws.append_row(["Waktu", "Pelaku", "Aksi", "Detail"])
        now = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([now, pelaku, aksi, detail])
    except:
        pass

# --- 4. GENERATE PDF ---
def generate_pdf(df_bulan, nama_sekolah, nama_wali, tahun_ajaran, bulan_tahun):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # Header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, nama_sekolah, ln=True, align='C')
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'LAPORAN ABSENSI SISWA', ln=True, align='C')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f'Bulan: {bulan_tahun}', ln=True, align='C')
    pdf.cell(0, 7, f'Tahun Ajaran: {tahun_ajaran}', ln=True, align='C')
    pdf.ln(5)

    # Garis
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Tabel Header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(70, 130, 180)
    pdf.set_text_color(255, 255, 255)

    col_no = 10
    col_nama = 75
    col_h = 18
    col_i = 18
    col_s = 18
    col_t = 22
    col_pct = 20

    pdf.cell(col_no, 9, 'No', border=1, align='C', fill=True)
    pdf.cell(col_nama, 9, 'Nama Siswa', border=1, align='C', fill=True)
    pdf.cell(col_h, 9, 'Hadir', border=1, align='C', fill=True)
    pdf.cell(col_i, 9, 'Izin', border=1, align='C', fill=True)
    pdf.cell(col_s, 9, 'Sakit', border=1, align='C', fill=True)
    pdf.cell(col_t, 9, 'Terlambat', border=1, align='C', fill=True)
    pdf.cell(col_pct, 9, '%', border=1, align='C', fill=True)
    pdf.ln()

    # Isi Tabel
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)

    for i, row in enumerate(df_bulan.itertuples(), 1):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(235, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.cell(col_no, 8, str(i), border=1, align='C', fill=True)
        pdf.cell(col_nama, 8, str(row.Nama), border=1, align='L', fill=True)
        pdf.cell(col_h, 8, str(row.Hadir), border=1, align='C', fill=True)
        pdf.cell(col_i, 8, str(row.Izin), border=1, align='C', fill=True)
        pdf.cell(col_s, 8, str(row.Sakit), border=1, align='C', fill=True)
        pdf.cell(col_t, 8, str(row.Terlambat), border=1, align='C', fill=True)
        pdf.cell(col_pct, 8, f"{row.Persen}%", border=1, align='C', fill=True)
        pdf.ln()

    # Total
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(200, 220, 240)
    total_h = df_bulan['Hadir'].sum()
    total_i = df_bulan['Izin'].sum()
    total_s = df_bulan['Sakit'].sum()
    total_t = df_bulan['Terlambat'].sum()
    pdf.cell(col_no + col_nama, 8, 'TOTAL', border=1, align='C', fill=True)
    pdf.cell(col_h, 8, str(total_h), border=1, align='C', fill=True)
    pdf.cell(col_i, 8, str(total_i), border=1, align='C', fill=True)
    pdf.cell(col_s, 8, str(total_s), border=1, align='C', fill=True)
    pdf.cell(col_t, 8, str(total_t), border=1, align='C', fill=True)
    pdf.cell(col_pct, 8, '', border=1, align='C', fill=True)
    pdf.ln(15)

    # Tanda Tangan
    now = datetime.now(WIB)
    bulan_indo = {
        1:'Januari',2:'Februari',3:'Maret',4:'April',
        5:'Mei',6:'Juni',7:'Juli',8:'Agustus',
        9:'September',10:'Oktober',11:'November',12:'Desember'
    }
    tgl_ttd = f"Subang, {now.day} {bulan_indo[now.month]} {now.year}"
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 7, tgl_ttd, ln=True, align='R')
    pdf.cell(0, 7, 'Wali Kelas,', ln=True, align='R')
    pdf.ln(20)
    pdf.set_font('Helvetica', 'BU', 10)
    pdf.cell(0, 7, nama_wali, ln=True, align='R')

    # Footer
    pdf.set_y(-20)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, f'Dicetak oleh sistem absensi digital - {nama_sekolah}', align='C')

    return bytes(pdf.output())

# --- 5. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
    .stApp {
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 60%, #fbc2eb 100%);
        min-height: 100vh;
    }
    .judul-ceria {
        color: #ff6f61; text-align: center;
        font-size: 2.8rem; font-weight: 800;
        text-shadow: 3px 3px 0px #fff; margin-bottom: 5px;
    }
    .subtitle-ceria {
        text-align: center; color: #5a4fcf;
        font-size: 1.1rem; font-weight: 700; margin-bottom: 5px;
    }
    .kartu-absen {
        background: rgba(255,255,255,0.9); border-radius: 25px;
        padding: 30px; margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 100%);
        color: white !important; font-weight: 800 !important;
        font-size: 1.2rem !important; border-radius: 50px !important;
        height: 65px; width: 100%; border: none;
    }
    .sukses-banner {
        background: linear-gradient(45deg, #43e97b, #38f9d7);
        border-radius: 20px; padding: 20px;
        text-align: center; color: white;
        font-size: 1.3rem; font-weight: 800; margin-top: 10px;
    }
    .sudah-absen-banner {
        background: linear-gradient(45deg, #f7971e, #ffd200);
        border-radius: 20px; padding: 20px;
        text-align: center; color: white;
        font-size: 1.1rem; font-weight: 800; margin-top: 10px;
    }
    .tutup-banner {
        background: linear-gradient(45deg, #e0e0e0, #bdbdbd);
        border-radius: 20px; padding: 20px;
        text-align: center; color: #555;
        font-size: 1.1rem; font-weight: 800; margin-top: 10px;
    }
    .tolak-banner {
        background: linear-gradient(45deg, #ff416c, #ff4b2b);
        border-radius: 20px; padding: 20px;
        text-align: center; color: white;
        font-size: 1.1rem; font-weight: 800; margin-top: 10px;
    }
    .info-banner {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        border-radius: 15px; padding: 15px;
        text-align: center; color: white;
        font-size: 1rem; font-weight: 700; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. HEADER ---
st.markdown('<h1 class="judul-ceria">🎒 Absensi Ceria</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle-ceria">SD KARYABINANGKIT - Petualangan Belajar Dimulai dari Absen!</p>',
    unsafe_allow_html=True
)

# --- JAM DIGITAL ---
components.html("""
<style>
    .jam-box {
        text-align: center; font-size: 1.2rem; font-weight: 800;
        color: #444; background: rgba(255,255,255,0.7);
        border-radius: 15px; padding: 10px;
        border: 2px solid #ffcc5c; font-family: 'Nunito', sans-serif;
    }
</style>
<div class="jam-box" id="jam-box">🕐 Memuat waktu...</div>
<script>
    function updateJam() {
        var now = new Date();
        var optTanggal = {
            timeZone: 'Asia/Jakarta', weekday: 'long',
            day: 'numeric', month: 'long', year: 'numeric'
        };
        var optJam = {
            timeZone: 'Asia/Jakarta', hour: '2-digit',
            minute: '2-digit', second: '2-digit', hour12: false
        };
        var tgl = now.toLocaleDateString('id-ID', optTanggal);
        var jam = now.toLocaleTimeString('id-ID', optJam);
        var el = document.getElementById('jam-box');
        if (el) el.innerHTML = '📅 ' + tgl + ' &nbsp;|&nbsp; 🕐 ' + jam + ' WIB';
    }
    setInterval(updateJam, 1000);
    updateJam();
</script>
""", height=60)

# --- 7. CEK WAKTU ABSEN ---
boleh_absen, pesan_waktu = cek_waktu_absen()

# --- 8. FORM ABSENSI SISWA ---
st.markdown('<div class="kartu-absen">', unsafe_allow_html=True)
st.markdown("### 📝 Isi Absensi Kamu!")

# Info waktu absen
if boleh_absen:
    st.markdown(
        f'<div class="info-banner">{pesan_waktu}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="tutup-banner">{pesan_waktu}</div>',
        unsafe_allow_html=True
    )

if boleh_absen:
    try:
        list_siswa = get_data_siswa()
        if list_siswa:
            nama = st.selectbox(
                "👤 Pilih Nama Kamu:",
                ["--- Pilih Nama ---"] + list_siswa
            )
            status_raw = st.radio(
                "💬 Kabar Kamu Hari Ini:",
                ["😊 Hadir", "✉️ Izin", "🤢 Sakit"],
                horizontal=True
            )
            keterangan = st.text_input("📝 Keterangan (opsional):")

            # GPS Component
            components.html("""
<div id="gps-status" style="
    background: #fff3cd; border-radius: 10px;
    padding: 10px; text-align: center;
    font-weight: bold; margin: 10px 0;
    border: 1px solid #ffc107;">
    📡 Mendeteksi lokasi kamu...
</div>
<input type="hidden" id="lat-val" value="">
<input type="hidden" id="lon-val" value="">
<input type="hidden" id="gps-ok" value="waiting">
<script>
    function cekLokasi() {
        if (!navigator.geolocation) {
            document.getElementById('gps-status').innerHTML =
                '❌ Browser tidak support GPS';
            document.getElementById('gps-ok').value = 'false';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                var lat = pos.coords.latitude;
                var lon = pos.coords.longitude;
                var latSekolah = -6.2844296;
                var lonSekolah = 107.8748021;
                var R = 6371000;
                var dLat = (lat - latSekolah) * Math.PI / 180;
                var dLon = (lon - lonSekolah) * Math.PI / 180;
                var a = Math.sin(dLat/2)*Math.sin(dLat/2) +
                        Math.cos(latSekolah*Math.PI/180)*
                        Math.cos(lat*Math.PI/180)*
                        Math.sin(dLon/2)*Math.sin(dLon/2);
                var c = 2*Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                var jarak = Math.round(R * c);
                document.getElementById('lat-val').value = lat;
                document.getElementById('lon-val').value = lon;
                if (jarak <= 100) {
                    document.getElementById('gps-status').innerHTML =
                        '✅ Lokasi terdeteksi! Jarak dari sekolah: ' + jarak + ' meter';
                    document.getElementById('gps-status').style.background = '#d4edda';
                    document.getElementById('gps-status').style.border = '1px solid #28a745';
                    document.getElementById('gps-ok').value = 'true';
                } else {
                    document.getElementById('gps-status').innerHTML =
                        '❌ Kamu diluar area sekolah! Jarak: ' + jarak + ' meter (Max: 100m)';
                    document.getElementById('gps-status').style.background = '#f8d7da';
                    document.getElementById('gps-status').style.border = '1px solid #dc3545';
                    document.getElementById('gps-ok').value = 'false';
                }
            },
            function(err) {
                document.getElementById('gps-status').innerHTML =
                    '❌ GPS tidak aktif atau ditolak! Mohon aktifkan GPS kamu.';
                document.getElementById('gps-status').style.background = '#f8d7da';
                document.getElementById('gps-ok').value = 'false';
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }
    cekLokasi();
</script>
""", height=80)

            if st.button("🚀 KLIK UNTUK ABSEN!", use_container_width=True):
                if nama == "--- Pilih Nama ---":
                    st.warning("⚠️ Pilih namamu dulu ya!")
                else:
                    now_server = datetime.now(WIB)
                    tanggal_hari_ini = now_server.strftime("%Y-%m-%d")

                    if cek_sudah_absen(nama, tanggal_hari_ini):
                        st.markdown(
                            f'<div class="sudah-absen-banner">'
                            f'⚠️ <b>{nama}</b> sudah absen hari ini!</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        ws_absen = get_worksheet("Sheet1")
                        ws_absen.append_row([
                            tanggal_hari_ini,
                            now_server.strftime("%H:%M:%S"),
                            nama,
                            status_raw.split(" ", 1)[1],
                            keterangan if keterangan else ""
                        ])
                        get_data_absen.clear()
                        tambah_log("Absen", f"{nama} - {status_raw}", nama)
                        st.markdown(
                            f'<div class="sukses-banner">'
                            f'🎉 Hore! <b>{nama}</b> berhasil absen '
                            f'sebagai {status_raw.split(" ", 1)[1]}!</div>',
                            unsafe_allow_html=True
                        )
                        st.balloons()
        else:
            st.warning("⚠️ Data siswa kosong.")
    except Exception as e:
        st.error(f"Kesalahan: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- 9. MENU GURU ---
with st.expander("🔒 Menu Guru"):
    password = st.text_input("Password Guru:", type="password", key="pw_guru")
    pengaturan = get_pengaturan()
    pw_benar = pengaturan.get("password_guru", "guru123")

    if password == pw_benar:
        st.success("✅ Selamat datang, Guru!")

        if st.button("🔄 Refresh Semua Data"):
            get_data_siswa.clear()
            get_data_absen.clear()
            get_pengaturan.clear()
            st.success("✅ Data direfresh!")
            st.rerun()

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 Dashboard",
            "⏰ Absen Manual",
            "👥 Data Siswa",
            "📊 Rekap & Grafik",
            "📄 Export PDF",
            "⚙️ Pengaturan"
        ])

        # =====================
        # TAB 1: DASHBOARD
        # =====================
        with tab1:
            st.markdown("### 📋 Dashboard Hari Ini")
            now = datetime.now(WIB)
            tanggal_hari_ini = now.strftime("%Y-%m-%d")

            try:
                list_siswa = get_data_siswa()
                data_absen = get_data_absen()

                # Siswa yang sudah absen hari ini
                sudah_absen = {}
                for baris in data_absen:
                    if len(baris) >= 4 and baris[0] == tanggal_hari_ini:
                        if baris[0].lower() != "tanggal":
                            sudah_absen[baris[2]] = baris[3]

                belum_absen = [s for s in list_siswa if s not in sudah_absen]

                # Metrik
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("👥 Total", len(list_siswa))
                with col2:
                    st.metric(
                        "✅ Hadir",
                        sum(1 for v in sudah_absen.values() if v == "Hadir")
                    )
                with col3:
                    st.metric(
                        "✉️ Izin",
                        sum(1 for v in sudah_absen.values() if v == "Izin")
                    )
                with col4:
                    st.metric(
                        "🤢 Sakit",
                        sum(1 for v in sudah_absen.values() if v == "Sakit")
                    )
                with col5:
                    st.metric(
                        "⏰ Terlambat",
                        sum(1 for v in sudah_absen.values() if v == "Terlambat")
                    )

                st.markdown("---")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("#### ✅ Sudah Absen")
                    if sudah_absen:
                        for nama_s, status_s in sudah_absen.items():
                            emoji = {
                                "Hadir": "✅", "Izin": "✉️",
                                "Sakit": "🤢", "Terlambat": "⏰"
                            }.get(status_s, "📌")
                            st.write(f"{emoji} {nama_s} - **{status_s}**")
                    else:
                        st.info("Belum ada yang absen.")

                with col_b:
                    st.markdown("#### ❌ Belum Absen")
                    if belum_absen:
                        for nama_b in belum_absen:
                            st.write(f"❌ {nama_b}")
                    else:
                        st.success("Semua siswa sudah absen! 🎉")

            except Exception as e:
                st.error(f"Error dashboard: {e}")

        # =====================
        # TAB 2: ABSEN MANUAL
        # =====================
        with tab2:
            st.markdown("### ⏰ Absen Manual (Guru)")
            st.info(
                "Gunakan fitur ini untuk mengabsenkan siswa yang "
                "terlambat atau berhalangan absen sendiri."
            )
            try:
                list_siswa = get_data_siswa()
                now = datetime.now(WIB)
                tanggal_hari_ini = now.strftime("%Y-%m-%d")

                # Filter siswa yang belum absen
                data_absen = get_data_absen()
                sudah = [
                    b[2] for b in data_absen
                    if len(b) >= 3 and b[0] == tanggal_hari_ini
                ]
                belum = [s for s in list_siswa if s not in sudah]

                if belum:
                    nama_manual = st.selectbox(
                        "👤 Pilih Siswa:",
                        ["--- Pilih ---"] + belum,
                        key="manual_nama"
                    )
                    status_manual = st.selectbox(
                        "📌 Status:",
                        ["Terlambat", "Hadir", "Izin", "Sakit"],
                        key="manual_status"
                    )
                    ket_manual = st.text_input(
                        "📝 Keterangan:",
                        key="manual_ket"
                    )

                    if st.button(
                        "📝 Absenkan Siswa",
                        use_container_width=True,
                        key="btn_manual"
                    ):
                        if nama_manual == "--- Pilih ---":
                            st.warning("Pilih nama siswa dulu!")
                        else:
                            ws_absen = get_worksheet("Sheet1")
                            ws_absen.append_row([
                                tanggal_hari_ini,
                                now.strftime("%H:%M:%S"),
                                nama_manual,
                                status_manual,
                                ket_manual if ket_manual else ""
                            ])
                            get_data_absen.clear()
                            tambah_log(
                                "Absen Manual",
                                f"{nama_manual} - {status_manual}"
                            )
                            st.success(
                                f"✅ {nama_manual} berhasil diabsen "
                                f"sebagai {status_manual}!"
                            )
                            st.rerun()
                else:
                    st.success("✅ Semua siswa sudah absen hari ini!")

            except Exception as e:
                st.error(f"Error absen manual: {e}")

        # =====================
        # TAB 3: DATA SISWA
        # =====================
        with tab3:
            st.markdown("### 👥 Data Siswa")
            try:
                list_siswa = get_data_siswa()
                if list_siswa:
                    df_siswa = pd.DataFrame(list_siswa, columns=["Nama Siswa"])
                    df_siswa.index += 1
                    st.dataframe(df_siswa, use_container_width=True)
                    st.info(f"Total: {len(list_siswa)} siswa")

                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### ➕ Tambah Siswa")
                    nama_baru = st.text_input(
                        "Nama siswa baru:",
                        key="nama_baru"
                    )
                    if st.button("➕ Tambah", key="btn_tambah"):
                        if nama_baru.strip() == "":
                            st.warning("Nama tidak boleh kosong!")
                        elif nama_baru.strip() in list_siswa:
                            st.warning("Nama sudah ada!")
                        else:
                            ws = get_worksheet("DaftarSiswa")
                            ws.append_row([nama_baru.strip()])
                            get_data_siswa.clear()
                            tambah_log("Tambah Siswa", nama_baru.strip())
                            st.success(f"✅ {nama_baru} berhasil ditambahkan!")
                            st.rerun()

                with col2:
                    st.markdown("#### 🗑️ Hapus Siswa")
                    if list_siswa:
                        nama_hapus = st.selectbox(
                            "Pilih siswa:",
                            ["--- Pilih ---"] + list_siswa,
                            key="nama_hapus"
                        )
                        if st.button(
                            "🗑️ Hapus",
                            key="btn_hapus",
                            type="primary"
                        ):
                            if nama_hapus == "--- Pilih ---":
                                st.warning("Pilih nama dulu!")
                            else:
                                ws = get_worksheet("DaftarSiswa")
                                cell = ws.find(nama_hapus)
                                if cell:
                                    ws.delete_rows(cell.row)
                                    get_data_siswa.clear()
                                    tambah_log(
                                        "Hapus Siswa",
                                        nama_hapus
                                    )
                                    st.success(
                                        f"✅ {nama_hapus} berhasil dihapus!"
                                    )
                                    st.rerun()

            except Exception as e:
                st.error(f"Error data siswa: {e}")

        # =====================
        # TAB 4: REKAP & GRAFIK
        # =====================
        with tab4:
            st.markdown("### 📊 Rekap & Grafik Kehadiran")
            try:
                data = get_data_absen()
                if data:
                    # Bersihkan data
                    data_bersih = []
                    for baris in data:
                        if len(baris) > 0 and baris[0].strip().lower() == "tanggal":
                            continue
                        if len(baris) == 0 or all(
                            cell.strip() == "" for cell in baris
                        ):
                            continue
                        data_bersih.append(rapikan_baris(baris, 5))

                    if data_bersih:
                        df = pd.DataFrame(
                            data_bersih,
                            columns=["Tanggal", "Jam", "Nama", "Status", "Keterangan"]
                        )

                        # Filter
                        st.markdown("#### 🔍 Filter")
                        col1, col2 = st.columns(2)
                        with col1:
                            filter_nama = st.text_input(
                                "Cari Nama:",
                                key="filter_nama"
                            )
                        with col2:
                            filter_tgl = st.date_input(
                                "Pilih Tanggal:",
                                value=None,
                                key="filter_tgl"
                            )

                        df_f = df.copy()
                        if filter_nama:
                            df_f = df_f[
                                df_f["Nama"].str.contains(
                                    filter_nama, case=False, na=False
                                )
                            ]
                        if filter_tgl:
                            df_f = df_f[df_f["Tanggal"] == str(filter_tgl)]

                        st.dataframe(df_f, use_container_width=True)

                        # Ringkasan
                        st.markdown("#### 📈 Ringkasan")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("✅ Hadir", len(df_f[df_f["Status"] == "Hadir"]))
                        with col2:
                            st.metric("✉️ Izin", len(df_f[df_f["Status"] == "Izin"]))
                        with col3:
                            st.metric("🤢 Sakit", len(df_f[df_f["Status"] == "Sakit"]))
                        with col4:
                            st.metric(
                                "⏰ Terlambat",
                                len(df_f[df_f["Status"] == "Terlambat"])
                            )
                        with col5:
                            st.metric("📋 Total", len(df_f))

                        st.markdown("---")

                        # Grafik Pie
                        st.markdown("#### 🥧 Grafik Status Kehadiran")
                        status_count = df_f["Status"].value_counts().reset_index()
                        status_count.columns = ["Status", "Jumlah"]
                        fig_pie = px.pie(
                            status_count,
                            names="Status",
                            values="Jumlah",
                            color_discrete_sequence=[
                                "#43e97b", "#4facfe",
                                "#f7971e", "#ff416c"
                            ],
                            hole=0.4
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                        # Grafik Bar per Siswa
                        st.markdown("#### 📊 Kehadiran per Siswa")
                        siswa_status = df_f.groupby(
                            ["Nama", "Status"]
                        ).size().unstack(fill_value=0).reset_index()
                        for kolom in ["Hadir", "Izin", "Sakit", "Terlambat"]:
                            if kolom not in siswa_status.columns:
                                siswa_status[kolom] = 0
                        fig_bar = px.bar(
                            siswa_status,
                            x="Nama",
                            y=["Hadir", "Izin", "Sakit", "Terlambat"],
                            color_discrete_map={
                                "Hadir": "#43e97b",
                                "Izin": "#4facfe",
                                "Sakit": "#f7971e",
                                "Terlambat": "#ff416c"
                            },
                            barmode="stack"
                        )
                        fig_bar.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_bar, use_container_width=True)

                        # Persentase per Siswa
                        st.markdown("#### 🎯 Persentase Kehadiran per Siswa")
                        list_siswa_all = get_data_siswa()
                        rekap_siswa = []
                        for siswa in list_siswa_all:
                            df_siswa_row = df[df["Nama"] == siswa]
                            total = len(df_siswa_row)
                            hadir = len(df_siswa_row[df_siswa_row["Status"] == "Hadir"])
                            izin = len(df_siswa_row[df_siswa_row["Status"] == "Izin"])
                            sakit = len(df_siswa_row[df_siswa_row["Status"] == "Sakit"])
                            terlambat = len(
                                df_siswa_row[df_siswa_row["Status"] == "Terlambat"]
                            )
                            persen = round(
                                (hadir + terlambat) / total * 100, 1
                            ) if total > 0 else 0
                            rekap_siswa.append({
                                "Nama": siswa,
                                "Hadir": hadir,
                                "Izin": izin,
                                "Sakit": sakit,
                                "Terlambat": terlambat,
                                "Total": total,
                                "% Hadir": f"{persen}%"
                            })

                        df_rekap = pd.DataFrame(rekap_siswa)
                        df_rekap.index += 1
                        st.dataframe(df_rekap, use_container_width=True)

                        # Download CSV
                        csv = df_f.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "⬇️ Download CSV",
                            data=csv,
                            file_name=f"rekap_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("📭 Belum ada data.")
                else:
                    st.info("📭 Belum ada data.")
            except Exception as e:
                st.error(f"Error rekap: {e}")

        # =====================
        # TAB 5: EXPORT PDF
        # =====================
        with tab5:
            st.markdown("### 📄 Export PDF Laporan Bulanan")
            try:
                pengaturan = get_pengaturan()
                nama_sekolah = pengaturan.get(
                    "nama_sekolah", "SD KARYABINANGKIT"
                )
                nama_wali = pengaturan.get(
                    "nama_wali_kelas", "NURUL SEPTIANI BAROKAH S.M"
                )
                tahun_ajaran = pengaturan.get(
                    "tahun_ajaran", "2025/2026"
                )

                bulan_indo = {
                    1:'Januari', 2:'Februari', 3:'Maret',
                    4:'April', 5:'Mei', 6:'Juni',
                    7:'Juli', 8:'Agustus', 9:'September',
                    10:'Oktober', 11:'November', 12:'Desember'
                }

                col1, col2 = st.columns(2)
                with col1:
                    bulan_pilih = st.selectbox(
                        "Pilih Bulan:",
                        list(bulan_indo.values()),
                        index=datetime.now(WIB).month - 1
                    )
                with col2:
                    tahun_pilih = st.number_input(
                        "Tahun:",
                        min_value=2020,
                        max_value=2030,
                        value=datetime.now(WIB).year
                    )

                bulan_num = list(bulan_indo.values()).index(bulan_pilih) + 1
                bulan_tahun_str = f"{bulan_pilih} {tahun_pilih}"

                if st.button("📊 Generate Laporan", use_container_width=True):
                    data = get_data_absen()
                    data_bersih = []
                    for baris in data:
                        if len(baris) > 0 and baris[0].strip().lower() == "tanggal":
                            continue
                        if len(baris) == 0 or all(
                            cell.strip() == "" for cell in baris
                        ):
                            continue
                        data_bersih.append(rapikan_baris(baris, 5))

                    if data_bersih:
                        df_all = pd.DataFrame(
                            data_bersih,
                            columns=["Tanggal", "Jam", "Nama", "Status", "Keterangan"]
                        )

                        # Filter bulan & tahun
                        df_bulan_filter = df_all[
                            df_all["Tanggal"].str.startswith(
                                f"{tahun_pilih}-{bulan_num:02d}"
                            )
                        ]

                        if df_bulan_filter.empty:
                            st.warning(
                                f"⚠️ Tidak ada data untuk {bulan_tahun_str}"
                            )
                        else:
                            list_siswa = get_data_siswa()
                            rekap = []
                            for siswa in list_siswa:
                                df_s = df_bulan_filter[
                                    df_bulan_filter["Nama"] == siswa
                                ]
                                hadir = len(df_s[df_s["Status"] == "Hadir"])
                                izin = len(df_s[df_s["Status"] == "Izin"])
                                sakit = len(df_s[df_s["Status"] == "Sakit"])
                                terlambat = len(
                                    df_s[df_s["Status"] == "Terlambat"]
                                )
                                total = len(df_s)
                                persen = round(
                                    (hadir + terlambat) / total * 100, 1
                                ) if total > 0 else 0
                                rekap.append({
                                    "Nama": siswa,
                                    "Hadir": hadir,
                                    "Izin": izin,
                                    "Sakit": sakit,
                                    "Terlambat": terlambat,
                                    "Persen": persen
                                })

                            df_rekap_pdf = pd.DataFrame(rekap)

                            # Preview
                            st.markdown(f"#### 👀 Preview - {bulan_tahun_str}")
                            st.dataframe(df_rekap_pdf, use_container_width=True)

                            # Generate PDF
                            pdf_bytes = generate_pdf(
                                df_rekap_pdf,
                                nama_sekolah,
                                nama_wali,
                                tahun_ajaran,
                                bulan_tahun_str
                            )

                            st.download_button(
                                label=f"📥 Download PDF - {bulan_tahun_str}",
                                data=pdf_bytes,
                                file_name=f"Laporan_Absen_{bulan_tahun_str.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            tambah_log(
                                "Export PDF",
                                f"Laporan {bulan_tahun_str}"
                            )
                    else:
                        st.info("📭 Belum ada data absensi.")

            except Exception as e:
                st.error(f"Error PDF: {e}")

        # =====================
        # TAB 6: PENGATURAN
        # =====================
        with tab6:
            st.markdown("### ⚙️ Pengaturan Aplikasi")
            try:
                pengaturan = get_pengaturan()
                tab6a, tab6b, tab6c = st.tabs([
                    "🏫 Info Sekolah",
                    "📍 Lokasi GPS",
                    "📜 Log Aktivitas"
                ])

                with tab6a:
                    st.markdown("#### 🏫 Informasi Sekolah")
                    new_nama_sekolah = st.text_input(
                        "Nama Sekolah:",
                        value=pengaturan.get("nama_sekolah", "SD KARYABINANGKIT")
                    )
                    new_wali = st.text_input(
                        "Nama Wali Kelas:",
                        value=pengaturan.get(
                            "nama_wali_kelas",
                            "NURUL SEPTIANI BAROKAH S.M"
                        )
                    )
                    new_ta = st.text_input(
                        "Tahun Ajaran:",
                        value=pengaturan.get("tahun_ajaran", "2025/2026")
                    )
                    new_pw = st.text_input(
                        "Password Guru Baru:",
                        type="password",
                        placeholder="Kosongkan jika tidak ingin ganti"
                    )

                    if st.button("💾 Simpan Info Sekolah"):
                        simpan_pengaturan("nama_sekolah", new_nama_sekolah)
                        simpan_pengaturan("nama_wali_kelas", new_wali)
                        simpan_pengaturan("tahun_ajaran", new_ta)
                        if new_pw.strip() != "":
                            simpan_pengaturan("password_guru", new_pw.strip())
                            tambah_log("Ganti Password", "Password guru diubah")
                        tambah_log("Edit Pengaturan", "Info sekolah diperbarui")
                        st.success("✅ Pengaturan berhasil disimpan!")
                        st.rerun()

                with tab6b:
                    st.markdown("#### 📍 Pengaturan Lokasi GPS")
                    new_lat = st.text_input(
                        "Latitude Sekolah:",
                        value=pengaturan.get("lat_sekolah", "-6.2844296")
                    )
                    new_lon = st.text_input(
                        "Longitude Sekolah:",
                        value=pengaturan.get("long_sekolah", "107.8748021")
                    )
                    new_radius = st.number_input(
                        "Radius (meter):",
                        min_value=50,
                        max_value=1000,
                        value=int(pengaturan.get("radius_meter", "100"))
                    )

                    # Preview Maps
                    if new_lat and new_lon:
                        maps_url = (
                            f"https://www.google.com/maps?q="
                            f"{new_lat},{new_lon}&z=18&output=embed"
                        )
                        st.markdown("**📌 Preview Lokasi Sekolah:**")
                        st.markdown(
                            f'<iframe src="{maps_url}" width="100%" '
                            f'height="250" style="border-radius:15px;" '
                            f'allowfullscreen></iframe>',
                            unsafe_allow_html=True
                        )

                    if st.button("💾 Simpan Lokasi GPS"):
                        simpan_pengaturan("lat_sekolah", new_lat)
                        simpan_pengaturan("long_sekolah", new_lon)
                        simpan_pengaturan("radius_meter", str(new_radius))
                        tambah_log("Edit Lokasi GPS", f"Lat:{new_lat} Lon:{new_lon}")
                        st.success("✅ Lokasi GPS berhasil disimpan!")

                with tab6c:
                    st.markdown("#### 📜 Log Aktivitas")
                    try:
                        client = get_sheet_conn()
                        sh = client.open_by_key(SPREADSHEET_ID)
                        ws_log = sh.worksheet("LogAktivitas")
                        log_data = ws_log.get_all_values()
                        if log_data:
                            if log_data[0][0].lower() == "waktu":
                                log_data = log_data[1:]
                            df_log = pd.DataFrame(
                                log_data,
                                columns=["Waktu", "Pelaku", "Aksi", "Detail"]
                            )
                            df_log = df_log.iloc[::-1].reset_index(drop=True)
                            df_log.index += 1
                            st.dataframe(df_log, use_container_width=True)
                        else:
                            st.info("Belum ada log aktivitas.")
                    except:
                        st.info("Sheet LogAktivitas belum tersedia.")

            except Exception as e:
                st.error(f"Error pengaturan: {e}")

    elif password != "":
        st.error("❌ Password salah!")
