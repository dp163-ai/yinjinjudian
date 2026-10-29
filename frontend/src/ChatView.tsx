import { useEffect, useRef, useState } from 'react'
import { chat, postJson } from './api'
import XiaoWei from './XiaoWei'

interface Msg {
  id: number
  role: 'user' | 'agent'
  reply?: string
  data?: Record<string, unknown>
  intent?: string
}

const QUICK = [
  '我这个月花了多少',
  '我有几个会员在扣钱',
  '转给老王 200',
  '看看适合我的理财',
]

let uid = 1

const WELCOME_SUGGESTIONS = [
  { icon: 'M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm2 4h12v2H6V9zm0 4h8v2H6v-2z', label: '查账单', text: '我这个月花了多少' },
  { icon: 'M21 12a8 8 0 0 1-8 8H5.8c-.5 0-.9-.4-.9-.9V19a8 8 0 1 1 16.1-7z', label: '退订阅', text: '我有几个会员在扣钱' },
  { icon: 'M12 3l7 3v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z', label: '转账', text: '转给老王 200' },
  { icon: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 8a7 7 0 0 1 14 0H5z', label: '看理财', text: '看看适合我的理财' },
  { icon: 'M12 3l7 3v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z', label: '查卡片', text: '查一下我的卡' },
  { icon: 'M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm2 4h12v2H6V9zm0 4h8v2H6v-2z', label: '异常排查', text: '有没有异常扣款' },
]

export default function ChatView({ sessionId = 'demo' }: { sessionId?: string }) {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMsgs([])
  }, [sessionId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs])

  async function send(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || busy) return
    setInput('')
    setMsgs((m) => [...m, { id: uid++, role: 'user', reply: msg }])
    setBusy(true)
    try {
      const body = await chat(msg, sessionId)
      setMsgs((m) => [...m, { id: uid++, role: 'agent', reply: body.reply, data: body.data, intent: body.intent }])
    } catch {
      setMsgs((m) => [...m, { id: uid++, role: 'agent', reply: '暂时连不上服务，请确认后端已启动。' }])
    }
    setBusy(false)
  }

  async function subAction(action: string, subId: number) {
    setBusy(true)
    try {
      const body = await postJson(`/subscription/${action}`, { sub_id: subId })
      if (body.ok) {
        const name = body.data?.name ?? ''
        const text = action === 'cancel' ? `已取消订阅「${name}」` : `已续订「${name}」`
        setMsgs((m) => [...m, { id: uid++, role: 'agent', reply: text }])
      } else {
        setMsgs((m) => [...m, { id: uid++, role: 'agent', reply: body.error || '操作失败，请重试。' }])
      }
    } catch {
      setMsgs((m) => [...m, { id: uid++, role: 'agent', reply: '操作失败，请重试。' }])
    }
    setBusy(false)
  }

  return (
    <div className="chat">
      <div className="chat-scroll" ref={scrollRef}>
        <div className="messages">
          {msgs.length === 0 && (
            <div className="welcome">
              <XiaoWei size={72} />
              <div className="welcome-title">你好，我是小微</div>
              <div className="welcome-sub">微众银行 AI 助手 · 一句话就能查账、理财、转账、管卡、退订阅</div>
              <div className="welcome-grid">
                {WELCOME_SUGGESTIONS.map((s) => (
                  <button key={s.label} className="welcome-card" onClick={() => send(s.text)}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
                      <path d={s.icon} />
                    </svg>
                    <span className="welcome-card-label">{s.label}</span>
                    <span className="welcome-card-text">{s.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
          {msgs.map((m) => (
            <div key={m.id} className={m.role === 'user' ? 'msg user' : 'msg agent'}>
              {m.role === 'agent' && (
                <div className="msg-avatar">
                  <XiaoWei size={28} />
                </div>
              )}
              <div className="msg-body">
                <div className="bubble">{m.reply}</div>
                {m.role === 'agent' && m.data && <Card data={m.data} intent={m.intent} onAction={send} onSubAction={subAction} />}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="quickbar">
        {QUICK.map((q) => (
          <button key={q} onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>
      <div className="inputbar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && send()}
          placeholder="说点什么，比如「转给老王 200」"
          disabled={busy}
        />
        <button className="btn primary" onClick={() => send()} disabled={busy}>
          发送
        </button>
      </div>
    </div>
  )
}

function Card({
  data,
  intent,
  onAction,
  onSubAction,
}: {
  data: Record<string, unknown>
  intent?: string
  onAction: (t: string) => void
  onSubAction: (action: string, subId: number) => void
}) {
  if (data.needs_confirm) {
    const action = data.action as string
    const to = data.to as string
    const amount = data.amount as number
    const isL3 = data.level === 'L3'
    return (
      <div className="card confirm">
        <div className="confirm-summary">
          {action === 'transfer' && to && (
            <>
              <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>转账确认</div>
              <div style={{ fontSize: 22, fontWeight: 600, margin: '6px 0 2px', fontFamily: 'var(--font-mono)' }}>
                <span>向「{to}」</span>{' '}
                <span className="amount" style={{ color: 'var(--amber)' }}>¥{amount?.toFixed(2)}</span>
              </div>
            </>
          )}
          {action !== 'transfer' && <span className="key">{(data.title as string) || '需要你确认'}</span>}
          {isL3 && <span className="badge l3" style={{ marginLeft: 8 }}>高风险 · L3</span>}
          {!isL3 && <span className="badge l2" style={{ marginLeft: 8 }}>L2</span>}
        </div>
        <div className="card-actions">
          <button className="btn ghost" onClick={() => onAction('取消')}>
            取消
          </button>
          <button className="btn primary" onClick={() => onAction('确认')}>
            确认转账
          </button>
        </div>
      </div>
    )
  }
  if (intent === 'blocked') {
    return (
      <div className="card blocked">
        <div className="row" style={{ borderTop: 'none' }}>
          <span className="row-label">已拦截可疑指令</span>
          <span className="badge bad">安全</span>
        </div>
      </div>
    )
  }
  if (data.by_category) {
    const cats = data.by_category as { category: string; total: number; cnt: number }[]
    const max = Math.max(...cats.map((c) => c.total), 1)
    const palette = ['#4c8dff', '#2ea36b', '#d29922', '#e5534b', '#8b5cf6', '#14b8a6']
    return (
      <div className="card">
        <div className="card-title">消费分类 · 共 ¥{String(data.total)}</div>
        {cats.map((c, i) => (
          <div key={c.category} className="bar-row">
            <div className="bar-label">
              <span>{c.category}</span>
              <span className="amount">¥{c.total} · {c.cnt} 笔</span>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(c.total / max) * 100}%`, background: palette[i % palette.length] }} />
            </div>
          </div>
        ))}
      </div>
    )
  }
  if (data.subscriptions) {
    const subs = data.subscriptions as { id: number; name: string; monthly_fee: number; note: string; next_renewal: string }[]
    return (
      <div className="card">
        <div className="card-title">订阅 · 月扣 ¥{String(data.monthly_total)}</div>
        {subs.map((s) => (
          <div key={s.id} className="row">
            <span className="sub-name">{s.name}</span>
            {s.note ? (
              <span className="tag" style={{ marginRight: 0 }}>{s.note}</span>
            ) : (
              <span className="amount">¥{s.monthly_fee}/月</span>
            )}
          </div>
        ))}
        <div className="card-hint">
          {subs.map((s) => (
            <div key={s.id} className="sub-actions">
              <span className="sub-info">
                {s.name} · ¥{s.monthly_fee}/月
                {s.next_renewal && <span className="sub-renew">下次续费 {s.next_renewal}</span>}
              </span>
              <button className="btn tiny danger" onClick={() => onSubAction('cancel', s.id)}>取消订阅</button>
              <button className="btn tiny" onClick={() => onSubAction('renew', s.id)}>续订</button>
            </div>
          ))}
        </div>
      </div>
    )
  }
  if (data.products) {
    const ps = data.products as { code: string; name: string; risk_level: string; yoy_return: number }[]
    return (
      <div className="card">
        <div className="card-title">理财推荐 · {String(data.risk_level)}</div>
        {ps.map((p) => (
          <div key={p.code} className="row">
            <span>{p.name}</span>
            <span>
              <span className="badge ok" style={{ marginRight: 6 }}>{p.risk_level}</span>
              <span className="amount positive">+{p.yoy_return}%</span>
            </span>
          </div>
        ))}
        <div className="disclaimer">{String(data.disclaimer)}</div>
      </div>
    )
  }
  if (data.linked_subscriptions) {
    const subs = data.linked_subscriptions as { id: number; name: string; monthly_fee: number }[]
    return (
      <div className="card">
        <div className="card-title">该卡关联的代扣</div>
        {subs.map((s) => (
          <div key={s.id} className="row">
            <span>{s.name}</span>
            <span className="amount">¥{s.monthly_fee}/月</span>
          </div>
        ))}
      </div>
    )
  }
  if (data.trend) {
    const trend = data.trend as { month: string; income: number; expense: number; net: number }[]
    const maxVal = Math.max(...trend.map((t) => Math.max(t.income, t.expense)), 1)
    return (
      <div className="card">
        <div className="card-title">近 {trend.length} 个月收支趋势</div>
        {trend.map((t) => (
          <div key={t.month} className="trend-row">
            <span className="trend-month">{t.month.slice(5)}月</span>
            <div className="trend-bars">
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(t.income / maxVal) * 100}%`, background: '#2ea36b' }} />
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(t.expense / maxVal) * 100}%`, background: '#e5534b' }} />
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
    )
  }
  if (data.holdings) {
    const holdings = data.holdings as { id: number; name: string; amount: number; risk_level: string; est_annual_return: number }[]
    return (
      <div className="card">
        <div className="card-title">我的持仓 · 共 ¥{String(data.total)}</div>
        {holdings.map((h) => (
          <div key={h.id} className="row">
            <span>{h.name}</span>
            <span>
              <span className="badge ok" style={{ marginRight: 6 }}>{h.risk_level}</span>
              <span className="amount">¥{h.amount}</span>
              <span className="amount positive" style={{ marginLeft: 6 }}>≈+{h.est_annual_return}/年</span>
            </span>
          </div>
        ))}
        <div className="disclaimer">{String(data.disclaimer)}</div>
      </div>
    )
  }
  if (data.records) {
    const records = data.records as { id: number; to_name: string; amount: number; ts: string; status: string }[]
    return (
      <div className="card">
        <div className="card-title">转账记录 · {String(data.count)} 笔</div>
        {records.map((r) => (
          <div key={r.id} className="row">
            <span>{r.to_name}</span>
            <span>
              <span className="amount" style={{ marginRight: 8 }}>¥{r.amount}</span>
              <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>{r.ts.slice(0, 10)}</span>
            </span>
          </div>
        ))}
      </div>
    )
  }
  if (data.transactions) {
    const txns = data.transactions as { id: number; merchant: string; category: string; amount: number; ts: string }[]
    return (
      <div className="card">
        <div className="card-title">最近交易</div>
        {txns.map((t) => (
          <div key={t.id} className="row">
            <span>{t.merchant}</span>
            <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>{t.category}</span>
            <span className="amount" style={{ color: t.category === '收入' ? 'var(--green)' : 'var(--text)' }}>
              {t.category === '收入' ? '+' : '-'}¥{t.amount}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}
