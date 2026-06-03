// ============================================================
// Screen 3 — Templates
// ============================================================
function TemplatesScreen({ toast }) {
  const [rows, setRows] = useState(TEMPLATES);
  const [editId, setEditId] = useState(null);
  const [draft, setDraft] = useState(null);
  const [confirm, setConfirm] = useState(null);
  const [reloading, setReloading] = useState(false);

  function startEdit(t) { setEditId(t.id); setDraft({ ...t }); }
  function saveEdit() {
    setRows((rs) => rs.map((r) => (r.id === editId ? draft : r)));
    setEditId(null);
    toast('success', 'Template gespeichert', draft.absender);
  }
  function reload() {
    setReloading(true);
    setTimeout(() => { setReloading(false); toast('info', 'Templates neu geladen', `${rows.length} Muster aktualisiert.`); }, 1200);
  }
  function doDelete() {
    setRows((rs) => rs.filter((r) => r.id !== confirm.id));
    toast('info', 'Template gelöscht', confirm.absender);
    setConfirm(null);
  }

  const headers = [
    { label: 'Absender' }, { label: 'Muster', right: true }, { label: 'Felder', right: true },
    { label: 'Schwelle', right: true }, { label: 'Verwendet', right: true }, { label: 'ID' }, { label: '', w: 90 },
  ];

  return (
    <div>
      <SectionHeader icon="wand-2" title="Templates" right={
        <Button variant="flat" icon="refresh-cw" onClick={reload} disabled={reloading}>
          {reloading ? <span className="flex items-center gap-2"><Icon name="loader" size={14} className="df-spin" />Lädt…</span> : 'Templates neu laden'}
        </Button>
      } />

      <p className="text-sm mb-4" style={{ color: C.textSecondary }}>Automatisch generierte Muster für bekannte Absender.</p>

      {rows.length === 0 ? (
        <Card className="p-0"><EmptyState icon="wand-2" title="Keine Templates vorhanden" subtitle="Templates werden automatisch erstellt, wenn Dokumente bestätigt werden." /></Card>
      ) : (
        <Card className="overflow-hidden p-0">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {headers.map((h, i) => (
                  <th key={i} className={clsx('px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider', h.right ? 'text-right' : 'text-left')} style={{ color: C.textMuted, width: h.w }}>{h.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => {
                const editing = editId === t.id;
                return (
                  <tr key={t.id} style={{ borderBottom: `1px solid ${C.border}` }}>
                    <td className="px-3 py-2.5 text-sm font-semibold" style={{ color: C.textPrimary }}>
                      {editing ? <TextInput value={draft.absender} onChange={(v) => setDraft({ ...draft, absender: v })} className="w-full" /> : t.absender}
                    </td>
                    <td className="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style={{ color: C.textSecondary }}>{t.muster}</td>
                    <td className="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style={{ color: C.textSecondary }}>{t.felder}</td>
                    <td className="px-3 py-2.5 text-right">
                      {editing ? (
                        <input type="number" value={draft.schwelle} onChange={(v) => setDraft({ ...draft, schwelle: +v.target.value })} className="w-16 rounded-md px-2 py-1 text-sm font-mono text-right outline-none" style={{ background: C.page, border: `1px solid ${C.accent}`, color: C.textPrimary }} />
                      ) : <span className="text-sm font-mono tabular-nums" style={{ color: C.textSecondary }}>{t.schwelle}%</span>}
                    </td>
                    <td className="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style={{ color: C.textSecondary }}>{t.verwendet}</td>
                    <td className="px-3 py-2.5 text-xs font-mono" style={{ color: rgba(C.textMuted, 0.6) }}>{t.id}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        {editing ? (
                          <>
                            <button onClick={saveEdit} title="Speichern" className="p-1.5 rounded-md" style={{ background: rgba(C.success, 0.14), color: C.success }}><Icon name="check" size={14} /></button>
                            <button onClick={() => setEditId(null)} title="Abbrechen" className="p-1.5 rounded-md" style={{ background: C.elevated, color: C.textSecondary }}><Icon name="x" size={14} /></button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => startEdit(t)} title="Bearbeiten" className="p-1.5 rounded-md hover:bg-white/5" style={{ color: C.textSecondary }}><Icon name="pencil" size={14} /></button>
                            <button onClick={() => setConfirm(t)} title="Löschen" className="p-1.5 rounded-md hover:bg-white/5" style={{ color: C.error }}><Icon name="trash" size={14} /></button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}

      <ConfirmDialog
        open={!!confirm}
        title="Template löschen?"
        body={confirm ? `Das Template „${confirm.absender}" wird entfernt. Bereits sortierte Dokumente bleiben unverändert.` : ''}
        confirmLabel="Löschen"
        danger
        onConfirm={doDelete}
        onCancel={() => setConfirm(null)}
      />
    </div>
  );
}

Object.assign(window, { TemplatesScreen });
