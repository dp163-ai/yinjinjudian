"""编排器：完整 Agent 主循环。

流程：注入检测 → 意图识别 → 指代消解 → 任务规划 → 策略校验 → 确认卡 → 执行 → 审计 → 回执。
依据 docs/02_ARCHITECTURE.md §2.2、docs/03_SECURITY_DESIGN.md。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.data import store
from app.guard.input import detect_injection
from app.orchestrator.intent import INTENT_KEYWORDS, recognize
from app.policy.audit import log as audit_log
from app.policy.engine import ConfirmTokenStore, decide
from app.tools import bill, card, profile, subscription, transfer, wealth

ACCOUNT_ID = 1
_token_store = ConfirmTokenStore()
_sessions: dict[str, "Session"] = {}

CONFIRM_WORDS = {"确认", "好的", "可以", "是", "行", "转吧", "对", "没错", "确定", "同意", "嗯"}
CANCEL_WORDS = {"取消", "算了", "不要了", "等等", "别", "停", "不用了", "撤回"}
SKIP_WORDS = {"跳过确认", "直接转", "别问了", "不用确认", "直接执行", "别走确认", "别确认", "免确认", "不要确认"}


@dataclass
class PendingConfirm:
    action: str
    tool: str
    params: dict
    level: str
    confirm_text: str
    risk_warning: bool
    confirm_token: str


@dataclass
class Session:
    sid: str
    context: dict[str, Any] = field(default_factory=dict)
    pending: PendingConfirm | None = None
    trace: list[dict] = field(default_factory=list)


def get_session(sid: str) -> Session:
    return _sessions.setdefault(sid, Session(sid))


def extract_amount(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


def extract_recipient(text: str) -> str | None:
    for c in store.query("SELECT name FROM contacts WHERE account_id=?", (ACCOUNT_ID,)):
        if c["name"] in text:
            return c["name"]
    return None


def _detect_multi(text: str) -> list[str]:
    intents: list[str] = []
    for name in ("bill", "wealth", "transfer", "card", "subscription"):
        if any(kw in text for kw in INTENT_KEYWORDS[name]):
            intents.append(name)
    return intents


def _base(intent: str, reply: str, ok: bool = True, data: dict | None = None, trace: list | None = None) -> dict:
    return {"ok": ok, "intent": intent, "reply": reply, "data": data or {}, "trace": trace or []}


def _target_text(params: dict) -> str:
    """把操作参数转成可读的中文目标描述。"""
    to = params.get("to")
    amount = params.get("amount")
    code = params.get("code")
    sub_id = params.get("sub_id")
    card_id = params.get("card_id")
    new_limit = params.get("new_limit")
    if to is not None:
        return f"转账给 {to}"
    if code:
        return f"理财产品 {code}"
    if sub_id is not None:
        return f"订阅 #{sub_id}"
    if card_id is not None:
        if new_limit:
            return f"卡片 #{card_id} 调额"
        return f"卡片 #{card_id}"
    return "-"


def handle(session_id: str, message: str) -> dict:
    """Agent 主入口。"""
    sess = get_session(session_id)

    hit, patterns = detect_injection(message)
    if hit:
        audit_log("u001", "injection", "-", 0, "R6", message, "拦截")
        return _base("blocked", "检测到可疑指令，已拦截并不予执行。", ok=False, data={"blocked": patterns})

    # 确认卡待处理分支
    if sess.pending:
        return _handle_pending(sess, message)

    # 跨场景联动：挂失后暂停该卡代扣
    if ("暂停" in message or "一起停" in message or "停掉" in message) and sess.context.get("pending_pause_subs"):
        subs = sess.context.pop("pending_pause_subs")
        for s in subs:
            subscription.cancel_subscription(s["id"])
        audit_log("u001", "pause_subscriptions", "-", 0, "R3", message, "联动暂停")
        return _base("subscription", f"已暂停该卡上的 {len(subs)} 笔代扣，下月起不再扣费。", trace=[{"step": "跨场景联动", "result": "挂失→停代扣"}])

    # 跨场景联动：生日锁资金（只推荐，不代下单）
    if "生日" in message:
        return _base(
            "profile",
            "已为你锁定一笔活期 ¥1,000 用于生日准备，并推荐鲜花、蛋糕入口（仅推荐，不自动下单）。",
            data={"birthday_locked": 1000, "disclaimer": "本推荐不构成投资建议"},
            trace=[{"step": "跨场景联动", "result": "生日锁资金+推荐"}],
        )

    intents = _detect_multi(message)
    if len(intents) >= 2:
        return _run_multi(sess, message, intents)

    intent = intents[0] if intents else "chat"
    sess.trace.append({"step": "意图识别", "result": intent})
    return _dispatch(sess, intent, message)


def _handle_pending(sess: Session, message: str) -> dict:
    p = sess.pending
    assert p is not None
    if any(w in message for w in SKIP_WORDS):
        audit_log("u001", p.action, _target_text(p.params), p.params.get("amount", 0), "R4/红线6", message, "拒绝跳过确认")
        return _base("blocked", "安全起见，我不能跳过确认。请回复「确认」继续，或回复「取消」放弃。", ok=False)
    if any(w in message for w in CANCEL_WORDS):
        sess.pending = None
        audit_log("u001", p.action, _target_text(p.params), p.params.get("amount", 0), "R4", "用户取消", "取消")
        return _base("cancel", f"已取消「{p.confirm_text}」，本次未执行任何操作。", trace=[{"step": "中断改口", "result": "已回滚"}])
    if any(w in message for w in CONFIRM_WORDS):
        return _do_confirm(sess)
    # 既非确认也非取消：视为新指令，清 pending 继续
    sess.pending = None
    intent = recognize(message)
    return _dispatch(sess, intent.name, message)


def _do_confirm(sess: Session) -> dict:
    p = sess.pending
    sess.pending = None
    if not _token_store.verify(p.confirm_token, sess.sid):
        audit_log("u001", p.action, _target_text(p.params), p.params.get("amount", 0), "R4", "凭证失效", "拒绝")
        return _base(p.action, "确认凭证已失效或已使用，请重新发起操作。", ok=False)
    env = _execute_action(p)
    if env.ok:
        if p.tool == "transfer":
            sess.context["last_transfer"] = {"to": p.params["to"], "amount": p.params["amount"]}
        if p.tool == "card":
            sess.context["pending_pause_subs"] = (env.data or {}).get("linked_subscriptions", [])
    audit_log("u001", p.action, _target_text(p.params), p.params.get("amount", 0), f"R4-{p.level}", p.confirm_text, "已确认执行" if env.ok else "执行失败")
    sess.trace.append({"step": "确认执行", "result": env.source})
    reply = _env_reply(p.tool, env)
    return _base(p.action, reply, ok=env.ok, data=env.data, trace=list(sess.trace))


def _execute_action(p: PendingConfirm):
    if p.tool == "transfer":
        return transfer.transfer_by_name(p.params["to"], p.params["amount"])
    if p.tool == "subscription":
        return subscription.cancel_subscription(p.params["sub_id"])
    if p.tool == "card":
        return card.report_loss(p.params["card_id"])
    if p.tool == "wealth":
        if p.action == "redeem":
            return wealth.redeem(p.params["code"], p.params["amount"])
        return wealth.purchase(p.params["code"], p.params["amount"])
    if p.tool == "card_limit":
        return card.adjust_limit(p.params["card_id"], p.params["new_limit"])
    from app.envelope import Envelope

    return Envelope.fail("未知操作", "system")


def _run_multi(sess: Session, message: str, intents: list[str]) -> dict:
    """多意图：bill + subscription 联动（先看账单，再建议退无用订阅）。"""
    if "bill" in intents and "subscription" in intents:
        stats = bill.category_stats()
        subs = subscription.list_subscriptions()
        candidates = [s for s in subs.data["subscriptions"] if s.get("note")]
        reply = (
            f"本月消费 ¥{stats.data['total']}。检测到 {len(candidates)} 笔可优化的订阅："
            + "、".join(f"{s['name']}（{s['note']}）" for s in candidates)
            + "。需要我帮你取消吗？"
        )
        sess.trace.append({"step": "多意图拆解", "result": "bill→subscription 依赖"})
        return _base("multi", reply, data={"bill": stats.data, "candidates": candidates}, trace=list(sess.trace))
    return _dispatch(sess, intents[0], message)


def _dispatch(sess: Session, intent: str, text: str) -> dict:
    if intent == "bill":
        if "异常" in text:
            env = bill.detect_anomalies()
        elif "报告" in text or "月报" in text:
            env = bill.report()
        elif "趋势" in text or "结余" in text or "收支" in text:
            env = bill.monthly_trend()
        elif "流水" in text or "明细" in text or "最近" in text:
            env = bill.recent_transactions()
        else:
            env = bill.category_stats()
        return _base(intent, _env_reply(intent, env), ok=env.ok, data=env.data, trace=list(sess.trace))

    if intent == "subscription":
        if "退" in text or "取消" in text:
            return _require_confirm(sess, "cancel_subscription", "subscription", {"sub_id": 1}, "取消订阅「视频会员」")
        if "提醒" in text or "续费" in text:
            env = subscription.remind_renewal()
        else:
            env = subscription.list_subscriptions()
        return _base(intent, _env_reply(intent, env), ok=env.ok, data=env.data, trace=list(sess.trace))

    if intent == "card":
        if "挂失" in text:
            return _require_confirm(sess, "report_loss", "card", {"card_id": 1}, "挂失卡片「6222 **** 8888」")
        if "限额" in text or "额度" in text:
            amt = extract_amount(text) or 2000.0
            action = "raise_limit" if amt > 5000 else "lower_limit"
            return _require_confirm(sess, action, "card_limit", {"card_id": 1, "new_limit": amt}, f"将卡片限额调整为 ¥{amt:.0f}")
        if "冻结" in text:
            env = card.freeze_card(1)
        elif "解冻" in text or "解锁" in text:
            env = card.unfreeze_card(1)
        else:
            env = card.list_cards()
        return _base(intent, _env_reply("card", env), ok=env.ok, data=env.data, trace=list(sess.trace))

    if intent == "wealth":
        if "测评" in text:
            env = wealth.risk_assessment({"q1": "B", "q2": "B", "q3": "B"})
        elif "持仓" in text:
            env = wealth.list_holdings()
        elif "赎回" in text:
            return _require_confirm(sess, "redeem", "wealth", {"code": "F001", "amount": extract_amount(text) or 1000.0}, f"赎回 ¥{extract_amount(text) or 1000:.0f}")
        elif "申购" in text or "买入" in text:
            return _require_confirm(sess, "purchase", "wealth", {"code": "F001", "amount": extract_amount(text) or 1000.0}, f"申购「稳健货币基金」¥{extract_amount(text) or 1000:.0f}")
        else:
            env = wealth.recommend_products("稳健型")
        return _base(intent, _env_reply(intent, env), ok=env.ok, data=env.data, trace=list(sess.trace))

    if intent == "transfer":
        if "记录" in text or "历史" in text or "转了多少" in text:
            env = transfer.list_transfers()
            return _base(intent, _env_reply(intent, env), ok=env.ok, data=env.data, trace=list(sess.trace))
        return _handle_transfer(sess, text)

    if intent == "profile":
        env = profile.predict_intent()
        return _base(intent, _env_reply(intent, env), ok=env.ok, data=env.data, trace=list(sess.trace))

    return _handle_chat(sess, text)


def _handle_chat(sess: Session, text: str) -> dict:
    """闲聊兜底：优先规则聊天，可选大模型。"""
    # 1. 规则模式基础聊天
    from app.llm import call_llm, get_llm_mode, rule_chat_reply

    rule_reply = rule_chat_reply(text)
    mode = get_llm_mode()

    # 2. 若配置了大模型，尝试调用
    if mode["mode"] == "llm":
        llm_reply = call_llm([
            {"role": "system", "content": "你是小微，微众银行的 AI 助手。用友好简洁的中文回复用户的闲聊或问题，不要编造金融数据。涉及查账/转账/理财/订阅等银行业务时，提示用户可以直接说需求。"},
            {"role": "user", "content": text},
        ])
        if llm_reply:
            return _base("chat", llm_reply, data={"mode": "llm"})

    # 3. 规则兜底
    if rule_reply:
        return _base("chat", rule_reply, data={"mode": "rule"})
    return _base(
        "chat",
        "我是小微，微众银行 AI 助手。你可以直接告诉我需求，比如「我这个月花了多少」「转给老王 200」。",
        data={"mode": "rule"},
    )


def _handle_transfer(sess: Session, text: str) -> dict:
    amt = extract_amount(text)
    recipient = extract_recipient(text)

    if amt is None and ("再" in text or "刚才" in text or "那笔" in text):
        last = sess.context.get("last_transfer")
        if last:
            amt, recipient = last["amount"], last["to"]
        else:
            return _base("transfer", "我还没找到最近一笔转账，请直接告诉我金额和收款人。", ok=False)

    if amt is None:
        return _base("transfer", "请告诉我转账金额，例如：转给老王 200。", ok=False)
    if recipient is None:
        return _base("transfer", "请告诉我要转给谁（姓名或手机号），例如：转给老王 200。", ok=False)

    d = decide("transfer_now", amt, recipient_in_whitelist=(recipient is not None), session_id=sess.sid, token_store=_token_store)
    if not d.allowed:
        audit_log("u001", "transfer_now", recipient, amt, "R4", text, "策略拒绝")
        return _base("transfer", f"操作被拒绝：{d.reason}", ok=False)

    if d.needs_confirm:
        confirm_text = f"将向「{recipient}」转账 ¥{amt:.2f}"
        sess.pending = PendingConfirm("transfer_now", "transfer", {"to": recipient, "amount": amt}, d.level.name, confirm_text, d.risk_warning, d.confirm_token)
        suffix = "（大额或高风险，需二次确认）" if d.risk_warning else "（请回复「确认」或「取消」）"
        sess.trace.append({"step": "策略校验", "result": f"{d.level.name} 需确认"})
        return _base("transfer", confirm_text + suffix, data={
            "needs_confirm": True,
            "level": d.level.name,
            "action": "transfer",
            "to": recipient,
            "amount": amt,
            "risk_warning": d.risk_warning,
        }, trace=list(sess.trace))

    env = transfer.transfer_by_name(recipient, amt)
    sess.context["last_transfer"] = {"to": recipient, "amount": amt}
    audit_log("u001", "transfer_now", recipient, amt, f"R4-{d.level.name}", text, "已执行")
    return _base("transfer", _env_reply("transfer", env), ok=env.ok, data=env.data, trace=list(sess.trace))


def _require_confirm(sess: Session, action: str, tool: str, params: dict, confirm_text: str) -> dict:
    """写操作统一入口：策略校验 → 需确认则挂起确认卡。"""
    d = decide(action, params.get("amount", 0), session_id=sess.sid, token_store=_token_store)
    if not d.allowed:
        audit_log("u001", action, _target_text(params), params.get("amount", 0), "R4", confirm_text, "策略拒绝")
        return _base(action, f"操作被拒绝：{d.reason}", ok=False)
    sess.pending = PendingConfirm(action, tool, params, d.level.name, confirm_text, d.risk_warning, d.confirm_token)
    suffix = "（大额或高风险，需二次确认）" if d.risk_warning else "（请回复「确认」或「取消」）"
    sess.trace.append({"step": "策略校验", "result": f"{action} {d.level.name} 需确认"})
    return _base(action, confirm_text + suffix, data={
        "needs_confirm": True,
        "level": d.level.name,
        "action": action,
        "title": confirm_text,
        "risk_warning": d.risk_warning,
    }, trace=list(sess.trace))


def _env_reply(intent: str, env) -> str:
    if not env.ok:
        return env.error or "操作失败"
    data = env.data or {}
    if intent == "transfer":
        return f"转账成功：已向「{data.get('to')}」转账 ¥{data.get('amount', 0):.2f}，可在 30 秒内撤销。"
    if intent == "subscription" and data.get("subscriptions"):
        return f"你有 {data['count']} 个订阅，每月共扣 ¥{data['monthly_total']}，明细见下方。"
    if intent == "subscription" and data.get("status") == "cancelled":
        return f"已取消订阅「{data['name']}」，每月可省 ¥{data['monthly_fee']}。"
    if intent == "card" and isinstance(data, dict) and data.get("status") == "lost":
        subs = data.get("linked_subscriptions", [])
        if subs:
            names = "、".join(s["name"] for s in subs)
            return f"卡片已挂失。检测到该卡上有 {len(subs)} 笔代扣（{names}），是否一并暂停？回复「暂停」即可。"
        return "卡片已挂失。"
    if intent == "card" and isinstance(data, dict) and data.get("status") in ("frozen", "normal"):
        return f"卡片「{data.get('card')}」已{'冻结' if data['status'] == 'frozen' else '解冻'}。"
    if intent == "card_limit" and data.get("new_limit"):
        return f"卡片限额已{direction_word(data)}为 ¥{data['new_limit']:.0f}。"
    if intent == "card" and isinstance(data, list):
        cards = "、".join(c["card_no"] for c in data)
        return f"你有 {len(data)} 张卡：{cards}"
    if intent == "bill" and data.get("by_category"):
        return f"本月共消费 ¥{data['total']}，分类明细见下方。"
    if intent == "bill" and data.get("anomalies") is not None:
        return f"帮你查到 {data['count']} 笔异常交易，详见下方。"
    if intent == "bill" and data.get("income") is not None:
        return f"收入 ¥{data['income']}，支出 ¥{data['expense']}，结余 ¥{data['net']}。"
    if intent == "bill" and data.get("trend"):
        return f"近 {len(data['trend'])} 个月收支趋势见下方。"
    if intent == "bill" and data.get("transactions"):
        return f"最近 {len(data['transactions'])} 笔交易流水见下方。"
    if intent == "wealth" and data.get("products"):
        return f"为你匹配了 {len(data['products'])} 只产品，明细见下方。"
    if intent == "wealth" and data.get("holdings"):
        return f"你当前持仓 {len(data['holdings'])} 只产品，共 ¥{data['total']}，明细见下方。"
    if intent == "wealth" and data.get("product"):
        return f"已申购「{data['product']}」¥{data['amount']}。{data.get('tip','')}"
    if intent == "wealth" and data.get("status") == "已赎回":
        return f"已赎回 ¥{data['amount']}。"
    if intent == "transfer" and data.get("records"):
        return f"你最近有 {data['count']} 笔转账，共 ¥{data['total']}，明细见下方。"
    return str(data)


def direction_word(data: dict) -> str:
    return data.get("direction", "调整")
