"""卡片管理工具：查卡、额度调整、冻结/解锁、挂失（联动停代扣）。"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok, fail

ACCOUNT_ID = 1


def list_cards() -> Envelope:
    """查询名下卡片。"""
    rows = store.query("SELECT * FROM cards WHERE account_id=?", (ACCOUNT_ID,))
    return ok(rows, "card")


def adjust_limit(card_id: int, new_limit: float) -> Envelope:
    """额度调整：调低 L2，调高 L3。"""
    card = store.query("SELECT * FROM cards WHERE id=? AND account_id=?", (card_id, ACCOUNT_ID))
    if not card:
        return fail("卡片不存在", "card")
    if card[0]["status"] != "normal":
        return fail(f"卡片状态为 {card[0]['status']}，无法调整", "card")
    if new_limit <= 0:
        return fail("额度必须大于 0", "card")
    old = card[0]["daily_limit"]
    store.execute("UPDATE cards SET daily_limit=? WHERE id=?", (new_limit, card_id))
    direction = "调高" if new_limit > old else "调低"
    return ok({"card": card[0]["card_no"], "old_limit": old, "new_limit": new_limit, "direction": direction}, "card")


def freeze_card(card_id: int) -> Envelope:
    """冻结卡片。"""
    card = store.query("SELECT * FROM cards WHERE id=? AND account_id=?", (card_id, ACCOUNT_ID))
    if not card:
        return fail("卡片不存在", "card")
    store.execute("UPDATE cards SET status='frozen' WHERE id=?", (card_id,))
    return ok({"card": card[0]["card_no"], "status": "frozen"}, "card")


def unfreeze_card(card_id: int) -> Envelope:
    """解锁卡片。"""
    card = store.query("SELECT * FROM cards WHERE id=? AND account_id=?", (card_id, ACCOUNT_ID))
    if not card:
        return fail("卡片不存在", "card")
    store.execute("UPDATE cards SET status='normal' WHERE id=?", (card_id,))
    return ok({"card": card[0]["card_no"], "status": "normal"}, "card")


def report_loss(card_id: int) -> Envelope:
    """挂失（L3）：置为 lost，并联动列出该卡上的代扣。"""
    card = store.query("SELECT * FROM cards WHERE id=? AND account_id=?", (card_id, ACCOUNT_ID))
    if not card:
        return fail("卡片不存在", "card")
    store.execute("UPDATE cards SET status='lost' WHERE id=?", (card_id,))
    subs = store.query(
        "SELECT * FROM subscriptions WHERE card_no=? AND status='active'", (card[0]["card_no"],)
    )
    return ok(
        {"card": card[0]["card_no"], "status": "lost", "linked_subscriptions": subs, "tip": "是否一并暂停该卡上的代扣？"},
        "card",
    )
