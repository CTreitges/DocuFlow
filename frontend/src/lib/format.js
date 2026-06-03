// Formatierungs- und Anzeige-Helfer.

export function pct(v) {
  return v == null ? '' : Math.round(v * 100) + '%';
}

export function confColor(v) {
  if (v >= 0.8) return 'var(--success)';
  if (v >= 0.5) return 'var(--warning)';
  if (v > 0) return 'var(--error)';
  return 'var(--muted)';
}

export function money(amount, currency = 'EUR') {
  if (amount == null || amount === '') return '';
  try {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: currency || 'EUR' }).format(amount);
  } catch {
    return `${amount} ${currency || ''}`.trim();
  }
}

const STATUS = {
  neu: 'Neu',
  verarbeitung: 'In Arbeit',
  review: 'Review',
  verarbeitet: 'Verarbeitet',
  fehler: 'Fehler',
  ignoriert: 'Ignoriert',
};
export function statusLabel(s) {
  return STATUS[s] || s;
}

export function dateDE(s) {
  if (!s) return '';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleDateString('de-DE');
}

export function dateTimeDE(s) {
  if (!s) return '';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' });
}

export function avgConfidence(ext) {
  if (!ext || !ext.confidence) return null;
  const vals = Object.entries(ext.confidence)
    .filter(([k, v]) => k !== 'overall' && v > 0)
    .map(([, v]) => v);
  if (!vals.length) return ext.confidence.overall ?? null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}
