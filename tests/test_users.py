"""Tests for src/users.py using a temp-file-backed UserStore (never touches
the real data/auth/users.json)."""

import pytest

from src.users import UserStore, _SEED_ACCOUNTS


@pytest.fixture
def store(tmp_path):
    return UserStore(path=tmp_path / "users.json")


def test_ensure_seeded_creates_one_account_per_role(store):
    store.ensure_seeded()
    users = store.all_users()
    assert len(users) == len(_SEED_ACCOUNTS)
    roles = {record["role"] for record in users.values()}
    from src.permissions import ROLES

    assert roles == set(ROLES)


def test_ensure_seeded_is_idempotent(store):
    store.ensure_seeded()
    store.ensure_seeded()
    assert len(store.all_users()) == len(_SEED_ACCOUNTS)


def test_create_hashes_the_password(store):
    record = store.create("cikgu1", "s3cret-pw", "Cikgu Satu", "Guru")
    assert record["password_hash"] != "s3cret-pw"
    assert record["password_hash"].startswith("$2b$")


def test_create_duplicate_username_raises(store):
    store.create("cikgu1", "pw", "Cikgu Satu", "Guru")
    with pytest.raises(ValueError):
        store.create("cikgu1", "pw2", "Cikgu Dua", "Guru")


def test_create_invalid_role_raises(store):
    with pytest.raises(ValueError):
        store.create("cikgu1", "pw", "Cikgu Satu", "NotARole")


def test_get_missing_user_returns_none(store):
    assert store.get("nobody") is None


def test_persists_across_instances(tmp_path):
    path = tmp_path / "users.json"
    UserStore(path=path).create("cikgu1", "pw", "Cikgu Satu", "Guru")
    reloaded = UserStore(path=path)
    assert reloaded.get("cikgu1")["full_name"] == "Cikgu Satu"
