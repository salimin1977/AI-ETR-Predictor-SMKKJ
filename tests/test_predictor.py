"""Tests for src/predictor.py using synthetic data (no dependency on real files)."""

import numpy as np
import pandas as pd
import pytest

from src.exceptions import InsufficientDataError, ModelNotTrainedError
from src.predictor import ETRPredictor


def _synthetic_df(n=20, seed=0):
    rng = np.random.default_rng(seed)
    pct_lulus = rng.uniform(0, 100, n)
    gp = 9 - 0.08 * pct_lulus + rng.normal(0, 0.3, n)
    gp = np.clip(gp, 1.0, 9.0)
    status = np.where(gp <= 3.0, "BAIK", np.where(gp <= 5.0, "SEDERHANA", np.where(gp <= 7.0, "LEMAH", "KRITIKAL")))
    return pd.DataFrame({"PCT_LULUS": pct_lulus, "GRED_PURATA": gp, "STATUS_CLEAN": status})


def test_fit_gp_regressor_real_split():
    predictor = ETRPredictor()
    metrics = predictor.fit_gp_regressor(_synthetic_df(20), feature_cols=["PCT_LULUS"], target_col="GRED_PURATA")
    assert metrics["n_train"] + metrics["n_test"] == 20
    assert metrics["n_test"] > 0
    assert metrics["r2"] > 0.5  # data was constructed with a strong linear relationship


def test_fit_gp_regressor_small_sample_fallback():
    predictor = ETRPredictor()
    df = _synthetic_df(5)
    metrics = predictor.fit_gp_regressor(df, feature_cols=["PCT_LULUS"], target_col="GRED_PURATA")
    assert metrics["n_train"] == metrics["n_test"] == 5


def test_predict_gp_before_fit_raises():
    predictor = ETRPredictor()
    with pytest.raises(ModelNotTrainedError):
        predictor.predict_gp(_synthetic_df(3))


def test_predict_gp_after_fit():
    predictor = ETRPredictor()
    df = _synthetic_df(20)
    predictor.fit_gp_regressor(df, feature_cols=["PCT_LULUS"], target_col="GRED_PURATA")
    preds = predictor.predict_gp(df.head(3))
    assert len(preds) == 3


def test_fit_gp_regressor_empty_data_raises():
    predictor = ETRPredictor()
    df = pd.DataFrame({"PCT_LULUS": [None, None], "GRED_PURATA": [None, None]})
    with pytest.raises(InsufficientDataError):
        predictor.fit_gp_regressor(df, feature_cols=["PCT_LULUS"], target_col="GRED_PURATA")


def test_fit_status_classifier():
    predictor = ETRPredictor()
    df = _synthetic_df(30)
    metrics = predictor.fit_status_classifier(df, feature_cols=["PCT_LULUS"], target_col="STATUS_CLEAN")
    assert 0.0 <= metrics["accuracy"] <= 1.0
    preds = predictor.predict_status(df.head(3))
    assert len(preds) == 3


def test_fit_status_classifier_needs_two_classes():
    predictor = ETRPredictor()
    df = pd.DataFrame({"PCT_LULUS": [10, 20, 30], "STATUS_CLEAN": ["LEMAH", "LEMAH", "LEMAH"]})
    with pytest.raises(InsufficientDataError):
        predictor.fit_status_classifier(df, feature_cols=["PCT_LULUS"], target_col="STATUS_CLEAN")


def test_predict_status_before_fit_raises():
    predictor = ETRPredictor()
    with pytest.raises(ModelNotTrainedError):
        predictor.predict_status(_synthetic_df(3))


def test_save_load_round_trip(tmp_path):
    df = _synthetic_df(20)
    predictor = ETRPredictor()
    predictor.fit_gp_regressor(df, feature_cols=["PCT_LULUS"], target_col="GRED_PURATA")
    predictor.fit_status_classifier(df, feature_cols=["PCT_LULUS"], target_col="STATUS_CLEAN")

    path = tmp_path / "model.joblib"
    predictor.save(path)

    loaded = ETRPredictor().load(path)
    np.testing.assert_allclose(loaded.predict_gp(df.head(5)), predictor.predict_gp(df.head(5)))
    assert list(loaded.predict_status(df.head(5))) == list(predictor.predict_status(df.head(5)))


def test_load_missing_file_raises(tmp_path):
    predictor = ETRPredictor()
    with pytest.raises(ModelNotTrainedError):
        predictor.load(tmp_path / "does_not_exist.joblib")


def test_original_train_predict_still_works():
    predictor = ETRPredictor()
    X = pd.DataFrame({"x": [1, 2, 3, 4]})
    y = pd.Series([2, 4, 6, 8])
    predictor.train(X, y)
    preds = predictor.predict(pd.DataFrame({"x": [5]}))
    assert preds[0] == pytest.approx(10, rel=0.2)
