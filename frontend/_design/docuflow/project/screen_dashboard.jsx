// ============================================================
// Screen 2 — Dashboard
// ============================================================
const ACTION_ICON = {
  scan: { icon: 'search', color: C.info },
  template: { icon: 'layout-template', color: C.accent },
  ocr: { icon: 'scan-text', color: C.accent2 },
  sortiert: { icon: 'check-circle', color: C.success },
  'auto-sortiert': { icon: 'zap', color: C.success },
  bestätigt: { icon: 'thumbs-up', color: C.success },
  fehler: { icon: 'alert-circle', color: C.error },
  'template-erstellt': { icon: 'wand-2', color: C.accent },
  undo: { icon: 'undo', color: C.muted },
  korrektur: { icon: 'pencil', color: C.warning },
  reaktiviert: { icon: 'rotate-ccw', color: C.info },
  ignoriert: { icon: 'ban', color: C.muted },
};

function DashboardScreen({ docs, log, setLog, toast }) {
  const [period, setPeriod] = useState('heute');

  const counts = {
    neu: docs.filter((d) => d.status === 'neu').length,
    review: docs.filter((d) => d.status === 'review').length,
    verarbeitet: docs.filter((d) => d.status === 'verarbeitet').length,
    total: docs.length,
  };

  const periodRank = { heute: 0, woche: 1, alles: 2 };
  const filteredLog = log.filter((e) => periodRank[e.period] <= periodRank[period]);
  const errors = log.filter((e) => e.type === 'fehler');

  function undo(entry) {
    setLog((l) => l.map((e) => (e.id === entry.id ? { ...e, undoable: false, type: 'undo', details: 'Sortierung rückgängig gemacht' } : e)));
    toast('info', 'Rückgängig gemacht', entry.filename);
  }

  return (
    <div>
      <SectionHeader icon="layout-dashboard" title="Dashboard" />

      {/* StatCards */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <StatCard label="Neu / Inbox" value={counts.neu} icon="inbox" color={C.accent} />
        <StatCard label="Im Review" value={counts.review} icon="pencil" color={C.warning} />
        <StatCard label="Verarbeitet" value={counts.verarbeitet} icon="check-circle" color={C.success} />
        <StatCard label="Gesamt" value={counts.total} icon="database" color={C.muted} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Sorted documents */}
        <Card className="p-0 overflow-hidden">
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: `1px solid ${C.border}` }}>
            <Icon name="check-circle" size={15} style={{ color: C.success }} />
            <span className="text-sm font-semibold" style={{ color: C.textPrimary }}>Sortierte Dokumente</span>
          </div>
          {SORTED_DOCS.length === 0 ? (
            <EmptyState icon="box" title="Noch keine sortierten Dokumente" subtitle="Bestätigte Dokumente erscheinen hier mit Zielpfad." />
          ) : (
            <div className="overflow-auto" style={{ maxHeight: 360 }}>
              <table className="w-full">
                <thead className="sticky top-0" style={{ background: C.surface }}>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {['Datei', 'Absender', 'Datum', 'Betrag', 'Sortiert nach', 'Verarbeitet'].map((h, i) => (
                      <th key={h} className={clsx('px-3 py-2 text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap', i === 3 ? 'text-right' : 'text-left')} style={{ color: C.textMuted }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SORTED_DOCS.map((d, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}` }}>
                      <td className="px-3 py-2 text-sm font-mono truncate" style={{ color: C.textPrimary, maxWidth: 140 }}>{d.filename}</td>
                      <td className="px-3 py-2 text-sm truncate" style={{ color: C.textSecondary, maxWidth: 120 }}>{d.absender}</td>
                      <td className="px-3 py-2 text-sm font-mono whitespace-nowrap" style={{ color: C.textSecondary }}>{d.datum}</td>
                      <td className="px-3 py-2 text-sm font-mono text-right tabular-nums whitespace-nowrap" style={{ color: C.textPrimary }}>{d.betrag}</td>
                      <td className="px-3 py-2 text-xs font-mono truncate" style={{ color: C.info, maxWidth: 150 }}>{d.sortedTo}</td>
                      <td className="px-3 py-2 text-xs font-mono whitespace-nowrap" style={{ color: C.textMuted }}>{d.processedAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Activity log */}
        <Card className="p-0 overflow-hidden flex flex-col">
          <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-2">
              <Icon name="list-filter" size={15} style={{ color: C.accent }} />
              <span className="text-sm font-semibold" style={{ color: C.textPrimary }}>Aktivitäts-Log</span>
            </div>
            <SegTabs size="sm" active={period} onChange={setPeriod} tabs={[
              { key: 'heute', label: 'Heute' }, { key: 'woche', label: 'Woche' }, { key: 'alles', label: 'Alles' },
            ]} />
          </div>
          {filteredLog.length === 0 ? (
            <div className="py-12 text-center text-sm italic" style={{ color: C.textMuted }}>Keine Aktivitäten im Zeitraum</div>
          ) : (
            <div className="overflow-auto divide-y" style={{ maxHeight: 360, '--tw-divide-opacity': 1 }}>
              {filteredLog.map((e) => {
                const a = ACTION_ICON[e.type] || ACTION_ICON.scan;
                return (
                  <div key={e.id} className="flex items-start gap-3 px-4 py-2.5" style={{ borderTop: `1px solid ${C.border}` }}>
                    <div className="flex items-center justify-center rounded-md shrink-0 mt-0.5" style={{ width: 26, height: 26, background: rgba(a.color, 0.12) }}>
                      <Icon name={a.icon} size={14} style={{ color: a.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate" style={{ color: C.textPrimary }}>{e.filename}</div>
                      <div className="text-xs mt-0.5" style={{ color: C.textMuted }}>{e.details}</div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className="text-xs font-mono whitespace-nowrap" style={{ color: C.textMuted }}>{e.time}</span>
                      {e.undoable && <button onClick={() => undo(e)} className="text-xs flex items-center gap-1 hover:underline" style={{ color: C.accent }}><Icon name="undo" size={12} />Undo</button>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Error log card (only if errors) */}
      {errors.length > 0 && (
        <Card className="mt-4 p-0 overflow-hidden" style={{ borderColor: rgba(C.error, 0.3), background: rgba(C.error, 0.05) }}>
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: `1px solid ${rgba(C.error, 0.2)}` }}>
            <Icon name="alert-circle" size={15} style={{ color: C.error }} />
            <span className="text-sm font-semibold" style={{ color: C.error }}>Fehler-Log</span>
            <span className="text-xs font-mono px-1.5 py-0.5 rounded" style={{ background: rgba(C.error, 0.15), color: C.error }}>{errors.length}</span>
          </div>
          <div>
            {errors.map((e) => (
              <div key={e.id} className="flex items-center justify-between px-4 py-2.5" style={{ borderTop: `1px solid ${rgba(C.error, 0.12)}` }}>
                <div className="min-w-0">
                  <div className="text-sm font-mono truncate" style={{ color: C.textPrimary }}>{e.filename}</div>
                  <div className="text-xs mt-0.5" style={{ color: rgba(C.error, 0.8) }}>{e.details}</div>
                </div>
                <span className="text-xs font-mono shrink-0" style={{ color: C.textMuted }}>{e.time}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

Object.assign(window, { DashboardScreen });
