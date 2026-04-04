"""
Dogesh Assistant – SQLite user database
"""

import sqlite3
import hashlib
import json
import os
from pathlib import Path
from config import DB_PATH, KEYS_PATH, CALIBRATION_PATH


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class Database:
    """Lightweight SQLite wrapper for user auth & preferences."""

    def __init__(self):
        self._init_db()

    # ── Internal ──────────────────────────────────────────────────────────────
    def _connect(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    username    TEXT    UNIQUE NOT NULL,
                    password    TEXT    NOT NULL,
                    display_name TEXT   DEFAULT '',
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    calibrated  INTEGER DEFAULT 0,
                    api_configured INTEGER DEFAULT 0
                );
            """)

    # ── Public API ────────────────────────────────────────────────────────────
    def register(self, username: str, password: str, display_name: str = "") -> dict:
        """Create a new user. Returns {'ok': True} or {'ok': False, 'error': str}."""
        if not username or len(username) < 3:
            return {"ok": False, "error": "Username must be at least 3 characters."}
        if not password or len(password) < 6:
            return {"ok": False, "error": "Password must be at least 6 characters."}
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, password, display_name) VALUES (?,?,?)",
                    (username.lower().strip(), _hash(password), display_name.strip() or username),
                )
            return {"ok": True}
        except sqlite3.IntegrityError:
            return {"ok": False, "error": "Username already exists."}

    def login(self, username: str, password: str) -> dict:
        """Authenticate. Returns user dict or {'ok': False, 'error': str}."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username.lower().strip(), _hash(password)),
            ).fetchone()
        if not row:
            return {"ok": False, "error": "Invalid username or password."}
        return {"ok": True, "user": dict(row)}

    def get_user(self, username: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=?", (username.lower().strip(),)
            ).fetchone()
        return dict(row) if row else None

    def mark_calibrated(self, username: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET calibrated=1 WHERE username=?", (username.lower(),)
            )

    def mark_api_configured(self, username: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET api_configured=1 WHERE username=?", (username.lower(),)
            )

    # ── Key store (JSON file, keyed by username) ─────────────────────────────
    def _load_keys(self) -> dict:
        if KEYS_PATH.exists():
            try:
                return json.loads(KEYS_PATH.read_text())
            except Exception:
                pass
        return {}

    def save_keys(self, username: str, keys: dict):
        """Persist provider API keys for a user."""
        store = self._load_keys()
        store[username.lower()] = keys
        KEYS_PATH.write_text(json.dumps(store, indent=2))

    def load_keys(self, username: str) -> dict:
        """Return saved API keys for a user (or empty dict)."""
        return self._load_keys().get(username.lower(), {})

    # ── Calibration data ─────────────────────────────────────────────────────
    def _load_calibrations(self) -> dict:
        if CALIBRATION_PATH.exists():
            try:
                return json.loads(CALIBRATION_PATH.read_text())
            except Exception:
                pass
        return {}

    def save_calibration(self, username: str, data: dict):
        store = self._load_calibrations()
        store[username.lower()] = data
        CALIBRATION_PATH.write_text(json.dumps(store, indent=2))

    def load_calibration(self, username: str) -> dict:
        return self._load_calibrations().get(username.lower(), {})
