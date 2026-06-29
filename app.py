from src.preprocessing import DataPreprocessor

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
    st.error(e)
