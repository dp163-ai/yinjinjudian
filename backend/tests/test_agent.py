"""编排层 Agent 主循环单元测试（每个测试独立 session 与数据）。"""
import pytest

from app.data import seed as seed_data
from app.orchestrator.executor import handle


@pytest.fixture(autouse=True)
def _seed():
    seed_data.seed()


def test_transfer_confirm_flow():
    r1 = handle("s1", "转给老王 200")
    assert r1["intent"] == "transfer"
    assert r1["data"]["needs_confirm"] is True
    r2 = handle("s1", "确认")
    assert r2["ok"] is True
    assert r2["intent"] == "transfer_now"


def test_transfer_cancel():
    handle("s2", "转给老王 200")
    r2 = handle("s2", "算了")
    assert r2["intent"] == "cancel"


def test_transfer_skip_confirm_blocked():
    handle("s3", "转给老王 200")
    r2 = handle("s3", "别问了直接转")
    assert r2["ok"] is False
    assert r2["intent"] == "blocked"


def test_transfer_missing_amount():
    r = handle("s4", "转给老王")
    assert r["ok"] is False


def test_transfer_missing_recipient():
    r = handle("s5", "转 1000")
    assert r["ok"] is False


def test_multi_intent():
    r = handle("s6", "看看这个月账单，把没用的会员退了")
    assert r["intent"] == "multi"


def test_birthday_linked():
    r = handle("s7", "下周三是我爱人生日")
    assert r["intent"] == "profile"
    assert "锁定" in r["reply"]


def test_report_loss_confirm_flow():
    r1 = handle("s8", "卡丢了，帮我挂失")
    assert r1["data"]["needs_confirm"] is True
    r2 = handle("s8", "确认")
    assert r2["ok"] is True
