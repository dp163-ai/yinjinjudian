"""中文字段映射：把内部英文枚举/状态转成用户可读中文。

前端展示专用，避免英文裸字段直接上屏。
"""
from __future__ import annotations

CARD_STATUS = {
    "normal": "正常",
    "frozen": "已冻结",
    "lost": "已挂失",
}

CARD_TYPE = {
    "消费卡": "消费卡",
    "储蓄卡": "储蓄卡",
}

SUB_STATUS = {
    "active": "生效中",
    "cancelled": "已取消",
}

RISK_LEVEL = {
    "低": "低风险",
    "中低": "中低风险",
    "中高": "中高风险",
    "高": "高风险",
}

INTENT_NAME = {
    "bill": "账单分析",
    "wealth": "理财操作",
    "transfer": "智能转账",
    "card": "卡片管理",
    "subscription": "订阅管理",
    "profile": "习惯画像",
    "chat": "闲聊",
    "blocked": "已拦截",
    "cancel": "已取消",
    "multi": "多意图",
    "transfer_now": "转账",
    "report_loss": "挂失",
    "cancel_subscription": "取消订阅",
    "purchase": "申购",
    "redeem": "赎回",
}

ACTION_NAME = {
    "transfer_now": "转账",
    "report_loss": "挂失卡片",
    "cancel_subscription": "取消订阅",
    "purchase": "理财申购",
    "redeem": "理财赎回",
    "raise_limit": "调高额度",
    "lower_limit": "调低额度",
    "freeze_card": "冻结卡片",
    "unfreeze_card": "解锁卡片",
    "schedule_transfer": "定时转账",
    "injection": "拦截注入攻击",
    "pause_subscriptions": "暂停代扣",
}
