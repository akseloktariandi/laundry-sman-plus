import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Laundry SMAN Plus Riau", layout="wide")

# Link Google Sheets kamu
url_sheet = "https://docs.google.com/spreadsheets/d/10fNN90PsmRN61bYXv8lG6XlmiAx0VmO3IO7LFtXTKdc/edit?gid=0#gid=0"

# Inisialisasi koneksi
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi ambil data dengan ttl=0 agar data langsung muncul setelah di-input
def load_data():
    return conn.read(spreadsheet=url_sheet, ttl=0)

# Navigasi
st.sidebar.title("🧺 Menu Laundry")
halaman = st.sidebar.radio("Pilih Akses:", ["Cek Status (Siswa)", "Panel Petugas (Login)"])

# --- HALAMAN SISWA ---
if halaman == "Cek Status (Siswa)":
    st.title("🧺 Cek Status Laundry Siswa")
    try:
        data = load_data()
        nama_cari = st.text_input("Masukkan Nama Lengkap:")
        if nama_cari:
            # Pastikan kolom Nama dibaca sebagai teks
            hasil = data[data['Nama'].astype(str).str.contains(nama_cari, case=False, na=False)]
            if not hasil.empty:
                for index, row in hasil.iterrows():
                    warna = "🟢" if str(row['Bayar']) == "Sudah Lunas" else "🔴"
                    with st.expander(f"{row['Tgl_Masuk']} - {row['Nama']} ({row['Status']})"):
                        st.write(f"**Berat:** {row['Berat']}")
                        st.write(f"**Total Biaya:** {row['Total_Harga']}")
                        st.write(f"**Status Bayar:** {warna} {row['Bayar']}")
            else:
                st.error("Nama tidak ditemukan.")
    except:
        st.info("Sistem sedang menyiapkan database...")

# --- HALAMAN PETUGAS ---
else:
    st.title("👨‍🔧 Panel Petugas")
    pw = st.sidebar.text_input("Password:", type="password")
    
    if pw == "plusriau123":
        data = load_data()
            
        with st.form("input_form", clear_on_submit=True):
            st.subheader("➕ Input Order Baru")
            nama = st.text_input("Nama Siswa")
            col1, col2 = st.columns(2)
            with col1:
                berat = st.number_input("Berat (kg)", 0.1, step=0.1)
            with col2:
                # FITUR: Harga per kg bisa diubah-ubah petugas
                harga_per_kg = st.number_input("Harga per Kg (Rp)", value=6000, step=500)
            
            sudah_bayar = st.checkbox("Sudah Bayar?")
            
            if st.form_submit_button("Simpan Data ke Cloud"):
                total = berat * harga_per_kg
                status_bayar = "Sudah Lunas" if sudah_bayar else "Belum Bayar"
                
                new_row = pd.DataFrame([{
                    "Nama": nama, 
                    "Berat": f"{berat} kg", 
                    "Total_Harga": f"Rp {total:,.0f}",
                    "Tgl_Masuk": datetime.now().strftime("%d/%m/%y"), 
                    "Status": "Proses", 
                    "Bayar": status_bayar
                }])
                
                # Gabungkan data lama dengan data baru
                updated_df = pd.concat([data, new_row], ignore_index=True)
                
                # Update ke Sheets
                conn.update(spreadsheet=url_sheet, data=updated_df)
                st.success(f"Berhasil! Data {nama} sudah masuk ke Google Sheets.")
                st.rerun() # Refresh aplikasi agar tabel di bawah langsung terisi
        
        st.divider()
        st.write("### 📊 Database Real-time (Dari Google Sheets)")
        # Menampilkan tabel yang selalu up-to-date
        st.dataframe(data, hide_index=True, use_container_width=True)
    else:
        st.info("Silakan masukkan password di sidebar untuk mengelola data.")
