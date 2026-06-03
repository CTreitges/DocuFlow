// DocuFlow Design-Tokens — 1:1 aus dem Claude-Design (data.jsx).

export const C = {
  page: '#0f172a', // slate-900
  surface: '#1e293b', // slate-800
  elevated: '#334155', // slate-700
  accent: '#3b82f6', // blue-500
  accent2: '#8b5cf6', // violet-500 (in Arbeit)
  success: '#22c55e', // green-500
  warning: '#f59e0b', // amber-500
  error: '#ef4444', // red-500
  muted: '#6b7280', // gray-500
  info: '#38bdf8', // sky-400
  textPrimary: '#f1f5f9',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  border: 'rgba(255,255,255,0.08)',
};

// Status → Farbe/Label (Backend-Status inklusive 'verarbeitung')
export const STATUS = {
  neu: { label: 'Neu', color: C.accent },
  review: { label: 'Im Review', color: C.warning },
  verarbeitet: { label: 'Verarbeitet', color: C.success },
  fehler: { label: 'Fehler', color: C.error },
  arbeit: { label: 'In Arbeit', color: C.accent2 },
  verarbeitung: { label: 'In Arbeit', color: C.accent2 },
  ignoriert: { label: 'Ignoriert', color: C.muted },
};

// EIN einheitliches Konfidenz-Schema (0–100): >=90 grün, >=70 amber, <70 rot
export function confColor(v) {
  if (v >= 90) return C.success;
  if (v >= 70) return C.warning;
  return C.error;
}

export function clsx(...a) {
  return a.filter(Boolean).join(' ');
}

// hex → rgba mit Alpha
export function rgba(hex, a) {
  if (typeof hex !== 'string' || hex[0] !== '#') return hex;
  const h = hex.replace('#', '');
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}
