import { useEffect, useMemo, useState } from 'react'
import { getJson, postJson } from './api'

interface LogItem {
  action: string
  action_cn: string
  target: string
  amount: number
  result: string
  ts: string
}

interface PermAction {
  key: string
  name: string
  level: string
}

const LEVEL_BADGE: Record<string, string> = { L0: 'l0', L1: 'l1', L2: 'l2', L3: 'l3' }
const LEVEL_DESC: Record<string, string> = {
  L0: '只读·非敏感',
  L1: '只读·敏感',
  L2: '写·需确认',
  L3: '写·高风险',
}

export default function SecurityView() {
  const [logs, setLogs] = useState<LogItem[]>([])
  const [dateFilter, setDateFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [actions, setActions] = useState<PermAction[]>([])

  useEffect(() => {
    getJson('/audit').then((d) => setLogs(d.logs || [])).catch(() => {})
    getJson('/permissions').then((d) => setActions(d.actions || [])).catch(() => {})
  }, [])

  const types = useMemo(() => Array.from(new Set(logs.map((l) => l.action_cn || l.action))), [logs])

  const filtered = useMemo(() => {
    return logs.filter((l) => {
      if (dateFilter && !l.ts.startsWith(dateFilter)) return false
      if (typeFilter && (l.action_cn || l.action) !== typeFilter) return false
      return true
    })
  }, [logs, dateFilter, typeFilter])

  async function changeLevel(key: string, level: string) {
    const prev = actions.find((a) => a.key === key)?.level
    setActions((as) => as.map((a) => (a.key === key ? { ...a, level } : a)))
    try {
      await postJson('/permissions', { key, level })
    } catch {
      setActions((as) => as.map((a) => (a.key === key ? { ...a, level: prev || 'L2' } : a)))
    }
  }

  return (
    <div className="dash">
      <div className="page-head" style={{ padding: '0 0 20px' }}>
        <div className="page-title">安全中心</div>
        <div className="page-sub">每个行为可独立调节权限等级 · 审计留痕 · 注入拦截</div>
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <h3>行为权限设置</h3>
        <div className="perm-grid">
          {actions.map((a) => (
            <div key={a.key} className="perm-item">
              <div className="perm-name">{a.name}</div>
              <div className="perm-levels">
                {(['L0', 'L1', 'L2', 'L3'] as const).map((lv) => (
                  <button
                    key={lv}
                    className={`level-btn ${a.level === lv ? `active ${LEVEL_BADGE[lv]}` : ''}`}
                    onClick={() => changeLevel(a.key, lv)}
                    title={LEVEL_DESC[lv]}
                  >
                    {lv}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="perm-legend">
          <span><span className="badge l0">L0</span> 只读·非敏感</span>
          <span><span className="badge l1">L1</span> 只读·敏感</span>
          <span><span className="badge l2">L2</span> 写·需确认</span>
          <span><span className="badge l3">L3</span> 写·高风险</span>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head-row">
          <h3 style={{ marginBottom: 0 }}>审计日志 · {filtered.length} 条</h3>
          <div className="filter-row">
            <input
              type="date"
              className="filter-input"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            />
            <select
              className="filter-input"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">全部类型</option>
              {types.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            {(dateFilter || typeFilter) && (
              <button className="btn tiny" onClick={() => { setDateFilter(''); setTypeFilter('') }}>清除</button>
            )}
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>动作</th>
              <th>目标</th>
              <th>金额</th>
              <th>结果</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((l, i) => (
              <tr key={i}>
                <td>{l.action_cn || l.action}</td>
                <td>{l.target === '-' || !l.target ? '—' : l.target}</td>
                <td className="amount">{l.amount ? `¥${l.amount}` : '—'}</td>
                <td>{l.result}</td>
                <td style={{ color: 'var(--text-faint)', fontSize: 12 }}>{l.ts.slice(0, 19).replace('T', ' ')}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="empty">无匹配记录</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
