"""Smoke tests for src/preprocessing.py against the real bundled sample data."""

import pandas as pd
import pytest

from src.exceptions import DataFileNotFoundError
from src.preprocessing import DataPreprocessor, classify_gp_band


@pytest.fixture(scope="module")
def processor():
    return DataPreprocessor()


def test_load_gps_ringkasan_bidang(processor):
    df = processor.load_gps_ringkasan_bidang()
    assert not df.empty
    assert {"BIDANG", "BIL_SUBJEK", "GPS_TERENDAH", "GP_BIDANG", "STATUS", "STATUS_CLEAN"} <= set(df.columns)
    assert df["GP_BIDANG"].notna().all()


def test_load_gps_school_summary(processor):
    summary = processor.load_gps_school_summary()
    assert summary["label"].upper().startswith("GPS SEKOLAH")
    assert summary["gp_purata"] == pytest.approx(4.76875)
    assert summary["etr_sasaran"] == pytest.approx(4.84)


def test_load_gps_dashboard(processor):
    df = processor.load_gps_dashboard()
    assert len(df) == 18
    assert df["BIDANG"].notna().all()
    assert df["SUBJEK"].notna().all()


def test_load_gps_kemanusiaan_detail(processor):
    df = processor.load_gps_kemanusiaan_detail()
    assert len(df) == 7
    assert "GURU_PIC" in df.columns


def test_load_ppt_summary(processor):
    df = processor.load_ppt_summary()
    assert len(df) == 18
    row = df[df["KOD"] == "1103"].iloc[0]
    assert row["MATA_PELAJARAN"] == "BAHASA MELAYU"
    assert row["BIL_DAFTAR"] == 98
    assert row["PCT_LULUS"] == pytest.approx(81.72)
    assert row["GRED_PURATA"] == pytest.approx(3.90)
    assert row["GP_BAND"] == "SEDERHANA"


def test_load_ppt_school_gp(processor):
    assert processor.load_ppt_school_gp() == pytest.approx(6.46)


def test_load_ppt_class_breakdown(processor):
    df = processor.load_ppt_class_breakdown()
    assert not df.empty
    assert df["KOD"].nunique() == 18
    assert {"KELAS", "PCT_LULUS", "GP"} <= set(df.columns)


def test_backward_compatible_load_gps_and_load_ppt(processor):
    assert not processor.load_gps().empty
    assert not processor.load_ppt().empty


def test_clean_dataframe_still_works(processor):
    df = pd.DataFrame({"A": [1, None], "Unnamed: 1": [2, 3], "B": [None, None]})
    cleaned = processor.clean_dataframe(df)
    assert "Unnamed: 1" not in cleaned.columns


def test_missing_file_raises(tmp_path):
    processor = DataPreprocessor(raw_path=tmp_path)
    with pytest.raises(DataFileNotFoundError):
        processor.load_gps_ringkasan_bidang()


@pytest.mark.parametrize(
    "gp,expected",
    [(1.5, "CEMERLANG"), (2.5, "BAIK"), (4.0, "SEDERHANA"), (6.0, "LEMAH"), (8.0, "KRITIKAL"), (None, None)],
)
def test_classify_gp_band(gp, expected):
    assert classify_gp_band(gp) == expected
