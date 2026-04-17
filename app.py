import streamlit as st
from datetime import datetime, date, timedelta
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Petualangan Absensi Ceria",
    page_icon="🎒",
    layout="centered"
)

SPREADSHEET_ID = "1bjrCAF1WSQORDhgCE8yT2RMP7sydzGmbbTXddW1uO_Q"

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheet_conn():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
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

    html, body, [class*="css"] {
        font-family: 'Nunito', sans-serif;
    }
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
        text-shadow: 3px 3px 0px #fff, 5px 5px 0px rgba(255,111,97,0.2);
        margin-bottom: 5px;
    }
    .subtitle-ceria {
        text-align: center;
        color: #5a4fcf;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .kotak-tanggal {
        background: rgba(255,255,255,0.85);
        border-radius: 20px;
        padding: 12px 20px;
        text-align: center;
        font-weight: 800;
        font-size: 1.1rem;
        border: 3px solid #ffcc5c;
        margin-bottom: 25px;
        color: #444;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .kartu-absen {
        background: rgba(255,255,255,0.9);
        border-radius: 25px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        border: 2px solid rgba(255,255,255,0.6);
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
        box-shadow: 0 5px 20px rgba(255,154,158,0.5);
        transition: all 0.3s ease;
        cursor: pointer;
        font-family: 'Nunito', sans-serif !important;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255,154,158,0.6);
    }
    .stSelectbox>div>div {
        border-radius: 15px !important;
        border: 2px solid #a1c4fd !important;
        background: rgba(255,255,255,0.9) !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 700 !important;
    }
    .stRadio>div {
        background: rgba(255,255,255,0.7);
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #c2e9fb;
    }
    .stRadio label {
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    .stTextInput>div>div>input {
        border-radius: 15px !important;
        border: 2px solid #a1c4fd !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 700;
    }
    .stExpander {
        background: rgba(255,255,255,0.85);
        border-radius: 20px;
        border: 2px solid #fbc2eb;
    }
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
    }
    .sukses-banner {
        background: linear-gradient(45deg, #43e97b, #38f9d7);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        color: white;
        font-size: 1.3rem;
        font-weight: 800;
        box-shadow: 0 5px 20px rgba(67,233,123,0.4);
        margin-top: 10px;
    }
    .rekap-header {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 15px;
        padding: 15px 20px;
        font-weight: 800;
        font-size: 1.2rem;
        margin-bottom: 15px;
        text-align: center;
    }
    .stat-box {
        background: rgba(255,255,255,0.9);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid #e0e0e0;
    }
    .stat-angka {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        font-weight: 700;
    }
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.9);
        border-radius: 15px;
        padding: 15px;
        border: 2px solid #c2e9fb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.07);
    }
    .info-box {
        background: rgba(255, 255, 255, 0.8);
        border-left: 5px solid #5a4fcf;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 10px 0;
        font-weight: 700;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. HEADER ---
now = datetime.now()
hari_id = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
}
bulan_id = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}
nama_hari = hari_id[now.strftime("%A")]
nama_bulan = bulan_id[now.month]

st.markdown('<h1 class="judul-ceria">🎒 Absensi Ceria</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-ceria">Petualangan Belajar Dimulai dari Absen!</p>', unsafe_allow_html=True)
st.markdown(
    f'<div class="kotak-tanggal">📅 {nama_hari}, {now.day} {nama_bulan} {now.year} &nbsp;|&nbsp; 🕐 {now.strftime("%H:%M")}</div>',
    unsafe_allow_html=True
)

# --- 5. FORM ABSENSI SISWA ---
st.markdown('<div class="kartu-absen">', unsafe_allow_html=True)
st.markdown("### 📝 Isi Absensi Kamu!")

