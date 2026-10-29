"""工具层真实逻辑单元测试（每个测试前重置演示数据）。"""
import pytest

from app.data import seed as seed_data
from app.tools import bill, card, subscription, transfer, wealth


@pytest.fixture(autouse=True)
def _seed():
    seed_data.seed()


def test_category_stats():
    r = bill.category_stats()
    assert r.ok
    assert r.data["total"] > 0
    assert any(c["category"] == "餐饮" for c in r.data["by_category"])


def test_detect_anomalies():
    r = bill.detect_anomalies()
    assert r.ok
    assert r.data["count"] >= 1


def test_report():
    r = bill.report()
    assert r.ok
    assert r.data["income"] > 0
    assert r.data["expense"] > 0


def test_transfer_by_name_ok():
    r = transfer.transfer_by_name("老王", 100)
    assert r.ok
    assert r.data["amount"] == 100


def test_transfer_unknown_recipient():
    r = transfer.transfer_by_name("陌生人", 100)
    assert not r.ok


def test_transfer_insufficient():
    r = transfer.transfer_by_name("老王", 999999)
    assert not r.ok
    assert "余额不足" in r.error


def test_split_aa():
    r = transfer.split_aa(386, ["A", "B", "C"])
    assert r.ok
    total = round(sum(s["amount"] for s in r.data["shares"]), 2)
    assert abs(total - 386) < 0.01


def test_list_subscriptions():
    r = subscription.list_subscriptions()
    assert r.ok
    assert r.data["count"] == 3


def test_cancel_subscription():
    r = subscription.cancel_subscription(1)
    assert r.ok
    assert r.data["status"] == "cancelled"


def test_report_loss_links_subs():
    r = card.report_loss(1)
    assert r.ok
    assert r.data["status"] == "lost"
    assert len(r.data["linked_subscriptions"]) >= 1


def test_adjust_limit():
    r = card.adjust_limit(1, 2000.0)
    assert r.ok
    assert r.data["new_limit"] == 2000.0


def test_risk_assessment():
    r = wealth.risk_assessment({"q1": "B", "q2": "B", "q3": "B"})
    assert r.ok
    assert r.data["level"] == "平衡型"


def test_recommend_products():
    r = wealth.recommend_products("稳健型")
    assert r.ok
    assert any(p["code"] == "F001" for p in r.data["products"])
