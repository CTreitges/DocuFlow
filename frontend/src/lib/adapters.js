// Adapter zwischen Backend-Modellen (core.models) und den Design-View-Shapes.
import { PREVIEW_DATA } from './mock.js';

// --- Formatierung ----------------------------------------------------------
export function fmtBetrag(amount, currency = 'EUR') {
  if (amount == null || amount === '') return '—';
  const n = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount);
  return `${n} ${currency || 'EUR'}`;
}

export function parseBetrag(str) {
  if (str == null) return null;
  let raw = String(str).replace(/[^\d.,-]/g, '');
  if (raw.includes('.') && raw.includes(',')) raw = raw.replace(/\./g, '').replace(',', '.');
  else if (raw.includes(',')) raw = raw.replace(',', '.');
  const n = parseFloat(raw);
  return Number.isNaN(n) ? null : n;
}

const conf100 = (c) => (c == null ? null : Math.round(c * 100));

// --- Dokument: Backend → View ----------------------------------------------
export function docToView(d) {
  const e = d.extraction;
  const overall = e?.confidence?.overall;
  const view = {
    id: String(d.id),
    filename: d.file_name,
    path: d.file_path,
    status: d.status,
    absender: e?.sender || '—',
    datum: e?.date || '—',
    betrag: e?.total_amount != null ? fmtBetrag(e.total_amount, e.currency) : '—',
    reNr: e?.invoice_number || '—',
    konfidenz: overall != null ? Math.round(overall * 100) : 0,
    _raw: d,
  };
  if (e) {
    view.extraction = {
      absender: { value: e.sender || '', conf: conf100(e.confidence?.sender) },
      datum: { value: e.date || '', conf: conf100(e.confidence?.date) },
      rechnungsnr: { value: e.invoice_number || '', conf: conf100(e.confidence?.invoice_number) },
      betrag: { value: e.total_amount != null ? fmtBetrag(e.total_amount, e.currency) : '', conf: conf100(e.confidence?.total_amount) },
      iban: { value: e.iban || '' },
      kundennr: { value: e.customer_number || '' },
      mwst: { value: e.vat_rate != null ? `${e.vat_rate} %` : '' },
      zahlungsziel: { value: e.due_date || '' },
      dokumenttyp: { value: e.document_type || '' },
    };
    view.positionen = (e.line_items || []).map((li, i) => ({
      nr: i + 1,
      beschreibung: li.description || '',
      menge: li.quantity != null ? String(li.quantity) : '',
      gesamt: li.total != null ? fmtBetrag(li.total, e.currency) : '',
    }));
  }
  if (d.status === 'fehler' && !view.error) {
    view.error = 'Verarbeitung fehlgeschlagen — Details im Aktivitäts-Log.';
  }
  return view;
}

// Edit eines View-Felds → angepasste Backend-Extraction (für PATCH)
export function applyEdit(rawDoc, key, value) {
  const e = { ...(rawDoc?.extraction || {}) };
  if (key === 'absender') e.sender = value;
  else if (key === 'datum') e.date = value || null;
  else if (key === 'rechnungsnr') e.invoice_number = value;
  else if (key === 'betrag') e.total_amount = parseBetrag(value);
  else if (key === 'iban') e.iban = value;
  else if (key === 'kundennr') e.customer_number = value;
  return e;
}

// --- Regeln: Backend ↔ View ------------------------------------------------
const FIELD_B2V = { absender: 'Absender', betrag: 'Betrag', inhalt: 'Inhalt', dokumenttyp: 'Dokumenttyp', rechnungsnr: 'Rechnungsnr.' };
const FIELD_V2B = Object.fromEntries(Object.entries(FIELD_B2V).map(([b, v]) => [v, b]));
const OP_B2V = { enthaelt: 'enthält', ist: 'ist', beginnt_mit: 'beginnt mit', groesser_als: 'größer als', kleiner_als: 'kleiner als' };
const OP_V2B = Object.fromEntries(Object.entries(OP_B2V).map(([b, v]) => [v, b]));

