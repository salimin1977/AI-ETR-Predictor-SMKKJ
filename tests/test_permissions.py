"""Tests for src/permissions.py."""

import pytest

from src import permissions


@pytest.mark.parametrize("role", permissions.ROLES)
def test_every_role_has_pages_and_a_default(role):
    pages = permissions.pages_for_role(role)
    assert pages, f"{role} should see at least one page"
    default = permissions.default_page_for(role)
    assert default in pages


def test_pengetua_and_pk_pentadbiran_see_everything():
    all_pages = set(permissions.pages_for_role("Pengetua"))
    assert all_pages == set(permissions.pages_for_role("PK Pentadbiran"))
    assert "Ramalan AI ETR" in all_pages
    assert "GPS Bidang" in all_pages


def test_guru_cannot_see_admin_pages():
    guru_pages = permissions.pages_for_role("Guru")
    assert "GPS Bidang" not in guru_pages
    assert "Ramalan AI ETR" not in guru_pages
    assert "Analisis PPT" in guru_pages


def test_has_permission():
    assert permissions.has_permission("Guru", "Tentang") is True
    assert permissions.has_permission("Guru", "GPS Bidang") is False


def test_unknown_role_has_no_pages():
    assert permissions.pages_for_role("Nobody") == ()
    assert permissions.default_page_for("Nobody") is None
    assert permissions.has_permission("Nobody", "Ringkasan") is False
