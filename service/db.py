"""SQLite storage: message thread, offer log (read by A's nowcaster), per-phone conversation state.
Phones are stored only as salted hashes."""
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "service.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    phone_hash TEXT NOT NULL,
    crop TEXT, market TEXT, price_per_kg REAL, unit TEXT, raw_text TEXT,
    verdict TEXT, band_p10 REAL, band_p50 REAL, band_p90 REAL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    phone_hash TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_phone ON messages (phone_hash, id);
CREATE TABLE IF NOT EXISTS sessions (
    phone_hash TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path() -> Path:
    return Path(os.environ.get("SMALLAI_DB", DEFAULT_DB))


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def hash_phone(phone: str) -> str:
    salt = os.environ.get("PHONE_SALT", "smallai-dev")
    return hashlib.sha256((salt + phone.strip()).encode()).hexdigest()[:16]


def log_message(conn, phone_hash: str, direction: str, text: str) -> None:
    conn.execute(
        "INSERT INTO messages (ts, phone_hash, direction, text) VALUES (?, ?, ?, ?)",
        (now(), phone_hash, direction, text),
    )
    conn.commit()


def thread(conn, phone_hash: str, limit: int = 50) -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT ts, direction, text FROM messages WHERE phone_hash = ? ORDER BY id DESC LIMIT ?",
        (phone_hash, limit),
    ).fetchall()
    return rows[::-1]


OFFER_FIELDS = ("crop", "market", "price_per_kg", "unit", "raw_text",
                "verdict", "band_p10", "band_p50", "band_p90")


def log_offer(conn, phone_hash: str, offer: dict) -> int:
    cur = conn.execute(
        f"INSERT INTO offers (ts, phone_hash, {', '.join(OFFER_FIELDS)}) "
        f"VALUES (?, ?, {', '.join('?' * len(OFFER_FIELDS))})",
        (now(), phone_hash, *(offer.get(f) for f in OFFER_FIELDS)),
    )
    conn.commit()
    return cur.lastrowid


def get_state(conn, phone_hash: str) -> dict | None:
    row = conn.execute("SELECT state FROM sessions WHERE phone_hash = ?", (phone_hash,)).fetchone()
    return json.loads(row["state"]) if row else None


def set_state(conn, phone_hash: str, state: dict | None) -> None:
    if state is None:
        conn.execute("DELETE FROM sessions WHERE phone_hash = ?", (phone_hash,))
    else:
        conn.execute(
            "INSERT INTO sessions (phone_hash, state, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(phone_hash) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
            (phone_hash, json.dumps(state), now()),
        )
    conn.commit()
