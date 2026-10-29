export const API_BASE = 'http://127.0.0.1:8000'

export async function chat(message: string, sessionId = 'demo') {
  const r = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  return r.json()
}

export async function getJson(path: string) {
  const r = await fetch(`${API_BASE}${path}`)
  return r.json()
}

export async function postJson(path: string, body: Record<string, unknown>) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return r.json()
}
