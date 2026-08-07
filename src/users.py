"""
JSON-backed user store for AI ETR Predictor SMKKJ.

Deliberately simple: one JSON file (`data/auth/users.json`, path from
`config.USERS_FILE`) holding a list of user records. This is an explicit
"good enough for now" choice - the schema (username/password_hash/
full_name/role/active) maps directly onto a future `users` table, so
migrating to a real database later is a straight data copy, not a
redesign.

Password hashing lives in `src/auth.py` (bcrypt); this module only stores
and retrieves whatever hash it's given, plus seeds default accounts on
first run so the app is usable out of the box.
"""

import json

from src.config import USERS_FILE
from src.logging_config import get_logger
from src.permissions import ROLES

logger = get_logger(__name__)

# Seed accounts created only if data/auth/users.json doesn't exist yet.
# Username = role slug, password = "<RoleSlug>@SMKKJ2026" - MUST be changed
# after first login (see README). Kept here as plain constants (not
# fabricated secrets tied to any real deployment) purely to make the app
# runnable immediately after a fresh checkout.
_SEED_ACCOUNTS = [
    {"username": "pengetua", "password": "Pengetua@SMKKJ2026", "full_name": "Pengetua", "role": "Pengetua"},
    {"username": "pk_pentadbiran", "password": "PkPentadbiran@SMKKJ2026", "full_name": "PK Pentadbiran", "role": "PK Pentadbiran"},
    {"username": "gkmp", "password": "Gkmp@SMKKJ2026", "full_name": "GKMP", "role": "GKMP"},
    {"username": "ketua_panitia", "password": "KetuaPanitia@SMKKJ2026", "full_name": "Ketua Panitia", "role": "Ketua Panitia"},
    {"username": "guru", "password": "Guru@SMKKJ2026", "full_name": "Guru", "role": "Guru"},
]


class UserStore:
    """CRUD access to the JSON user file."""

    def __init__(self, path=None):
        self.path = path or USERS_FILE

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            records = json.load(f)
        return {record["username"]: record for record in records}

    def _write(self, users: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(list(users.values()), f, indent=2, ensure_ascii=False)

    def all_users(self) -> dict:
        """{username: record} for every stored user."""
        return self._read()

    def get(self, username: str):
        return self._read().get(username)

    def create(self, username: str, password: str, full_name: str, role: str) -> dict:
        if role not in ROLES:
            raise ValueError(f"Peranan tidak sah: {role}")
        users = self._read()
        if username in users:
            raise ValueError(f"Nama pengguna sudah wujud: {username}")

        from src.auth import hash_password  # deferred: avoids an auth<->users import cycle

        record = {
            "username": username,
            "password_hash": hash_password(password),
            "full_name": full_name,
            "role": role,
            "active": True,
        }
        users[username] = record
        self._write(users)
        logger.info("Pengguna dicipta: %s (%s)", username, role)
        return record

    def ensure_seeded(self) -> None:
        """Create the default per-role accounts if the user file doesn't exist yet."""
        if self.path.exists():
            return
        logger.warning(
            "Tiada fail pengguna dijumpai - menjana %d akaun lalai di %s. "
            "TUKAR kata laluan lalai serta-merta (lihat README).",
            len(_SEED_ACCOUNTS), self.path,
        )
        for account in _SEED_ACCOUNTS:
            self.create(**account)
