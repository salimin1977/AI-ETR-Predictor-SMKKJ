"""
Role-based access control for AI ETR Predictor SMKKJ.

Pure logic, no Streamlit/bcrypt dependency - independently testable.

Page-level RBAC only: each role sees a filtered subset of the app's
existing pages (defined in `app.py`'s `PAGES` dict) and lands on a
role-appropriate default page after login. There is currently no
user-to-subject/bidang data mapping, so this does not filter *rows* of
data (e.g. a Guru does not see only their own subject's numbers) - only
which *pages* are reachable. Finer per-subject data scoping would need
users to be linked to a specific subject/bidang, which is a natural
future extension but out of scope here.
"""

ROLES = ("Pengetua", "PK Pentadbiran", "GKMP", "Ketua Panitia", "Guru")

_ALL_PAGES = ("Ringkasan", "GPS Bidang", "Analisis PPT", "Ramalan AI ETR", "Tentang")

ROLE_PAGES = {
    "Pengetua": _ALL_PAGES,
    "PK Pentadbiran": _ALL_PAGES,
    "GKMP": ("Ringkasan", "GPS Bidang", "Analisis PPT", "Ramalan AI ETR", "Tentang"),
    "Ketua Panitia": ("Ringkasan", "Analisis PPT", "Ramalan AI ETR", "Tentang"),
    "Guru": ("Ringkasan", "Analisis PPT", "Tentang"),
}

ROLE_DEFAULT_PAGE = {
    "Pengetua": "Ringkasan",
    "PK Pentadbiran": "Ringkasan",
    "GKMP": "GPS Bidang",
    "Ketua Panitia": "Analisis PPT",
    "Guru": "Analisis PPT",
}


def pages_for_role(role: str) -> tuple:
    """Ordered pages visible to `role`. Unknown roles get no pages."""
    return ROLE_PAGES.get(role, ())


def default_page_for(role: str) -> str:
    """Landing page for `role` after login, falling back to the first
    page that role can see (or None if the role has no pages)."""
    default = ROLE_DEFAULT_PAGE.get(role)
    pages = pages_for_role(role)
    if default in pages:
        return default
    return pages[0] if pages else None


def has_permission(role: str, page: str) -> bool:
    return page in pages_for_role(role)
