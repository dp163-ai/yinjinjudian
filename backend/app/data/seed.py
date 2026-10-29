"""演示数据：构造"张同学"账户，覆盖五场景 + 丰富可查看数据。

依据 docs/01_PRD.md §2 画像 A。所有主键显式指定，保证重复 seed 幂等。
"""
from __future__ import annotations

from app.data import store


def seed() -> None:
    """灌入演示数据。重复执行先清空再灌入。"""
    store.init_schema()
    conn = store.get_conn()
    for t in ("transfer_records", "signals", "contacts", "holdings", "subscriptions", "transactions", "cards", "wealth_products", "accounts"):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()

    # 账户
    conn.execute("INSERT INTO accounts(id,user_id,name,balance) VALUES(1,?,?,?)", ("u001", "张同学", 3242.50))

    # 卡片：1 消费卡（绑定订阅，有信用额度+账单日）+ 2 储蓄卡
    conn.execute(
        "INSERT INTO cards(id,account_id,card_no,card_type,status,daily_limit,credit_limit,bill_day) VALUES(1,1,?,?,?,?,?,?)",
        ("6222 **** 8888", "消费卡", "normal", 5000.0, 20000.0, 5),
    )
    conn.execute(
        "INSERT INTO cards(id,account_id,card_no,card_type,status,daily_limit,credit_limit,bill_day) VALUES(2,1,?,?,?,?,?,?)",
        ("6217 **** 1234", "储蓄卡", "normal", 20000.0, 0.0, 15),
    )

    # 订阅：3 笔，含下次续费日
    subs = [
        (1, 1, "6222 **** 8888", "视频会员", 25.0, 15, "active", "本月已涨价 5 元", "2026-11-15"),
        (2, 1, "6222 **** 8888", "健身 App", 30.0, 3, "active", "已连续 3 月扣费但无使用记录", "2026-11-03"),
        (3, 1, "6222 **** 8888", "云存储", 12.0, 20, "active", "", "2026-11-20"),
    ]
    conn.executemany(
        "INSERT INTO subscriptions(id,account_id,card_no,name,monthly_fee,renew_day,status,note,next_renewal) VALUES(?,?,?,?,?,?,?,?,?)",
        subs,
    )

    # 流水：覆盖 3 个月，多分类，含异常交易
    txns = [
        # 10 月（本月）
        (1, "6222 **** 8888", "美团外卖", "餐饮", 32.5, "2026-10-27 19:12", "晚饭"),
        (1, "6222 **** 8888", "海底捞", "餐饮", 386.0, "2026-10-24 20:30", "聚餐"),
        (1, "6222 **** 8888", "京东", "购物", 299.0, "2026-10-20 14:02", "耳机"),
        (1, "6222 **** 8888", "地铁", "交通", 4.0, "2026-10-19 08:15", "通勤"),
        (1, "6222 **** 8888", "XX 商场", "购物", 1200.0, "2026-10-26 03:11", "异地大额异常"),
        (1, "6217 **** 1234", "工资入账", "收入", 6000.0, "2026-10-15 09:00", "10 月工资"),
        (1, "6222 **** 8888", "优衣库", "购物", 359.0, "2026-10-18 15:30", "外套"),
        (1, "6222 **** 8888", "肯德基", "餐饮", 48.0, "2026-10-22 12:10", "午餐"),
        (1, "6222 **** 8888", "视频会员", "娱乐", 25.0, "2026-10-15 08:00", "订阅扣费"),
        (1, "6222 **** 8888", "健身房", "健身", 30.0, "2026-10-03 08:00", "订阅扣费"),
        # 9 月
        (1, "6222 **** 8888", "美团外卖", "餐饮", 210.5, "2026-09-27 19:00", "9月外卖"),
        (1, "6222 **** 8888", "淘宝", "购物", 488.0, "2026-09-15 10:00", "日用品"),
        (1, "6217 **** 1234", "工资入账", "收入", 6000.0, "2026-09-15 09:00", "9 月工资"),
        (1, "6222 **** 8888", "地铁", "交通", 52.0, "2026-09-30 18:00", "9月通勤"),
        # 8 月
        (1, "6222 **** 8888", "美团外卖", "餐饮", 198.0, "2026-08-27 19:00", "8月外卖"),
        (1, "6217 **** 1234", "工资入账", "收入", 6000.0, "2026-08-15 09:00", "8 月工资"),
        (1, "6222 **** 8888", "电影院", "娱乐", 120.0, "2026-08-12 20:00", "电影"),
    ]
    conn.executemany(
        "INSERT INTO transactions(account_id,card_no,merchant,category,amount,ts,remark) VALUES(?,?,?,?,?,?,?)",
        txns,
    )

    # 理财产品：6 只，覆盖低/中低/中高/高风险
    products = [
        ("F001", "稳健货币基金", "低", "货币", 2.1, 1.0),
        ("F002", "债券型基金", "中低", "债券", 3.8, 100.0),
        ("F003", "指数型基金", "中高", "指数", 8.5, 100.0),
        ("F004", "黄金 ETF", "中高", "商品", 12.3, 100.0),
        ("F005", "混合型基金", "中高", "混合", 6.7, 100.0),
        ("F006", "股票型基金", "高", "股票", 15.2, 500.0),
    ]
    conn.executemany(
        "INSERT INTO wealth_products(code,name,risk_level,type,yoy_return,min_amount) VALUES(?,?,?,?,?,?)",
        products,
    )

    # 持仓：3 笔
    holdings = [
        (1, 1, "F001", 5000.0, "2026-08-20 10:00"),
        (2, 1, "F002", 3000.0, "2026-09-05 14:30"),
        (3, 1, "F004", 2000.0, "2026-10-01 09:15"),
    ]
    conn.executemany(
        "INSERT INTO holdings(id,account_id,product_code,amount,ts) VALUES(?,?,?,?,?)",
        holdings,
    )

    # 收款人白名单
    contacts = [
        (1, 1, "老王", "13800001111"),
        (2, 1, "房东", "13900002222"),
        (3, 1, "李同学", "13700003333"),
        (4, 1, "妈妈", "13600004444"),
    ]
    conn.executemany("INSERT INTO contacts(id,account_id,name,phone) VALUES(?,?,?,?)", contacts)

    # 转账记录：3 笔历史
    transfers = [
        (1, 1, "房东", 3000.0, "2026-10-15 10:00", "完成"),
        (2, 1, "李同学", 128.5, "2026-10-10 18:30", "完成"),
        (3, 1, "老王", 200.0, "2026-09-20 12:00", "完成"),
    ]
    conn.executemany(
        "INSERT INTO transfer_records(id,account_id,to_name,amount,ts,status) VALUES(?,?,?,?,?,?)",
        transfers,
    )

    # 行为信号（让习惯画像有数据）
    signals = [
        (1, 1, "查账单", "2026-10-28 20:00"),
        (2, 1, "查账单", "2026-10-27 20:00"),
        (3, 1, "查账单", "2026-10-26 20:00"),
        (4, 1, "看理财", "2026-10-20 12:00"),
        (5, 1, "看理财", "2026-10-18 12:00"),
    ]
    conn.executemany(
        "INSERT INTO signals(id,account_id,signal,ts) VALUES(?,?,?,?)",
        signals,
    )

    conn.commit()
    conn.close()
    print("演示数据已灌入：账户1 卡2 订阅3 流水17 理财6 持仓3 收款人4 转账记录3 信号5")


if __name__ == "__main__":
    seed()
