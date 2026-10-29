"""输出侧：幻觉防护——数字校验与违规表述拦截。

依据 docs/00_CONSTITUTION.md R5、docs/03_SECURITY_DESIGN.md §3。
"""
from __future__ import annotations

# 违规承诺类表述，出现在回复中即拦截
FORBIDDEN_WORDS = ["保本", "稳赚", "必涨", "稳赚不赔", "无风险", "guaranteed", "risk-free"]


def check_forbidden(reply: str) -> list[str]:
    """返回命中的违规表述列表。"""
    if not reply:
        return []
    return [w for w in FORBIDDEN_WORDS if w.lower() in reply.lower()]


def validate_number_in(reply: str, allowed: list[float]) -> list[str]:
    """校验回复中的金额/数字是否落在工具返回的允许集合内。

    简化实现：提取回复中的浮点数，逐个检查是否在 allowed 中（容差 0.01）。
    返回"疑似编造"的数字字符串列表。
    """
    import re

    suspect: list[str] = []
    for m in re.finditer(r"\d+(?:\.\d+)?", reply):
        val = float(m.group())
        if allowed and not any(abs(val - a) < 0.01 for a in allowed):
            suspect.append(m.group())
    return suspect
