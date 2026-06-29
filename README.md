README.md

AI ETR Predictor SMKKJ

Pengenalan

AI ETR Predictor SMKKJ ialah aplikasi berasaskan Python dan Streamlit untuk membantu SMK Kelana Jaya membuat ramalan ETR (Expected Target Result) SPM menggunakan data peperiksaan sekolah.

Objektif

- Mengimport data peperiksaan.
- Menganalisis GPS, GPMP dan Gred Purata Bidang.
- Menjana ramalan ETR setiap murid.
- Memaparkan dashboard interaktif.
- Menyediakan laporan automatik.

Struktur Projek

AI-ETR-Predictor-SMKKJ/

- app.py
- src/
- data/
- models/
- reports/
- notebooks/
- assets/

Pemasangan

pip install -r requirements.txt

Menjalankan aplikasi

streamlit run app.py

Data yang disokong

- GPS_Bidang_SMKKJ_2026.xlsx
- ANALISIS_PPT_2026_T5_OPTIMISED.xlsx
- ANALISIS SPM 2025 (SEKOLAH).pdf

Roadmap

Versi 1.0

- Struktur projek
- Dashboard asas

Versi 1.1

- Analisis GPS
- Analisis GPMP
- Analisis Bidang

Versi 2.0

- Machine Learning ETR
- AI Recommendation
- Auto Report
