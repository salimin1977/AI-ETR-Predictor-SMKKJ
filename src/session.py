"""
Streamlit session state wrapper for AI ETR Predictor SMKKJ.

Thin, Streamlit-coupled by necessity (there's nothing to unit test here
beyond what `src/auth.py` already covers - `st.session_state` only exists
inside a running Streamlit script). Enforces a simple idle timeout so a
logged-in session doesn't stay valid forever.
"""

import time

import streamlit as st

from src.config import SESSION_TIMEOUT_MINUTES
from src.logging_config import get_logger

logger = get_logger(__name__)

_USER_KEY = "auth_user"
_LAST_ACTIVITY_KEY = "auth_last_activity"


def login(user) -> None:
    """Store an `auth.AuthenticatedUser` as the active session."""
    st.session_state[_USER_KEY] = user
    st.session_state[_LAST_ACTIVITY_KEY] = time.time()


def logout() -> None:
    st.session_state.pop(_USER_KEY, None)
    st.session_state.pop(_LAST_ACTIVITY_KEY, None)


def current_user():
    """The active `auth.AuthenticatedUser`, or None if not logged in."""
    return st.session_state.get(_USER_KEY)


def is_authenticated() -> bool:
    """True if a user is logged in and hasn't been idle past the timeout.

    Refreshes the last-activity timestamp on every call, and auto-logs-out
    (returns False) once the session has been idle longer than
    `config.SESSION_TIMEOUT_MINUTES`.
    """
    user = st.session_state.get(_USER_KEY)
    if user is None:
        return False

    last_activity = st.session_state.get(_LAST_ACTIVITY_KEY, 0)
    if (time.time() - last_activity) / 60 > SESSION_TIMEOUT_MINUTES:
        logger.info("Sesi tamat tempoh (tidak aktif): %s", user.username)
        logout()
        return False

    st.session_state[_LAST_ACTIVITY_KEY] = time.time()
    return True
