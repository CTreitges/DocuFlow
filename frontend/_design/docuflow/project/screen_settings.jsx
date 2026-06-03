// ============================================================
// Screen 5 — Einstellungen
// ============================================================
function SettingCard({ title, badge, badgeColor, right, icon, iconColor, children }) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
        <div className="flex items-center gap-2">
          {icon && <Icon name={icon} size={15} style={{ color: iconColor || C.accent }} />}
          <span className="text-sm font-semibold" style={{ color: C.textPrimary }}>{title}</span>
          {badge && <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded" style={{ background: rgba(badgeColor, 0.14), color: badgeColor, border: `1px solid ${rgba(badgeColor, 0.3)}` }}>{badge}</span>}
        </div>
        {right}
      </div>
      <div className="p-4">{children}</div>
    </Card>
  );
}

function StatusDot({ color, pulse }) {
  return <span className={clsx('inline-block rounded-full', pulse && 'df-pulse-dot')} style={{ width: 8, height: 8, background: color }} />;
}

function SettingsScreen({ toast }) {
  const [watchdog, setWatchdog] = useState(true);
  const [autoSort, setAutoSort] = useState(true);
  const [threshold, setThreshold] = useState(85);
  const [folders, setFolders] = useState(INPUT_FOLDERS);
  const [outputFolder, setOutputFolder] = useState('D:/Rechnungen');
  const [confirmReset, setConfirmReset] = useState(false);

  // OCR state machine: 'not-installed' | 'installed' | 'loaded'
  const [ocrEnabled, setOcrEnabled] = useState(true);
  const [ocrStatus, setOcrStatus] = useState('installed');
  const [ocrBackend, setOcrBackend] = useState('Ollama-GPU');
  const [installing, setInstalling] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const [log, setLog] = useState(['$ docuflow ocr status', 'german-ocr v2.3 erkannt — Modell nicht geladen']);
  const logRef = useRef(null);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [log]);

  // Ollama
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3.1:8b');
  const [ollamaTimeout, setOllamaTimeout] = useState(120);
  const [ollamaConn, setOllamaConn] = useState('connected'); // 'idle' | 'checking' | 'connected' | 'offline'

  const warnFolders = folders.filter((f) => f.active && !f.exists);
  const activeCount = folders.filter((f) => f.active).length;

  function appendLog(lines, done) {
    let i = 0;
    const tick = () => {
      setLog((l) => [...l, lines[i]]);
      i++;
      if (i < lines.length) setTimeout(tick, 550);
      else done && done();
    };
    tick();
  }

  function runOcrAction() {
    if (ocrStatus === 'not-installed') {
      setInstalling(true); setShowLog(true);
      appendLog(['$ pip install german-ocr==2.3', 'Downloading wheels… 142 MB', 'Installiere Abhängigkeiten…', '✓ german-ocr installiert'], () => { setInstalling(false); setOcrStatus('installed'); toast('success', 'OCR installiert', 'Modell kann jetzt geladen werden.'); });
    } else if (ocrStatus === 'installed') {
      setInstalling(true); setShowLog(true);
      appendLog([`$ ollama pull ${ollamaModel}`, 'pulling manifest…', 'pulling model layers… 4.7 GB', 'verifying sha256…', '✓ Modell geladen — Backend aktiv'], () => { setInstalling(false); setOcrStatus('loaded'); toast('success', 'Modell geladen', 'German-OCR ist aktiv.'); });
    } else {
      setOcrStatus('installed'); toast('info', 'Modell entladen', 'GPU-Speicher freigegeben.');
    }
  }

  const ocrStatusMeta = {
    'not-installed': { label: 'Nicht installiert', color: C.error, action: 'Installieren', actionIcon: 'play' },
    'installed': { label: 'Installiert · Modell nicht geladen', color: C.warning, action: 'Modell laden', actionIcon: 'play' },
    'loaded': { label: 'Geladen · Aktiv', color: C.success, action: 'Modell entladen', actionIcon: 'x' },
  }[ocrStatus];

  function testOllama() {
    setOllamaConn('checking');
    setTimeout(() => { setOllamaConn('connected'); toast('success', 'Verbindung OK', `${ollamaUrl} erreichbar.`); }, 1300);
  }
  const ollamaMeta = {
    idle: { label: 'Nicht geprüft', color: C.muted },
    checking: { label: 'Prüfe…', color: C.warning },
    connected: { label: 'Verbunden', color: C.success },
    offline: { label: 'Offline', color: C.error },
  }[ollamaConn];

  return (
    <div className="max-w-3xl">
      <SectionHeader icon="settings" title="Einstellungen" />

      <div className="flex flex-col gap-4">
        {/* Warn card (conditional) */}
        {warnFolders.length > 0 && (
          <Card className="p-4" style={{ background: rgba(C.warning, 0.06), borderColor: rgba(C.warning, 0.3) }}>
            <div className="flex items-start gap-3">
              <Icon name="alert-triangle" size={18} style={{ color: C.warning }} className="mt-0.5 shrink-0" />
              <div>
                <div className="text-sm font-semibold mb-1" style={{ color: C.warning }}>Konfigurationswarnung</div>
                <div className="text-xs leading-relaxed" style={{ color: C.textSecondary }}>
                  {warnFolders.length} aktivierte{warnFolders.length > 1 ? '' : 'r'} Ordner existier{warnFolders.length > 1 ? 'en' : 't'} nicht:
                  <span className="font-mono ml-1" style={{ color: C.textPrimary }}>{warnFolders.map((f) => f.path).join(', ')}</span>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Ordner-Überwachung */}
        <SettingCard title="Ordner-Überwachung" icon="eye" right={<Button variant="flat" size="sm" icon="refresh-cw" onClick={() => { setWatchdog(true); toast('info', 'Watchdog neu gestartet', `${activeCount} Ordner überwacht.`); }}>Neu starten</Button>}>
          <div className="flex items-center gap-2 mb-3">
            <StatusDot color={watchdog ? C.success : C.muted} pulse={watchdog} />
            <span className="text-sm whitespace-nowrap" style={{ color: watchdog ? C.textPrimary : C.textMuted }}>
              {watchdog ? `Aktiv — ${activeCount} Ordner überwacht` : 'Inaktiv'}
            </span>
          </div>
          {watchdog && (
            <div className="flex flex-col gap-1.5">
              {folders.filter((f) => f.active).map((f) => (
                <div key={f.id} className="text-xs font-mono flex items-center gap-2" style={{ color: f.exists ? C.textSecondary : C.error }}>
                  <Icon name="folder" size={13} />{f.path}{!f.exists && ' (fehlt)'}
                </div>
              ))}
            </div>
          )}
        </SettingCard>

        {/* Auto-Sortierung */}
        <SettingCard title="Auto-Sortierung" icon="zap" right={<Switch checked={autoSort} onChange={setAutoSort} />}>
          <p className="text-xs mb-4" style={{ color: C.textSecondary }}>Dokumente, die alle Bedingungen erfüllen, werden automatisch ohne manuelle Prüfung einsortiert.</p>
          <div className={clsx('transition-opacity', !autoSort && 'opacity-40 pointer-events-none')}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: C.textSecondary }}>Konfidenz-Schwellwert</span>
              <span className="text-sm font-mono font-semibold" style={{ color: C.accent }}>{threshold}%</span>
            </div>
            <input type="range" min={50} max={100} step={5} value={threshold} onChange={(e) => setThreshold(+e.target.value)} className="w-full" />
            <p className="text-xs mt-2" style={{ color: C.textMuted }}>Dokumente unterhalb dieser Schwelle gehen immer in die Inbox.</p>
          </div>
        </SettingCard>

        {/* Eingabe-Ordner */}
        <SettingCard title="Eingabe-Ordner" icon="folder">
          <div className="flex flex-col gap-2">
            {folders.map((f) => (
              <div key={f.id} className="flex items-center gap-2">
                <TextInput value={f.path} onChange={(v) => setFolders((fs) => fs.map((x) => (x.id === f.id ? { ...x, path: v } : x)))} mono className="flex-1" style={{ borderColor: !f.exists ? rgba(C.error, 0.4) : C.border }} />
                <Button variant="flat" size="sm" icon="folder-open" onClick={() => toast('info', 'Ordner-Picker', 'Systemdialog würde sich öffnen.')}>Wählen</Button>
                <Switch checked={f.active} onChange={(v) => setFolders((fs) => fs.map((x) => (x.id === f.id ? { ...x, active: v } : x)))} />
                <button onClick={() => setFolders((fs) => fs.filter((x) => x.id !== f.id))} className="p-1.5 rounded-md hover:bg-white/5" style={{ color: C.error }}><Icon name="trash" size={15} /></button>
              </div>
            ))}
          </div>
          <button onClick={() => setFolders((fs) => [...fs, { id: 'f' + Date.now(), path: 'D:/Neuer/Ordner', active: true, exists: true }])} className="mt-3 text-xs flex items-center gap-1.5 hover:underline whitespace-nowrap" style={{ color: C.accent }}><Icon name="plus" size={13} />Ordner hinzufügen</button>
        </SettingCard>

        {/* Ausgabe */}
        <SettingCard title="Ausgabe" icon="hard-drive">
          <div className="flex items-center gap-2">
            <span className="text-xs w-24 shrink-0" style={{ color: C.textMuted }}>Basis-Ordner</span>
            <TextInput value={outputFolder} onChange={setOutputFolder} mono className="flex-1" />
            <Button variant="flat" size="sm" icon="folder-open" onClick={() => toast('info', 'Ordner-Picker', 'Systemdialog würde sich öffnen.')}>Wählen</Button>
          </div>
        </SettingCard>

        {/* German-OCR */}
        <SettingCard title="German-OCR" badge="Primär" badgeColor={C.accent} icon="cpu" iconColor={C.accent2} right={<Switch checked={ocrEnabled} onChange={setOcrEnabled} />}>
          <p className="text-xs mb-3" style={{ color: C.textSecondary }}>Lokales Sprachmodell zur Extraktion aus gescannten, bildbasierten PDFs ohne Textebene.</p>
          <div className={clsx(!ocrEnabled && 'opacity-40 pointer-events-none')}>
            <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
              <div className="flex items-center gap-2">
                <StatusDot color={ocrStatusMeta.color} pulse={ocrStatus === 'loaded'} />
                <span className="text-sm" style={{ color: C.textPrimary }}>{ocrStatusMeta.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: C.textMuted }}>Backend</span>
                <Select value={ocrBackend} onChange={setOcrBackend} options={['Ollama-GPU', 'HuggingFace-CPU', 'LlamaCPP-GGUF']} />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant={ocrStatus === 'loaded' ? 'flat' : 'primary'} size="sm" icon={installing ? undefined : ocrStatusMeta.actionIcon} onClick={runOcrAction} disabled={installing}>
                {installing ? <span className="flex items-center gap-2"><Icon name="loader" size={14} className="df-spin" />Läuft…</span> : ocrStatusMeta.action}
              </Button>
              <Button variant="ghost" size="sm" icon={showLog ? 'chevron-down' : 'chevron-right'} onClick={() => setShowLog((s) => !s)}>{showLog ? 'Log ausblenden' : 'Log anzeigen'}</Button>
            </div>
            {showLog && (
              <div ref={logRef} className="mt-3 rounded-lg p-3 font-mono text-xs overflow-auto df-fade-in" style={{ background: C.page, border: `1px solid ${C.border}`, maxHeight: 140 }}>
                {log.map((l, i) => (
                  <div key={i} style={{ color: l.startsWith('✓') ? C.success : l.startsWith('$') ? C.accent : C.textSecondary }}>{l}</div>
                ))}
                {installing && <div style={{ color: C.warning }} className="flex items-center gap-1.5"><Icon name="loader" size={12} className="df-spin" />arbeite…</div>}
              </div>
            )}
          </div>
        </SettingCard>

        {/* Ollama */}
        <SettingCard title="Ollama" badge="Fallback" badgeColor={C.muted} icon="server"
          right={<div className="flex items-center gap-2"><StatusDot color={ollamaMeta.color} pulse={ollamaConn === 'connected'} /><span className="text-xs font-medium" style={{ color: ollamaMeta.color }}>{ollamaMeta.label}</span></div>}>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-xs mb-1" style={{ color: C.textMuted }}>URL</div>
              <TextInput value={ollamaUrl} onChange={setOllamaUrl} mono className="w-full" />
            </div>
            <div>
              <div className="text-xs mb-1" style={{ color: C.textMuted }}>Modell</div>
              <TextInput value={ollamaModel} onChange={setOllamaModel} mono className="w-full" />
            </div>
            <div>
              <div className="text-xs mb-1" style={{ color: C.textMuted }}>Timeout (s)</div>
              <input type="number" value={ollamaTimeout} onChange={(e) => setOllamaTimeout(+e.target.value)} className="w-full rounded-md px-2.5 py-1.5 text-sm font-mono outline-none" style={{ background: C.page, border: `1px solid ${C.border}`, color: C.textPrimary }} />
            </div>
            <div className="flex items-end">
              <Button variant="flat" size="sm" icon={ollamaConn === 'checking' ? undefined : 'refresh-cw'} onClick={testOllama} disabled={ollamaConn === 'checking'}>
                {ollamaConn === 'checking' ? <span className="flex items-center gap-2"><Icon name="loader" size={14} className="df-spin" />Prüfe…</span> : 'Verbindung testen'}
              </Button>
            </div>
          </div>
        </SettingCard>

        {/* Datenbank zurücksetzen */}
        <SettingCard title="Datenbank zurücksetzen" icon="database" iconColor={C.error}>
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs leading-relaxed" style={{ color: C.textSecondary }}>Löscht alle erkannten Dokumente, Templates und Logs. Bereits sortierte Dateien auf der Festplatte bleiben erhalten. Diese Aktion kann nicht rückgängig gemacht werden.</p>
            <Button variant="danger" icon="trash" onClick={() => setConfirmReset(true)}>Alles löschen</Button>
          </div>
        </SettingCard>
      </div>

      <ConfirmDialog open={confirmReset} title="Datenbank wirklich zurücksetzen?" body="Alle Dokumente, Templates und Logs werden unwiderruflich gelöscht. Sortierte Dateien bleiben auf der Festplatte." confirmLabel="Alles löschen" danger
        onConfirm={() => { setConfirmReset(false); toast('error', 'Datenbank zurückgesetzt', 'Alle Einträge wurden gelöscht.'); }} onCancel={() => setConfirmReset(false)} />
    </div>
  );
}

Object.assign(window, { SettingsScreen });
