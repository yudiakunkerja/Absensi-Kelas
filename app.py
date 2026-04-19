import streamlit as st
from datetime import datetime
import gspread
import pytz
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Petualangan Absensi Ceria",
    page_icon="🎒",
    layout="centered"
)

# --- AUTO REFRESH SETIAP 1 DETIK UNTUK JAM ---
st_autorefresh(interval=1000, limit=None, key="jam_refresh")

SPREADSHEET_ID = "1bjrCAF1WSQORDhgCE8yT2RMP7sydzGmbbTXddW1uO_Q"

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheet_conn():
    try:
        # Cara aman: baca dari secrets tapi perbaiki format private key otomatis
        creds_dict = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
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

def get_worksheet(name):
    client = get_sheet_conn()
    if client:
        sh = client.open_by_key(SPREADSHEET_ID)
        try:
            return sh.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            return sh.add_worksheet(title=name, rows=1000, cols=10)
    return None

# --- 3. TAMPILAN CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
    .stApp { 
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 60%, #fbc2eb 100%); 
        min-height: 100vh; 
    }
    .judul-ceria { 
        font-family: 'Nunito', cursive, sans-serif; 
        color: #ff6f61; 
        text-align: center; 
        font-size: 2.8rem; 
        font-weight: 800; 
        text-shadow: 3px 3px 0px #fff; 
        margin-bottom: 5px; 
    }
    .subtitle-ceria { 
        text-align: center; 
        color: #5a4fcf; 
        font-size: 1.1rem; 
        font-weight: 700; 
        margin-bottom: 5px; 
    }
    .jam-digital { 
        text-align: center; 
        font-size: 1.3rem; 
        font-weight: 800; 
        color: #444; 
        margin-bottom: 20px; 
        background: rgba(255,255,255,0.7); 
        border-radius: 15px; 
        padding: 10px; 
        border: 2px solid #ffcc5c; 
    }
    .kartu-absen { 
        background: rgba(255,255,255,0.9); 
        border-radius: 25px; 
        padding: 30px; 
        margin-bottom: 20px; 
        box-shadow: 0 8px 30px rgba(0,0,0,0.1); 
    }
    .stButton>button { 
        background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 100%); 
        color: white !important; 
        font-weight: 800 !important; 
        font-size: 1.2rem !important; 
        border-radius: 50px !important; 
        height: 65px; 
        width: 100%; 
        border: none; 
    }
    .sukses-banner { 
        background: linear-gradient(45deg, #43e97b, #38f9d7); 
        border-radius: 20px; 
        padding: 20px; 
        text-align: center; 
        color: white; 
        font-size: 1.3rem; 
        font-weight: 800; 
        margin-top: 10px; 
    }
    .rekap-header { 
        background: linear-gradient(45deg, #667eea, #764ba2); 
        color: white; 
        border-radius: 15px; 
        padding: 15px; 
        font-weight: 800; 
        text-align: center; 
    }
</style>
""", unsafe_allow_html=True)

# --- 4. HEADER ---
st.markdown('<h1 class="judul-ceria">🎒 Absensi Ceria</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-ceria">Petualangan Belajar Dimulai dari Absen!</p>', unsafe_allow_html=True)

# --- JAM DIGITAL PYTHON ---
now = datetime.now(pytz.timezone('Asia/Jakarta'))

hari_indo = {
    'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
    'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
}
bulan_indo = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}

hari = hari_indo[now.strftime('%A')]
tanggal = now.day
bulan = bulan_indo[now.month]
tahun = now.year
jam = now.strftime('%H:%M:%S')

st.markdown(f'''
<div class="jam-digital">
    📅 {hari}, {tanggal} {bulan} {tahun} &nbsp;|&nbsp; 🕐 {jam} WIB
</div>
''', unsafe_allow_html=True)

# --- 5. FORM ABSENSI ---
st.markdown('<div class="kartu-absen">', unsafe_allow_html=True)
st.markdown("### 📝 Isi Absensi Kamu!")

try:
    ws_siswa = get_worksheet("DaftarSiswa")
    if ws_siswa:
        data_siswa = ws_siswa.col_values(1)
        list_siswa = [
            v for v in data_siswa 
            if v and v.strip() and v.strip() != "Nama Siswa"
        ]
        nama = st.selectbox("👤 Pilih Nama Kamu:", ["--- Pilih Nama ---"] + list_siswa)
        status_raw = st.radio(
            "💬 Kabar Kamu Hari Ini:", 
            ["😊 Hadir", "✉️ Izin", "🤢 Sakit"], 
            horizontal=True
        )
        keterangan = st.text_input("📝 Keterangan (opsional):")

        if st.button("🚀 KLIK UNTUK ABSEN!", use_container_width=True):
            if nama == "--- Pilih Nama ---":
                st.warning("⚠️ Pilih namamu dulu ya!")
            else:
                ws_absen = get_worksheet("Sheet1")
                now_server = datetime.now(pytz.timezone('Asia/Jakarta'))
                ws_absen.append_row([
                    now_server.strftime("%Y-%m-%d"),
                    now_server.strftime("%H:%M:%S"),
                    nama,
                    status_raw.split(" ", 1)[1],
                    keterangan
                ])
                st.markdown(
                    f'<div class="sukses-banner">🎉 Hore! <b>{nama}</b> berhasil absen!</div>', 
                    unsafe_allow_html=True
                )
                st.balloons()
except Exception as e:
    st.error(f"Kesalahan: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MENU GURU ---
with st.expander("🔒 Menu Guru"):
    password = st.text_input("Password:", type="password")
    if password == st.secrets.get("guru_password", "guru123"):
        tab1, tab2 = st.tabs(["👥 Data Siswa", "📊 Rekap"])

        with tab1:
            st.markdown("### 👥 Daftar Siswa")
            try:
                ws_siswa = get_worksheet("DaftarSiswa")
                data = ws_siswa.get_all_values()
                if data:
                    df_siswa = pd.DataFrame(data[1:], columns=["Nama Siswa"])
                    st.dataframe(df_siswa, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal memuat data siswa: {e}")

        with tab2:
            st.markdown("### 📊 Rekap Absensi")
            try:
                ws_absen = get_worksheet("Sheet1")
                data = ws_absen.get_all_values()
                if data:
                    df_absen = pd.DataFrame(data, columns=["Tanggal", "Jam", "Nama", "Status", "Keterangan"])
                    
                    # Filter by tanggal
                    st.markdown("#### 🔍 Filter Data")
                    col1, col2 = st.columns(2)
                    with col1:
                        filter_nama = st.text_input("Cari Nama:")
                    with col2:
                        filter_tanggal = st.text_input("Cari Tanggal (YYYY-MM-DD):")
                    
                    if filter_nama:
                        df_absen = df_absen[df_absen["Nama"].str.contains(filter_nama, case=False)]
                    if filter_tanggal:
                        df_absen = df_absen[df_absen["Tanggal"] == filter_tanggal]
                    
                    st.dataframe(df_absen, use_container_width=True)
                    
                    # Ringkasan
                    st.markdown("#### 📈 Ringkasan")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Hadir", len(df_absen[df_absen["Status"] == "Hadir"]))
                    with col2:
                        st.metric("Total Izin", len(df_absen[df_absen["Status"] == "Izin"]))
                    with col3:
                        st.metric("Total Sakit", len(df_absen[df_absen["Status"] == "Sakit"]))
                else:
                    st.info("Belum ada data absensi.")
            except Exception as e:
                st.error(f"Gagal memuat rekap: {e}")
