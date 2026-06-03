// ============================================================
// Screen 6 — OCR-Debug
// ============================================================
function OcrDebugScreen({ toast }) {
  const RUNS = ['template', 'ocr', 'error'];
  const [runIdx, setRunIdx] = useState(0);
  const [phase, setPhase] = useState('initial'); // initial | running | success | error
  const [steps, setSteps] = useState(initSteps());
  const [result, setResult] = useState(null); // { source, pages, kind, usedOcr }
  const [tab, setTab] = useState('felder');
  const [fileName, setFileName] = useState('');
  const timers = useRef([]);

  function initSteps() {
    return [
      { key: 'extract', label: 'Text-Extraktion', status: 'pending', text: '' },
      { key: 'match', label: 'Template-Match', status: 'pending', text: '' },
      { key: 'ocr', label: 'OCR-Fallback', status: 'pending', text: '' },
    ];
  }
  function clearTimers() { timers.current.forEach(clearTimeout); timers.current = []; }
  function at(ms, fn) { timers.current.push(setTimeout(fn, ms)); }
  function setStep(key, fields) { setSteps((s) => s.map((st) => (st.key === key ? { ...st, ...fields } : st))); }

  function clear() {
    clearTimers();
    setPhase('initial'); setSteps(initSteps()); setResult(null); setFileName('');
    toast('info', 'Geleert', 'Diagnose zurückgesetzt.');
  }

  function pickPdf() {
    clearTimers();
    const mode = RUNS[runIdx % RUNS.length];
    setRunIdx((i) => i + 1);
    const name = mode === 'template' ? 'rechnung_amazon_4412.pdf' : mode === 'ocr' ? 'scan_2026-03-18_093442.pdf' : 'schneider_elektro_fehler.pdf';
    setFileName(name);
    setPhase('running'); setSteps(initSteps()); setResult(null); setTab('felder');

    // Stage 1: text extraction
    setStep('extract', { status: 'active', text: `Lese ${name}…` });
    at(900, () => {
      const chars = mode === 'template' ? '1.842' : mode === 'ocr' ? '0' : '0';
      setStep('extract', { status: 'done', text: mode === 'template' ? `3 Seiten, 1.842 Zeichen. Prüfe Templates…` : `2 Seiten, 0 Zeichen (Bild-PDF).` });
      // Stage 2: template match
      setStep('match', { status: 'active', text: 'Vergleiche mit bekannten Mustern…' });
      at(1100, () => {
        if (mode === 'template') {
          setStep('match', { status: 'done', text: '✓ Template: Amazon EU S.à r.l. (96%)' });
          setStep('ocr', { status: 'done', text: 'Übersprungen — Template ausreichend.' });
          at(400, () => { setPhase('success'); setResult({ source: 'Template', pages: 3, kind: 'Text-PDF', usedOcr: false }); toast('success', 'Template gefunden', 'Amazon EU S.à r.l.'); });
        } else {
          setStep('match', { status: 'done', text: 'Kein Template — German-OCR läuft…' });
          // Stage 3: OCR fallback
          setStep('ocr', { status: 'active', text: 'Kein Template — German-OCR läuft… (30–120 s)' });
          at(2600, () => {
            if (mode === 'ocr') {
              setStep('ocr', { status: 'done', text: '✓ OCR abgeschlossen — 10 Felder erkannt.' });
              at(400, () => { setPhase('success'); setResult({ source: 'OCR', pages: 2, kind: 'Bild-PDF', usedOcr: true }); toast('success', 'OCR abgeschlossen', '10 Felder extrahiert.'); });
            } else {
              setStep('ocr', { status: 'error', text: '✗ OCR-Backend timeout nach 120 s.' });
              at(300, () => { setPhase('error'); toast('error', 'Pipeline fehlgeschlagen', 'OCR-Backend nicht erreichbar.'); });
            }
          });
        }
      });
    });
  }

  const ocrActive = steps.find((s) => s.key === 'ocr')?.status === 'active';

  return (
    <div>
      <SectionHeader icon="bug" title="OCR-Debug" right={
        <div className="flex items-center gap-2">
          <Button variant="primary" icon="file-search" onClick={pickPdf} disabled={phase === 'running'}>PDF auswählen</Button>
          <Button variant="ghost" icon="x" onClick={clear} disabled={phase === 'initial'}>Leeren</Button>
        </div>
      } />
      <p className="text-sm mb-4 flex items-center gap-2" style={{ color: C.textSecondary }}>
        <Icon name="arrow-right" size={14} style={{ color: C.textMuted }} />
        PDF auswählen → Pipeline läuft → Extrahierte Daten + Template-Vorschau.
      </p>

      {phase === 'initial' ? (
        <Card className="p-0"><EmptyState icon="file-search" title="Keine PDF geladen" subtitle="Wähle eine PDF, um die Extraktions-Pipeline schrittweise zu beobachten."
          action={<Button variant="primary" icon="file-search" onClick={pickPdf}>PDF auswählen</Button>} /></Card>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Stepper */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Icon name="file-text" size={14} style={{ color: C.textMuted }} />
              <span className="text-sm font-mono" style={{ color: C.textPrimary }}>{fileName}</span>
            </div>
            <div className="flex flex-col gap-0">
              {steps.map((s, i) => (
                <StepRow key={s.key} step={s} last={i === steps.length - 1} />
              ))}
            </div>
            {ocrActive && (
              <div className="mt-4 relative h-1.5 rounded-full overflow-hidden" style={{ background: C.elevated }}>
                <div className="df-bar-indeterminate" style={{ background: C.accent2 }} />
              </div>
            )}
          </Card>

          {/* Result */}
          {phase === 'error' && (
            <Card className="p-4" style={{ background: rgba(C.error, 0.06), borderColor: rgba(C.error, 0.3) }}>
              <div className="flex items-center gap-2 mb-2"><Icon name="alert-circle" size={16} style={{ color: C.error }} /><span className="text-sm font-semibold" style={{ color: C.error }}>Extraktion fehlgeschlagen</span></div>
              <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: rgba(C.error, 0.85) }}>OCRError: Backend „Ollama-GPU" nach 120s nicht erreichbar.{'\n'}  → Prüfe Ollama-Verbindung in den Einstellungen.</pre>
            </Card>
          )}

          {phase === 'success' && result && (
            <Card className="overflow-hidden">
              {/* result header */}
              <div className="flex items-center gap-3 px-4 py-3 flex-wrap" style={{ borderBottom: `1px solid ${C.border}` }}>
                <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                  style={{ background: rgba(result.source === 'Template' ? C.success : C.accent, 0.12), color: result.source === 'Template' ? C.success : C.accent, border: `1px solid ${rgba(result.source === 'Template' ? C.success : C.accent, 0.3)}` }}>
                  <Icon name={result.source === 'Template' ? 'layout-template' : 'scan-text'} size={13} />
                  Quelle: {result.source}
                </span>
                <span className="text-xs font-mono" style={{ color: C.textMuted }}>{result.pages} Seiten</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: C.elevated, color: C.textSecondary }}>{result.kind}</span>
              </div>

              {/* tabs */}
              <div className="px-4 pt-3">
                <SegTabs size="sm" active={tab} onChange={setTab} tabs={[
                  { key: 'felder', label: 'Extrahierte Felder' },
                  { key: 'template', label: 'Template-Vorschau' },
                  { key: 'pdftext', label: 'PDF-Text' },
                  ...(result.usedOcr ? [{ key: 'ocr', label: 'OCR-Output' }] : []),
                ]} />
              </div>

              <div className="p-4">
                {tab === 'felder' && (
                  <div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-2.5">
                      {OCR_FIELDS.map((f) => (
                        <div key={f.label} className="flex items-center justify-between gap-2 rounded-md px-2.5 py-2" style={{ background: C.page, border: `1px solid ${C.border}` }}>
                          <div className="min-w-0">
                            <div className="text-[11px]" style={{ color: C.textMuted }}>{f.label}</div>
                            <div className="text-sm font-mono truncate" style={{ color: C.textPrimary }}>{f.value}</div>
                          </div>
                          <ConfidenceBadge value={f.conf} />
                        </div>
                      ))}
                    </div>
                    <div className="mt-4">
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
                            {DOCUMENTS[0].positionen.map((p) => (
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
                  </div>
                )}

                {tab === 'template' && (
                  result.usedOcr ? (
                    <EmptyState icon="layout-template" title="Kein Template verwendet" subtitle="Dieses Dokument wurde per OCR-Fallback verarbeitet." />
                  ) : (
                    <pre className="rounded-lg p-3.5 text-xs font-mono overflow-auto leading-relaxed" style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textSecondary, maxHeight: 360 }}>{OCR_TEMPLATE_YAML}</pre>
                  )
                )}

                {tab === 'pdftext' && (
                  result.usedOcr ? (
                    <EmptyState icon="file-text" title="Keine Textebene" subtitle="Bild-PDF ohne eingebetteten Text — siehe OCR-Output." />
                  ) : (
                    <div>
                      <div className="text-xs font-mono mb-2" style={{ color: C.textMuted }}>{OCR_PDF_TEXT.length} Zeichen</div>
                      <textarea readOnly value={OCR_PDF_TEXT} className="w-full rounded-lg p-3.5 text-xs font-mono outline-none resize-none leading-relaxed" style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textSecondary, height: 300 }} />
                    </div>
                  )
                )}

                {tab === 'ocr' && (
                  <div>
                    <div className="text-xs font-mono mb-2" style={{ color: C.textMuted }}>German-OCR · llama3.1:8b · {result.pages} Seiten</div>
                    <textarea readOnly value={OCR_PDF_TEXT + '\n\n[OCR-Konfidenz pro Block: 0.88 / 0.91 / 0.77]'} className="w-full rounded-lg p-3.5 text-xs font-mono outline-none resize-none leading-relaxed" style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textSecondary, height: 300 }} />
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function StepRow({ step, last }) {
  const meta = {
    pending: { color: C.textMuted, icon: null, bg: C.elevated },
    active: { color: C.accent, icon: 'loader', bg: rgba(C.accent, 0.15) },
    done: { color: C.success, icon: 'check', bg: rgba(C.success, 0.15) },
    error: { color: C.error, icon: 'x', bg: rgba(C.error, 0.15) },
  }[step.status];
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="flex items-center justify-center rounded-full shrink-0" style={{ width: 26, height: 26, background: meta.bg, border: `1px solid ${rgba(meta.color, 0.3)}` }}>
          {step.status === 'active' ? <Icon name="loader" size={14} className="df-spin" style={{ color: meta.color }} />
            : meta.icon ? <Icon name={meta.icon} size={14} style={{ color: meta.color }} />
            : <span className="rounded-full" style={{ width: 6, height: 6, background: meta.color }} />}
        </div>
        {!last && <div style={{ width: 2, flex: 1, minHeight: 18, background: C.border, margin: '2px 0' }} />}
      </div>
      <div className="pb-4 min-w-0">
        <div className="text-sm font-medium" style={{ color: step.status === 'pending' ? C.textMuted : C.textPrimary }}>{step.label}</div>
        {step.text && <div className="text-xs font-mono mt-0.5" style={{ color: step.status === 'error' ? C.error : C.textMuted }}>{step.text}</div>}
      </div>
    </div>
  );
}

Object.assign(window, { OcrDebugScreen });
