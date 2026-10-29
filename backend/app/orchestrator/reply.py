"""回复生成：模板话术（离线）/ 大模型叙述（在线）。

所有数字只来自工具返回值，模板只做叙述翻译，符合幻觉防护要求。
"""
from __future__ import annotations

REPLY_TEMPLATES: dict[str, str] = {
    "transfer": "我理解你想转账。请补充收款人（姓名/手机号/备注）和金额，例如：转给老王 200。",
    "bill": "我来帮你查账单。请告诉我想看的时间段（本月 / 上月 / 去年）。",
    "wealth": "理财相关操作请先完成风险测评，或告诉我你想申购 / 赎回 / 对比的产品。",
    "card": "卡片管理请告诉我想查卡、调限额、冻结还是挂失。",
    "subscription": "订阅管理请告诉我想查看订阅、设置续费提醒还是取消订阅。",
    "profile": "我在学习你的使用习惯，稍后会为你推荐常用入口和资料。",
    "chat": "我是《引金据典》银行智能体，可以帮你查账、理财、转账、管卡、退订阅。",
}


def generate_reply(intent_name: str) -> str:
    """按意图返回兜底话术。"""
    return REPLY_TEMPLATES.get(intent_name, REPLY_TEMPLATES["chat"])
