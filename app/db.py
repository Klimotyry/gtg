import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/bot.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                sbp_phone TEXT,
                sbp_bank TEXT,
                card_number TEXT,
                successful_deals INTEGER NOT NULL DEFAULT 0,
                bought_bc INTEGER NOT NULL DEFAULT 0,
                sold_bc INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name
            """,
            (telegram_id, username, first_name),
        )


def get_user(telegram_id: int):
    with _connect() as conn:
        return conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()


def set_sbp(telegram_id: int, phone: str, bank: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET sbp_phone=?, sbp_bank=? WHERE telegram_id=?",
            (phone, bank, telegram_id),
        )


def set_card(telegram_id: int, card_number: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET card_number=? WHERE telegram_id=?",
            (card_number, telegram_id),
        )
