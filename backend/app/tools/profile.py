"""用户习惯画像工具：行为信号采集、意图预判、推荐生成。"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok

ACCOUNT_ID = 1


def record_signal(signal: str) -> Envelope:
    """采集行为信号（最小必要集，仅行为不含内容）。"""
    store.execute("INSERT INTO signals(account_id,signal,ts) VALUES(?,?,?)", (ACCOUNT_ID, signal, store.now()))
    return ok({"recorded": signal}, "profile")


def predict_intent() -> Envelope:
    """预判下一步意图：输出推荐入口/资料卡片。"""
    rows = store.query(
        "SELECT signal, COUNT(*) AS cnt FROM signals WHERE account_id=? GROUP BY signal ORDER BY cnt DESC",
        (ACCOUNT_ID,),
    )
    recs = []
    for r in rows:
        if r["signal"] == "查账单":
            recs.append({"type": "入口", "text": "你常查账单，已把「月度报告」放到首页", "why": f"近 {r['cnt']} 次查询账单"})
        if r["signal"] == "看理财":
            recs.append({"type": "资料", "text": "3 篇关于货基风险的文章", "why": "你近期关注理财"})
    if not recs:
        recs.append({"type": "提示", "text": "继续使用后，我会学习你的习惯并推荐常用入口", "why": ""})
    return ok({"recommendations": recs, "disclaimer": "本推荐基于你的操作习惯生成，不构成投资建议"}, "profile")
