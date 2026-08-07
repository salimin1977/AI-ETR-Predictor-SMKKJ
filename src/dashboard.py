"""
Plotly figure builders for AI ETR Predictor SMKKJ.

Every function here returns a `plotly.graph_objects.Figure` and has no
Streamlit dependency - `app.py` is responsible for calling
`st.plotly_chart(fig, use_container_width=True)`. Keeping the figure
construction Streamlit-free makes it independently testable and reusable
(e.g. for exporting a static report later).

`show_header()` is kept as the original Streamlit-coupled convenience
function for backward compatibility.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.logging_config import get_logger

logger = get_logger(__name__)

# Shared colour vocabulary across the two source workbooks' different
# status labels (GP performance bands vs GPS target-achievement labels).
STATUS_COLORS = {
    "CEMERLANG": "#2E7D32",
    "BAIK": "#66BB6A",
    "SEDERHANA": "#FDD835",
    "LEMAH": "#FB8C00",
    "KRITIKAL": "#E53935",
    "Di Sasaran": "#2E7D32",
    "TERCAPAI": "#2E7D32",
    "Melebihi ETR": "#FB8C00",
    "Perlu Usaha": "#FB8C00",
    "PANTAU": "#FB8C00",
}
DEFAULT_COLOR = "#9E9E9E"


def show_header():
    st.title("🎯 AI ETR Predictor SMKKJ")
    st.caption("Dashboard Analisis Prestasi Sekolah")


def _color_for(labels):
    return [STATUS_COLORS.get(str(label).strip(), DEFAULT_COLOR) for label in labels]


def fig_subject_gp_bar(
    summary_df: pd.DataFrame,
    gp_col: str = "GRED_PURATA",
    label_col: str = "MATA_PELAJARAN",
    status_col: str = "STATUS_CLEAN",
    title: str = "Gred Purata (GP) Mengikut Subjek",
) -> go.Figure:
    """Horizontal bar of GP per subject, worst (highest GP) at top, coloured
    by performance status."""
    df = summary_df.sort_values(gp_col, ascending=True)
    fig = go.Figure(
        go.Bar(
            x=df[gp_col],
            y=df[label_col],
            orientation="h",
            marker_color=_color_for(df[status_col]) if status_col in df.columns else None,
            text=df[gp_col].round(2),
            textposition="outside",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Gred Purata (lebih rendah = lebih baik)",
        yaxis_title=None,
        height=max(350, 28 * len(df)),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def fig_status_distribution(
    summary_df: pd.DataFrame,
    status_col: str = "STATUS_CLEAN",
    title: str = "Taburan Status Pencapaian",
) -> go.Figure:
    """Donut chart of row counts per status label."""
    counts = summary_df[status_col].value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.5,
            marker_colors=_color_for(counts.index),
        )
    )
    fig.update_layout(title=title, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def fig_bidang_comparison(
    ringkasan_df: pd.DataFrame,
    bidang_col: str = "BIDANG",
    gp_col: str = "GP_BIDANG",
    target_col: str = "GPS_TERENDAH",
    title: str = "GP Bidang vs Sasaran GPS",
) -> go.Figure:
    """Grouped bar comparing achieved GP against the target per bidang."""
    fig = go.Figure()
    fig.add_bar(name="GP Bidang (Pencapaian)", x=ringkasan_df[bidang_col], y=ringkasan_df[gp_col])
    if target_col in ringkasan_df.columns:
        fig.add_bar(name="GPS Sasaran (Terendah)", x=ringkasan_df[bidang_col], y=ringkasan_df[target_col])
    fig.update_layout(
        title=title,
        barmode="group",
        yaxis_title="Gred Purata (lebih rendah = lebih baik)",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def fig_class_grade_distribution(
    class_df: pd.DataFrame,
    subject_label: str,
    subject_col: str = "SUBJEK",
    class_col: str = "KELAS",
    grade_cols=("A_PLUS", "A", "A_MINUS", "B_PLUS", "B", "C_PLUS", "C", "D", "E", "G", "TH"),
    title: str = None,
) -> go.Figure:
    """Stacked bar of grade-count distribution per class, for one subject."""
    subset = class_df[class_df[subject_col] == subject_label]
    fig = go.Figure()
    for grade in grade_cols:
        if grade in subset.columns:
            fig.add_bar(name=grade.replace("_PLUS", "+").replace("_MINUS", "-"), x=subset[class_col], y=subset[grade])
    fig.update_layout(
        title=title or f"Taburan Gred — {subject_label}",
        barmode="stack",
        yaxis_title="Bilangan Murid",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def fig_prediction_scatter(
    y_true,
    y_pred,
    labels=None,
    title: str = "Ramalan vs Sebenar (GP)",
) -> go.Figure:
    """Scatter of predicted vs actual values with a y=x reference line."""
    y_true = list(y_true)
    y_pred = list(y_pred)
    lo = min(y_true + y_pred)
    hi = max(y_true + y_pred)

    fig = go.Figure()
    fig.add_scatter(
        x=y_true, y=y_pred, mode="markers", name="Subjek",
        text=labels, marker=dict(size=10, color="#1E88E5"),
    )
    fig.add_scatter(
        x=[lo, hi], y=[lo, hi], mode="lines", name="Ramalan Sempurna (y = x)",
        line=dict(dash="dash", color="#9E9E9E"),
    )
    fig.update_layout(
        title=title,
        xaxis_title="GP Sebenar",
        yaxis_title="GP Ramalan",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig
