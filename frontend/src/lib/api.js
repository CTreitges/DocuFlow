// DocuFlow API-Client. Basis ist leer → same-origin in Produktion; im Dev
// proxyt Vite /api an den uvicorn-Server (siehe vite.config.js).

async function req(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch { /* kein JSON-Body */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  return ct.includes('application/json') ? res.json() : res.text();
}

export const api = {
  // System
  health: () => req('/api/health'),
  stats: () => req('/api/stats'),
  history: (limit = 50) => req(`/api/history?limit=${limit}`),

  // Dokumente
  documents: (status) => req('/api/documents' + (status ? `?status=${encodeURIComponent(status)}` : '')),
  document: (id) => req(`/api/documents/${id}`),
  scan: () => req('/api/scan', { method: 'POST' }),
  process: (id) => req(`/api/documents/${id}/process`, { method: 'POST' }),
  processAll: () => req('/api/process-all', { method: 'POST' }),
  confirm: (id) => req(`/api/documents/${id}/confirm`, { method: 'POST' }),
  ignore: (id) => req(`/api/documents/${id}/ignore`, { method: 'POST' }),
  reactivate: (id) => req(`/api/documents/${id}/reactivate`, { method: 'POST' }),
  updateExtraction: (id, extraction) =>
    req(`/api/documents/${id}/extraction`, { method: 'PATCH', body: JSON.stringify({ extraction }) }),
  previewUrl: (id) => `/api/documents/${id}/preview`,

  // Regeln
  rules: () => req('/api/rules'),
  blankRule: () => req('/api/rules/blank'),
  saveRules: (rules) => req('/api/rules', { method: 'PUT', body: JSON.stringify({ rules }) }),
  createRule: (rule) => req('/api/rules', { method: 'POST', body: JSON.stringify(rule) }),
  updateRule: (id, rule) => req(`/api/rules/${id}`, { method: 'PUT', body: JSON.stringify(rule) }),
  deleteRule: (id) => req(`/api/rules/${id}`, { method: 'DELETE' }),
  reorderRules: (order) => req('/api/rules/reorder', { method: 'POST', body: JSON.stringify({ order }) }),
  rulePreview: (rule, extraction = null) =>
    req('/api/rules/preview', { method: 'POST', body: JSON.stringify({ rule, extraction }) }),

  // Templates
  templates: () => req('/api/templates'),
  deleteTemplate: (id) => req(`/api/templates/${id}`, { method: 'DELETE' }),

  // Einstellungen
  settings: () => req('/api/settings'),
  saveSettings: (patch) => req('/api/settings', { method: 'PUT', body: JSON.stringify(patch) }),
  resetDatabase: () => req('/api/reset', { method: 'POST' }),

  // Ordner-Überwachung (Watchdog)
  watchStatus: () => req('/api/watch/status'),
  watchStart: () => req('/api/watch/start', { method: 'POST' }),
  watchStop: () => req('/api/watch/stop', { method: 'POST' }),
  watchScanNow: () => req('/api/watch/scan-now', { method: 'POST' }),
};
