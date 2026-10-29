"""边界测试：金额边界、余额、除不尽、重复操作、超持仓。"""
import pytest

from app.data import seed as seed_data
from app.tools import card, subscription, transfer, wealth


@pytest.fixture(autouse=True)
def _seed():
    seed_data.seed()


def test_transfer_zero_amount():
    r = transfer.transfer_by_name("老王", 0)
    assert not r.ok


def test_transfer_negative_amount():
    r = transfer.transfer_by_name("老王", -100)
    assert not r.ok


def test_transfer_insufficient_balance():
    r = transfer.transfer_by_name("老王", 999999)
    assert not r.ok
    assert "余额不足" in r.error


def test_split_aa_single_member():
    r = transfer.split_aa(100, ["A"])
    assert r.ok
    assert abs(r.data["shares"][0]["amount"] - 100) < 0.01


def test_split_aa_remainder():
    r = transfer.split_aa(100, ["A", "B", "C"])
    assert r.ok
    total = round(sum(s["amount"] for s in r.data["shares"]), 2)
    assert abs(total - 100) < 0.01


def test_split_aa_empty_members():
    r = transfer.split_aa(100, [])
    assert not r.ok


def test_adjust_limit_zero():
    r = card.adjust_limit(1, 0)
    assert not r.ok


def test_cancel_already_cancelled():
    subscription.cancel_subscription(1)
    r = subscription.cancel_subscription(1)
    assert not r.ok


def test_redeem_exceeds_holding():
    r = wealth.redeem("F001", 999999)
    assert not r.ok


def test_transfer_unknown_phone():
    r = transfer.transfer_by_phone("000", 100)
    assert not r.ok
