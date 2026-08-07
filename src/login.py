"""
Streamlit login page for AI ETR Predictor SMKKJ.

Presentation-only: delegates credential checking to `src.auth.authenticate`
and session state to `src.session`. Mirrors the project's existing split
between pure logic and Streamlit UI (e.g. `src/dashboard.py`'s figure
builders vs. `app.py`'s `st.plotly_chart` calls).
"""

import streamlit as st

from src.auth import authenticate
from src.exceptions import AuthenticationError
from src.logging_config import get_logger
from src.session import login as start_session

logger = get_logger(__name__)


def render_login_form() -> None:
    st.title("🎯 AI ETR Predictor SMKKJ")
    st.subheader("Log Masuk")

    with st.form("login_form"):
        username = st.text_input("Nama Pengguna")
        password = st.text_input("Kata Laluan", type="password")
        submitted = st.form_submit_button("Log Masuk")

    if submitted:
        try:
            user = authenticate(username, password)
        except AuthenticationError as exc:
            st.error(str(exc))
            return

        start_session(user)
        st.rerun()
