"""
Central configuration for the AI ETR Predictor SMKKJ project.

Holds filesystem paths and constants shared across modules so that no
other module hardcodes a path string. All paths are resolved relative to
the project root (the parent of the `src/` package).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

AUTH_DIR = DATA_DIR / "auth"
USERS_FILE = AUTH_DIR / "users.json"
# How long a session may sit idle before is_authenticated() forces a logout.
SESSION_TIMEOUT_MINUTES = 60

GPS_BIDANG_FILE = "GPS_Bidang_SMKKJ_2026.xlsx"
PPT_ANALYSIS_FILE = "ANALISIS_PPT_2026_T5_OPTIMISED.xlsx"

LOG_FILE = LOGS_DIR / "app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Minimum number of rows required before a train/test split is attempted.
# Below this, models are fitted on the full sample (small-data mode) and a
# warning is logged instead of raising an error.
MIN_ROWS_FOR_SPLIT = 10

APP_VERSION = "2.1.0"
