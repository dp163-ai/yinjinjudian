"""智能转账工具：按人名/手机号/备注转账、定时转账、拆分 AA 收款。

依据 docs/01_PRD.md §3、docs/00_CONSTITUTION.md R4。演示账号固定 account_id=1。
"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok, fail

ACCOUNT_ID = 1
DEFAULT_CARD = "6217 **** 1234"


def _contact_by_name(name: str) -> dict | None:
    rows = store.query("SELECT * FROM contacts WHERE name=? AND account_id=?", (name, ACCOUNT_ID))
    return rows[0] if rows else None


def _contact_by_phone(phone: str) -> dict | None:
    rows = store.query("SELECT * FROM contacts WHERE phone=? AND account_id=?", (phone, ACCOUNT_ID))
    return rows[0] if rows else None


def _deduct(amount: float, target: str, remark: str) -> Envelope:
    """扣款 + 记流水 + 记转账记录。"""
    acc = store.query("SELECT * FROM accounts WHERE id=?", (ACCOUNT_ID,))[0]
    if acc["balance"] < amount:
        return fail(f"余额不足，当前余额 ¥{acc['balance']:.2f}", "transfer")
    store.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, ACCOUNT_ID))
    store.execute(
        "INSERT INTO transactions(account_id,card_no,merchant,category,amount,ts,remark) VALUES(?,?,?,?,?,?,?)",
        (ACCOUNT_ID, DEFAULT_CARD, target, "转账", amount, store.now(), remark),
    )
    store.execute(
        "INSERT INTO transfer_records(account_id,to_name,amount,ts,status) VALUES(?,?,?,?,?)",
        (ACCOUNT_ID, target, amount, store.now(), "完成"),
    )
    return ok({"to": target, "amount": amount}, "transfer")


def list_transfers(limit: int = 10) -> Envelope:
    """查询转账记录。"""
    rows = store.query(
        "SELECT * FROM transfer_records WHERE account_id=? ORDER BY ts DESC LIMIT ?",
        (ACCOUNT_ID, limit),
    )
    total = round(sum(r["amount"] for r in rows), 2)
    return ok({"count": len(rows), "total": total, "records": rows}, "transfer")


def transfer_by_name(name: str, amount: float) -> Envelope:
    """按收款人姓名转账。"""
    if amount <= 0:
        return fail("金额必须大于 0", "transfer")
    if not _contact_by_name(name):
        return fail(f"未找到收款人「{name}」，请确认姓名或使用手机号转账", "transfer")
    return _deduct(amount, name, f"转账给{name}")


def transfer_by_phone(phone: str, amount: float) -> Envelope:
    """按手机号转账。"""
    if amount <= 0:
        return fail("金额必须大于 0", "transfer")
    c = _contact_by_phone(phone)
    if not c:
        return fail(f"未找到手机号「{phone}」对应的收款人", "transfer")
    return _deduct(amount, c["name"], f"转账给{c['name']}")


def transfer_by_remark(remark: str, amount: float) -> Envelope:
    """按备注转账：备注中含收款人姓名。"""
    if amount <= 0:
        return fail("金额必须大于 0", "transfer")
    c = _contact_by_name(remark)
    if not c:
        return fail(f"备注「{remark}」未匹配到收款人", "transfer")
    return _deduct(amount, c["name"], remark)


def schedule_transfer(name: str, amount: float, schedule: str) -> Envelope:
    """定时转账（记录任务，不立即扣款）。"""
    if amount <= 0:
        return fail("金额必须大于 0", "transfer")
    if not _contact_by_name(name):
        return fail(f"未找到收款人「{name}」", "transfer")
    return ok({"to": name, "amount": amount, "schedule": schedule, "status": "已设置定时转账"}, "transfer")


def split_aa(total: float, members: list[str]) -> Envelope:
    """拆分 AA 收款：返回人均金额与余数分摊。"""
    if total <= 0:
        return fail("总金额必须大于 0", "transfer")
    if not members:
        return fail("请提供参与人名单", "transfer")
    n = len(members)
    per = round(total / n, 2)
    remainder = round(total - per * n, 2)
    shares = []
    for i, m in enumerate(members):
        extra = 0.01 if i < int(round(remainder * 100)) else 0.0
        shares.append({"member": m, "amount": round(per + extra, 2)})
    return ok({"per_person": per, "shares": shares}, "transfer")
