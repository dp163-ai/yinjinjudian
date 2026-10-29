"""意图识别（离线规则版 + 大模型可切换）。

在线模式由大模型做意图识别；离线模式用关键词规则，保证无 Key 可演示。
"""
from __future__ import annotations

from dataclasses import dataclass

INTENT_KEYWORDS: dict[str, list[str]] = {
    "transfer": ["转", "转账", "打款", "汇款", "AA", "aa", "分摊", "收款", "转给"],
    "bill": ["账单", "花了", "花哪", "流水", "消费", "异常", "报告", "明细", "支出", "趋势", "月报", "收支", "结余", "超支"],
    "wealth": ["理财", "基金", "申购", "赎回", "风险测评", "收益", "投资", "持仓", "资产配置"],
    "card": ["卡", "挂失", "限额", "额度", "冻结", "解冻", "尾号", "账单日"],
    "subscription": ["订阅", "会员", "扣费", "续费", "退订", "取消", "代扣", "续费日"],
    "profile": ["推荐", "画像", "习惯", "猜猜", "预测"],
}


@dataclass
class Intent:
    name: str
    confidence: float


def recognize(text: str) -> Intent:
    """返回识别出的意图。命中多个时取第一个关键词命中的意图。"""
    for name, kws in INTENT_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return Intent(name, 0.9)
    return Intent("chat", 0.5)
