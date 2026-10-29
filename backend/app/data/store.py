"""资金事实库：SQLite 存储与查询。

表：accounts / cards / transactions / subscriptions / wealth_products / holdings / contacts / signals。
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "bank.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT, name TEXT, balance REAL
);
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, card_no TEXT, card_type TEXT,
    status TEXT DEFAULT 'normal', daily_limit REAL,
    credit_limit REAL, bill_day INTEGER
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, card_no TEXT, merchant TEXT, category TEXT,
    amount REAL, ts TEXT, remark TEXT
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, card_no TEXT, name TEXT,
    monthly_fee REAL, renew_day INTEGER, status TEXT, note TEXT,
    next_renewal TEXT
);
CREATE TABLE IF NOT EXISTS wealth_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT, name TEXT, risk_level TEXT, type TEXT,
    yoy_return REAL, min_amount REAL
);
CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, product_code TEXT, amount REAL, ts TEXT
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, name TEXT, phone TEXT
);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, signal TEXT, ts TEXT
);
CREATE TABLE IF NOT EXISTS transfer_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER, to_name TEXT, amount REAL, ts TEXT, status TEXT
);
"""


def now() -> str:
    """返回带时区的 ISO 时间串。"""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)  # 自愈：确保表结构存在（幂等）
    return conn


def init_schema() -> None:
    conn = get_conn()
    conn.commit()
    conn.close()


def query(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(sql: str, params: tuple = ()) -> None:
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()
