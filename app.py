import streamlit as st
from src.preprocessing import DataPreprocessor

# Konfigurasi halaman
st.set_page_config(
    page_title="AI ETR Predictor SMKKJ",
    page_icon="🎯",
    layout="wide"
)

# Tajuk aplikasi
st.title("🎯 AI ETR Predictor SMKKJ")
st.subheader("Versi 1.0")

processor = DataPreprocessor()

try:
    gps = processor.load_gps()
    ppt = processor.load_ppt()

    st.success("✅ Data berjaya dimuatkan")

    st.subheader("GPS Bidang")
    st.dataframe(gps)

    st.subheader("Analisis PPT")
    st.dataframe(ppt)

except Exception as e:
    st.error(f"Ralat: {e}")