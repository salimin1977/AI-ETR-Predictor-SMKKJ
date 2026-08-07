"""
AI ETR prediction module for AI ETR Predictor SMKKJ.

Data reality check: the source workbooks are aggregated at class/subject/
bidang level - there is no per-student data anywhere in this project. So
`ETRPredictor` does not (and cannot) predict an individual student's SPM
result. Instead it demonstrates two genuine, small-sample ML tasks over
subject/class-level rows:

1. `fit_gp_regressor` - estimate GRED PURATA (average grade, lower = better)
   from pass-rate/cohort-size features.
2. `fit_status_classifier` - classify the performance band (e.g. LEMAH,
   KRITIKAL) from the same features.

Both deliberately exclude GRED PURATA itself from the classifier's
features - GRED PURATA already determines the STATUS/GP band by the
school's own published thresholds (see `preprocessing.GP_BAND_LEGEND`),
so including it would make the "prediction" a trivial lookup rather than
a genuine estimate from earlier-available signals (pass rate, cohort size).

Sample sizes here are small (tens of rows, not thousands), so this is a
demonstrative pipeline, not a high-confidence production forecaster - the
metrics returned by `evaluate_*` should be read with that in mind.
"""

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MIN_ROWS_FOR_SPLIT, MODELS_DIR
from src.exceptions import InsufficientDataError, ModelNotTrainedError
from src.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL_FILENAME = "etr_predictor.joblib"


class ETRPredictor:
    """Small-sample regression + classification pipeline over subject/class rows.

    `train`/`predict` are the original generic regression methods, kept
    for backward compatibility. `fit_gp_regressor`/`fit_status_classifier`
    are the richer, evaluated pipelines used by the Streamlit app.
    """

    def __init__(self):
        self.model = LinearRegression()

        self.gp_regressor = None
        self.gp_feature_cols = None

        self.status_classifier = None
        self.status_feature_cols = None

    # ------------------------------------------------------------------
    # Original generic regression API (kept for backward compatibility)
    # ------------------------------------------------------------------

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    # ------------------------------------------------------------------
    # GP regressor: predict GRED PURATA from pass-rate / cohort-size
    # ------------------------------------------------------------------

    def fit_gp_regressor(self, df: pd.DataFrame, feature_cols=("PCT_LULUS",), target_col="GRED_PURATA") -> dict:
        """Fit a StandardScaler+LinearRegression pipeline. Returns evaluation
        metrics (R2, MAE) computed on a held-out split when there's enough
        data, otherwise fitted+evaluated on the full sample (small-sample
        mode - logged as a warning, and `n_test` will equal `n_train`)."""
        feature_cols = list(feature_cols)
        data = df[feature_cols + [target_col]].dropna()
        if data.empty:
            raise InsufficientDataError("Tiada baris lengkap untuk melatih model regresi GP")

        X, y = data[feature_cols], data[target_col]
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])

        if len(data) >= MIN_ROWS_FOR_SPLIT:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        else:
            logger.warning(
                "fit_gp_regressor: hanya %d baris (< %d) - dilatih & dinilai pada set penuh",
                len(data), MIN_ROWS_FOR_SPLIT,
            )
            X_train = X_test = X
            y_train = y_test = y

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        self.gp_regressor = pipeline
        self.gp_feature_cols = feature_cols

        metrics = {
            "r2": r2_score(y_test, y_pred),
            "mae": mean_absolute_error(y_test, y_pred),
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
        logger.info("fit_gp_regressor: %s", metrics)
        return metrics

    def predict_gp(self, df: pd.DataFrame):
        if self.gp_regressor is None:
            raise ModelNotTrainedError("fit_gp_regressor() belum dipanggil")
        return self.gp_regressor.predict(df[self.gp_feature_cols])

    # ------------------------------------------------------------------
    # Status classifier: predict performance band from pass-rate / cohort-size
    # ------------------------------------------------------------------

    def fit_status_classifier(
        self, df: pd.DataFrame, feature_cols=("PCT_LULUS",), target_col="STATUS_CLEAN"
    ) -> dict:
        """Fit a StandardScaler+LogisticRegression pipeline. Same small-sample
        fallback behaviour as `fit_gp_regressor`."""
        feature_cols = list(feature_cols)
        data = df[feature_cols + [target_col]].dropna()
        if data.empty:
            raise InsufficientDataError("Tiada baris lengkap untuk melatih model klasifikasi status")
        if data[target_col].nunique() < 2:
            raise InsufficientDataError("Sekurang-kurangnya 2 kelas status diperlukan untuk klasifikasi")

        X, y = data[feature_cols], data[target_col]
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=1000))])

        stratify = y if y.value_counts().min() >= 2 else None
        if len(data) >= MIN_ROWS_FOR_SPLIT:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=stratify
            )
        else:
            logger.warning(
                "fit_status_classifier: hanya %d baris (< %d) - dilatih & dinilai pada set penuh",
                len(data), MIN_ROWS_FOR_SPLIT,
            )
            X_train = X_test = X
            y_train = y_test = y

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        self.status_classifier = pipeline
        self.status_feature_cols = feature_cols

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "report": classification_report(y_test, y_pred, zero_division=0, output_dict=True),
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
        logger.info("fit_status_classifier: accuracy=%.3f", metrics["accuracy"])
        return metrics

    def predict_status(self, df: pd.DataFrame):
        if self.status_classifier is None:
            raise ModelNotTrainedError("fit_status_classifier() belum dipanggil")
        return self.status_classifier.predict(df[self.status_feature_cols])

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path=None):
        path = path or (MODELS_DIR / DEFAULT_MODEL_FILENAME)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "gp_regressor": self.gp_regressor,
                "gp_feature_cols": self.gp_feature_cols,
                "status_classifier": self.status_classifier,
                "status_feature_cols": self.status_feature_cols,
            },
            path,
        )
        logger.info("Model disimpan di: %s", path)
        return path

    def load(self, path=None):
        path = path or (MODELS_DIR / DEFAULT_MODEL_FILENAME)
        if not path.exists():
            raise ModelNotTrainedError(f"Fail model tidak dijumpai: {path}")
        state = joblib.load(path)
        self.model = state["model"]
        self.gp_regressor = state["gp_regressor"]
        self.gp_feature_cols = state["gp_feature_cols"]
        self.status_classifier = state["status_classifier"]
        self.status_feature_cols = state["status_feature_cols"]
        logger.info("Model dimuatkan dari: %s", path)
        return self
