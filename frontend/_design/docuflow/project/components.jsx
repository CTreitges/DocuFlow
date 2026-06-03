// ============================================================
// DocuFlow — Wiederverwendbare Komponenten
// ============================================================
const { useState, useRef, useEffect } = React;
const LR = window.lucide;

// --- Icon helper: name string → lucide-react component ----------------------
const ICON_MAP = {
  inbox: 'Inbox', 'layout-dashboard': 'LayoutDashboard', 'wand-2': 'Wand2',
  'list-filter': 'ListFilter', settings: 'Settings', bug: 'Bug',
  search: 'Search', 'scan-text': 'ScanText', 'check-circle': 'CheckCircle2',
  zap: 'Zap', 'thumbs-up': 'ThumbsUp', 'alert-circle': 'AlertCircle',
  undo: 'Undo2', pencil: 'Pencil', 'rotate-ccw': 'RotateCcw', ban: 'Ban',
  'layout-template': 'LayoutTemplate', check: 'Check', x: 'X', plus: 'Plus',
  trash: 'Trash2', 'grip-vertical': 'GripVertical', 'chevron-down': 'ChevronDown',
  'chevron-right': 'ChevronRight', folder: 'Folder', 'folder-open': 'FolderOpen',
  'file-text': 'FileText', menu: 'Menu', 'refresh-cw': 'RefreshCw',
  'rotate-cw': 'RotateCw', play: 'Play', loader: 'Loader2', 'arrow-right': 'ArrowRight',
  'alert-triangle': 'AlertTriangle', box: 'Box', file: 'File', eye: 'Eye',
  database: 'Database', 'hard-drive': 'HardDrive', server: 'Server', cpu: 'Cpu',
  'file-code': 'FileCode2', 'file-search': 'FileSearch', 'corner-down-right': 'CornerDownRight',
};
function Icon({ name, size = 20, className, style, strokeWidth = 2 }) {
  const pascal = ICON_MAP[name] || name;
  const icons = (LR && LR.icons) || {};
  const node = icons[pascal] || icons.Square || ['svg', {}, []];
  const children = node[2] || [];
  return React.createElement('svg', {
    xmlns: 'http://www.w3.org/2000/svg', width: size, height: size, viewBox: '0 0 24 24',
    fill: 'none', stroke: 'currentColor', strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round',
    className, style,
  }, children.map((c, i) => React.createElement(c[0], { key: i, ...c[1] })));
}

// --- Card -------------------------------------------------------------------
function Card({ children, className, style, ...rest }) {
  return (
    <div
      className={clsx('rounded-xl', className)}
      style={{ background: C.surface, border: `1px solid ${C.border}`, ...style }}
      {...rest}
    >
      {children}
    </div>
  );
}

// --- Section header (per screen) -------------------------------------------
function SectionHeader({ icon, title, right }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <div className="flex items-center gap-2.5">
        <Icon name={icon} size={20} style={{ color: C.accent }} />
        <h1 className="text-lg font-semibold whitespace-nowrap" style={{ color: C.textPrimary }}>{title}</h1>
      </div>
      {right}
    </div>
  );
}

// --- Button -----------------------------------------------------------------
function Button({ children, variant = 'flat', size = 'md', icon, onClick, disabled, className, title, style }) {
  const pad = size === 'sm' ? 'px-2.5 py-1.5 text-xs' : 'px-3.5 py-2 text-sm';
  const base = 'inline-flex items-center gap-2 rounded-lg font-medium transition-colors select-none whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed';
  const variants = {
    primary: { background: C.accent, color: '#fff', border: '1px solid transparent' },
    success: { background: C.success, color: '#04210f', border: '1px solid transparent' },
    amber:   { background: C.warning, color: '#241803', border: '1px solid transparent' },
    danger:  { background: 'transparent', color: C.error, border: `1px solid ${rgba(C.error, 0.4)}` },
    flat:    { background: C.elevated, color: C.textPrimary, border: `1px solid ${C.border}` },
    ghost:   { background: 'transparent', color: C.textSecondary, border: '1px solid transparent' },
  };
  const [hover, setHover] = useState(false);
  const v = variants[variant];
  const hoverBg = {
    primary: '#2563eb', success: '#16a34a', amber: '#d97706',
    danger: rgba(C.error, 0.12), flat: '#3e4c63', ghost: 'rgba(255,255,255,0.06)',
  }[variant];
  return (
    <button
      title={title}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className={clsx(base, pad, className)}
      style={{ ...v, background: hover && !disabled ? hoverBg : v.background, ...style }}
    >
      {icon && <Icon name={icon} size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  );
}

// --- StatCard ---------------------------------------------------------------
function StatCard({ label, value, icon, color }) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium" style={{ color: C.textSecondary }}>{label}</span>
        <div className="flex items-center justify-center rounded-lg" style={{ width: 30, height: 30, background: rgba(color, 0.12) }}>
          <Icon name={icon} size={16} style={{ color }} />
        </div>
      </div>
      <div className="text-2xl font-bold tabular-nums" style={{ color: C.textPrimary }}>{value}</div>
    </Card>
  );
}

