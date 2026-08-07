# Dokumentasi Modul

Rujukan ringkas untuk setiap modul dalam `src/`, `app.py` dan `tests/`.
Setiap modul juga mempunyai docstring lengkap dalam kod - fail ini adalah
peta keseluruhan, bukan pengganti kod sumber.

## `src/config.py`

Konfigurasi berpusat: laluan fail (`RAW_DATA_DIR`, `PROCESSED_DATA_DIR`,
`MODELS_DIR`, `LOGS_DIR`), nama fail data mentah, dan pemalar (`APP_VERSION`,
`MIN_ROWS_FOR_SPLIT`). Tiada modul lain yang hardcode laluan/pemalar ini.

## `src/logging_config.py`

- `configure_logging(level=logging.INFO)` - lekap console handler + rotating
  file handler (`logs/app.log`) pada root logger. Selamat dipanggil berkali-kali.
- `get_logger(name)` - dapatkan logger bernamakan modul; konfigur logging
  secara automatik jika belum dipanggil.

## `src/exceptions.py`

Hierarki ralat khusus projek (semua mewarisi `ETRPredictorError`):
`DataFileNotFoundError`, `DataParsingError`, `ModelNotTrainedError`,
`InsufficientDataError`, `AuthenticationError`. `app.py` menangkap
`ETRPredictorError` untuk memaparkan mesej mesra pengguna, sambil log
penuh terus ke `logs/app.log`.

## `src/preprocessing.py`

`DataPreprocessor` - memuat & menghurai kedua-dua workbook sumber kepada
`pandas.DataFrame` yang kemas. Helaian sumber diformat sebagai laporan
cetak (tajuk hiasan, sel header bergabung, jadual dua-baris header), jadi
penghuraian mengesan sel header melalui *teks*, bukan nombor baris/lajur
tetap - degradasi anggun (skip + log amaran) apabila sesuatu helaian tidak
sepadan templat dijangka.

Kaedah utama:
- `load_gps_ringkasan_bidang()` / `load_gps_school_summary()` /
  `load_gps_dashboard()` / `load_gps_kemanusiaan_detail()` - dari
  `GPS_Bidang_SMKKJ_2026.xlsx`.
- `load_ppt_summary()` / `load_ppt_school_gp()` / `load_ppt_class_breakdown()`
  - dari `ANALISIS_PPT_2026_T5_OPTIMISED.xlsx`.
- `load_gps()` / `load_ppt()` - kekal untuk keserasian ke belakang, kini
  memulangkan jadual kemas (`load_gps_ringkasan_bidang` /
  `load_ppt_summary`) dan bukan helaian mentah.
- `load_excel()`, `save_processed()`, `clean_dataframe()` - kekal seperti asal.

Fungsi modul: `classify_gp_band(gp)` mengklasifikasikan nilai GP kepada jalur
prestasi rasmi (CEMERLANG/BAIK/SEDERHANA/LEMAH/KRITIKAL) berdasarkan legenda
yang dicetak pada setiap helaian subjek PPT (`GP_BAND_LEGEND`).

**Penting:** data sumber diagregat pada peringkat kelas/subjek/bidang -
tiada data individu murid dalam mana-mana fail sumber.

## `src/analytics.py`

`Analytics` - pengiraan KPI/ringkasan tanpa keadaan (stateless) atas
DataFrame. Kekal `total_students`, `missing_values`, `summary` (asal).
Tambahan: `status_counts`, `average_gp`, `subjects_at_risk`,
`gap_to_target`, `bidang_ranking`. Nota konvensyen: bagi GRED PURATA (GP),
**nilai lebih rendah adalah lebih baik**.

## `src/predictor.py`

`ETRPredictor` - modul AI/ML. Kekal `__init__`/`train(X, y)`/`predict(X)`
(regresi generik asal). Tambahan:
- `fit_gp_regressor(df, feature_cols, target_col)` - Pipeline
  (StandardScaler + LinearRegression) meramal GRED PURATA daripada
  peratus kelulusan/saiz kohort. Pulangkan metrik R² dan MAE.
- `fit_status_classifier(df, feature_cols, target_col)` - Pipeline
  (StandardScaler + LogisticRegression) mengklasifikasikan jalur prestasi.
  GRED PURATA sengaja **tidak** dimasukkan sebagai ciri kerana ia sudah
  menentukan label secara langsung mengikut `GP_BAND_LEGEND` - memasukkannya
  akan menjadikan "ramalan" hanya carian jadual (lookup), bukan anggaran
  sebenar.
- `predict_gp(df)` / `predict_status(df)` - lemparkan `ModelNotTrainedError`
  jika dipanggil sebelum `fit_*`.
- `save(path)` / `load(path)` - simpan/muat model via `joblib`
  (lalai `models/etr_predictor.joblib`, sudah di-gitignore).

Saiz sampel kecil (puluhan baris, bukan ribuan) - metrik adalah
demonstratif, bukan ramalan berketepatan tinggi produksi.

## `src/dashboard.py`

