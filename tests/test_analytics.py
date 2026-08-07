"""Tests for src/analytics.py using small synthetic DataFrames."""

import pandas as pd
import pytest

from src.analytics import Analytics


@pytest.fixture
def analytics():
    return Analytics()


@pytest.fixture
def summary_df():
    return pd.DataFrame(
        {
            "MATA_PELAJARAN": ["A", "B", "C", "D"],
            "GRED_PURATA": [2.0, 5.5, 7.5, 4.0],
            "STATUS_CLEAN": ["BAIK", "LEMAH", "KRITIKAL", "SEDERHANA"],
        }
    )


def test_total_students(analytics, summary_df):
    assert analytics.total_students(summary_df) == 4


def test_missing_values(analytics, summary_df):
    result = analytics.missing_values(summary_df)
    assert result.sum() == 0


def test_summary(analytics, summary_df):
    result = analytics.summary(summary_df)
    assert "GRED_PURATA" in result.columns


def test_status_counts(analytics, summary_df):
    counts = analytics.status_counts(summary_df)
    assert counts["LEMAH"] == 1
    assert counts.sum() == 4


def test_status_counts_missing_column(analytics, summary_df):
    result = analytics.status_counts(summary_df, status_col="NOPE")
    assert result.empty


def test_average_gp(analytics, summary_df):
    assert analytics.average_gp(summary_df) == pytest.approx((2.0 + 5.5 + 7.5 + 4.0) / 4)


def test_average_gp_missing_column(analytics, summary_df):
    assert analytics.average_gp(summary_df, gp_col="NOPE") is None


def test_subjects_at_risk(analytics, summary_df):
    at_risk = analytics.subjects_at_risk(summary_df)
    assert set(at_risk["MATA_PELAJARAN"]) == {"B", "C"}
    # sorted worst (highest GP) first
    assert at_risk.iloc[0]["MATA_PELAJARAN"] == "C"


def test_gap_to_target(analytics):
    df = pd.DataFrame({"GP_BIDANG": [4.0, 5.0], "GPS_SASARAN": [3.5, 5.5]})
    result = analytics.gap_to_target(df)
    assert list(result["GAP"]) == pytest.approx([0.5, -0.5])
    # original untouched
    assert "GAP" not in df.columns


def test_bidang_ranking(analytics):
    df = pd.DataFrame({"BIDANG": ["X", "Y"], "GP_BIDANG": [6.0, 3.0]})
    ranked = analytics.bidang_ranking(df)
    assert list(ranked["BIDANG"]) == ["Y", "X"]
