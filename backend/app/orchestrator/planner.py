"""任务规划：拆子任务、定依赖、标风险级。

依据 docs/00_CONSTITUTION.md R3。当前为骨架，PROMPT 5 填肉。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Subtask:
    name: str
    action: str
    params: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


def plan(intent_name: str, params: dict) -> list[Subtask]:
    """把意图拆成子任务。单意图返回单任务；多意图/联动在 PROMPT 5 扩展。"""
    return [Subtask(name=intent_name, action=intent_name, params=params)]
