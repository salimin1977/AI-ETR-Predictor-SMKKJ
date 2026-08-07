"""
Streamlit entrypoint for AI ETR Predictor SMKKJ.

Thin UI layer: all data parsing lives in src/preprocessing.py, all KPI
maths in src/analytics.py, all charts in src/dashboard.py and all ML in
src/predictor.py. This file wires them together behind Streamlit caching
and a sidebar navigation, and translates the project's custom exceptions
into friendly on-page error messages (full details always go to the log).
"""

import pandas as pd
import streamlit as st

from src.analytics import Analytics
from src.config import APP_VERSION
from src.dashboard import (
    fig_bidang_comparison,
    fig_class_grade_distribution,
    fig_prediction_scatter,
    fig_status_distribution,
    fig_subject_gp_bar,
    show_header,
)
from src.exceptions import ETRPredictorError
from src.logging_config import configure_logging, get_logger
from src.login import render_login_form
from src.predictor import ETRPredictor
from src.preprocessing import DataPreprocessor, classify_gp_band
from src import permissions, session
from src.users import UserStore

configure_logging()
logger = get_logger(__name__)

st.set_page_config(page_title="AI ETR Predictor SMKKJ", page_icon="🎯", layout="wide")

processor = DataPreprocessor()
analytics = Analytics()
UserStore().ensure_seeded()


# ----------------------------------------------------------------------
# Cached data access
# ----------------------------------------------------------------------

@st.cache_data(show_spinner="Memuatkan Ringkasan Bidang...")
def get_gps_ringkasan_bidang():
    return processor.load_gps_ringkasan_bidang()


@st.cache_data(show_spinner="Memuatkan ringkasan GPS sekolah...")
def get_gps_school_summary():
    return processor.load_gps_school_summary()


@st.cache_data(show_spinner="Memuatkan GP Bidang Dashboard...")
def get_gps_dashboard():
    return processor.load_gps_dashboard()


@st.cache_data(show_spinner="Memuatkan butiran Bidang Kemanusiaan...")
def get_gps_kemanusiaan_detail():
    return processor.load_gps_kemanusiaan_detail()


@st.cache_data(show_spinner="Memuatkan ringkasan PPT...")
def get_ppt_summary():
    return processor.load_ppt_summary()


@st.cache_data(show_spinner="Memuatkan GPS sekolah (PPT)...")
def get_ppt_school_gp():
    return processor.load_ppt_school_gp()


@st.cache_data(show_spinner="Memuatkan pecahan kelas (18 helaian)...")
def get_ppt_class_breakdown():
    df = processor.load_ppt_class_breakdown()
    df["GP_BAND"] = df["GP"].apply(classify_gp_band)
    return df


@st.cache_resource(show_spinner="Melatih model AI ETR...")
def train_predictor(class_df: pd.DataFrame):
    predictor = ETRPredictor()
    gp_metrics = predictor.fit_gp_regressor(class_df, feature_cols=["PCT_LULUS"], target_col="GP")
    status_metrics = predictor.fit_status_classifier(
        class_df, feature_cols=["PCT_LULUS"], target_col="GP_BAND"
    )
    return predictor, gp_metrics, status_metrics


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------

