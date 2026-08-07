"""Tests for src/auth.py using a temp-file-backed UserStore."""

import pytest

from src.auth import AuthenticatedUser, authenticate, hash_password, verify_password
from src.exceptions import AuthenticationError
from src.users import UserStore


@pytest.fixture
def store(tmp_path):
    s = UserStore(path=tmp_path / "users.json")
    s.create("cikgu1", "correct-horse", "Cikgu Satu", "Guru")
    return s


def test_hash_password_roundtrip():
    h = hash_password("hunter2")
    assert h != "hunter2"
    assert verify_password("hunter2", h) is True
    assert verify_password("wrong", h) is False


def test_verify_password_rejects_malformed_hash():
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False


def test_authenticate_success(store):
    user = authenticate("cikgu1", "correct-horse", store=store)
    assert user == AuthenticatedUser(username="cikgu1", full_name="Cikgu Satu", role="Guru")


def test_authenticate_wrong_password(store):
    with pytest.raises(AuthenticationError):
        authenticate("cikgu1", "wrong-password", store=store)


def test_authenticate_unknown_user(store):
    with pytest.raises(AuthenticationError):
        authenticate("nobody", "whatever", store=store)


def test_authenticate_inactive_account_rejected(store):
    users = store.all_users()
    users["cikgu1"]["active"] = False
    store._write(users)
    with pytest.raises(AuthenticationError):
        authenticate("cikgu1", "correct-horse", store=store)


def test_authenticate_error_message_does_not_reveal_which_field_was_wrong(store):
    try:
        authenticate("cikgu1", "wrong-password", store=store)
    except AuthenticationError as exc:
        wrong_password_msg = str(exc)
    try:
        authenticate("nobody", "whatever", store=store)
    except AuthenticationError as exc:
        unknown_user_msg = str(exc)
    assert wrong_password_msg == unknown_user_msg