export function ruleToView(r) {
  return {
    id: r.id || ('r' + Math.random().toString(36).slice(2, 8)),
    name: r.name || '',
    enabled: r.enabled !== false,
    conditions: (r.conditions || []).map((c, i) => ({
      logic: i === 0 ? 'WENN' : c.logic === 'OR' ? 'ODER' : 'UND',
      field: FIELD_B2V[c.field] || 'Absender',
      operator: OP_B2V[c.operator] || 'enthält',
      value: c.value || '',
    })),
    baseFolder: r.target_base || 'D:/Rechnungen',
    subfolders: [...(r.target_subfolders || [])],
    nameParts: [...(r.filename_parts || [])],
  };
}

export function viewToRule(v, priority) {
  return {
    id: v.id,
    name: v.name,
    enabled: v.enabled,
    conditions: v.conditions.map((c, i) => ({
      field: FIELD_V2B[c.field] || 'absender',
      operator: OP_V2B[c.operator] || 'enthaelt',
      value: c.value || '',
      logic: i === 0 ? 'AND' : c.logic === 'ODER' ? 'OR' : 'AND',
    })),
    target_base: v.baseFolder,
    target_subfolders: [...v.subfolders],
    filename_parts: [...v.nameParts],
    priority: priority ?? 0,
  };
}

export function resolvePart(p) {
  return PREVIEW_DATA[p] ?? p;
}

export function previewPath(rule) {
  const sub = rule.subfolders.map(resolvePart).join('/');
  const name = rule.nameParts.map(resolvePart).join('_');
  return `${rule.baseFolder}/${sub}/${name}.pdf`.replace(/\/+/g, '/');
}

// --- History → Aktivitäts-Log ----------------------------------------------
const ACTION_B2V = {
  scan: 'scan', template_match: 'template', ocr: 'ocr', sorted: 'sortiert',
  auto_sorted: 'auto-sortiert', confirmed: 'bestätigt', error: 'fehler',
  template_created: 'template-erstellt', korrigiert: 'korrektur',
  reaktiviert: 'reaktiviert', ignoriert: 'ignoriert', auto_skipped: 'ocr',
};

export function historyToActivity(h, now = new Date()) {
  const ts = new Date(h.timestamp);
  const valid = !Number.isNaN(ts.getTime());
  const sameDay = valid && ts.toDateString() === now.toDateString();
  const days = valid ? (now - ts) / 86400000 : 999;
  const period = sameDay ? 'heute' : days < 7 ? 'woche' : 'alles';
  const time = !valid
    ? ''
    : sameDay
      ? ts.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
      : ts.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  return {
    id: String(h.id),
    type: ACTION_B2V[h.action] || h.action || 'scan',
    filename: h.file_name || '—',
    details: h.details || '',
    time,
    period,
  };
}

// --- Settings: Backend-Config → View ---------------------------------------
export function settingsToView(cfg) {
  return {
    folders: (cfg.input_folders || []).map((f, i) => ({ id: 'f' + i, path: f.path, active: f.enabled !== false, exists: true })),
    outputFolder: cfg.output?.base_path || 'D:/Rechnungen',
    autoSort: !!cfg.auto_mode,
    threshold: Math.round((cfg.auto_confidence_threshold ?? 0.9) * 100),
    ollamaUrl: cfg.ollama?.url || 'http://localhost:11434',
    ollamaModel: cfg.ollama?.model || 'minicpm-v',
    ollamaTimeout: cfg.ollama?.timeout ?? 120,
    ocrEnabled: cfg.german_ocr?.enabled !== false,
    ocrBackendRaw: cfg.german_ocr?.backend || 'ollama',
  };
}

export function viewToSettings(v) {
  return {
    input_folders: v.folders.map((f) => ({ path: f.path, enabled: f.active, watch: true })),
    output: { base_path: v.outputFolder },
    auto_mode: v.autoSort,
    auto_confidence_threshold: v.threshold / 100,
    ollama: { url: v.ollamaUrl, model: v.ollamaModel, timeout: Number(v.ollamaTimeout) },
    german_ocr: { enabled: v.ocrEnabled, backend: v.ocrBackendRaw },
  };
}
