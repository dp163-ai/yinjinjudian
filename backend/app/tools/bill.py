"""账单分析工具：分类统计、异常识别、月度/年度报告。"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok

ACCOUNT_ID = 1


def category_stats(period: str = "month") -> Envelope:
    """消费分类统计（排除收入）。"""
    rows = store.query(
        "SELECT category, ROUND(SUM(amount),2) AS total, COUNT(*) AS cnt "
        "FROM transactions WHERE account_id=? AND category != '收入' GROUP BY category ORDER BY total DESC",
        (ACCOUNT_ID,),
    )
    total = round(sum(r["total"] for r in rows), 2)
    return ok({"period": period, "total": total, "by_category": rows}, "bill")


def detect_anomalies(period: str = "month") -> Envelope:
    """异常交易识别：凌晨大额 / 备注含异常。"""
    rows = store.query(
        "SELECT * FROM transactions WHERE account_id=? AND category != '收入'", (ACCOUNT_ID,)
    )
    anomalies = []
    for r in rows:
        hour = int(r["ts"][11:13]) if len(r["ts"]) >= 13 else 0
        is_late_large = r["amount"] > 1000 and 0 <= hour < 6
        is_flagged = "异常" in (r["remark"] or "")
        if is_late_large or is_flagged:
            r["reason"] = "凌晨大额交易" if is_late_large else "备注标记异常"
            anomalies.append(r)
    return ok({"count": len(anomalies), "anomalies": anomalies}, "bill")


def report(period: str = "year") -> Envelope:
    """月度/年度账单报告：收支汇总。"""
    income_rows = store.query(
        "SELECT ROUND(SUM(amount),2) AS total FROM transactions WHERE account_id=? AND category='收入'",
        (ACCOUNT_ID,),
    )
    expense_rows = store.query(
        "SELECT ROUND(SUM(amount),2) AS total FROM transactions WHERE account_id=? AND category!='收入'",
        (ACCOUNT_ID,),
    )
    income = income_rows[0]["total"] or 0 if income_rows else 0
    expense = expense_rows[0]["total"] or 0 if expense_rows else 0
    cats = category_stats().data
    return ok(
        {"period": period, "income": income, "expense": expense, "net": round(income - expense, 2), "by_category": cats["by_category"]},
        "bill",
    )


def monthly_trend() -> Envelope:
    """近 3 月收支趋势：按月聚合收入/支出/结余。"""
    rows = store.query(
        "SELECT substr(ts,1,7) AS month, category, ROUND(SUM(amount),2) AS total "
        "FROM transactions WHERE account_id=? GROUP BY month, category ORDER BY month",
        (ACCOUNT_ID,),
    )
    months: dict[str, dict] = {}
    for r in rows:
        m = months.setdefault(r["month"], {"month": r["month"], "income": 0.0, "expense": 0.0})
        if r["category"] == "收入":
            m["income"] = round(m["income"] + r["total"], 2)
        else:
            m["expense"] = round(m["expense"] + r["total"], 2)
    trend = []
    for m in sorted(months.keys()):
        d = months[m]
        d["net"] = round(d["income"] - d["expense"], 2)
        trend.append(d)
    return ok({"trend": trend}, "bill")


def recent_transactions(limit: int = 10) -> Envelope:
    """最近交易流水。"""
    rows = store.query(
        "SELECT * FROM transactions WHERE account_id=? ORDER BY ts DESC LIMIT ?",
        (ACCOUNT_ID, limit),
    )
    return ok({"transactions": rows}, "bill")