Pembina rajah Plotly tulen (`go.Figure`, tiada panggilan Streamlit) supaya
boleh diuji & diguna semula bebas daripada `app.py`:
`fig_subject_gp_bar`, `fig_status_distribution`, `fig_bidang_comparison`,
`fig_class_grade_distribution`, `fig_prediction_scatter`. `show_header()`
kekal sebagai fungsi mudah bersandar-Streamlit yang asal.

## `src/permissions.py`

Kawalan akses berperanan (RBAC), logik tulen tanpa Streamlit/bcrypt.
`ROLES` (5 peranan), `ROLE_PAGES` (halaman yang boleh dilihat setiap
peranan), `ROLE_DEFAULT_PAGE` (halaman pendaratan selepas log masuk),
`pages_for_role(role)`, `default_page_for(role)`, `has_permission(role, page)`.
Ini adalah RBAC peringkat **halaman** sahaja - tiada pemetaan akaun ke
subjek/bidang tertentu lagi, jadi data itu sendiri tidak ditapis mengikut
pengguna (lihat nota "Akan datang" dalam README).

## `src/users.py`

`UserStore` - storan pengguna berasaskan fail JSON (`data/auth/users.json`,
laluan dari `config.USERS_FILE`). Skema rekod (`username`, `password_hash`,
`full_name`, `role`, `active`) sengaja dipilih supaya mudah dipindah ke
pangkalan data sebenar kelak. `all_users()`, `get(username)`,
`create(username, password, full_name, role)` (hash melalui
`auth.hash_password`, sahkan peranan terhadap `permissions.ROLES`),
`ensure_seeded()` (jana satu akaun lalai bagi setiap peranan jika fail
belum wujud, log amaran WARNING supaya kata laluan lalai ditukar - lihat
README untuk senarai akaun lalai).

## `src/auth.py`

Hash & pengesahan kata laluan (bcrypt), logik tulen tanpa Streamlit.
`hash_password(password)` / `verify_password(password, hash)`;
`AuthenticatedUser` (dataclass: `username, full_name, role`);
`authenticate(username, password, store=None) -> AuthenticatedUser`,
melemparkan `AuthenticationError` untuk sebarang kegagalan (pengguna tidak
wujud, kata laluan salah, akaun tidak aktif) dengan mesej generik yang
sama supaya borang log masuk tidak mendedahkan bahagian mana yang salah.

## `src/session.py`

Pembalut nipis `st.session_state` (perlu bersandar-Streamlit kerana
`session_state` hanya wujud dalam skrip Streamlit yang sedang berjalan).
`login(user)`, `logout()`, `current_user()`, `is_authenticated()` -
yang terakhir menguatkuasakan had masa tidak aktif
(`config.SESSION_TIMEOUT_MINUTES`, lalai 60 minit) dan log keluar automatik
apabila melebihinya.

## `src/login.py`

Halaman log masuk Streamlit. `render_login_form()` - borang nama
pengguna/kata laluan, panggil `auth.authenticate`, jika berjaya panggil
`session.login(...)` + `st.rerun()`, jika gagal papar `st.error(...)`.

## `app.py`

Lapisan UI Streamlit nipis. Susun atur:
- Get bermula dengan gerbang log masuk: jika `session.is_authenticated()`
  palsu, papar `login.render_login_form()` dan `st.stop()`.
- Navigasi bar sisi (`st.sidebar.radio`) ditapis mengikut peranan pengguna
  via `permissions.pages_for_role(user.role)`, dengan halaman pendaratan
  lalai dari `permissions.default_page_for(user.role)`, ditambah butang
  "Log Keluar". `PAGES` dict dan setiap fungsi `page_*` (Ringkasan, GPS
  Bidang, Analisis PPT, Ramalan AI ETR, Tentang) tidak diubah langsung.
- Setiap pemuat data dibalut `st.cache_data`; model AI dilatih sekali per
  sesi via `st.cache_resource`.
- Setiap halaman dibalut penanganan ralat: `ETRPredictorError` (dan
  subkelasnya) dipaparkan sebagai `st.error` mesra pengguna, dengan
  `logger.exception(...)` merekod butiran penuh ke `logs/app.log`; ralat
  tidak dijangka lain ditangkap sebagai jaringan keselamatan terakhir.

## `tests/`

Ujian asap `pytest` (jalankan dengan `pytest -q` daripada root projek):
- `test_preprocessing.py` - kesahihan penghuraian atas data sampel benar
  (disemak silang terhadap nilai dalam hamparan sumber), laluan ralat fail
  hilang.
- `test_analytics.py` - pembantu KPI/gap/ranking atas data sintetik kecil.
- `test_predictor.py` - regresi/klasifikasi fit-predict, fallback sampel
  kecil, laluan ralat, dan pusingan simpan/muat `joblib`.
- `test_permissions.py` - akses halaman bagi setiap peranan.
- `test_users.py` - CRUD `UserStore` dan `ensure_seeded()` (fail sementara
  via `tmp_path`, tidak pernah menyentuh `data/auth/users.json` sebenar).
- `test_auth.py` - kitaran hash/sah kata laluan, `authenticate()` berjaya/
  gagal, mesej ralat konsisten tanpa mendedahkan sebab kegagalan.
