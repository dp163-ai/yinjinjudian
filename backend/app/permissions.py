"""权限配置：每个具体行为可独立调节权限等级（L0-L3）。

行为清单与默认等级，用户可在线调整。
"""
from __future__ import annotations

import json

from app.llm import get_config, set_config

# 行为 -> 默认等级
DEFAULT_ACTIONS: list[dict] = [
    {"key": "view_bill_category", "name": "查账单分类", "level": "L0"},
    {"key": "view_recommend", "name": "看推荐", "level": "L0"},
    {"key": "view_transactions", "name": "查完整流水", "level": "L1"},
    {"key": "view_card_info", "name": "查卡号尾号", "level": "L1"},
    {"key": "view_holdings", "name": "查理财持仓", "level": "L1"},
    {"key": "cancel_subscription", "name": "取消订阅", "level": "L2"},
    {"key": "lower_limit", "name": "调低额度", "level": "L2"},
    {"key": "freeze_card", "name": "冻结卡片", "level": "L2"},
    {"key": "schedule_transfer", "name": "定时转账", "level": "L2"},
    {"key": "transfer_now", "name": "即时转账", "level": "L3"},
    {"key": "purchase", "name": "理财申购", "level": "L3"},
    {"key": "redeem", "name": "理财赎回", "level": "L3"},
    {"key": "report_loss", "name": "卡片挂失", "level": "L3"},
    {"key": "raise_limit", "name": "调高额度", "level": "L3"},
    {"key": "unfreeze_card", "name": "解锁卡片", "level": "L3"},
]

LEVELS = ["L0", "L1", "L2", "L3"]


def _load() -> dict[str, str]:
    raw = get_config("permission_levels", "")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {a["key"]: a["level"] for a in DEFAULT_ACTIONS}


def list_permissions() -> list[dict]:
    """返回所有行为及其当前等级。"""
    levels = _load()
    return [
        {"key": a["key"], "name": a["name"], "level": levels.get(a["key"], a["level"])}
        for a in DEFAULT_ACTIONS
    ]


def set_permission(key: str, level: str) -> bool:
    """设置某行为的权限等级。"""
    if level not in LEVELS:
        return False
    levels = _load()
    levels[key] = level
    set_config("permission_levels", json.dumps(levels, ensure_ascii=False))
    return True


def get_level(key: str) -> str:
    """查询某行为的等级。"""
    levels = _load()
    return levels.get(key, "L2")
