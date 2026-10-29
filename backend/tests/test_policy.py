"""权限分级与确认凭证单元测试。"""
from app.policy.engine import ConfirmTokenStore, PermLevel, decide


def test_transfer_small_l2_single_confirm():
    d = decide("transfer_now", 100)
    assert d.allowed
    assert d.level == PermLevel.L2
    assert d.needs_confirm
    assert not d.risk_warning


def test_transfer_medium_risk_warning():
    d = decide("transfer_now", 2000)
    assert d.risk_warning is True


def test_transfer_huge_l3():
    d = decide("transfer_now", 6000)
    assert d.level == PermLevel.L3


def test_report_loss_always_l3():
    d = decide("report_loss")
    assert d.level == PermLevel.L3


def test_card_lost_blocks_transfer():
    d = decide("transfer_now", 100, card_status="lost")
    assert d.allowed is False


def test_token_one_time():
    ts = ConfirmTokenStore()
    tok = ts.issue("s1")
    assert ts.verify(tok, "s1") is True
    assert ts.verify(tok, "s1") is False


def test_token_wrong_session():
    ts = ConfirmTokenStore()
    tok = ts.issue("s1")
    assert ts.verify(tok, "s2") is False
