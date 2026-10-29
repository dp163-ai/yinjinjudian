import { useEffect, useState } from 'react'
import { getJson } from './api'

export default function DataView() {
  const [ov, setOv] = useState<Record<string, unknown> | null>(null)
  useEffect(() => {
    getJson('/overview').then(setOv).catch(() => setOv({}))
  }, [])
  if (!ov) return <div className="page-head"><div className="page-title">加载中…</div></div>

  const account = ov.account as { name: string; balance: number } | null
  const bill = ov.bill as { total: number; by_category: { category: string; total: number; cnt: number }[] } | null
  const subs = ov.subscriptions as { count: number; monthly_total: number } | null
  const cards = (ov.cards as { id: number; card_no: string; card_type: string; type_cn: string; status: string; status_cn: string; daily_limit: number; credit_limit: number; bill_day: number }[]) || []
  const trend = (ov.trend as { trend: { month: string; income: number; expense: number; net: number }[] })?.trend || []
  const holdings = (ov.holdings as { total: number; holdings: { id: number; name: string; amount: number; risk_level: string; est_annual_return: number }[] })?.holdings || []
  const holdingsTotal = (ov.holdings as { total: number })?.total || 0
  const transfers = (ov.transfers as { records: { id: number; to_name: string; amount: number; ts: string }[] })?.records || []
  const recent = (ov.recent as { transactions: { id: number; merchant: string; category: string; amount: number; ts: string }[] })?.transactions || []
  const maxCat = bill?.by_category?.length ? Math.max(...bill.by_category.map((c) => c.total), 1) : 1
  const maxTrend = trend.length ? Math.max(...trend.map((t) => Math.max(t.income, t.expense)), 1) : 1

  return (
    <div className="dash">
      <div className="page-head" style={{ padding: '0 0 20px' }}>
        <div className="page-title">资金总览</div>
        <div className="page-sub">每个数字都能追溯到原始流水</div>
      </div>

      <div className="grid">
        <div className="panel">
          <h3>账户余额</h3>
          <div className="metric">¥{account?.balance?.toFixed(2) ?? '—'}</div>
          <div className="metric-hint">{account?.name ?? '请先灌入演示数据'}</div>
        </div>
        <div className="panel">
          <h3>本月消费</h3>
          <div className="metric">¥{bill?.total?.toFixed(2) ?? '—'}</div>
          <div className="metric-hint">{bill?.by_category?.length ?? 0} 个分类</div>
        </div>
        <div className="panel">
          <h3>订阅月扣</h3>
          <div className="metric">¥{subs?.monthly_total?.toFixed(2) ?? '—'}</div>
          <div className="metric-hint">{subs?.count ?? 0} 笔订阅</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>近 {trend.length} 月收支趋势</h3>
          {trend.map((t) => (
            <div key={t.month} className="trend-row">
              <span className="trend-month">{t.month.slice(5)}月</span>
              <div className="trend-bars">
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(t.income / maxTrend) * 100}%`, background: '#2ea36b' }} />
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(t.expense / maxTrend) * 100}%`, background: '#e5534b' }} />
                </div>
              </div>
              <span className="trend-net amount" style={{ color: t.net >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {t.net >= 0 ? '+' : ''}{t.net}
              </span>
            </div>
          ))}
          <div className="trend-legend">
            <span><i style={{ background: '#2ea36b' }} />收入</span>
            <span><i style={{ background: '#e5534b' }} />支出</span>
          </div>
        </div>
        <div className="panel">
          <h3>消费分类</h3>
          {(bill?.by_category ?? []).map((c) => (
            <div key={c.category} className="bar-row">
              <div className="bar-label">
                <span>{c.category}</span>
                <span className="amount">¥{c.total} · {c.cnt}笔</span>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(c.total / maxCat) * 100}%`, background: '#4c8dff' }} />
              </div>
            </div>
          ))}
          {!bill?.by_category?.length && <div className="empty">暂无账单数据</div>}
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>卡片</h3>
          <table>
            <thead>
              <tr>
                <th>卡号</th>
                <th>类型</th>
                <th>状态</th>
                <th>日限额</th>
                <th>账单日</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{c.card_no}</td>
                  <td>{c.type_cn || c.card_type}</td>
                  <td>
                    <span className={`badge ${c.status === 'normal' ? 'ok' : c.status === 'frozen' ? 'warn' : 'bad'}`}>
                      {c.status_cn || c.status}
                    </span>
                  </td>
                  <td className="amount">¥{c.daily_limit}</td>
                  <td>{c.bill_day ? `${c.bill_day} 日` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h3>理财持仓 · 共 ¥{holdingsTotal}</h3>
          <table>
            <thead>
              <tr>
                <th>产品</th>
                <th>风险</th>
                <th>金额</th>
                <th>估算年化</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr key={h.id}>
                  <td>{h.name}</td>
                  <td><span className="badge ok">{h.risk_level}</span></td>
                  <td className="amount">¥{h.amount}</td>
                  <td className="amount positive">+{h.est_annual_return}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>最近转账</h3>
          <table>
            <thead>
              <tr>
                <th>收款人</th>
                <th>金额</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              {transfers.map((r) => (
                <tr key={r.id}>
                  <td>{r.to_name}</td>
                  <td className="amount">¥{r.amount}</td>
                  <td style={{ color: 'var(--text-faint)', fontSize: 12 }}>{r.ts.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h3>最近流水</h3>
          <table>
            <thead>
              <tr>
                <th>商户</th>
                <th>分类</th>
                <th>金额</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((t) => (
                <tr key={t.id}>
                  <td>{t.merchant}</td>
                  <td style={{ color: 'var(--text-faint)' }}>{t.category}</td>
                  <td className="amount" style={{ color: t.category === '收入' ? 'var(--green)' : 'var(--text)' }}>
                    {t.category === '收入' ? '+' : '-'}¥{t.amount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
