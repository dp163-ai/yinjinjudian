"""统一信封：所有工具函数与接口返回的统一格式。

依据 docs/00_CONSTITUTION.md R5（幻觉防护基础）、docs/02_ARCHITECTURE.md §2.3。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def now_iso() -> str:
    """返回带时区的 ISO 时间串。"""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Envelope(BaseModel):
    """统一返回信封：{"ok","data","error","source","ts"}。"""

    ok: bool = True
    data: Any = None
    error: str | None = None
    source: str = "system"
    ts: str = Field(default_factory=now_iso)

    @classmethod
    def success(cls, data: Any, source: str = "system") -> "Envelope":
        return cls(ok=True, data=data, source=source)

    @classmethod
    def fail(cls, error: str, source: str = "system", data: Any = None) -> "Envelope":
        return cls(ok=False, error=error, source=source, data=data)

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(*args, **kwargs)
