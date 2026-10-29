import { useEffect, useState } from 'react'
import ChatView from './ChatView'
import DataView from './DataView'
import ProfileView from './ProfileView'
import SecurityView from './SecurityView'
import XiaoWei from './XiaoWei'
import { getJson } from './api'

type Tab = 'chat' | 'data' | 'profile' | 'security'

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'chat', label: '对话', icon: 'M21 12a8 8 0 0 1-8 8H5.8c-.5 0-.9-.4-.9-.9V19a8 8 0 1 1 16.1-7z' },
  { key: 'data', label: '资金总览', icon: 'M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm2 4h12v2H6V9zm0 4h8v2H6v-2z' },
  { key: 'profile', label: '习惯画像', icon: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 8a7 7 0 0 1 14 0H5z' },
  { key: 'security', label: '安全中心', icon: 'M12 3l7 3v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z' },
]

interface SessionItem {
  id: number
  title: string
  time: string
}

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [sessions, setSessions] = useState<SessionItem[]>([
    { id: 1, title: '查账单', time: '14:02' },
    { id: 2, title: '退订阅', time: '13:50' },
    { id: 3, title: '转账给老王', time: '昨天' },
  ])
  const [activeSession, setActiveSession] = useState(1)
  const [mode, setMode] = useState('rule')
  const [showConfig, setShowConfig] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('deepseek-chat')

  useEffect(() => {
    getJson('/llm/mode').then((d) => setMode(d.mode)).catch(() => {})
  }, [])

  async function saveConfig() {
    const body = await (await fetch('http://127.0.0.1:8000/llm/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, base_url: baseUrl, model }),
    })).json()
    setMode(body.mode)
    setShowConfig(false)
  }

  function newSession() {
    const s: SessionItem = { id: Date.now(), title: '新会话', time: '刚刚' }
    setSessions((prev) => [s, ...prev])
    setActiveSession(s.id)
    setTab('chat')
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <XiaoWei size={44} />
          <div className="brand-text">
            <div className="brand-name">引金据典</div>
            <div className="brand-sub">小微 · 微众银行 AI 助手</div>
          </div>
        </div>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={tab === t.key ? 'nav active' : 'nav'}
            onClick={() => setTab(t.key)}
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d={t.icon} />
            </svg>
            <span>{t.label}</span>
          </button>
        ))}
        <div className="sidebar-footer">
          <button className="mode-chip-left" onClick={() => setShowConfig(true)}>
            <span className={`mode-dot ${mode === 'llm' ? 'llm' : 'rule'}`} />
            <span>{mode === 'llm' ? '大模型模式' : '规则模式'}</span>
            <span className="mode-config">配置</span>
          </button>
        </div>
      </aside>
      <main className="content">
        {tab === 'chat' && <ChatView sessionId={`s${activeSession}`} />}
        {tab === 'data' && <DataView />}
        {tab === 'profile' && <ProfileView onNavigate={() => setTab('chat')} />}
        {tab === 'security' && <SecurityView />}
      </main>
      <aside className="rightbar">
        <div className="rightbar-section">
          <div className="rightbar-title">
            会话记录
            <button className="icon-btn" onClick={newSession} title="新增会话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="16" height="16">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>
          </div>
          {sessions.map((s) => (
            <button
              key={s.id}
              className={s.id === activeSession ? 'session-item active' : 'session-item'}
              onClick={() => { setActiveSession(s.id); setTab('chat') }}
            >
              <span className="session-dot" />
              <span className="session-title">{s.title}</span>
              <span className="session-time">{s.time}</span>
            </button>
          ))}
        </div>
      </aside>

      {showConfig && (
        <div className="modal-mask" onClick={() => setShowConfig(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">配置 API Key</div>
            <div className="modal-sub">配置后小微走大模型模式，不配置则使用规则模式（仍可处理基础聊天与银行业务）</div>
            <label className="field-label">API Key</label>
            <input type="password" className="field-input" placeholder="sk-..." value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            <label className="field-label">接口地址（可选）</label>
            <input className="field-input" placeholder="https://api.deepseek.com/v1" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
            <label className="field-label">模型</label>
            <input className="field-input" placeholder="deepseek-chat" value={model} onChange={(e) => setModel(e.target.value)} />
            <div className="modal-actions">
              <button className="btn ghost" onClick={() => setShowConfig(false)}>取消</button>
              <button className="btn primary" onClick={saveConfig}>保存</button>
            </div>
            <div className="modal-hint">留空 API Key 保存 = 切换到规则模式</div>
          </div>
        </div>
      )}
    </div>
  )
}
