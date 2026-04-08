import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cek Laundry Siswa")

def load_data():
    try: return pd.read_csv("data_laundry.csv")
    except: return pd.DataFrame()

st.title("🧺 Cek Status Laundry")
nama_cari = st.text_input("Masukkan Nama:")

if nama_cari:
    df = load_data()
    if not df.empty:
        hasil = df[df['Nama'].str.contains(nama_cari, case=False, na=False)]
        if not hasil.empty:
            for index, row in hasil.iterrows():
                # Warna teks bayar
                warna_bayar = "🟢" if row['Bayar'] == "Sudah Lunas" else "🔴"
                
                with st.expander(f"{row['Tgl_Masuk']} - {row['Nama']} ({row['Status']})"):
                    st.write(f"**Total Biaya:** {row['Total_Harga']}")
                    st.write(f"**Status Bayar:** {warna_bayar} {row['Bayar']}")
                    if row['Status'] == "Selesai":
                        st.success("Cucian siap diambil!")
        else:
            st.error("Nama tidak ditemukan.")