// --- StatusBadge ------------------------------------------------------------
function StatusBadge({ status }) {
  const s = STATUS[status] || STATUS.neu;
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{ background: rgba(s.color, 0.12), color: s.color, border: `1px solid ${rgba(s.color, 0.27)}` }}
    >
      {s.label}
    </span>
  );
}

// --- ConfidenceBadge (single scheme) ---------------------------------------
function ConfidenceBadge({ value }) {
  const col = confColor(value);
  return (
    <span
      className="inline-flex items-center rounded-md px-1.5 py-0.5 text-[11px] font-mono font-medium tabular-nums"
      style={{ background: rgba(col, 0.12), color: col, border: `1px solid ${rgba(col, 0.27)}` }}
    >
      {value}%
    </span>
  );
}

// --- Switch -----------------------------------------------------------------
function Switch({ checked, onChange, disabled }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className="relative inline-flex items-center rounded-full transition-colors shrink-0 disabled:opacity-40"
      style={{ width: 38, height: 22, background: checked ? C.accent : C.elevated, border: `1px solid ${C.border}` }}
    >
      <span
        className="inline-block rounded-full bg-white transition-transform"
        style={{ width: 16, height: 16, transform: `translateX(${checked ? 18 : 3}px)` }}
      />
    </button>
  );
}

// --- EditableField ----------------------------------------------------------
function EditableField({ label, value, confidence, mono, onSave, readOnly }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef(null);
  useEffect(() => { setDraft(value); }, [value]);
  useEffect(() => { if (editing && inputRef.current) { inputRef.current.focus(); inputRef.current.select(); } }, [editing]);

  function commit() { onSave && onSave(draft); setEditing(false); }
  function cancel() { setDraft(value); setEditing(false); }

  return (
    <div className="min-w-0">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs" style={{ color: C.textMuted }}>{label}</span>
        {confidence != null && <ConfidenceBadge value={confidence} />}
        {readOnly && <span className="text-[10px] uppercase tracking-wider" style={{ color: C.textMuted }}>read-only</span>}
      </div>
      {editing ? (
        <div className="flex items-center gap-1.5">
          <input
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') cancel(); }}
            className={clsx('flex-1 min-w-0 rounded-md px-2 py-1.5 text-sm outline-none', mono && 'font-mono')}
            style={{ background: C.page, border: `1px solid ${C.accent}`, color: C.textPrimary }}
          />
          <button onClick={commit} title="Speichern" className="p-1.5 rounded-md" style={{ background: rgba(C.success, 0.14), color: C.success }}>
            <Icon name="check" size={15} />
          </button>
          <button onClick={cancel} title="Abbrechen" className="p-1.5 rounded-md" style={{ background: C.elevated, color: C.textSecondary }}>
            <Icon name="x" size={15} />
          </button>
        </div>
      ) : (
        <div
          className={clsx('group flex items-center justify-between gap-2 rounded-md px-2 py-1.5', !readOnly && 'cursor-text')}
          style={{ background: C.page, border: `1px solid ${C.border}` }}
          onClick={() => !readOnly && setEditing(true)}
        >
          <span className={clsx('text-sm truncate', mono && 'font-mono')} style={{ color: value && value !== '—' ? C.textPrimary : C.textMuted }}>
            {value || '—'}
          </span>
          {!readOnly && (
            <Icon name="pencil" size={13} className="opacity-40 group-hover:opacity-100 transition-opacity shrink-0" style={{ color: C.textSecondary }} />
          )}
        </div>
      )}
    </div>
  );
}

// --- ConfirmDialog ----------------------------------------------------------
function ConfirmDialog({ open, title, body, confirmLabel = 'Bestätigen', danger, onConfirm, onCancel }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center df-fade-in" style={{ background: 'rgba(2,6,23,0.6)' }} onClick={onCancel}>
      <div
        className="df-dialog-in rounded-xl p-5"
        style={{ background: C.surface, border: `1px solid ${C.border}`, minWidth: 360, maxWidth: 440, boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold mb-2" style={{ color: C.textPrimary }}>{title}</h3>
        <p className="text-sm leading-relaxed mb-5" style={{ color: C.textSecondary }}>{body}</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel}>Abbrechen</Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm}>{confirmLabel}</Button>
        </div>
      </div>
    </div>
  );
}

