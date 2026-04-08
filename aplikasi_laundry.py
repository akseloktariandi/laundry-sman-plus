import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Laundry SMAN Plus Riau", layout="wide")

# MENGHUBUNGKAN KE GOOGLE SHEETS MENGGUNAKAN SECRETS
# Masukkan link Google Sheets kamu di sini
url_sheet = "https://docs.google.com/spreadsheets/d/10fNN90PsmRN61bYXv8lG6XlmiAx0VmO3IO7LFtXTKdc/edit?gid=0#gid=0"

# Inisialisasi koneksi (dia akan otomatis membaca dari Secrets yang kamu isi tadi)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(spreadsheet=url_sheet)

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
            hasil = data[data['Nama'].astype(str).str.contains(nama_cari, case=False, na=False)]
            if not hasil.empty:
                for index, row in hasil.iterrows():
                    warna = "🟢" if row['Bayar'] == "Sudah Lunas" else "🔴"
                    with st.expander(f"{row['Tgl_Masuk']} - {row['Nama']} ({row['Status']})"):
                        st.write(f"**Total Biaya:** {row['Total_Harga']}")
                        st.write(f"**Status Bayar:** {warna} {row['Bayar']}")
            else:
                st.error("Nama tidak ditemukan.")
    except Exception as e:
        st.warning("Menunggu data masuk dari petugas...")

# --- HALAMAN PETUGAS ---
else:
    st.title("👨‍🔧 Panel Petugas")
    pw = st.sidebar.text_input("Password:", type="password")
    
    if pw == "plusriau123":
        try:
            data = load_data()
        except:
            data = pd.DataFrame(columns=["Nama", "Berat", "Total_Harga", "Tgl_Masuk", "Status", "Bayar"])
            
        with st.form("input_form"):
            nama = st.text_input("Nama Siswa")
            berat = st.number_input("Berat (kg)", 0.1, step=0.1)
            sudah_bayar = st.checkbox("Sudah Bayar?")
            if st.form_submit_button("Simpan Data"):
                total = berat * 6000
                status_bayar = "Sudah Lunas" if sudah_bayar else "Belum Bayar"
                new_row = pd.DataFrame([{
                    "Nama": nama, "Berat": f"{berat}kg", "Total_Harga": f"Rp {total:,.0f}",
                    "Tgl_Masuk": datetime.now().strftime("%d/%m/%y"), 
                    "Status": "Proses", "Bayar": status_bayar
                }])
                updated_df = pd.concat([data, new_row], ignore_index=True)
                
                # Mengirim data ke Google Sheets menggunakan koneksi Service Account
                conn.update(spreadsheet=url_sheet, data=updated_df)
                st.success("Berhasil! Data tersimpan permanen di Google Sheets.")
                st.rerun()
        
        st.divider()
        st.write("### Database Real-time")
        st.dataframe(data, hide_index=True)
    else:
        st.info("Masukkan password di sidebar.")
