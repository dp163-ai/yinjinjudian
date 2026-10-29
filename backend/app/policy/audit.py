"""审计留痕：所有写操作记录审计日志，防抵赖、可回溯。

依据 docs/00_CONSTITUTION.md R4、docs/03_SECURITY_DESIGN.md §2.5。
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "audit.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT,
    target TEXT,
    amount REAL,
    policy_rule TEXT,
    confirm_text TEXT,
    ts TEXT,
    result TEXT
)
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def log(
    user_id: str,
    action: str,
    target: str,
    amount: float,
    policy_rule: str,
    confirm_text: str,
    result: str,
) -> None:
    """写入一条审计日志。"""
    conn = _connect()
    conn.execute(
        "INSERT INTO audit(user_id,action,target,amount,policy_rule,confirm_text,ts,result) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            user_id,
            action,
            target,
            amount,
            policy_rule,
            confirm_text,
            datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            result,
        ),
    )
    conn.commit()
    conn.close()


def list_logs(limit: int = 50) -> list[dict]:
    """按时间倒序返回审计日志。"""
    conn = _connect()
    rows = conn.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    cols = ["id", "user_id", "action", "target", "amount", "policy_rule", "confirm_text", "ts", "result"]
    return [dict(zip(cols, r)) for r in rows]
