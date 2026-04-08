import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Laundry SMAN Plus Riau", layout="wide")

# 1. LINK GOOGLE SHEETS (Ganti dengan link spreadsheet kamu)
url_sheet = "MASUKKAN_LINK_GOOGLE_SHEETS_KAMU_DI_SINI"

# 2. INISIALISASI KONEKSI
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi ambil data dengan ttl=0 agar data selalu paling baru
def load_data():
    return conn.read(spreadsheet=url_sheet, ttl=0)

# 3. MEMORI HARGA (Agar harga per kg tidak reset saat simpan data)
if 'harga_tetap' not in st.session_state:
    st.session_state.harga_tetap = 6000

# 4. NAVIGASI SIDEBAR
st.sidebar.title("🧺 Menu Laundry")
halaman = st.sidebar.radio("Pilih Akses:", ["Cek Status (Siswa)", "Panel Petugas (Login)"])

# --- HALAMAN SISWA ---
if halaman == "Cek Status (Siswa)":
    st.title("🧺 Cek Status Laundry Siswa")
    try:
        data = load_data()
        nama_cari = st.text_input("Cari Nama Lengkap Kamu:")
        if nama_cari:
            # Mencari nama (tidak peduli huruf besar/kecil)
            hasil = data[data['Nama'].astype(str).str.contains(nama_cari, case=False, na=False)]
            if not hasil.empty:
                for index, row in hasil.iterrows():
                    warna_bayar = "🟢" if str(row['Bayar']) == "Sudah Lunas" else "🔴"
                    with st.expander(f"📦 Order {row['Tgl_Masuk']} - {row['Nama']} ({row['Status']})"):
                        st.write(f"**Berat:** {row['Berat']}")
                        st.write(f"**Total Biaya:** {row['Total_Harga']}")
                        st.write(f"**Status Bayar:** {warna_bayar} {row['Bayar']}")
                        if row['Status'] == "Selesai":
                            st.success("✅ Cucian siap diambil di loket asrama!")
                        else:
                            st.info("⏳ Masih dalam proses pengerjaan.")
            else:
                st.error("Nama tidak ditemukan. Pastikan ejaan benar.")
    except:
        st.info("Menunggu petugas memasukkan data pertama...")

# --- HALAMAN PETUGAS ---
else:
    st.title("👨‍🔧 Panel Petugas Laundry")
    pw = st.sidebar.text_input("Password Petugas:", type="password")
    
    if pw == "plusriau123":
        # Ambil data terbaru
        data = load_data()
        
        # Tabs untuk memisahkan fungsi petugas
        tab_input, tab_update, tab_hapus = st.tabs(["➕ Input Data", "🔄 Update Status & Bayar", "🗑️ Hapus Data"])
        
        # TAB 1: INPUT DATA BARU
        with tab_input:
            with st.form("input_form", clear_on_submit=True):
                st.subheader("Tambah Order Laundry")
                nama_input = st.text_input("Nama Lengkap Siswa")
                c1, c2 = st.columns(2)
                with c1:
                    berat_input = st.number_input("Berat (kg)", 0.1, step=0.1)
                with c2:
                    # Mengambil nilai dari session_state agar tidak reset
                    harga_input = st.number_input("Harga per Kg (Rp)", 
                                                   value=st.session_state.harga_tetap, 
                                                   step=500)
                
                bayar_input = st.checkbox("Sudah Bayar?")
                
                if st.form_submit_button("Simpan Data"):
                    # Update memori harga dengan input terakhir
                    st.session_state.harga_tetap = harga_input
                    
                    total_biaya = berat_input * harga_input
                    label_bayar = "Sudah Lunas" if bayar_input else "Belum Bayar"
                    
                    # Buat baris baru
                    new_row = pd.DataFrame([{
                        "Nama": nama_input, 
                        "Berat": f"{berat_input} kg", 
                        "Total_Harga": f"Rp {total_biaya:,.0f}",
                        "Tgl_Masuk": datetime.now().strftime("%d/%m/%y"), 
                        "Status": "Proses", 
                        "Bayar": label_bayar
                    }])
                    
                    # Gabung data dan simpan ke Cloud
                    updated_df = pd.concat([data, new_row], ignore_index=True)
                    conn.update(spreadsheet=url_sheet, data=updated_df)
                    st.success(f"Data {nama_input} berhasil disimpan!")
                    st.rerun()

        # TAB 2: UPDATE STATUS (REAL-TIME)
        with tab_update:
            st.subheader("Perbarui Status Laundry & Pembayaran")
            if not data.empty:
                # Kolom pembantu untuk memilih data secara spesifik
                data['ID_Order'] = data['Nama'] + " (" + data['Tgl_Masuk'] + ")"
                opsi = data['ID_Order'].tolist()
                pilihan = st.selectbox("Pilih Siswa:", opsi)
                
                # Ambil index data yang dipilih
                idx = data[data['ID_Order'] == pilihan].index[0]
                
                up_col1, up_col2 = st.columns(2)
                with up_col1:
                    st.write(f"**Status Saat Ini:** {data.at[idx, 'Status']}")
                    if st.button("Tandai SELESAI"):
                        data.at[idx, 'Status'] = "Selesai"
                        # Simpan tanpa kolom pembantu ID_Order
                        conn.update(spreadsheet=url_sheet, data=data.drop(columns=['ID_Order']))
                        st.success("Status diperbarui!")
                        st.rerun()
                
                with up_col2:
                    st.write(f"**Pembayaran:** {data.at[idx, 'Bayar']}")
                    if st.button("Tandai SUDAH LUNAS"):
                        data.at[idx, 'Bayar'] = "Sudah Lunas"
                        conn.update(spreadsheet=url_sheet, data=data.drop(columns=['ID_Order']))
                        st.balloons()
                        st.success("Pembayaran dikonfirmasi!")
                        st.rerun()
            else:
                st.info("Database kosong.")

        # TAB 3: HAPUS DATA
        with tab_hapus:
            st.subheader("Hapus Data Salah Input")
            if not data.empty:
                if 'ID_Order' not in data.columns:
                    data['ID_Order'] = data['Nama'] + " (" + data['Tgl_Masuk'] + ")"
                
                target_hapus = st.selectbox("Pilih Data untuk Dihapus:", data['ID_Order'].tolist())
                
                if st.button("Hapus Permanen", type="primary"):
                    data_clean = data[data['ID_Order'] != target_hapus]
                    conn.update(spreadsheet=url_sheet, data=data_clean.drop(columns=['ID_Order']))
                    st.warning(f"Data {target_hapus} telah dihapus dari server.")
                    st.rerun()
        
        # TABEL MONITORING (SELALU MUNCUL DI BAWAH)
        st.divider()
        st.write("### 📊 Ringkasan Database Laundry")
        # Hilangkan kolom pembantu saat tampil di tabel
        tabel_final = data.drop(columns=['ID_Order']) if 'ID_Order' in data.columns else data
        st.dataframe(tabel_final, hide_index=True, use_container_width=True)
        
    else:
        st.info("🔐 Masukkan password di sidebar untuk mengakses Panel Petugas.")
