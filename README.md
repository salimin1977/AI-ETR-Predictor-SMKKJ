# AI ETR Predictor SMKKJ

## Pengenalan

AI ETR Predictor SMKKJ ialah aplikasi berasaskan Python dan Streamlit untuk
membantu SMK Kelana Jaya menganalisis prestasi peperiksaan dan meramal
Gred Purata (GP) serta status pencapaian ETR (Expected Target Result) SPM
menggunakan data peperiksaan sekolah sebenar.

## Objektif

- Mengimport dan menghurai data peperiksaan (GPS Bidang & Analisis PPT).
- Menganalisis GPS, GP Bidang dan prestasi setiap subjek/kelas.
- Menjana ramalan AI bagi Gred Purata dan status prestasi.
- Memaparkan dashboard interaktif (Plotly).
- Log dan pengendalian ralat yang konsisten merentasi aplikasi.

## Struktur Projek

```
AI-ETR-Predictor-SMKKJ/
├── app.py                     # Entri Streamlit (navigasi, caching, error handling)
├── src/
│   ├── config.py              # Laluan & pemalar berpusat
│   ├── logging_config.py      # Persediaan logging (konsol + fail berputar)
│   ├── exceptions.py          # Ralat khusus projek
│   ├── preprocessing.py       # Penghuraian & pembersihan data (DataPreprocessor)
│   ├── analytics.py           # Pengiraan KPI/ringkasan (Analytics)
│   ├── predictor.py           # Model AI ETR (ETRPredictor)
│   └── dashboard.py           # Rajah Plotly (fig_*) + show_header()
├── tests/                     # Ujian pytest
├── docs/
│   └── MODULES.md             # Dokumentasi terperinci setiap modul
├── data/
│   ├── raw/                   # Fail sumber (.xlsx / .pdf, tidak diubah)
│   └── processed/             # Output DataPreprocessor.save_processed()
├── models/                    # Model terlatih (.joblib, di-gitignore)
├── logs/                      # Log aplikasi (app.log, di-gitignore)
├── reports/
├── notebooks/
└── assets/
```

Lihat [`docs/MODULES.md`](docs/MODULES.md) untuk penerangan penuh setiap
modul, kaedah dan andaian reka bentuknya.

## Pemasangan

```bash
pip install -r requirements.txt
```

## Menjalankan aplikasi

```bash
streamlit run app.py
```

## Menjalankan ujian

```bash
pytest -q
```

## Data yang disokong

- `GPS_Bidang_SMKKJ_2026.xlsx` — Ringkasan GP Bidang, sasaran GPS setiap
  subjek, dan butiran Bidang Kemanusiaan (guru/PIC).
- `ANALISIS_PPT_2026_T5_OPTIMISED.xlsx` — Ringkasan prestasi 18 subjek dan
  pecahan gred setiap kelas.
- `ANALISIS SPM 2025 (SEKOLAH).pdf` — disertakan dalam `data/raw/` untuk
  rujukan; belum diintegrasikan ke dalam paip data automatik.

**Nota penting:** kesemua data sumber diagregat pada peringkat
kelas/subjek/bidang. Tiada data individu murid dalam projek ini — modul AI
(`ETRPredictor`) meramal Gred Purata dan status prestasi peringkat
kelas/subjek daripada peratus kelulusan, bukan keputusan murid secara
individu. Lihat docstring `src/predictor.py` untuk penjelasan penuh.

## Roadmap

**Versi 1.0**
- Struktur projek
- Dashboard asas

**Versi 1.1**
- Analisis GPS
- Analisis GP Bidang

**Versi 2.0** *(semasa)*
- Penghuraian data tulen (bukan pembersihan generik) untuk kedua-dua
  workbook sumber
- Analitik KPI/risiko sebenar
- Model AI ETR (regresi GP + klasifikasi status)
- Dashboard Plotly sepenuhnya interaktif
- Log berpusat + pengendalian ralat konsisten
- Ujian pytest

**Akan datang**
- Integrasi PDF (`ANALISIS SPM 2025 (SEKOLAH).pdf`) ke dalam paip data
- Auto report / eksport laporan
