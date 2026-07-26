# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AI ETR Predictor SMKKJ is a Python/Streamlit application built for SMK Kelana Jaya to predict student ETR (Expected Target Result) SPM outcomes from school exam data. Documentation, UI text, and code comments in this repo are written in **Bahasa Malaysia**; keep new comments/UI strings consistent with that convention unless told otherwise.

The project is at an early stage (README lists it as "Versi 1.0" — basic structure + dashboard). Machine learning prediction, GPS/GPMP/Bidang analysis, and auto-reporting (planned "Versi 1.1"/"Versi 2.0" in the README roadmap) are only partially wired up — see Architecture below for what's actually connected today.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

There is no test suite, linter, or CI configuration in this repo yet — don't assume `pytest`, `flake8`, etc. are set up. If you add tests or lint tooling, wire the run commands into this file.

## Architecture

- **`app.py`** — Streamlit entry point. Instantiates `DataPreprocessor` directly, loads GPS and PPT data, and renders them as raw dataframes. This is the only wired-up UI flow currently; run it with `streamlit run app.py`.
- **`src/preprocessing.py`** (`DataPreprocessor`) — Reads raw Excel files from `data/raw/` (hardcoded relative path `Path("data/raw")`, so must be run from the repo root), cleans them (drops blank rows, `Unnamed` columns, duplicates, fills NaN with `""`), and can write cleaned output to `data/processed/` via `save_processed`. `load_gps()` and `load_ppt()` are thin wrappers around specific filenames (`GPS_Bidang_SMKKJ_2026.xlsx`, `ANALISIS_PPT_2026_T5_OPTIMISED.xlsx`) in `data/raw/`.
- **`src/analytics.py`** (`Analytics`) — Basic dataframe summary helpers (`total_students`, `missing_values`, `summary`). Not yet called from `app.py`.
- **`src/predictor.py`** (`ETRPredictor`) — Thin wrapper around `sklearn.linear_model.LinearRegression` (`train`/`predict`). Not yet wired into the app or given feature/label extraction logic.
- **`src/dashboard.py`** — `show_header()` renders a Streamlit title/caption. Not currently called by `app.py` (which duplicates its own header via `st.set_page_config`/`st.title`); if you consolidate the header, update `app.py` to call this instead of inlining it.

When extending prediction or analytics features, the natural seam is: `DataPreprocessor` (raw Excel → cleaned DataFrame) → `Analytics`/`ETRPredictor` (cleaned DataFrame → insights/predictions) → `app.py` or `src/dashboard.py` (render in Streamlit). Follow that flow rather than reading raw files directly from new code.

## Data and directories

- **`data/raw/`** — Source spreadsheets/PDFs checked into the repo (`GPS_Bidang_SMKKJ_2026.xlsx`, `ANALISIS_PPT_2026_T5_OPTIMISED.xlsx`, `1. ANALISIS SPM 2025 (SEKOLAH).pdf`). `PyPDF2` is in `requirements.txt` but no code currently parses the PDF.
- **`data/processed/`**, **`models/*.pkl`** — gitignored; generated/derivative artifacts, not committed.
- **`models/`**, **`reports/`**, **`notebooks/`**, **`assets/`** — currently empty scaffold directories (only `.gitkeep`), reserved for future trained models, generated reports, exploratory notebooks, and static assets respectively.
