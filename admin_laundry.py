import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Panel Admin Laundry", layout="wide")

def load_data():
    try: 
        return pd.read_csv("data_laundry.csv")
    except: 
        # Tambah kolom Bayar di database awal
        return pd.DataFrame(columns=["Nama", "Berat", "Total_Harga", "Tgl_Masuk", "Status", "Bayar"])

def save_data(df):
    df.to_csv("data_laundry.csv", index=False)

st.sidebar.title("Login Petugas")
pw = st.sidebar.text_input("Password:", type="password")

if pw == "plusriau123":
    st.title("👨‍🔧 Panel Petugas Laundry SMAN Plus")
    data = load_data()
    
    tab1, tab2, tab3 = st.tabs(["➕ Input Baru", "✅ Update Status & Bayar", "🗑️ Hapus Data"])
    
    with tab1:
        st.subheader("Input Data Baru")
        with st.form("input"):
            nama = st.text_input("Nama Siswa")
            berat = st.number_input("Berat (kg)", 0.1, step=0.1)
            harga_kg = st.number_input("Harga per Kg (Rp)", value=6000)
            # FITUR BARU: Centang sudah bayar saat input
            sudah_bayar = st.checkbox("Sudah Bayar?") 
            
            if st.form_submit_button("Simpan"):
                total = berat * harga_kg
                status_bayar = "Sudah Lunas" if sudah_bayar else "Belum Bayar"
                new = {
                    "Nama": nama, 
                    "Berat": f"{berat} kg", 
                    "Total_Harga": f"Rp {total:,.0f}", 
                    "Tgl_Masuk": datetime.now().strftime("%d/%m/%y"), 
                    "Status": "Proses",
                    "Bayar": status_bayar
                }
                data = pd.concat([data, pd.DataFrame([new])], ignore_index=True)
                save_data(data)
                st.success(f"Data {nama} disimpan ({status_bayar})!")
                st.rerun()

    with tab2:
        st.subheader("Update Status & Pembayaran")
        if not data.empty:
            pilih = st.selectbox("Pilih Nama Siswa:", data['Nama'].tolist())
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Tandai Laundry Selesai"):
                    data.loc[data['Nama'] == pilih, 'Status'] = "Selesai"
                    save_data(data)
                    st.success("Status diperbarui!")
                    st.rerun()
            
            with col_b:
                if st.button("Tandai Sudah Lunas"):
                    data.loc[data['Nama'] == pilih, 'Bayar'] = "Sudah Lunas"
                    save_data(data)
                    st.balloons()
                    st.success("Pembayaran dikonfirmasi!")
                    st.rerun()
        else:
            st.info("Data kosong.")

    with tab3:
        st.subheader("Hapus Data")
        if not data.empty:
            hapus_nama = st.selectbox("Pilih Data yang Akan Dihapus:", data['Nama'].tolist(), key="hapus")
            if st.button("Hapus Selamanya", type="primary"):
                data = data[data['Nama'] != hapus_nama]
                save_data(data)
                st.rerun()
    
    st.divider()
    st.write("### Daftar Laundry")
    # Menampilkan tabel dengan warna agar mudah membedakan yang sudah bayar
    st.dataframe(data, use_container_width=True, hide_index=True)

else:
    st.info("Silakan masukkan password.")