// --- Toast host -------------------------------------------------------------
const TOAST_STYLE = {
  success: { color: C.success, icon: 'check-circle' },
  info:    { color: C.info, icon: 'alert-circle' },
  error:   { color: C.error, icon: 'alert-circle' },
  warning: { color: C.warning, icon: 'alert-triangle' },
};
function ToastHost({ toasts, onDismiss }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2" style={{ width: 320 }}>
      {toasts.map((t) => {
        const st = TOAST_STYLE[t.kind] || TOAST_STYLE.info;
        return (
          <div
            key={t.id}
            className="df-toast-in flex items-start gap-2.5 rounded-lg px-3.5 py-3"
            style={{ background: C.surface, border: `1px solid ${rgba(st.color, 0.4)}`, boxShadow: '0 8px 30px rgba(0,0,0,0.4)' }}
          >
            <Icon name={st.icon} size={17} style={{ color: st.color, marginTop: 1 }} />
            <div className="flex-1 min-w-0">
              {t.title && <div className="text-sm font-medium" style={{ color: C.textPrimary }}>{t.title}</div>}
              {t.body && <div className="text-xs mt-0.5" style={{ color: C.textSecondary }}>{t.body}</div>}
            </div>
            <button onClick={() => onDismiss(t.id)} className="opacity-50 hover:opacity-100 transition-opacity">
              <Icon name="x" size={14} style={{ color: C.textSecondary }} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

// useToasts hook
function useToasts() {
  const [toasts, setToasts] = useState([]);
  const push = (kind, title, body) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, kind, title, body }]);
    const ttl = kind === 'error' || kind === 'warning' ? 5000 : 3000;
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), ttl);
  };
  const dismiss = (id) => setToasts((t) => t.filter((x) => x.id !== id));
  return { toasts, push, dismiss };
}

// --- EmptyState -------------------------------------------------------------
function EmptyState({ icon, title, subtitle, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="flex items-center justify-center rounded-2xl mb-4" style={{ width: 56, height: 56, background: C.elevated, border: `1px solid ${C.border}` }}>
        <Icon name={icon} size={26} style={{ color: C.textMuted }} />
      </div>
      <div className="text-sm font-semibold mb-1" style={{ color: C.textPrimary }}>{title}</div>
      {subtitle && <div className="text-xs max-w-xs leading-relaxed" style={{ color: C.textMuted }}>{subtitle}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// --- Sub-tabs / segmented control -------------------------------------------
function SegTabs({ tabs, active, onChange, size = 'md' }) {
  const pad = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm';
  return (
    <div className="inline-flex rounded-lg p-0.5 gap-0.5" style={{ background: C.page, border: `1px solid ${C.border}` }}>
      {tabs.map((t) => {
        const on = active === t.key;
        return (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            className={clsx('rounded-md font-medium transition-colors flex items-center gap-1.5', pad)}
            style={{ background: on ? C.elevated : 'transparent', color: on ? C.textPrimary : C.textSecondary }}
          >
            {t.icon && <Icon name={t.icon} size={14} />}
            {t.label}
            {t.count != null && (
              <span className="text-[10px] font-mono px-1 rounded" style={{ background: on ? C.surface : 'transparent', color: C.textMuted }}>{t.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// --- Native-styled Select ---------------------------------------------------
function Select({ value, onChange, options, className, style }) {
  return (
    <div className="relative inline-flex">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={clsx('appearance-none rounded-md pl-2.5 pr-7 py-1.5 text-sm outline-none cursor-pointer', className)}
        style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textPrimary, ...style }}
      >
        {options.map((o) => <option key={o} value={o} style={{ background: C.surface }}>{o}</option>)}
      </select>
      <Icon name="chevron-down" size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: C.textMuted }} />
    </div>
  );
}

// --- Text input -------------------------------------------------------------
function TextInput({ value, onChange, placeholder, mono, className, style, onKeyDown }) {
  return (
    <input
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={onKeyDown}
      className={clsx('rounded-md px-2.5 py-1.5 text-sm outline-none focus:ring-1', mono && 'font-mono', className)}
      style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textPrimary, '--tw-ring-color': C.accent, ...style }}
    />
  );
}

Object.assign(window, {
  Icon, Card, SectionHeader, Button, StatCard, StatusBadge, ConfidenceBadge, Switch,
  EditableField, ConfirmDialog, ToastHost, useToasts, EmptyState, SegTabs, Select, TextInput,
});
