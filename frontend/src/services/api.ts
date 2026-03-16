const API_BASE = '/api'

export const api = {
  // 시뮬레이션
  async loadExample() {
    const res = await fetch(`${API_BASE}/simulation/load-example`, { method: 'POST' })
    return res.json()
  },

  async getState() {
    const res = await fetch(`${API_BASE}/simulation/state`)
    return res.json()
  },

  async getMetrics() {
    const res = await fetch(`${API_BASE}/simulation/metrics`)
    return res.json()
  },

  // 인텐트
  async parseIntent(text: string) {
    const res = await fetch(`${API_BASE}/intent/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    return res.json()
  },

  // DSL
  async compileDsl(intentData: any) {
    const res = await fetch(`${API_BASE}/dsl/compile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intentData),
    })
    return res.json()
  },

  // IR
  async compileIr(dslData: any) {
    const res = await fetch(`${API_BASE}/ir/compile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dslData),
    })
    return res.json()
  },

  // 패치
  async generatePatches(irData: any) {
    const res = await fetch(`${API_BASE}/patches/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(irData),
    })
    return res.json()
  },

  async verifyPatch(patchId: string) {
    const res = await fetch(`${API_BASE}/patches/${patchId}/verify`, { method: 'POST' })
    return res.json()
  },

  async applyPatch(patchId: string) {
    const res = await fetch(`${API_BASE}/patches/${patchId}/apply`, { method: 'POST' })
    return res.json()
  },

  // 원장
  async getLedger() {
    const res = await fetch(`${API_BASE}/ledger`)
    return res.json()
  },

  // 리플레이
  async getReplayTimeline() {
    const res = await fetch(`${API_BASE}/replay/timeline`)
    return res.json()
  },

  async replayFromEvent(eventId: string) {
    const res = await fetch(`${API_BASE}/replay/replay-from/${eventId}`, { method: 'POST' })
    return res.json()
  },
}
