import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Laundry SMAN Plus Riau", layout="wide")

# Link Google Sheets kamu
url_sheet = "https://docs.google.com/spreadsheets/d/10fNN90PsmRN61bYXv8lG6XlmiAx0VmO3IO7LFtXTKdc/edit?gid=0#gid=0"

# Inisialisasi koneksi
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi ambil data dengan ttl=0 agar selalu segar
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
        nama_cari = st.text_input("Masukkan Nama :")
        if nama_cari:
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
        
        # TABS UNTUK PETUGAS (Sekarang ada 3 Tab)
        tab_input, tab_update, tab_hapus = st.tabs(["➕ Input Data", "🔄 Update Status & Bayar", "🗑️ Hapus Data"])
        
        with tab_input:
            with st.form("input_form", clear_on_submit=True):
                st.subheader("➕ Input Order Baru")
                nama = st.text_input("Nama Siswa")
                col1, col2 = st.columns(2)
                with col1:
                    berat = st.number_input("Berat (kg)", 0.1, step=0.1)
                with col2:
                    harga_per_kg = st.number_input("Harga per Kg (Rp)", value=6000, step=500)
                
                sudah_bayar = st.checkbox("Sudah Bayar?")
                
                if st.form_submit_button("Simpan Data ke Cloud"):
                    total = berat * harga_per_kg
                    status_bayar = "Sudah Lunas" if sudah_bayar else "Belum Bayar"
                    new_row = pd.DataFrame([{
                        "Nama": nama, "Berat": f"{berat} kg", "Total_Harga": f"Rp {total:,.0f}",
                        "Tgl_Masuk": datetime.now().strftime("%d/%m/%y"), 
                        "Status": "Proses", "Bayar": status_bayar
                    }])
                    updated_df = pd.concat([data, new_row], ignore_index=True)
                    conn.update(spreadsheet=url_sheet, data=updated_df)
                    st.success(f"Berhasil! Data {nama} tersimpan.")
                    st.rerun()

        with tab_update:
            st.subheader("🔄 Update Status Laundry & Pembayaran")
            if not data.empty:
                # Pilih baris data berdasarkan Nama dan Tanggal (agar unik jika nama sama)
                data['Info_Opsi'] = data['Nama'] + " (" + data['Tgl_Masuk'] + ")"
                opsi_pilihan = data['Info_Opsi'].tolist()
                pilih_update = st.selectbox("Pilih Order Siswa:", opsi_pilihan)
                
                # Ambil index data yang dipilih
                idx = data[data['Info_Opsi'] == pilih_update].index[0]
                
                col_up1, col_up2 = st.columns(2)
                with col_up1:
                    st.write(f"**Status Saat Ini:** {data.at[idx, 'Status']}")
                    if st.button("Ubah ke SELESAI"):
                        data.at[idx, 'Status'] = "Selesai"
                        # Hapus kolom bantuan sebelum simpan
                        df_save = data.drop(columns=['Info_Opsi'])
                        conn.update(spreadsheet=url_sheet, data=df_save)
                        st.success("Status Laundry Diperbarui!")
                        st.rerun()
                
                with col_up2:
                    st.write(f"**Pembayaran:** {data.at[idx, 'Bayar']}")
                    if st.button("Ubah ke SUDAH LUNAS"):
                        data.at[idx, 'Bayar'] = "Sudah Lunas"
                        df_save = data.drop(columns=['Info_Opsi'])
                        conn.update(spreadsheet=url_sheet, data=df_save)
                        st.balloons()
                        st.success("Pembayaran Lunas!")
                        st.rerun()
            else:
                st.info("Belum ada data untuk di-update.")

        with tab_hapus:
            st.subheader("🗑️ Hapus Data Salah Input")
            if not data.empty:
                # Pastikan kolom Info_Opsi ada
                if 'Info_Opsi' not in data.columns:
                    data['Info_Opsi'] = data['Nama'] + " (" + data['Tgl_Masuk'] + ")"
                
                nama_hapus = st.selectbox("Pilih Data yang Akan Dihapus:", data['Info_Opsi'].tolist())
                
                if st.button("Hapus Permanen", type="primary"):
                    data_baru = data[data['Info_Opsi'] != nama_hapus]
                    # Hapus kolom bantuan sebelum simpan
                    df_save = data_baru.drop(columns=['Info_Opsi'])
                    conn.update(spreadsheet=url_sheet, data=df_save)
                    st.warning("Data telah dihapus!")
                    st.rerun()
            else:
                st.info("Belum ada data yang bisa dihapus.")
        
        st.divider()
        st.write("### 📊 Database Real-time")
        # Tampilkan tabel tanpa kolom bantuan Info_Opsi
        tampilan_tabel = data.drop(columns=['Info_Opsi']) if 'Info_Opsi' in data.columns else data
        st.dataframe(tampilan_tabel, hide_index=True, use_container_width=True)
    else:
        st.info("Silakan masukkan password di sidebar.")
