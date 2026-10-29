"""《引金据典》后端入口。

启动：cd backend && uvicorn app.main:app --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data import store
from app.i18n import ACTION_NAME, CARD_STATUS, CARD_TYPE, RISK_LEVEL, SUB_STATUS
from app import llm, permissions
from app.orchestrator.executor import handle
from app.policy.audit import list_logs
from app.tools import bill as bill_tool, card as card_tool, profile as profile_tool, subscription as sub_tool
from app.tools import transfer as transfer_tool, wealth as wealth_tool

app = FastAPI(title="引金据典", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "demo"


class LlmConfigRequest(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = "deepseek-chat"


@app.get("/health")
def health() -> dict:
    return {"ok": True, "app": "引金据典", "version": "1.0"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    """对话入口：完整编排（注入检测 → 意图 → 规划 → 策略 → 确认 → 执行 → 审计）。"""
    return handle(req.session_id, req.message)


@app.get("/overview")
def overview() -> dict:
    """资金总览看板：账户 + 卡片 + 订阅 + 账单 + 趋势 + 持仓 + 转账（字段已中文化）。"""
    accounts = store.query("SELECT * FROM accounts WHERE id=1")
    if not accounts:
        return {"account": None, "cards": [], "subscriptions": None, "bill": None, "trend": None, "holdings": None, "transfers": None}
    cards = card_tool.list_cards().data or []
    for c in cards:
        c["status_cn"] = CARD_STATUS.get(c.get("status"), c.get("status", ""))
        c["type_cn"] = CARD_TYPE.get(c.get("card_type"), c.get("card_type", ""))
    subs = sub_tool.list_subscriptions().data or {}
    for s in subs.get("subscriptions", []):
        s["status_cn"] = SUB_STATUS.get(s.get("status"), s.get("status", ""))
    return {
        "account": accounts[0],
        "cards": cards,
        "subscriptions": subs,
        "bill": bill_tool.category_stats().data,
        "trend": bill_tool.monthly_trend().data,
        "holdings": wealth_tool.list_holdings().data,
        "transfers": transfer_tool.list_transfers().data,
        "recent": bill_tool.recent_transactions(8).data,
    }


@app.get("/audit")
def audit() -> dict:
    """安全中心：审计日志流（动作中文化，目标转可读文字）。"""
    logs = list_logs(50)
    for l in logs:
        l["action_cn"] = ACTION_NAME.get(l.get("action"), l.get("action", ""))
        # 兜底：历史脏数据若是字典字符串，转成可读文字
        t = l.get("target", "")
        if t and t.startswith("{"):
            l["target"] = _target_readable(t, l.get("action", ""), l.get("amount", 0))
    return {"logs": logs}


def _target_readable(raw: str, action: str, amount: float) -> str:
    """把历史遗留的字典字符串 target 转成可读文字。"""
    import re
    m = re.search(r"'to'\s*:\s*'([^']+)'", raw)
    if m:
        return f"转账给 {m.group(1)}"
    if "card_id" in raw:
        return "卡片"
    if "sub_id" in raw:
        return "订阅"
    if "code" in raw:
        return "理财产品"
    return "—"


@app.get("/profile")
def profile_view() -> dict:
    """习惯画像与推荐。"""
    return {"profile": profile_tool.predict_intent().data}


@app.get("/profile/stats")
def profile_stats() -> dict:
    """使用行为统计：各功能使用次数与占比。"""
    rows = store.query(
        "SELECT signal, COUNT(*) AS cnt FROM signals WHERE account_id=1 GROUP BY signal ORDER BY cnt DESC",
    )
    total = sum(r["cnt"] for r in rows) or 1
    for r in rows:
        r["pct"] = round(r["cnt"] / total * 100, 1)
    return {"stats": rows, "total": total}


@app.get("/llm/mode")
def llm_mode() -> dict:
    """查询当前 LLM 模式。"""
    return llm.get_llm_mode()


@app.post("/llm/config")
def llm_config(req: LlmConfigRequest) -> dict:
    """配置 API Key 与模型。api_key 为空则清除配置，回到规则模式。"""
    llm.set_config("api_key", req.api_key.strip())
    llm.set_config("base_url", req.base_url.strip())
    llm.set_config("model", req.model.strip() or "deepseek-chat")
    return llm.get_llm_mode()


@app.post("/subscription/cancel")
def sub_cancel(req: dict) -> dict:
    """取消订阅。"""
    sub_id = int(req.get("sub_id", 1))
    env = sub_tool.cancel_subscription(sub_id)
    return env.dict()


@app.post("/subscription/renew")
def sub_renew(req: dict) -> dict:
    """续订。"""
    sub_id = int(req.get("sub_id", 1))
    env = sub_tool.renew_subscription(sub_id)
    return env.dict()


@app.get("/subscription/all")
def sub_all() -> dict:
    """全部订阅（含已取消），供详情展示。"""
    env = sub_tool.all_subscriptions()
    return env.dict()


class PermissionRequest(BaseModel):
    key: str
    level: str


@app.get("/permissions")
def permissions_list() -> dict:
    """返回所有行为及其权限等级。"""
    return {"actions": permissions.list_permissions(), "levels": permissions.LEVELS}


@app.post("/permissions")
def permissions_set(req: PermissionRequest) -> dict:
    """设置某行为的权限等级。"""
    ok = permissions.set_permission(req.key, req.level)
    return {"ok": ok, "actions": permissions.list_permissions()}
