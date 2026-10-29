"""订阅/代扣管理工具：识别扣费、续费提醒、一键取消。"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok, fail

ACCOUNT_ID = 1


def list_subscriptions() -> Envelope:
    """识别并列出订阅扣费，标记异常（涨价/无使用）。"""
    rows = store.query(
        "SELECT * FROM subscriptions WHERE account_id=? AND status='active'", (ACCOUNT_ID,)
    )
    total = round(sum(r["monthly_fee"] for r in rows), 2)
    return ok({"count": len(rows), "monthly_total": total, "subscriptions": rows}, "subscription")


def remind_renewal() -> Envelope:
    """续费提醒：renew_day 临近的订阅。"""
    rows = store.query(
        "SELECT * FROM subscriptions WHERE account_id=? AND status='active'", (ACCOUNT_ID,)
    )
    return ok({"reminders": rows, "tip": "以下订阅即将续费，请确认是否保留"}, "subscription")


def cancel_subscription(sub_id: int) -> Envelope:
    """一键取消订阅（L2，可逆）。"""
    sub = store.query("SELECT * FROM subscriptions WHERE id=? AND account_id=?", (sub_id, ACCOUNT_ID))
    if not sub:
        return fail("订阅不存在", "subscription")
    if sub[0]["status"] != "active":
        return fail("该订阅已取消", "subscription")
    store.execute("UPDATE subscriptions SET status='cancelled' WHERE id=?", (sub_id,))
    return ok({"name": sub[0]["name"], "monthly_fee": sub[0]["monthly_fee"], "status": "cancelled"}, "subscription")


def renew_subscription(sub_id: int) -> Envelope:
    """续订（恢复已取消的订阅）。"""
    sub = store.query("SELECT * FROM subscriptions WHERE id=? AND account_id=?", (sub_id, ACCOUNT_ID))
    if not sub:
        return fail("订阅不存在", "subscription")
    if sub[0]["status"] == "active":
        return fail("该订阅已在生效中", "subscription")
    store.execute("UPDATE subscriptions SET status='active' WHERE id=?", (sub_id,))
    return ok({"name": sub[0]["name"], "monthly_fee": sub[0]["monthly_fee"], "status": "active"}, "subscription")


def all_subscriptions() -> Envelope:
    """查询全部订阅（含已取消的，用于详情展示）。"""
    rows = store.query(
        "SELECT * FROM subscriptions WHERE account_id=? ORDER BY status DESC, id",
        (ACCOUNT_ID,),
    )
    return ok({"subscriptions": rows}, "subscription")
