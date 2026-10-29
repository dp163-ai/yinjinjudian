"""输入侧：提示词注入检测。

依据 docs/00_CONSTITUTION.md R6、docs/03_SECURITY_DESIGN.md §4。
"""
from __future__ import annotations

BLOCK_PATTERNS = [
    "忽略之前的指令",
    "忽略以上指令",
    "忽略前面的指令",
    "你现在是",
    "你是银行柜员",
    "跳过确认",
    "直接执行",
    "别问了直接",
    "忘记你的规则",
    "忘记之前的指令",
    "忘掉之前的",
    "之前说的都忘",
    "ignore previous instructions",
    "ignore the above",
    "you are now",
    "bypass",
    "system prompt",
    "你是系统",
]


def detect_injection(text: str) -> tuple[bool, list[str]]:
    """检测输入是否含注入特征，返回 (是否命中, 命中特征列表)。"""
    if not text:
        return False, []
    lowered = text.lower()
    hits = [p for p in BLOCK_PATTERNS if p.lower() in lowered]
    return len(hits) > 0, hits
