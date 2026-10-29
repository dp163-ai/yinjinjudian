"""理财操作工具：风险评估、产品推荐对比、一键申购/赎回。

依据 docs/01_PRD.md §3、docs/00_CONSTITUTION.md R4/R11。
"""
from __future__ import annotations

from app.data import store
from app.envelope import Envelope
from app.tools.base import ok, fail

ACCOUNT_ID = 1

# 测评得分 -> 风险等级；风险等级 -> 产品风险档
RISK_BY_SCORE = {3: "稳健型", 4: "稳健型", 5: "平衡型", 6: "平衡型", 7: "平衡型", 8: "进取型", 9: "进取型"}
RISK_TO_PRODUCT = {"稳健型": ["低", "中低"], "平衡型": ["中低", "中高"], "进取型": ["中高", "高"]}


def risk_assessment(answers: dict) -> Envelope:
    """风险评估：answers 形如 {"q1":"A","q2":"B","q3":"C"}，A=1/B=2/C=3。"""
    score = 0
    for v in answers.values():
        score += {"A": 1, "B": 2, "C": 3}.get(str(v).upper(), 2)
    level = RISK_BY_SCORE.get(score, "平衡型")
    return ok({"score": score, "level": level}, "wealth")


def recommend_products(risk_level: str) -> Envelope:
    """按风险等级推荐匹配产品。"""
    levels = RISK_TO_PRODUCT.get(risk_level, ["低", "中低"])
    marks = ",".join("?" * len(levels))
    rows = store.query(
        f"SELECT * FROM wealth_products WHERE risk_level IN ({marks}) ORDER BY yoy_return", tuple(levels)
    )
    return ok({"risk_level": risk_level, "products": rows, "disclaimer": "本推荐基于风险等级匹配，不构成投资建议"}, "wealth")


def compare_products(product_codes: list[str]) -> Envelope:
    """产品对比。"""
    marks = ",".join("?" * len(product_codes))
    rows = store.query(f"SELECT * FROM wealth_products WHERE code IN ({marks})", tuple(product_codes))
    if not rows:
        return fail("未找到对应产品", "wealth")
    return ok(rows, "wealth")


def purchase(product_code: str, amount: float) -> Envelope:
    """申购（L3，需确认后调用）。"""
    if amount <= 0:
        return fail("金额必须大于 0", "wealth")
    prod = store.query("SELECT * FROM wealth_products WHERE code=?", (product_code,))
    if not prod:
        return fail(f"产品 {product_code} 不存在", "wealth")
    acc = store.query("SELECT * FROM accounts WHERE id=?", (ACCOUNT_ID,))[0]
    if acc["balance"] < amount:
        return fail(f"余额不足，当前 ¥{acc['balance']:.2f}", "wealth")
    store.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, ACCOUNT_ID))
    store.execute(
        "INSERT INTO holdings(account_id,product_code,amount,ts) VALUES(?,?,?,?)",
        (ACCOUNT_ID, product_code, amount, store.now()),
    )
    return ok({"product": prod[0]["name"], "amount": amount, "risk": prod[0]["risk_level"], "tip": "历史收益不代表未来"}, "wealth")


def redeem(product_code: str, amount: float) -> Envelope:
    """赎回（L3，需确认后调用）。"""
    if amount <= 0:
        return fail("金额必须大于 0", "wealth")
    held = store.query(
        "SELECT * FROM holdings WHERE account_id=? AND product_code=? AND amount>=?",
        (ACCOUNT_ID, product_code, amount),
    )
    if not held:
        return fail("持仓不足或未持有该产品", "wealth")
    store.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (amount, ACCOUNT_ID))
    store.execute(
        "UPDATE holdings SET amount=amount-? WHERE id=?", (amount, held[0]["id"])
    )
    return ok({"product": product_code, "amount": amount, "status": "已赎回"}, "wealth")


def list_holdings() -> Envelope:
    """查询持仓：联产品名/风险/年化，计算估算收益。"""
    rows = store.query(
        "SELECT h.*, p.name, p.risk_level, p.yoy_return FROM holdings h "
        "JOIN wealth_products p ON h.product_code = p.code WHERE h.account_id=?",
        (ACCOUNT_ID,),
    )
    total = 0.0
    for r in rows:
        est = round(r["amount"] * r["yoy_return"] / 100, 2)
        r["est_annual_return"] = est
        total += r["amount"]
    return ok({"total": round(total, 2), "holdings": rows, "disclaimer": "收益为按年化估算，历史不代表未来"}, "wealth")


def all_products() -> Envelope:
    """全部理财产品（按风险排序）。"""
    rows = store.query("SELECT * FROM wealth_products ORDER BY yoy_return")
    return ok({"products": rows}, "wealth")