try:
    ws_siswa = get_worksheet("DaftarSiswa")
    if ws_siswa:
        semua_nilai = ws_siswa.col_values(1)
        list_siswa = [v for v in semua_nilai if v and v.strip() and v.strip() != "Nama Siswa"][1:]

        if not list_siswa:
            st.info("📋 Belum ada data siswa. Guru perlu menambahkan siswa terlebih dahulu.")
        else:
            nama = st.selectbox(
                "👤 Pilih Nama Kamu:",
                ["--- Pilih Nama ---"] + list_siswa
            )
            status_raw = st.radio(
                "💬 Kabar Kamu Hari Ini:",
                ["😊 Hadir", "✉️ Izin", "🤢 Sakit"],
                horizontal=True
            )
            keterangan = st.text_input("📝 Keterangan (opsional):", placeholder="Contoh: izin ke dokter")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 KLIK UNTUK ABSEN!", use_container_width=True):
                    if nama == "--- Pilih Nama ---":
                        st.warning("⚠️ Pilih namamu dulu ya!")
                    else:
                        with st.spinner("🌀 Mencatat absensi kamu..."):
                            ws_absen = get_worksheet("Sheet1")
                            status_bersih = status_raw.split(" ", 1)[1]
                            ws_absen.append_row([
                                now.strftime("%Y-%m-%d"),
                                now.strftime("%H:%M:%S"),
                                nama,
                                status_bersih,
                                keterangan
                            ])
                        st.markdown(
                            f'<div class="sukses-banner">🎉 Hore! <b>{nama}</b> berhasil absen sebagai <b>{status_bersih}</b>!</div>',
                            unsafe_allow_html=True
                        )
                        st.balloons()
    else:
        st.error("Gagal terhubung ke Google Sheets.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MENU GURU ---
st.markdown("---")
with st.expander("🔒 Menu Guru"):
    password = st.text_input("Masukkan Password Guru:", type="password", key="pw_guru")
    GURU_PASSWORD = st.secrets.get("guru_password", "guru123")

    if password == GURU_PASSWORD:
        st.success("✅ Selamat datang, Guru!")
        tab1, tab2, tab3 = st.tabs(["👥 Data Siswa", "📊 Rekap Absensi", "📅 Rekap Mingguan"])

        # --- TAB 1: DATA SISWA ---
        with tab1:
            st.markdown("#### 👥 Daftar Siswa")
            try:
                ws_siswa = get_worksheet("DaftarSiswa")
                data_siswa = ws_siswa.get_all_values()
                if len(data_siswa) > 1:
                    df_siswa = pd.DataFrame(data_siswa[1:], columns=["Nama Siswa"])
                    df_siswa = df_siswa[df_siswa["Nama Siswa"].str.strip() != ""]
                    st.dataframe(df_siswa, use_container_width=True, hide_index=True)
                    st.caption(f"Total: {len(df_siswa)} siswa terdaftar")
                else:
                    st.info("Belum ada siswa terdaftar.")
            except Exception as e:
                st.error(f"Error: {e}")

            st.markdown("#### ➕ Tambah Siswa Baru")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                nama_baru = st.text_input("Nama Siswa Baru:", key="siswa_baru", placeholder="Masukkan nama lengkap")
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Simpan", key="btn_simpan_siswa"):
                    if nama_baru.strip():
                        ws_s = get_worksheet("DaftarSiswa")
                        ws_s.append_row([nama_baru.strip()])
                        st.success(f"✅ Siswa '{nama_baru}' berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.warning("Nama tidak boleh kosong!")

            st.markdown("#### 🗑️ Hapus Siswa")
            try:
                ws_hapus = get_worksheet("DaftarSiswa")
                semua = ws_hapus.get_all_values()
                list_nama_hapus = [r[0] for r in semua[1:] if r and r[0].strip()]
                if list_nama_hapus:
                    nama_hapus = st.selectbox("Pilih siswa yang akan dihapus:", list_nama_hapus, key="hapus_siswa")
                    if st.button("🗑️ Hapus Siswa Ini", key="btn_hapus"):
                        cell = ws_hapus.find(nama_hapus)
                        if cell:
                            ws_hapus.delete_rows(cell.row)
                            st.success(f"✅ Siswa '{nama_hapus}' berhasil dihapus.")
                            st.rerun()
                else:
                    st.info("Tidak ada siswa untuk dihapus.")
            except Exception as e:
                st.error(f"Error: {e}")

        # --- TAB 2: REKAP ABSENSI ---
        with tab2:
            st.markdown('<div class="rekap-header">📊 Rekap Absensi Lengkap</div>', unsafe_allow_html=True)
            try:
                ws_absen = get_worksheet("Sheet1")
                data_absen = ws_absen.get_all_values()

                if len(data_absen) > 1:
                    df = pd.DataFrame(data_absen[1:], columns=["Tanggal", "Jam", "Nama", "Status", "Keterangan"])
                    df = df[df["Nama"].str.strip() != ""]
                    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        tgl_mulai = st.date_input("Dari Tanggal:", value=date.today() - timedelta(days=7), key="tgl_mulai")
                    with col_f2:
                        tgl_selesai = st.date_input("Sampai Tanggal:", value=date.today(), key="tgl_selesai")

                    df_filter = df[
                        (df["Tanggal"].dt.date >= tgl_mulai) &
                        (df["Tanggal"].dt.date <= tgl_selesai)
                    ].copy()
                    df_filter["Tanggal"] = df_filter["Tanggal"].dt.strftime("%d/%m/%Y")

                    jumlah_hadir = len(df_filter[df_filter["Status"] == "Hadir"])
                    jumlah_izin = len(df_filter[df_filter["Status"] == "Izin"])
                    jumlah_sakit = len(df_filter[df_filter["Status"] == "Sakit"])

                    c1, c2, c3 = st.columns(3)
                    c1.metric("😊 Hadir", jumlah_hadir)
                    c2.metric("✉️ Izin", jumlah_izin)
                    c3.metric("🤢 Sakit", jumlah_sakit)

                    st.markdown("#### 📋 Detail Absensi")
                    filter_nama = st.text_input("🔍 Cari nama siswa:", key="cari_nama", placeholder="Ketik nama...")
                    if filter_nama:
                        df_filter = df_filter[df_filter["Nama"].str.contains(filter_nama, case=False)]

                    st.dataframe(df_filter, use_container_width=True, hide_index=True)
                    st.caption(f"Menampilkan {len(df_filter)} data absensi")
                else:
                    st.info("Belum ada data absensi.")
            except Exception as e:
                st.error(f"Error memuat rekap: {e}")

        # --- TAB 3: REKAP MINGGUAN ---
        with tab3:
            st.markdown('<div class="rekap-header">📅 Rekap Mingguan per Siswa</div>', unsafe_allow_html=True)
            try:
                ws_absen_mgg = get_worksheet("Sheet1")
                data_mgg = ws_absen_mgg.get_all_values()

                if len(data_mgg) > 1:
                    df_mgg = pd.DataFrame(data_mgg[1:], columns=["Tanggal", "Jam", "Nama", "Status", "Keterangan"])
                    df_mgg = df_mgg[df_mgg["Nama"].str.strip() != ""]
                    df_mgg["Tanggal"] = pd.to_datetime(df_mgg["Tanggal"], errors="coerce")

                    hari_ini = date.today()
                    awal_minggu = hari_ini - timedelta(days=hari_ini.weekday())
                    akhir_minggu = awal_minggu + timedelta(days=6)

                    minggu_dipilih = st.date_input(
                        "Pilih minggu (pilih tanggal mana saja dalam minggu itu):",
                        value=hari_ini,
                        key="minggu_dipilih"
                    )
                    awal_pilih = minggu_dipilih - timedelta(days=minggu_dipilih.weekday())
                    akhir_pilih = awal_pilih + timedelta(days=6)

                    st.markdown(
                        f'<div class="info-box">📅 Periode: {awal_pilih.strftime("%d %b %Y")} s/d {akhir_pilih.strftime("%d %b %Y")}</div>',
                        unsafe_allow_html=True
                    )

                    df_minggu = df_mgg[
                        (df_mgg["Tanggal"].dt.date >= awal_pilih) &
                        (df_mgg["Tanggal"].dt.date <= akhir_pilih)
                    ].copy()

                    if not df_minggu.empty:
                        rekap = df_minggu.groupby(["Nama", "Status"]).size().unstack(fill_value=0)
                        for k in ["Hadir", "Izin", "Sakit"]:
                            if k not in rekap.columns:
                                rekap[k] = 0
                        rekap = rekap[["Hadir", "Izin", "Sakit"]].reset_index()
                        rekap.columns.name = None
                        rekap["Total Hari"] = rekap["Hadir"] + rekap["Izin"] + rekap["Sakit"]
                        rekap = rekap.sort_values("Hadir", ascending=False)

                        col_r = st.columns(3)
                        col_r[0].metric("😊 Total Hadir", int(rekap["Hadir"].sum()))
                        col_r[1].metric("✉️ Total Izin", int(rekap["Izin"].sum()))
                        col_r[2].metric("🤢 Total Sakit", int(rekap["Sakit"].sum()))

                        st.markdown("#### 📊 Tabel Rekap per Siswa")
                        st.dataframe(
                            rekap.rename(columns={"Nama": "👤 Nama Siswa"}),
                            use_container_width=True,
                            hide_index=True
                        )

                        siswa_hadir_penuh = rekap[rekap["Hadir"] == rekap["Total Hari"]]
                        if not siswa_hadir_penuh.empty:
                            st.success(f"🌟 Hadir penuh minggu ini: {', '.join(siswa_hadir_penuh['Nama'].tolist())}")
                    else:
                        st.info("Tidak ada data absensi untuk minggu ini.")
                else:
                    st.info("Belum ada data absensi.")
            except Exception as e:
                st.error(f"Error rekap mingguan: {e}")

    elif password and password != GURU_PASSWORD:
        st.error("❌ Password salah. Coba lagi ya!")