def page_ringkasan():
    ppt_summary = get_ppt_summary()
    ppt_gp = get_ppt_school_gp()
    gps_summary = get_gps_school_summary()
    ringkasan_bidang = get_gps_ringkasan_bidang()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jumlah Subjek (PPT)", analytics.total_students(ppt_summary))
    col2.metric("GPS Sekolah (PPT)", f"{ppt_gp:.2f}")
    col3.metric("GPS Sekolah (Purata Bidang)", f"{gps_summary.get('gp_purata', float('nan')):.2f}")
    n_at_risk = len(analytics.subjects_at_risk(ppt_summary))
    col4.metric("Subjek Berisiko (Lemah/Kritikal)", f"{n_at_risk}/{len(ppt_summary)}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(fig_status_distribution(ppt_summary), width="stretch")
    with col_b:
        st.plotly_chart(fig_bidang_comparison(ringkasan_bidang), width="stretch")

    st.subheader("Subjek Paling Berisiko")
    st.dataframe(
        analytics.subjects_at_risk(ppt_summary)[
            ["KOD", "MATA_PELAJARAN", "BIL_DAFTAR", "PCT_LULUS", "GRED_PURATA", "STATUS"]
        ],
        width="stretch",
        hide_index=True,
    )


def page_gps_bidang():
    ringkasan_bidang = get_gps_ringkasan_bidang()
    dashboard_df = get_gps_dashboard()
    kemanusiaan_df = get_gps_kemanusiaan_detail()

    st.subheader("Ringkasan GP Bidang")
    st.dataframe(ringkasan_bidang, width="stretch", hide_index=True)
    st.plotly_chart(fig_bidang_comparison(ringkasan_bidang), width="stretch")

    st.subheader("Sasaran GPS Mengikut Subjek (Semua Bidang)")
    st.dataframe(
        dashboard_df[["BIL", "BIDANG", "SUBJEK", "GPS_SASARAN", "GP_BIDANG", "STATUS"]],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Butiran Bidang Kemanusiaan (Guru / PIC)")
    st.dataframe(kemanusiaan_df, width="stretch", hide_index=True)


def page_analisis_ppt():
    ppt_summary = get_ppt_summary()
    class_df = get_ppt_class_breakdown()

    st.subheader("Ringkasan Prestasi Subjek (PPT)")
    st.dataframe(ppt_summary, width="stretch", hide_index=True)
    st.plotly_chart(fig_subject_gp_bar(ppt_summary), width="stretch")

    st.subheader("Pecahan Gred Mengikut Kelas")
    subjects = sorted(ppt_summary["MATA_PELAJARAN"].unique())
    chosen = st.selectbox("Pilih subjek", subjects)
    st.plotly_chart(fig_class_grade_distribution(class_df, chosen), width="stretch")
    st.dataframe(
        class_df[class_df["SUBJEK"] == chosen].drop(columns=["KOD", "SUBJEK"]),
        width="stretch",
        hide_index=True,
    )


def page_ramalan_ai():
    st.info(
        "Data sumber diagregat pada peringkat kelas/subjek/bidang - tiada data "
        "individu murid. Model di bawah meramal Gred Purata (GP) dan status "
        "prestasi kelas daripada peratus kelulusan sahaja, bukan keputusan "
        "murid secara individu. Saiz sampel kecil (puluhan baris) - metrik "
        "adalah demonstratif, bukan ramalan berketepatan tinggi."
    )

    class_df = get_ppt_class_breakdown()

    try:
        predictor, gp_metrics, status_metrics = train_predictor(class_df)
    except ETRPredictorError as exc:
        st.error(f"Model tidak dapat dilatih: {exc}")
        logger.exception("Ralat melatih model AI ETR")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("R² (Regresi GP)", f"{gp_metrics['r2']:.3f}")
    col2.metric("MAE (Regresi GP)", f"{gp_metrics['mae']:.2f}")
    col3.metric("Ketepatan (Klasifikasi Status)", f"{status_metrics['accuracy']:.1%}")
    st.caption(
        f"Dilatih atas {gp_metrics['n_train']} baris, diuji atas {gp_metrics['n_test']} baris "
        f"(daripada {len(class_df)} baris kelas)."
    )

    predicted_gp = predictor.predict_gp(class_df)
    st.plotly_chart(
        fig_prediction_scatter(
            class_df["GP"], predicted_gp,
            labels=class_df["SUBJEK"] + " — " + class_df["KELAS"],
            title="Ramalan vs Sebenar (Set Penuh)",
        ),
        width="stretch",
    )

    with st.expander("Laporan Klasifikasi Status Terperinci"):
        report_df = pd.DataFrame(status_metrics["report"]).transpose()
        st.dataframe(report_df, width="stretch")

    st.subheader("Cuba Sendiri: Ramalan daripada Peratus Kelulusan")
    pct_lulus = st.slider("Peratus Kelulusan Kelas (%)", 0.0, 100.0, 50.0, step=1.0)
    what_if = pd.DataFrame({"PCT_LULUS": [pct_lulus]})
    pred_gp = predictor.predict_gp(what_if)[0]
    pred_status = predictor.predict_status(what_if)[0]
    col1, col2 = st.columns(2)
    col1.metric("Ramalan GP", f"{pred_gp:.2f}")
    col2.metric("Ramalan Status", pred_status)


def page_tentang():
    st.subheader("Tentang Aplikasi")
    st.markdown(
        f"""
        **AI ETR Predictor SMKKJ** — versi {APP_VERSION}

        Aplikasi analisis dan ramalan prestasi peperiksaan SMK Kelana Jaya,
        dibina dengan Streamlit, pandas dan scikit-learn.

        **Sumber data** (semuanya agregat kelas/subjek/bidang, tiada data
        individu murid):
        - `GPS_Bidang_SMKKJ_2026.xlsx`
        - `ANALISIS_PPT_2026_T5_OPTIMISED.xlsx`

        Lihat `docs/MODULES.md` untuk dokumentasi setiap modul.
        """
    )


PAGES = {
    "Ringkasan": page_ringkasan,
    "GPS Bidang": page_gps_bidang,
    "Analisis PPT": page_analisis_ppt,
    "Ramalan AI ETR": page_ramalan_ai,
    "Tentang": page_tentang,
}


def main():
    if not session.is_authenticated():
        render_login_form()
        st.stop()

    user = session.current_user()
    allowed_pages = permissions.pages_for_role(user.role)
    if not allowed_pages:
        st.error("Akaun anda tiada akses kepada mana-mana halaman. Hubungi pentadbir.")
        logger.error("Pengguna '%s' (peranan '%s') tiada halaman dibenarkan", user.username, user.role)
        st.stop()

    show_header()
    st.caption(f"Versi {APP_VERSION} • Log masuk sebagai {user.full_name} ({user.role})")

    if st.sidebar.button("Log Keluar"):
        session.logout()
        st.rerun()

    default_page = permissions.default_page_for(user.role)
    default_index = allowed_pages.index(default_page) if default_page in allowed_pages else 0
    choice = st.sidebar.radio("Navigasi", allowed_pages, index=default_index)

    try:
        PAGES[choice]()
    except ETRPredictorError as exc:
        st.error(f"Ralat memuatkan data: {exc}")
        logger.exception("Ralat data pada halaman '%s'", choice)
    except Exception as exc:  # noqa: BLE001 - last-resort guard for the UI
        st.error("Ralat tidak dijangka berlaku. Sila semak log untuk butiran.")
        logger.exception("Ralat tidak dijangka pada halaman '%s': %s", choice, exc)


if __name__ == "__main__":
    main()
