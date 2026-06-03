// ============================================================
// Screen 4 — Sortier-Regeln (visueller Editor)
// ============================================================
const PREVIEW_DATA = {
  '{absender}': 'Amazon', '{datum}': '2026-03-15', '{jahr}': '2026', '{monat}': '03',
  '{tag}': '15', '{rechnungsnr}': 'INV-12345', '{betrag}': '1234,56', '{typ}': 'Rechnung', '{waehrung}': 'EUR',
};
function resolve(part) { return PREVIEW_DATA[part] || part; }

function RulesScreen({ toast }) {
  const [rules, setRules] = useState(RULES);
  const [openSections, setOpenSections] = useState(() => {
    const o = {}; RULES.forEach((r) => { o[r.id] = { wann: true, wohin: false, wie: false }; }); return o;
  });
  const [dragId, setDragId] = useState(null);
  const [overId, setOverId] = useState(null);
  const [confirm, setConfirm] = useState(null);

  const update = (id, fields) => setRules((rs) => rs.map((r) => (r.id === id ? { ...r, ...fields } : r)));
  const toggleSection = (id, key) => setOpenSections((o) => ({ ...o, [id]: { ...o[id], [key]: !o[id][key] } }));

  function addRule() {
    const id = 'r' + Date.now();
    setRules((rs) => [...rs, { id, name: 'Neue Regel', enabled: true, conditions: [{ logic: 'WENN', field: 'Absender', operator: 'enthält', value: '' }], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}'], nameParts: ['{datum}'] }]);
    setOpenSections((o) => ({ ...o, [id]: { wann: true, wohin: true, wie: true } }));
    toast('success', 'Regel hinzugefügt', 'Neue Regel ans Ende gestellt.');
  }
  function deleteRule() { setRules((rs) => rs.filter((r) => r.id !== confirm.id)); setConfirm(null); toast('info', 'Regel gelöscht', confirm.name); }

  // drag reorder
  function onDrop(targetId) {
    if (!dragId || dragId === targetId) { setDragId(null); setOverId(null); return; }
    setRules((rs) => {
      const from = rs.findIndex((r) => r.id === dragId);
      const to = rs.findIndex((r) => r.id === targetId);
      const next = [...rs];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
    setDragId(null); setOverId(null);
    toast('info', 'Reihenfolge geändert', 'Regeln werden von oben nach unten geprüft.');
  }

  return (
    <div>
      <SectionHeader icon="list-filter" title="Sortier-Regeln" right={<Button variant="primary" icon="plus" onClick={addRule}>Neue Regel</Button>} />
      <p className="text-sm mb-4 flex items-center gap-2" style={{ color: C.textSecondary }}>
        <Icon name="arrow-right" size={14} style={{ color: C.textMuted }} />
        Regeln werden von oben nach unten geprüft. Erste passende gewinnt.
      </p>

      {rules.length === 0 ? (
        <Card className="p-0"><EmptyState icon="list-filter" title="Keine Regeln vorhanden" subtitle="Lege Regeln an, um Dokumente automatisch in Zielordner zu sortieren."
          action={<Button variant="primary" icon="plus" onClick={addRule}>Neue Regel</Button>} /></Card>
      ) : (
        <div className="flex flex-col gap-4">
          {rules.map((rule, idx) => (
            <RuleCard
              key={rule.id}
              rule={rule}
              index={idx + 1}
              sections={openSections[rule.id]}
              isDragging={dragId === rule.id}
              isOver={overId === rule.id && dragId !== rule.id}
              onUpdate={(f) => update(rule.id, f)}
              onToggle={(k) => toggleSection(rule.id, k)}
              onDelete={() => setConfirm(rule)}
              onDragStart={() => setDragId(rule.id)}
              onDragEnter={() => setOverId(rule.id)}
              onDragEnd={() => { setDragId(null); setOverId(null); }}
              onDrop={() => onDrop(rule.id)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog open={!!confirm} title="Regel löschen?" body={confirm ? `Die Regel „${confirm.name}" wird dauerhaft entfernt.` : ''} confirmLabel="Löschen" danger onConfirm={deleteRule} onCancel={() => setConfirm(null)} />
    </div>
  );
}

// --- RuleCard ---------------------------------------------------------------
function RuleCard({ rule, index, sections, isDragging, isOver, onUpdate, onToggle, onDelete, onDragStart, onDragEnter, onDragEnd, onDrop }) {
  const [grabbable, setGrabbable] = useState(false);

  const previewPath = rule.baseFolder + '/' + rule.subfolders.map(resolve).join('/') + '/' + rule.nameParts.map(resolve).join('_') + '.pdf';

  // condition helpers
  const setCond = (i, f) => onUpdate({ conditions: rule.conditions.map((c, j) => (j === i ? { ...c, ...f } : c)) });
  const addCond = () => onUpdate({ conditions: [...rule.conditions, { logic: 'UND', field: 'Absender', operator: 'enthält', value: '' }] });
  const rmCond = (i) => onUpdate({ conditions: rule.conditions.filter((_, j) => j !== i) });
  const setSub = (i, v) => onUpdate({ subfolders: rule.subfolders.map((s, j) => (j === i ? v : s)) });
  const addSub = () => onUpdate({ subfolders: [...rule.subfolders, '{absender}'] });
  const rmSub = (i) => onUpdate({ subfolders: rule.subfolders.filter((_, j) => j !== i) });
  const setName = (i, v) => onUpdate({ nameParts: rule.nameParts.map((s, j) => (j === i ? v : s)) });
  const addName = () => onUpdate({ nameParts: [...rule.nameParts, '{rechnungsnr}'] });
  const rmName = (i) => onUpdate({ nameParts: rule.nameParts.filter((_, j) => j !== i) });

  return (
    <div
      draggable={grabbable}
      onDragStart={onDragStart}
      onDragEnter={onDragEnter}
      onDragOver={(e) => e.preventDefault()}
      onDragEnd={() => { setGrabbable(false); onDragEnd(); }}
      onDrop={onDrop}
      className="rounded-xl transition-all"
      style={{
        background: C.surface,
        border: `1px solid ${isOver ? C.accent : C.border}`,
        opacity: isDragging ? 0.4 : 1,
        boxShadow: isOver ? `0 0 0 1px ${C.accent}` : 'none',
      }}
    >
      {/* header */}
      <div className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: sections && (sections.wann || sections.wohin || sections.wie) ? `1px solid ${C.border}` : 'none' }}>
        <div
          onMouseDown={() => setGrabbable(true)}
          onMouseUp={() => setGrabbable(false)}
          title="Ziehen zum Sortieren"
          className="cursor-grab active:cursor-grabbing p-1 -ml-1 rounded hover:bg-white/5"
          style={{ color: C.textMuted }}
        >
          <Icon name="grip-vertical" size={16} />
        </div>
        <span className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0" style={{ background: C.elevated, color: C.textMuted }}>#{index}</span>
        <input
          value={rule.name}
          onChange={(e) => onUpdate({ name: e.target.value })}
          className="flex-1 min-w-0 bg-transparent text-sm font-semibold outline-none rounded px-1 py-0.5 focus:bg-black/20"
          style={{ color: C.textPrimary }}
        />
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs" style={{ color: C.textMuted }}>Aktiv</span>
            <Switch checked={rule.enabled} onChange={(v) => onUpdate({ enabled: v })} />
          </div>
          <button onClick={onDelete} title="Regel löschen" className="p-1.5 rounded-md hover:bg-white/5" style={{ color: C.error }}><Icon name="trash" size={15} /></button>
        </div>
      </div>

      {/* WANN */}
      <RuleSection label="WANN — Bedingungen" open={sections.wann} onToggle={() => onToggle('wann')}>
        {rule.conditions.length === 0 ? (
          <div className="text-xs italic px-1 py-2" style={{ color: C.textMuted }}>Keine Bedingungen = Fallback-Regel (passt immer)</div>
        ) : (
          <div className="flex flex-col gap-2">
            {rule.conditions.map((c, i) => (
              <div key={i} className="flex items-center gap-2 flex-wrap">
                {i === 0 ? (
                  <span className="text-xs font-mono font-semibold px-2 py-1.5" style={{ color: C.accent }}>WENN</span>
                ) : (
                  <Select value={c.logic} onChange={(v) => setCond(i, { logic: v })} options={RULE_LOGIC} style={{ width: 80 }} />
                )}
                <Select value={c.field} onChange={(v) => setCond(i, { field: v })} options={RULE_FIELDS} />
                <Select value={c.operator} onChange={(v) => setCond(i, { operator: v })} options={RULE_OPERATORS} />
                <TextInput value={c.value} onChange={(v) => setCond(i, { value: v })} placeholder="Wert…" className="flex-1 min-w-[120px]" />
                <button onClick={() => rmCond(i)} className="p-1.5 rounded-md hover:bg-white/5" style={{ color: C.textMuted }}><Icon name="x" size={15} /></button>
              </div>
            ))}
          </div>
        )}
        <button onClick={addCond} className="mt-2 text-xs flex items-center gap-1.5 hover:underline" style={{ color: C.accent }}><Icon name="plus" size={13} />Bedingung</button>
      </RuleSection>

      {/* WOHIN */}
      <RuleSection label="WOHIN — Zielordner" open={sections.wohin} onToggle={() => onToggle('wohin')}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs w-20 shrink-0" style={{ color: C.textMuted }}>Basis-Ordner</span>
          <TextInput value={rule.baseFolder} onChange={(v) => onUpdate({ baseFolder: v })} mono className="flex-1" />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs w-20 shrink-0" style={{ color: C.textMuted }}>Unterordner</span>
          {rule.subfolders.map((s, i) => (
            <div key={i} className="flex items-center">
              <Select value={s} onChange={(v) => setSub(i, v)} options={SUBFOLDER_OPTIONS} />
              <button onClick={() => rmSub(i)} className="p-1 rounded hover:bg-white/5" style={{ color: C.textMuted }}><Icon name="x" size={13} /></button>
              {i < rule.subfolders.length - 1 && <span className="font-mono mx-0.5" style={{ color: C.textMuted }}>/</span>}
            </div>
          ))}
          <button onClick={addSub} className="text-xs flex items-center gap-1 px-2 py-1.5 rounded-md hover:bg-white/5" style={{ color: C.accent }}><Icon name="plus" size={13} />Hinzufügen</button>
        </div>
      </RuleSection>

      {/* WIE BENENNEN */}
      <RuleSection label="WIE BENENNEN — Dateiname" open={sections.wie} onToggle={() => onToggle('wie')}>
        <div className="flex items-center gap-1.5 flex-wrap">
          {rule.nameParts.map((s, i) => (
            <div key={i} className="flex items-center">
              <Select value={s} onChange={(v) => setName(i, v)} options={PLACEHOLDERS} />
              <button onClick={() => rmName(i)} className="p-1 rounded hover:bg-white/5" style={{ color: C.textMuted }}><Icon name="x" size={13} /></button>
              {i < rule.nameParts.length - 1 && <span className="font-mono mx-0.5" style={{ color: C.textMuted }}>_</span>}
            </div>
          ))}
          <span className="font-mono text-sm px-1" style={{ color: C.textMuted }}>.pdf</span>
          <button onClick={addName} className="text-xs flex items-center gap-1 px-2 py-1.5 rounded-md hover:bg-white/5" style={{ color: C.accent }}><Icon name="plus" size={13} />Baustein</button>
        </div>
      </RuleSection>

      {/* live preview */}
      <div className="px-4 py-2.5 flex items-center gap-2" style={{ borderTop: `1px solid ${C.border}`, background: 'rgba(0,0,0,0.15)' }}>
        <Icon name="corner-down-right" size={13} style={{ color: C.textMuted }} className="shrink-0" />
        <span className="text-xs font-mono italic truncate" style={{ color: C.info }}>{previewPath}</span>
      </div>
    </div>
  );
}

function RuleSection({ label, open, onToggle, children }) {
  return (
    <div style={{ borderBottom: `1px solid ${C.border}` }}>
      <button onClick={onToggle} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/[0.02]">
        <Icon name={open ? 'chevron-down' : 'chevron-right'} size={14} style={{ color: C.textMuted }} />
        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: C.textSecondary }}>{label}</span>
      </button>
      {open && <div className="px-4 pb-3.5 pt-0.5 df-fade-in">{children}</div>}
    </div>
  );
}

Object.assign(window, { RulesScreen });
