"""
Database helpers for CarValue.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "cars.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    # -----------------------------
    # Users
    # -----------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------
    # Valuations
    # -----------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS valuations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            make TEXT,
            model TEXT,
            vehicle_type TEXT,
            price REAL,
            age INTEGER,
            mileage INTEGER,
            estimated_value REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # ------------------------------------------------
    # Migration for an existing cars.db
    # ------------------------------------------------
    # CREATE TABLE IF NOT EXISTS will NOT add user_id
    # to a table that already exists, so check for it.
    columns = conn.execute(
        "PRAGMA table_info(valuations)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "user_id" not in column_names:
        conn.execute(
            "ALTER TABLE valuations ADD COLUMN user_id INTEGER"
        )

    conn.commit()
    conn.close()


# ====================================================
# USER FUNCTIONS
# ====================================================

def create_user(name, email, password_hash):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (name, email, password_hash),
    )

    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


# ====================================================
# VALUATION FUNCTIONS
# ====================================================

def save_valuation(
    user_id,
    make,
    model,
    vehicle_type,
    price,
    age,
    mileage,
    estimated_value,
):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO valuations (
            user_id,
            make,
            model,
            vehicle_type,
            price,
            age,
            mileage,
            estimated_value
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            make,
            model,
            vehicle_type,
            price,
            age,
            mileage,
            estimated_value,
        ),
    )

    conn.commit()
    conn.close()


def get_recent_valuations(user_id, limit=5):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM valuations
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()

    conn.close()

    queries = []

    for row in rows:
        item = dict(row)

        if item.get("created_at"):
            item["created_at"] = str(
                item["created_at"]
            ).split(" ")[0]

        queries.append(item)

    return queries