// ============================================================
// Screen 1 — Eingang (Inbox)
// ============================================================
function InboxScreen({ docs, setDocs, toast }) {
  const [tab, setTab] = useState('eingang');
  const [selectedId, setSelectedId] = useState('d1');
  const [sort, setSort] = useState({ key: 'datum', dir: 'desc' });
  const [scanLabel, setScanLabel] = useState({ text: '3 neue Dokumente gefunden', busy: false });

  const inboxDocs = docs.filter((d) => d.status !== 'verarbeitet' && d.status !== 'ignoriert');
  const ignoredDocs = docs.filter((d) => d.status === 'ignoriert');
  const selected = docs.find((d) => d.id === selectedId);
  const selectedVisible = selected && selected.status !== 'verarbeitet' && selected.status !== 'ignoriert';

  // --- sorting ---
  const sorted = [...inboxDocs].sort((a, b) => {
    const k = sort.key;
    let av = a[k] ?? '', bv = b[k] ?? '';
    if (k === 'konfidenz') { av = a.konfidenz; bv = b.konfidenz; }
    if (av < bv) return sort.dir === 'asc' ? -1 : 1;
    if (av > bv) return sort.dir === 'asc' ? 1 : -1;
    return 0;
  });
  const toggleSort = (key) => setSort((s) => ({ key, dir: s.key === key && s.dir === 'asc' ? 'desc' : 'asc' }));

  // --- mutations ---
  const patch = (id, fields) => setDocs((ds) => ds.map((d) => (d.id === id ? { ...d, ...fields } : d)));

  function synthExtraction(d) {
    return {
      absender:    { value: d.absender !== '—' ? d.absender : 'Unbekannt', conf: d.konfidenz || 71 },
      datum:       { value: d.datum !== '—' ? d.datum : '2026-03-18', conf: Math.max(60, (d.konfidenz || 70) - 4) },
      rechnungsnr: { value: d.reNr !== '—' ? d.reNr : 'RG-00000', conf: Math.max(60, (d.konfidenz || 70) - 8) },
      betrag:      { value: d.betrag !== '—' ? d.betrag : '0,00 EUR', conf: Math.max(60, (d.konfidenz || 70) - 6) },
      iban:        { value: 'DE—' },
      kundennr:    { value: '—' },
      mwst:        { value: '19 %' },
      zahlungsziel:{ value: '14 Tage netto' },
      dokumenttyp: { value: 'Rechnung' },
    };
  }

  function scanFolder() {
    setScanLabel({ text: 'Scanne Ordner…', busy: true });
    setTimeout(() => {
      setScanLabel({ text: `${inboxDocs.length || 3} Dokumente im Eingang`, busy: false });
      toast('info', 'Scan abgeschlossen', 'Überwachte Ordner geprüft.');
    }, 1400);
  }

  function processAll() {
    const queue = inboxDocs.filter((d) => d.status === 'neu');
    if (!queue.length) { toast('info', 'Nichts zu verarbeiten', 'Keine neuen Dokumente im Eingang.'); return; }
    let i = 0;
    const step = () => {
      i++;
      setScanLabel({ text: `Verarbeite ${i}/${queue.length}…`, busy: true });
      const d = queue[i - 1];
      patch(d.id, { status: 'review', extraction: synthExtraction(d), positionen: d.positionen || [{ nr: 1, beschreibung: 'Position 1', menge: '1', gesamt: d.betrag !== '—' ? d.betrag : '0,00 EUR' }] });
      if (i < queue.length) setTimeout(step, 700);
      else setTimeout(() => { setScanLabel({ text: `${queue.length} Dokumente verarbeitet`, busy: false }); toast('success', 'Verarbeitung fertig', `${queue.length} Dokumente bereit zur Prüfung.`); }, 700);
    };
    setTimeout(step, 300);
  }

  function confirmSort(d) {
    patch(d.id, { status: 'verarbeitet' });
    toast('success', 'Bestätigt & sortiert', `${d.filename} → D:/Rechnungen/2026/…`);
    const next = inboxDocs.find((x) => x.id !== d.id);
    setSelectedId(next ? next.id : null);
  }
  function ignore(d) {
    patch(d.id, { status: 'ignoriert' });
    toast('info', 'Ignoriert', d.filename);
    const next = inboxDocs.find((x) => x.id !== d.id);
    setSelectedId(next ? next.id : null);
  }
  function reactivate(d) { patch(d.id, { status: 'neu' }); toast('success', 'Reaktiviert', d.filename); }
  function processOne(d) {
    setScanLabel({ text: `Verarbeite ${d.filename}…`, busy: true });
    setTimeout(() => {
      patch(d.id, { status: 'review', extraction: synthExtraction(d), positionen: [{ nr: 1, beschreibung: 'Position 1', menge: '1', gesamt: d.betrag !== '—' ? d.betrag : '0,00 EUR' }] });
      setScanLabel({ text: '1 Dokument verarbeitet', busy: false });
      toast('success', 'Verarbeitet', `${d.filename} bereit zur Prüfung.`);
    }, 1400);
  }
  function retry(d) {
    setScanLabel({ text: `Neuer Versuch: ${d.filename}…`, busy: true });
    setTimeout(() => {
      patch(d.id, { status: 'review', error: undefined, extraction: synthExtraction({ ...d, konfidenz: 74 }), positionen: [{ nr: 1, beschreibung: 'Erkannte Position', menge: '1', gesamt: '142,00 EUR' }] });
      setScanLabel({ text: 'Erneut verarbeitet', busy: false });
      toast('success', 'Erfolg', 'OCR-Fallback hat funktioniert.');
    }, 1800);
  }

  const cols = [
    { key: 'filename', label: 'Dateiname', w: '24%' },
    { key: 'status', label: 'Status', w: '110px' },
    { key: 'absender', label: 'Absender', w: '20%' },
    { key: 'datum', label: 'Datum', w: '110px' },
    { key: 'betrag', label: 'Betrag', w: '130px', right: true },
    { key: 'reNr', label: 'Re-Nr.', w: '130px' },
    { key: 'konfidenz', label: 'Konfidenz', w: '100px', right: true },
  ];

  return (
    <div>
      <SectionHeader icon="inbox" title="Eingang" right={
        <div className="flex items-center gap-2">
          <Button variant="flat" icon="search" onClick={scanFolder} disabled={scanLabel.busy}>Ordner scannen</Button>
          <Button variant="primary" icon="zap" onClick={processAll} disabled={scanLabel.busy}>Alle verarbeiten</Button>
        </div>
      } />

      <div className="flex items-center justify-between mb-3">
        <SegTabs
          active={tab}
          onChange={setTab}
          tabs={[
            { key: 'eingang', label: 'Eingang', icon: 'inbox', count: inboxDocs.length },
            { key: 'ignoriert', label: 'Ignoriert', icon: 'ban', count: ignoredDocs.length },
          ]}
        />
        <div className="flex items-center gap-2 text-xs font-mono" style={{ color: scanLabel.busy ? C.accent : C.textMuted }}>
          {scanLabel.busy && <Icon name="loader" size={13} className="df-spin" />}
          {scanLabel.text}
        </div>
      </div>

      {tab === 'eingang' ? (
        inboxDocs.length === 0 ? (
          <Card className="p-0">
            <EmptyState icon="inbox" title="Keine neuen Dokumente" subtitle="Klicke auf »Ordner scannen«, um überwachte Ordner nach neuen PDFs zu durchsuchen."
              action={<Button variant="flat" icon="search" onClick={scanFolder}>Ordner scannen</Button>} />
          </Card>
        ) : (
          <Card className="overflow-hidden p-0">
            <table className="w-full border-collapse">
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                  {cols.map((c) => (
                    <th key={c.key} onClick={() => toggleSort(c.key)}
                      className={clsx('px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider cursor-pointer select-none', c.right ? 'text-right' : 'text-left')}
                      style={{ color: C.textMuted, width: c.w }}>
                      <span className={clsx('inline-flex items-center gap-1', c.right && 'flex-row-reverse')}>
                        {c.label}
                        {sort.key === c.key && <Icon name={sort.dir === 'asc' ? 'chevron-down' : 'chevron-down'} size={12} style={{ color: C.accent, transform: sort.dir === 'asc' ? 'rotate(180deg)' : 'none' }} />}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((d) => {
                  const on = d.id === selectedId;
                  return (
                    <tr key={d.id} onClick={() => setSelectedId(d.id)}
                      className="cursor-pointer transition-colors"
                      style={{ borderBottom: `1px solid ${C.border}`, background: on ? rgba(C.accent, 0.1) : 'transparent', boxShadow: on ? `inset 2px 0 0 ${C.accent}` : 'none' }}
                      onMouseEnter={(e) => { if (!on) e.currentTarget.style.background = 'rgba(255,255,255,0.025)'; }}
                      onMouseLeave={(e) => { if (!on) e.currentTarget.style.background = 'transparent'; }}>
                      <td className="px-3 py-2.5 text-sm font-semibold truncate" style={{ color: C.textPrimary, maxWidth: 0 }}>
                        <span className="flex items-center gap-2"><Icon name="file-text" size={14} style={{ color: C.textMuted }} className="shrink-0" /><span className="truncate">{d.filename}</span></span>
                      </td>
                      <td className="px-3 py-2.5"><StatusBadge status={d.status} /></td>
                      <td className="px-3 py-2.5 text-sm truncate" style={{ color: C.textSecondary, maxWidth: 0 }}>{d.absender}</td>
                      <td className="px-3 py-2.5 text-sm font-mono" style={{ color: C.textSecondary }}>{d.datum}</td>
                      <td className="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style={{ color: d.betrag.startsWith('−') ? C.error : C.textPrimary }}>{d.betrag}</td>
                      <td className="px-3 py-2.5 text-sm font-mono" style={{ color: C.textSecondary }}>{d.reNr}</td>
                      <td className="px-3 py-2.5 text-right">{d.konfidenz > 0 ? <ConfidenceBadge value={d.konfidenz} /> : <span className="text-xs font-mono" style={{ color: C.textMuted }}>—</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        )
      ) : (
        ignoredDocs.length === 0 ? (
          <Card className="p-0"><EmptyState icon="ban" title="Keine ignorierten Dokumente" subtitle="Dokumente, die du ignorierst, landen hier und können jederzeit reaktiviert werden." /></Card>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {ignoredDocs.map((d) => (
              <Card key={d.id} className="p-4 flex items-center gap-3">
                <div className="flex items-center justify-center rounded-lg shrink-0" style={{ width: 38, height: 38, background: C.elevated }}>
                  <Icon name="file-text" size={18} style={{ color: C.textMuted }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate" style={{ color: C.textPrimary }}>{d.filename}</div>
                  <div className="text-xs font-mono mt-0.5" style={{ color: C.textMuted }}>{d.datum}</div>
                </div>
                <Button variant="flat" size="sm" icon="rotate-ccw" onClick={() => reactivate(d)}>Reaktivieren</Button>
              </Card>
            ))}
          </div>
        )
      )}

      {/* Detail / Review panel */}
      {tab === 'eingang' && selectedVisible && (
        <ReviewPanel
          key={selected.id}
          doc={selected}
          onPatch={patch}
          onConfirm={() => confirmSort(selected)}
          onIgnore={() => ignore(selected)}
          onClose={() => setSelectedId(null)}
          onProcess={() => processOne(selected)}
          onRetry={() => retry(selected)}
          toast={toast}
        />
      )}
    </div>
  );
}

// --- Review panel (3 variants) ---------------------------------------------
function ReviewPanel({ doc, onPatch, onConfirm, onIgnore, onClose, onProcess, onRetry, toast }) {
  const variant = doc.status === 'fehler' ? 'error' : doc.extraction ? 'extraction' : 'unprocessed';

  const editField = (k, v) => {
    onPatch(doc.id, { extraction: { ...doc.extraction, [k]: { ...doc.extraction[k], value: v } } });
    toast('success', 'Feld aktualisiert', `${k}: ${v}`);
  };

  return (
    <Card className="mt-4 df-fade-in overflow-hidden">
      {/* header */}
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${C.border}`, background: 'rgba(0,0,0,0.15)' }}>
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <Icon name="file-text" size={16} style={{ color: C.accent }} />
            <span className="text-sm font-semibold" style={{ color: C.textPrimary }}>{doc.filename}</span>
            <StatusBadge status={doc.status} />
          </div>
          <div className="text-xs font-mono mt-1 ml-6 truncate" style={{ color: C.textMuted }}>{doc.path}</div>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-md hover:bg-white/5"><Icon name="x" size={16} style={{ color: C.textSecondary }} /></button>
      </div>

      <div className="p-4">
        {variant === 'unprocessed' && (
          <div className="flex flex-col items-center text-center py-6">
            <Icon name="file-search" size={26} style={{ color: C.textMuted }} className="mb-3" />
            <div className="text-sm font-medium mb-1" style={{ color: C.textPrimary }}>Noch nicht verarbeitet</div>
            <div className="text-xs mb-4" style={{ color: C.textMuted }}>Starte die Extraktion, um Felder zu erkennen.</div>
            <div className="flex gap-2">
              <Button variant="primary" icon="zap" onClick={onProcess}>Jetzt verarbeiten</Button>
              <Button variant="ghost" icon="ban" onClick={onIgnore}>Ignorieren</Button>
            </div>
          </div>
        )}

        {variant === 'error' && (
          <div>
            <div className="rounded-lg p-4 mb-4" style={{ background: rgba(C.error, 0.08), border: `1px solid ${rgba(C.error, 0.3)}` }}>
              <div className="flex items-center gap-2 mb-2">
                <Icon name="alert-circle" size={16} style={{ color: C.error }} />
                <span className="text-sm font-semibold" style={{ color: C.error }}>Verarbeitung fehlgeschlagen</span>
              </div>
              <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed" style={{ color: rgba(C.error, 0.85) }}>{doc.error}</pre>
            </div>
            <div className="flex gap-2">
              <Button variant="amber" icon="rotate-cw" onClick={onRetry}>Nochmal versuchen</Button>
              <Button variant="ghost" icon="ban" onClick={onIgnore}>Ignorieren</Button>
            </div>
          </div>
        )}

        {variant === 'extraction' && (
          <div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
              <EditableField label="Absender" value={doc.extraction.absender.value} confidence={doc.extraction.absender.conf} onSave={(v) => editField('absender', v)} />
              <EditableField label="Datum" value={doc.extraction.datum.value} confidence={doc.extraction.datum.conf} mono onSave={(v) => editField('datum', v)} />
              <EditableField label="Rechnungsnr." value={doc.extraction.rechnungsnr.value} confidence={doc.extraction.rechnungsnr.conf} mono onSave={(v) => editField('rechnungsnr', v)} />
              <EditableField label="Betrag" value={doc.extraction.betrag.value} confidence={doc.extraction.betrag.conf} mono onSave={(v) => editField('betrag', v)} />
              <EditableField label="IBAN" value={doc.extraction.iban.value} mono onSave={(v) => editField('iban', v)} />
              <EditableField label="Kundennr." value={doc.extraction.kundennr.value} mono onSave={(v) => editField('kundennr', v)} />
              <EditableField label="MwSt-Satz" value={doc.extraction.mwst.value} readOnly />
              <EditableField label="Zahlungsziel" value={doc.extraction.zahlungsziel.value} readOnly />
              <EditableField label="Dokumenttyp" value={doc.extraction.dokumenttyp.value} readOnly />
            </div>

            {doc.positionen && doc.positionen.length > 0 && (
              <div className="mt-5">
                <div className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: C.textMuted }}>Positionen</div>
                <div className="rounded-lg overflow-hidden" style={{ border: `1px solid ${C.border}` }}>
                  <table className="w-full">
                    <thead><tr style={{ background: 'rgba(0,0,0,0.2)' }}>
                      <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: C.textMuted, width: 40 }}>#</th>
                      <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: C.textMuted }}>Beschreibung</th>
                      <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style={{ color: C.textMuted, width: 80 }}>Menge</th>
                      <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style={{ color: C.textMuted, width: 130 }}>Gesamt</th>
                    </tr></thead>
                    <tbody>
                      {doc.positionen.map((p) => (
                        <tr key={p.nr} style={{ borderTop: `1px solid ${C.border}` }}>
                          <td className="px-3 py-2 text-sm font-mono" style={{ color: C.textMuted }}>{p.nr}</td>
                          <td className="px-3 py-2 text-sm" style={{ color: C.textPrimary }}>{p.beschreibung}</td>
                          <td className="px-3 py-2 text-sm font-mono text-right" style={{ color: C.textSecondary }}>{p.menge}</td>
                          <td className="px-3 py-2 text-sm font-mono text-right tabular-nums" style={{ color: C.textPrimary }}>{p.gesamt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 mt-5">
              <Button variant="success" icon="check-circle" onClick={onConfirm}>Bestätigen &amp; Sortieren</Button>
              <Button variant="ghost" icon="ban" onClick={onIgnore}>Ignorieren</Button>
              <Button variant="ghost" icon="x" onClick={onClose}>Schließen</Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

Object.assign(window, { InboxScreen });
