<script>
  import { onMount } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import Switch from '../lib/components/Switch.svelte';
  import Select from '../lib/components/Select.svelte';
  import TextInput from '../lib/components/TextInput.svelte';
  import StatusDot from '../lib/components/StatusDot.svelte';
  import SettingCard from '../lib/components/SettingCard.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import ConfirmDialog from '../lib/components/ConfirmDialog.svelte';
  import { C, rgba, clsx } from '../lib/tokens.js';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/store.svelte.js';
  import * as MOCK from '../lib/mock.js';

  const OCR_BACKENDS = [['Ollama-GPU', 'ollama'], ['HuggingFace-CPU', 'huggingface'], ['LlamaCPP-GGUF', 'llamacpp']];
  const dispFromRaw = (r) => (OCR_BACKENDS.find((x) => x[1] === r) || OCR_BACKENDS[0])[0];
  const rawFromDisp = (d) => (OCR_BACKENDS.find((x) => x[0] === d) || OCR_BACKENDS[0])[1];

  let watchdog = $state(true);
  let autoSort = $state(true);
  let threshold = $state(85);
  let folders = $state(MOCK.INPUT_FOLDERS.map((f) => ({ ...f })));
  let outputFolder = $state('D:/Rechnungen');
  let confirmReset = $state(false);
  let saving = $state(false);

  let ocrEnabled = $state(true);
  let ocrStatus = $state('installed'); // 'not-installed' | 'installed' | 'loaded'
  let ocrBackend = $state('Ollama-GPU');
  let installing = $state(false);
  let showLog = $state(false);
  let log = $state(['$ docuflow ocr status', 'german-ocr erkannt — Modell nicht geladen']);
  let logRef = $state(null);

  let ollamaUrl = $state('http://localhost:11434');
  let ollamaModel = $state('minicpm-v');
  let ollamaTimeout = $state(120);
  let ollamaConn = $state('idle'); // 'idle' | 'checking' | 'connected' | 'offline'

  let warnFolders = $derived(folders.filter((f) => f.active && !f.exists));
  let activeCount = $derived(folders.filter((f) => f.active).length);

  let ocrStatusMeta = $derived({
    'not-installed': { label: 'Nicht installiert', color: C.error, action: 'Installieren', actionIcon: 'play' },
    installed: { label: 'Installiert · Modell nicht geladen', color: C.warning, action: 'Modell laden', actionIcon: 'play' },
    loaded: { label: 'Geladen · Aktiv', color: C.success, action: 'Modell entladen', actionIcon: 'x' },
  }[ocrStatus]);

  let ollamaMeta = $derived({
    idle: { label: 'Nicht geprüft', color: C.muted },
    checking: { label: 'Prüfe…', color: C.warning },
    connected: { label: 'Verbunden', color: C.success },
    offline: { label: 'Offline', color: C.error },
  }[ollamaConn]);

  $effect(() => { if (logRef) logRef.scrollTop = logRef.scrollHeight; });

  onMount(async () => {
    try {
      const [cfg, health] = await Promise.all([api.settings(), api.health().catch(() => null)]);
      folders = (cfg.input_folders || []).map((f, i) => ({ id: 'f' + i, path: f.path, active: f.enabled !== false, exists: true }));
      outputFolder = cfg.output?.base_path || 'D:/Rechnungen';
      autoSort = !!cfg.auto_mode;
      threshold = Math.round((cfg.auto_confidence_threshold ?? 0.9) * 100);
      ollamaUrl = cfg.ollama?.url || ollamaUrl;
      ollamaModel = cfg.ollama?.model || ollamaModel;
      ollamaTimeout = cfg.ollama?.timeout ?? 120;
      ocrEnabled = cfg.german_ocr?.enabled !== false;
      ocrBackend = dispFromRaw(cfg.german_ocr?.backend || 'ollama');
      if (health) {
        ocrStatus = health.german_ocr_available ? 'loaded' : 'installed';
        ollamaConn = health.ocr_available ? 'connected' : 'offline';
      }
    } catch {
      toast('info', 'Demo-Daten', 'Backend nicht erreichbar — zeige Design-Beispieldaten.');
      ollamaConn = 'connected';
    }
  });

  async function save() {
    saving = true;
    try {
      await api.saveSettings({
        input_folders: folders.map((f) => ({ path: f.path, enabled: f.active, watch: true })),
        output: { base_path: outputFolder },
        auto_mode: autoSort,
        auto_confidence_threshold: threshold / 100,
        ollama: { url: ollamaUrl, model: ollamaModel, timeout: Number(ollamaTimeout) },
        german_ocr: { enabled: ocrEnabled, backend: rawFromDisp(ocrBackend) },
      });
      toast('success', 'Einstellungen gespeichert', 'config.yaml aktualisiert.');
    } catch (e) {
      toast('error', 'Speichern fehlgeschlagen', String(e.message || e));
    }
    saving = false;
  }

  function appendLog(lines, done) {
    let i = 0;
    const tick = () => {
      log = [...log, lines[i]];
      i++;
      if (i < lines.length) setTimeout(tick, 550);
      else done && done();
    };
    tick();
  }

  // Install/Load ist eine lokale Simulation (im Desktop-Fenster nicht pip-installierbar).
  function runOcrAction() {
    if (ocrStatus === 'not-installed') {
      installing = true; showLog = true;
      appendLog(['$ pip install german-ocr', 'Downloading wheels… 142 MB', 'Installiere Abhängigkeiten…', '✓ german-ocr installiert'], () => { installing = false; ocrStatus = 'installed'; toast('success', 'OCR installiert', 'Modell kann jetzt geladen werden.'); });
    } else if (ocrStatus === 'installed') {
      installing = true; showLog = true;
      appendLog([`$ ollama pull ${ollamaModel}`, 'pulling manifest…', 'pulling model layers… 4.7 GB', 'verifying sha256…', '✓ Modell geladen — Backend aktiv'], () => { installing = false; ocrStatus = 'loaded'; toast('success', 'Modell geladen', 'German-OCR ist aktiv.'); });
    } else {
      ocrStatus = 'installed'; toast('info', 'Modell entladen', 'GPU-Speicher freigegeben.');
    }
  }

  async function testOllama() {
    ollamaConn = 'checking';
    try {
      const h = await api.health();
      ollamaConn = h.ocr_available ? 'connected' : 'offline';
      if (h.ocr_available) toast('success', 'Verbindung OK', `${ollamaUrl} erreichbar.`);
      else toast('warning', 'Offline', 'Ollama/OCR-Backend nicht erreichbar.');
    } catch {
      ollamaConn = 'offline';
      toast('error', 'Fehler', 'Backend nicht erreichbar.');
    }
  }

  async function doReset() {
    confirmReset = false;
    try {
      await api.resetDatabase();
      toast('error', 'Datenbank zurückgesetzt', 'Alle Einträge wurden gelöscht.');
    } catch (e) {
      toast('error', 'Reset fehlgeschlagen', String(e.message || e));
    }
  }

  const addFolder = () => (folders = [...folders, { id: 'f' + Date.now(), path: 'D:/Neuer/Ordner', active: true, exists: true }]);
  const setFolder = (id, patch) => (folders = folders.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const rmFolder = (id) => (folders = folders.filter((x) => x.id !== id));
</script>

<div class="max-w-3xl">
  <SectionHeader icon="settings" title="Einstellungen">
    {#snippet right()}
      <Button variant="primary" icon={saving ? undefined : 'check'} onclick={save} disabled={saving}>
        {#if saving}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Speichert…</span>{:else}Speichern{/if}
      </Button>
    {/snippet}
  </SectionHeader>

  <div class="flex flex-col gap-4">
    {#if warnFolders.length > 0}
      <Card class="p-4" style="background:{rgba(C.warning, 0.06)}; border-color:{rgba(C.warning, 0.3)}">
        <div class="flex items-start gap-3">
          <Icon name="alert-triangle" size={18} color={C.warning} class="mt-0.5 shrink-0" />
          <div>
            <div class="text-sm font-semibold mb-1" style="color:{C.warning}">Konfigurationswarnung</div>
            <div class="text-xs leading-relaxed" style="color:{C.textSecondary}">
              {warnFolders.length} aktivierte{warnFolders.length > 1 ? '' : 'r'} Ordner existier{warnFolders.length > 1 ? 'en' : 't'} nicht:
              <span class="font-mono ml-1" style="color:{C.textPrimary}">{warnFolders.map((f) => f.path).join(', ')}</span>
            </div>
          </div>
        </div>
      </Card>
    {/if}

    <SettingCard title="Ordner-Überwachung" icon="eye">
      {#snippet right()}
        <Button variant="flat" size="sm" icon="refresh-cw" onclick={() => { watchdog = true; toast('info', 'Watchdog neu gestartet', `${activeCount} Ordner überwacht.`); }}>Neu starten</Button>
      {/snippet}
      <div class="flex items-center gap-2 mb-3">
        <StatusDot color={watchdog ? C.success : C.muted} pulse={watchdog} />
        <span class="text-sm whitespace-nowrap" style="color:{watchdog ? C.textPrimary : C.textMuted}">{watchdog ? `Aktiv — ${activeCount} Ordner überwacht` : 'Inaktiv'}</span>
      </div>
      {#if watchdog}
        <div class="flex flex-col gap-1.5">
          {#each folders.filter((f) => f.active) as f (f.id)}
            <div class="text-xs font-mono flex items-center gap-2" style="color:{f.exists ? C.textSecondary : C.error}">
              <Icon name="folder" size={13} />{f.path}{!f.exists ? ' (fehlt)' : ''}
            </div>
          {/each}
        </div>
      {/if}
    </SettingCard>

    <SettingCard title="Auto-Sortierung" icon="zap">
      {#snippet right()}<Switch checked={autoSort} onChange={(v) => (autoSort = v)} />{/snippet}
      <p class="text-xs mb-4" style="color:{C.textSecondary}">Dokumente, die alle Bedingungen erfüllen, werden automatisch ohne manuelle Prüfung einsortiert.</p>
      <div class={clsx('transition-opacity', !autoSort && 'opacity-40 pointer-events-none')}>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium" style="color:{C.textSecondary}">Konfidenz-Schwellwert</span>
          <span class="text-sm font-mono font-semibold" style="color:{C.accent}">{threshold}%</span>
        </div>
        <input type="range" min="50" max="100" step="5" value={threshold} oninput={(e) => (threshold = +e.currentTarget.value)} class="w-full" />
        <p class="text-xs mt-2" style="color:{C.textMuted}">Dokumente unterhalb dieser Schwelle gehen immer in die Inbox.</p>
      </div>
    </SettingCard>

    <SettingCard title="Eingabe-Ordner" icon="folder">
      <div class="flex flex-col gap-2">
        {#each folders as f (f.id)}
          <div class="flex items-center gap-2">
            <TextInput value={f.path} onChange={(v) => setFolder(f.id, { path: v })} mono class="flex-1" style={!f.exists ? `border-color:${rgba(C.error, 0.4)}` : ''} />
            <Button variant="flat" size="sm" icon="folder-open" onclick={() => toast('info', 'Ordner-Picker', 'Systemdialog würde sich öffnen.')}>Wählen</Button>
            <Switch checked={f.active} onChange={(v) => setFolder(f.id, { active: v })} />
            <button onclick={() => rmFolder(f.id)} class="p-1.5 rounded-md hover:bg-white/5" style="color:{C.error}"><Icon name="trash" size={15} /></button>
          </div>
        {/each}
      </div>
      <button onclick={addFolder} class="mt-3 text-xs flex items-center gap-1.5 hover:underline whitespace-nowrap" style="color:{C.accent}"><Icon name="plus" size={13} />Ordner hinzufügen</button>
    </SettingCard>

    <SettingCard title="Ausgabe" icon="hard-drive">
      <div class="flex items-center gap-2">
        <span class="text-xs w-24 shrink-0" style="color:{C.textMuted}">Basis-Ordner</span>
        <TextInput value={outputFolder} onChange={(v) => (outputFolder = v)} mono class="flex-1" />
        <Button variant="flat" size="sm" icon="folder-open" onclick={() => toast('info', 'Ordner-Picker', 'Systemdialog würde sich öffnen.')}>Wählen</Button>
      </div>
    </SettingCard>

    <SettingCard title="German-OCR" badge="Primär" badgeColor={C.accent} icon="cpu" iconColor={C.accent2}>
      {#snippet right()}<Switch checked={ocrEnabled} onChange={(v) => (ocrEnabled = v)} />{/snippet}
      <p class="text-xs mb-3" style="color:{C.textSecondary}">Lokales Sprachmodell zur Extraktion aus gescannten, bildbasierten PDFs ohne Textebene.</p>
      <div class={clsx(!ocrEnabled && 'opacity-40 pointer-events-none')}>
        <div class="flex items-center justify-between gap-3 mb-3 flex-wrap">
          <div class="flex items-center gap-2">
            <StatusDot color={ocrStatusMeta.color} pulse={ocrStatus === 'loaded'} />
            <span class="text-sm" style="color:{C.textPrimary}">{ocrStatusMeta.label}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs" style="color:{C.textMuted}">Backend</span>
            <Select value={ocrBackend} onChange={(v) => (ocrBackend = v)} options={OCR_BACKENDS.map((x) => x[0])} />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Button variant={ocrStatus === 'loaded' ? 'flat' : 'primary'} size="sm" icon={installing ? undefined : ocrStatusMeta.actionIcon} onclick={runOcrAction} disabled={installing}>
            {#if installing}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Läuft…</span>{:else}{ocrStatusMeta.action}{/if}
          </Button>
          <Button variant="ghost" size="sm" icon={showLog ? 'chevron-down' : 'chevron-right'} onclick={() => (showLog = !showLog)}>{showLog ? 'Log ausblenden' : 'Log anzeigen'}</Button>
        </div>
        {#if showLog}
          <div bind:this={logRef} class="mt-3 rounded-lg p-3 font-mono text-xs overflow-auto df-fade-in" style="background:{C.page}; border:1px solid {C.border}; max-height:140px">
            {#each log as l, i (i)}
              <div style="color:{l.startsWith('✓') ? C.success : l.startsWith('$') ? C.accent : C.textSecondary}">{l}</div>
            {/each}
            {#if installing}<div style="color:{C.warning}" class="flex items-center gap-1.5"><Icon name="loader" size={12} class="df-spin" />arbeite…</div>{/if}
          </div>
        {/if}
      </div>
    </SettingCard>

    <SettingCard title="Ollama" badge="Fallback" badgeColor={C.muted} icon="server">
      {#snippet right()}
        <div class="flex items-center gap-2"><StatusDot color={ollamaMeta.color} pulse={ollamaConn === 'connected'} /><span class="text-xs font-medium" style="color:{ollamaMeta.color}">{ollamaMeta.label}</span></div>
      {/snippet}
      <div class="grid grid-cols-2 gap-3">
        <div>
          <div class="text-xs mb-1" style="color:{C.textMuted}">URL</div>
          <TextInput value={ollamaUrl} onChange={(v) => (ollamaUrl = v)} mono class="w-full" />
        </div>
        <div>
          <div class="text-xs mb-1" style="color:{C.textMuted}">Modell</div>
          <TextInput value={ollamaModel} onChange={(v) => (ollamaModel = v)} mono class="w-full" />
        </div>
        <div>
          <div class="text-xs mb-1" style="color:{C.textMuted}">Timeout (s)</div>
          <input type="number" value={ollamaTimeout} oninput={(e) => (ollamaTimeout = +e.currentTarget.value)} class="w-full rounded-md px-2.5 py-1.5 text-sm font-mono outline-none" style="background:{C.page}; border:1px solid {C.border}; color:{C.textPrimary}" />
        </div>
        <div class="flex items-end">
          <Button variant="flat" size="sm" icon={ollamaConn === 'checking' ? undefined : 'refresh-cw'} onclick={testOllama} disabled={ollamaConn === 'checking'}>
            {#if ollamaConn === 'checking'}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Prüfe…</span>{:else}Verbindung testen{/if}
          </Button>
        </div>
      </div>
    </SettingCard>

    <SettingCard title="Datenbank zurücksetzen" icon="database" iconColor={C.error}>
      <div class="flex items-center justify-between gap-4">
        <p class="text-xs leading-relaxed" style="color:{C.textSecondary}">Löscht alle erkannten Dokumente, Templates und Logs. Bereits sortierte Dateien auf der Festplatte bleiben erhalten. Diese Aktion kann nicht rückgängig gemacht werden.</p>
        <Button variant="danger" icon="trash" onclick={() => (confirmReset = true)}>Alles löschen</Button>
      </div>
    </SettingCard>
  </div>

  <ConfirmDialog open={confirmReset} title="Datenbank wirklich zurücksetzen?" body="Alle Dokumente, Templates und Logs werden unwiderruflich gelöscht. Sortierte Dateien bleiben auf der Festplatte." confirmLabel="Alles löschen" danger onConfirm={doReset} onCancel={() => (confirmReset = false)} />
</div>
