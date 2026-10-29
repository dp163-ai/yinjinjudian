"""策略层：权限分级 L0-L3、风控校验、确认凭证。

依据 docs/00_CONSTITUTION.md R4、docs/03_SECURITY_DESIGN.md §2、docs/01_PRD.md §3。
设计原则：模型只产出意图与参数，写操作必经本层校验与确认，模型永不直接执行交易。
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from enum import IntEnum


class PermLevel(IntEnum):
    """权限级别。"""

    L0 = 0  # 只读·非敏感
    L1 = 1  # 只读·敏感
    L2 = 2  # 写·低风险·可逆（需单次确认）
    L3 = 3  # 写·高风险（需二次确认 + 风险提示）


# 金额阈值（单位：元）
CONFIRM_THRESHOLD = 500.0  # 超过则触发风险提示
L3_THRESHOLD = 5000.0      # 超过则升级 L3

# 恒为 L3 的高风险写操作（与金额无关）
L3_ACTIONS = {"purchase", "redeem", "report_loss", "raise_limit", "unfreeze_card"}

# 恒为 L2 的低风险可逆写操作
L2_ACTIONS = {"cancel_subscription", "schedule_transfer", "lower_limit", "freeze_card"}

# 级别由金额决定的操作（转账）
AMOUNT_SCALED_ACTIONS = {"transfer_now"}


@dataclass
class PolicyDecision:
    """策略判定结果。"""

    allowed: bool
    level: PermLevel
    reason: str
    needs_confirm: bool = False
    risk_warning: bool = False
    confirm_token: str | None = None


class ConfirmTokenStore:
    """一次性确认凭证：30 秒失效、绑定会话、不可复用。"""

    TTL = 30.0

    def __init__(self) -> None:
        self._tokens: dict[str, tuple[str, float]] = {}

    def issue(self, session_id: str) -> str:
        token = secrets.token_urlsafe(16)
        self._tokens[token] = (session_id, time.time() + self.TTL)
        return token

    def verify(self, token: str, session_id: str) -> bool:
        entry = self._tokens.get(token)
        if entry is None:
            return False
        sid, expires = entry
        if time.time() > expires:
            self._tokens.pop(token, None)
            return False
        if sid != session_id:
            return False
        self._tokens.pop(token, None)  # 一次性，用完即废
        return True


def classify_action(action: str, amount: float = 0.0) -> PermLevel:
    """按动作类型与金额判定权限级别。"""
    if action in L3_ACTIONS:
        return PermLevel.L3
    if action in L2_ACTIONS:
        return PermLevel.L2
    if action in AMOUNT_SCALED_ACTIONS:
        return PermLevel.L3 if amount > L3_THRESHOLD else PermLevel.L2
    return PermLevel.L0


def decide(
    action: str,
    amount: float = 0.0,
    *,
    card_status: str = "normal",
    recipient_in_whitelist: bool = True,
    is_first_time: bool = False,
    session_id: str = "demo",
    token_store: ConfirmTokenStore | None = None,
) -> PolicyDecision:
    """策略校验主入口。

    判定优先级：金额 ∧ 场景 ∧ 收款方白名单 ∧ 是否首次 ∧ 卡片状态 ∧ 设备/时段。
    """
    level = classify_action(action, amount)

    # 卡片状态：挂失/冻结卡上的资金类写操作直接拒绝
    if action.startswith(("transfer", "purchase", "redeem", "raise_limit")) and card_status != "normal":
        return PolicyDecision(False, level, f"卡片状态为 {card_status}，操作被拒绝")

    # 写操作（L2 及以上）均需确认
    needs_confirm = level >= PermLevel.L2

    # 风险提示：L3 或金额超阈值
    risk_warning = level >= PermLevel.L3 or amount > CONFIRM_THRESHOLD

    # 首次或非白名单收款方 -> 强制确认 + 风险提示
    if is_first_time or not recipient_in_whitelist:
        needs_confirm = True
        risk_warning = True

    confirm_token = None
    if needs_confirm and token_store is not None:
        confirm_token = token_store.issue(session_id)

    return PolicyDecision(
        True, level, "通过", needs_confirm=needs_confirm, risk_warning=risk_warning, confirm_token=confirm_token
    )
