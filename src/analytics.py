"""
Descriptive analytics helpers for AI ETR Predictor SMKKJ.

`Analytics` is a thin, stateless collection of DataFrame -> summary
transformations used by `dashboard.py` and `app.py`. Every method accepts
plain `pandas.DataFrame`/column-name arguments (no Streamlit dependency)
so it stays independently testable.

Note on grading convention: for GRED PURATA (GP) values, *lower is
better* (GP 1.00 is the best possible average grade). Ranking/"gap"
helpers below respect that convention.
"""

import pandas as pd

from src.logging_config import get_logger

logger = get_logger(__name__)


class Analytics:
    """Reusable KPI/summary computations over exam-performance DataFrames."""

    # ------------------------------------------------------------------
    # Original methods (kept for backward compatibility)
    # ------------------------------------------------------------------

    def total_students(self, df):
        return len(df)

    def missing_values(self, df):
        return df.isnull().sum()

    def summary(self, df):
        return df.describe(include="all")

    # ------------------------------------------------------------------
    # New KPI / risk helpers
    # ------------------------------------------------------------------

    def status_counts(self, df: pd.DataFrame, status_col: str = "STATUS_CLEAN") -> pd.Series:
        """Count of rows per status/GP-band label, most common first."""
        if status_col not in df.columns:
            return pd.Series(dtype=int)
        return df[status_col].value_counts()

    def average_gp(self, df: pd.DataFrame, gp_col: str = "GRED_PURATA"):
        """Mean GP across rows (NaNs ignored). Returns None if the column
        is missing or has no numeric values."""
        if gp_col not in df.columns:
            return None
        series = pd.to_numeric(df[gp_col], errors="coerce").dropna()
        return float(series.mean()) if not series.empty else None

    def subjects_at_risk(
        self,
        df: pd.DataFrame,
        status_col: str = "STATUS_CLEAN",
        risk_labels=("LEMAH", "KRITIKAL"),
        sort_col: str = "GRED_PURATA",
    ) -> pd.DataFrame:
        """Rows flagged as at-risk by `status_col`, worst GP first when
        `sort_col` is available."""
        if status_col not in df.columns:
            return df.iloc[0:0]
        at_risk = df[df[status_col].isin(risk_labels)].copy()
        if sort_col in at_risk.columns:
            at_risk = at_risk.sort_values(sort_col, ascending=False)
        logger.info("subjects_at_risk: %d/%d baris berisiko", len(at_risk), len(df))
        return at_risk

    def gap_to_target(
        self,
        df: pd.DataFrame,
        gp_col: str = "GP_BIDANG",
        target_col: str = "GPS_SASARAN",
        gap_col: str = "GAP",
    ) -> pd.DataFrame:
        """Return a copy of `df` with a `GAP` column = achieved GP - target GP.

        Positive GAP means the achieved GP is *worse* than target (since
        lower GP is better); negative/zero means the target is met.
        """
        result = df.copy()
        if gp_col not in result.columns or target_col not in result.columns:
            result[gap_col] = pd.NA
            return result
        result[gap_col] = pd.to_numeric(result[gp_col], errors="coerce") - pd.to_numeric(
            result[target_col], errors="coerce"
        )
        return result

    def bidang_ranking(self, ringkasan_df: pd.DataFrame, gp_col: str = "GP_BIDANG") -> pd.DataFrame:
        """Bidang rows sorted best-to-worst (ascending GP)."""
        if gp_col not in ringkasan_df.columns:
            return ringkasan_df
        return ringkasan_df.sort_values(gp_col, ascending=True).reset_index(drop=True)
