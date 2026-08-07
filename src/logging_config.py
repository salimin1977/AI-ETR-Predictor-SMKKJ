"""
Centralised logging setup for the AI ETR Predictor SMKKJ project.

Call `configure_logging()` once, as early as possible (e.g. at the top of
`app.py`). Every other module should then just do:

    from src.logging_config import get_logger
    logger = get_logger(__name__)

so log records carry the originating module name.
"""

import logging
from logging.handlers import RotatingFileHandler

from src.config import LOG_FILE, LOG_FORMAT, LOGS_DIR

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotently attach a console handler and a rotating file handler
    to the root logger. Safe to call multiple times (e.g. across Streamlit
    reruns) - only configures handlers once per process.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger. Configures logging on first use so
    modules can safely call this at import time without depending on
    `app.py` having run first (useful for tests/scripts).
    """
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
