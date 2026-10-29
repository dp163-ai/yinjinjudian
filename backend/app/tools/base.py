"""能力层工具基类与快捷函数。"""
from __future__ import annotations

from app.envelope import Envelope


def ok(data=None, source: str = "system") -> Envelope:
    return Envelope.success(data, source)


def fail(error: str, source: str = "system", data=None) -> Envelope:
    return Envelope.fail(error, source, data)
