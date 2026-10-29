"""LLM 配置与调用：支持 API Key 配置 + 规则模式降级。

- 配置了 API Key → 走大模型（OpenAI 兼容接口）
- 未配置 → 规则模式（关键词 + 模板），但仍能回复基础聊天
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

CONFIG_DB = Path(__file__).resolve().parent.parent / "data" / "config.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _conn() -> sqlite3.Connection:
    CONFIG_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CONFIG_DB)
    conn.execute(_SCHEMA)
    return conn


def get_config(key: str, default: str = "") -> str:
    """读取配置项。"""
    conn = _conn()
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_config(key: str, value: str) -> None:
    """写入配置项。"""
    conn = _conn()
    conn.execute(
        "INSERT INTO config(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_llm_mode() -> dict:
    """返回当前 LLM 模式与配置状态。"""
    key = get_config("api_key", "") or os.environ.get("LLM_API_KEY", "")
    base_url = get_config("base_url", "") or os.environ.get("LLM_BASE_URL", "")
    model = get_config("model", "") or os.environ.get("LLM_MODEL", "deepseek-chat")
    has_key = bool(key.strip())
    return {
        "mode": "llm" if has_key else "rule",
        "has_api_key": has_key,
        "base_url": base_url,
        "model": model,
        # 不返回 key 明文
    }


def call_llm(messages: list[dict]) -> str | None:
    """调用大模型。未配置或失败返回 None（降级规则模式）。"""
    key = get_config("api_key", "") or os.environ.get("LLM_API_KEY", "")
    base_url = (get_config("base_url", "") or os.environ.get("LLM_BASE_URL", "")).rstrip("/")
    model = get_config("model", "") or os.environ.get("LLM_MODEL", "deepseek-chat")
    if not key.strip():
        return None
    if not base_url:
        base_url = "https://api.deepseek.com/v1"
    try:
        import urllib.request
        import json

        payload = json.dumps({"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 500}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


# 基础聊天兜底（规则模式也能回复）
CHAT_KEYWORDS: dict[str, str] = {
    "你好": "你好呀，我是小微～ 微众银行的 AI 助手，可以帮你查账、理财、转账、管卡、退订阅。",
    "谢谢": "不客气，能帮到你我很开心～",
    "你是谁": "我是小微，微众银行 AI 助手。用自然语言就能让我帮你处理银行业务，每一步都有据可依。",
    "你能做什么": "我可以帮你：查账单、看收支趋势、理财申购赎回、转账、管理卡片、退订阅。你可以直接说，比如「我这个月花了多少」。",
    "再见": "再见～ 有需要随时叫我。",
    "早上好": "早上好呀！今天有什么需要我帮忙的吗？",
    "晚上好": "晚上好～ 需要我帮你看看今天的账单吗？",
}


def rule_chat_reply(text: str) -> str | None:
    """规则模式的基础聊天回复，未命中返回 None。"""
    for kw, reply in CHAT_KEYWORDS.items():
        if kw in text:
            return reply
    return None
