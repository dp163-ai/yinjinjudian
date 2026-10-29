import { useEffect, useState } from 'react'
import { getJson } from './api'

interface StatItem {
  signal: string
  cnt: number
  pct: number
}

export default function ProfileView({ onNavigate }: { onNavigate?: () => void }) {
  const [p, setP] = useState<Record<string, unknown> | null>(null)
  const [stats, setStats] = useState<StatItem[]>([])

  useEffect(() => {
    getJson('/profile').then((d) => setP(d.profile || {})).catch(() => setP({}))
    getJson('/profile/stats').then((d) => setStats(d.stats || [])).catch(() => setStats([]))
  }, [])

  const recs = (p?.recommendations as { text: string; why: string; type: string }[]) || []
  const total = stats.reduce((s, x) => s + x.cnt, 0)
  const palette = ['#4c8dff', '#2ea36b', '#d29922', '#8b5cf6', '#14b8a6', '#e5534b']

  return (
    <div className="dash">
      <div className="page-head" style={{ padding: '0 0 20px' }}>
        <div className="page-title">习惯画像</div>
        <div className="page-sub">只推荐入口，不代你决策</div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>使用行为统计 · 共 {total} 次</h3>
          {stats.length === 0 && <div className="empty">暂无使用记录</div>}
          {stats.map((s, i) => (
            <div key={s.signal} className="stat-row">
              <div className="stat-label">
                <span className="stat-dot" style={{ background: palette[i % palette.length] }} />
                <span>{s.signal}</span>
                <span className="stat-cnt">{s.cnt} 次</span>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${s.pct}%`, background: palette[i % palette.length] }} />
              </div>
              <div className="stat-pct">{s.pct}%</div>
            </div>
          ))}
        </div>
        <div className="panel">
          <h3>推荐给你</h3>
          {recs.map((r, i) => (
            <button key={i} className="rec-card" onClick={onNavigate} style={{ marginTop: i === 0 ? 0 : 10 }}>
              <span className="rec-body">
                <span className="rec-text">{r.text}</span>
                {r.why && <span className="rec-why">为什么推荐：{r.why}</span>}
              </span>
              <span className="tag" style={{ marginRight: 0 }}>{r.type}</span>
              <span className="rec-arrow">→</span>
            </button>
          ))}
          {recs.length === 0 && <div className="empty">继续使用后，我会学习你的习惯并推荐常用入口</div>}
          <div className="disclaimer">{String(p?.disclaimer || '')}</div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="compliance-row">
          <span className="badge ok">合规</span>
          <span>不构成投资建议</span>
          <span className="badge ok">可解释</span>
          <span>「为什么推荐我」可关闭</span>
          <span className="badge ok">不代决策</span>
          <span>只跳转入口，绝不自动下单</span>
        </div>
      </div>
    </div>
  )
}
