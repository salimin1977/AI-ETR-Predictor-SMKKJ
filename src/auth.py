"""
Password hashing and authentication for AI ETR Predictor SMKKJ.

Pure logic, no Streamlit dependency - independently testable. `src/login.py`
is the Streamlit-facing layer that calls `authenticate()` and translates
the result into UI state via `src/session.py`.
"""

from dataclasses import dataclass

import bcrypt

from src.exceptions import AuthenticationError
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    full_name: str
    role: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed stored hash - treat as a verification failure, not a crash.
        return False


def authenticate(username: str, password: str, store=None) -> AuthenticatedUser:
    """Verify credentials and return the authenticated user.

    Raises `AuthenticationError` for any failure (unknown user, wrong
    password, inactive account) with a single generic-enough message so
    the login form doesn't leak which part was wrong.
    """
    if store is None:
        from src.users import UserStore  # deferred: avoids an auth<->users import cycle

        store = UserStore()
        store.ensure_seeded()

    record = store.get(username)
    if record is None or not record.get("active", True) or not verify_password(password, record["password_hash"]):
        logger.warning("Percubaan log masuk gagal untuk pengguna: %s", username)
        raise AuthenticationError("Nama pengguna atau kata laluan tidak sah")

    logger.info("Log masuk berjaya: %s (%s)", username, record["role"])
    return AuthenticatedUser(username=record["username"], full_name=record["full_name"], role=record["role"])
