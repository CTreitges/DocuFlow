<script>
  import { onDestroy } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import SegTabs from '../lib/components/SegTabs.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import ConfidenceBadge from '../lib/components/ConfidenceBadge.svelte';
  import { C, rgba } from '../lib/tokens.js';
  import { toast } from '../lib/store.svelte.js';
  import { OCR_FIELDS, OCR_TEMPLATE_YAML, OCR_PDF_TEXT, DOCUMENTS } from '../lib/mock.js';

  const RUNS = ['template', 'ocr', 'error'];
  const initSteps = () => [
    { key: 'extract', label: 'Text-Extraktion', status: 'pending', text: '' },
    { key: 'match', label: 'Template-Match', status: 'pending', text: '' },
    { key: 'ocr', label: 'OCR-Fallback', status: 'pending', text: '' },
  ];

  let runIdx = $state(0);
  let phase = $state('initial'); // initial | running | success | error
  let steps = $state(initSteps());
  let result = $state(null);
  let tab = $state('felder');
  let fileName = $state('');
  let timers = [];

  let ocrActive = $derived(steps.find((s) => s.key === 'ocr')?.status === 'active');

  function clearTimers() { timers.forEach(clearTimeout); timers = []; }
  function at(ms, fn) { timers.push(setTimeout(fn, ms)); }
  function setStep(key, fields) { steps = steps.map((st) => (st.key === key ? { ...st, ...fields } : st)); }
  onDestroy(clearTimers);

  function clear() {
    clearTimers();
    phase = 'initial'; steps = initSteps(); result = null; fileName = '';
    toast('info', 'Geleert', 'Diagnose zurückgesetzt.');
  }

  function pickPdf() {
    clearTimers();
    const mode = RUNS[runIdx % RUNS.length];
    runIdx += 1;
    const name = mode === 'template' ? 'rechnung_amazon_4412.pdf' : mode === 'ocr' ? 'scan_2026-03-18_093442.pdf' : 'schneider_elektro_fehler.pdf';
    fileName = name;
    phase = 'running'; steps = initSteps(); result = null; tab = 'felder';

    setStep('extract', { status: 'active', text: `Lese ${name}…` });
    at(900, () => {
      setStep('extract', { status: 'done', text: mode === 'template' ? '3 Seiten, 1.842 Zeichen. Prüfe Templates…' : '2 Seiten, 0 Zeichen (Bild-PDF).' });
      setStep('match', { status: 'active', text: 'Vergleiche mit bekannten Mustern…' });
      at(1100, () => {
        if (mode === 'template') {
          setStep('match', { status: 'done', text: '✓ Template: Amazon EU S.à r.l. (96%)' });
          setStep('ocr', { status: 'done', text: 'Übersprungen — Template ausreichend.' });
          at(400, () => { phase = 'success'; result = { source: 'Template', pages: 3, kind: 'Text-PDF', usedOcr: false }; toast('success', 'Template gefunden', 'Amazon EU S.à r.l.'); });
        } else {
          setStep('match', { status: 'done', text: 'Kein Template — German-OCR läuft…' });
          setStep('ocr', { status: 'active', text: 'Kein Template — German-OCR läuft… (30–120 s)' });
          at(2600, () => {
            if (mode === 'ocr') {
              setStep('ocr', { status: 'done', text: '✓ OCR abgeschlossen — 10 Felder erkannt.' });
              at(400, () => { phase = 'success'; result = { source: 'OCR', pages: 2, kind: 'Bild-PDF', usedOcr: true }; toast('success', 'OCR abgeschlossen', '10 Felder extrahiert.'); });
            } else {
              setStep('ocr', { status: 'error', text: '✗ OCR-Backend timeout nach 120 s.' });
              at(300, () => { phase = 'error'; toast('error', 'Pipeline fehlgeschlagen', 'OCR-Backend nicht erreichbar.'); });
            }
          });
        }
      });
    });
  }

  const STEP_META = {
    pending: { color: C.textMuted, icon: null, bg: C.elevated },
    active: { color: C.accent, icon: 'loader', bg: rgba(C.accent, 0.15) },
    done: { color: C.success, icon: 'check', bg: rgba(C.success, 0.15) },
    error: { color: C.error, icon: 'x', bg: rgba(C.error, 0.15) },
  };
</script>

{#snippet stepRow(step, last)}
  {@const meta = STEP_META[step.status]}
  <div class="flex gap-3">
    <div class="flex flex-col items-center">
      <div class="flex items-center justify-center rounded-full shrink-0" style="width:26px; height:26px; background:{meta.bg}; border:1px solid {rgba(meta.color, 0.3)}">
        {#if step.status === 'active'}<Icon name="loader" size={14} class="df-spin" color={meta.color} />
        {:else if meta.icon}<Icon name={meta.icon} size={14} color={meta.color} />
        {:else}<span class="rounded-full" style="width:6px; height:6px; background:{meta.color}"></span>{/if}
      </div>
      {#if !last}<div style="width:2px; flex:1; min-height:18px; background:{C.border}; margin:2px 0"></div>{/if}
    </div>
    <div class="pb-4 min-w-0">
      <div class="text-sm font-medium" style="color:{step.status === 'pending' ? C.textMuted : C.textPrimary}">{step.label}</div>
      {#if step.text}<div class="text-xs font-mono mt-0.5" style="color:{step.status === 'error' ? C.error : C.textMuted}">{step.text}</div>{/if}
    </div>
  </div>
{/snippet}

<div>
  <SectionHeader icon="bug" title="OCR-Debug">
    {#snippet right()}
      <div class="flex items-center gap-2">
        <Button variant="primary" icon="file-search" onclick={pickPdf} disabled={phase === 'running'}>PDF auswählen</Button>
        <Button variant="ghost" icon="x" onclick={clear} disabled={phase === 'initial'}>Leeren</Button>
      </div>
    {/snippet}
  </SectionHeader>
  <p class="text-sm mb-4 flex items-center gap-2" style="color:{C.textSecondary}">
    <Icon name="arrow-right" size={14} color={C.textMuted} />
    PDF auswählen → Pipeline läuft → Extrahierte Daten + Template-Vorschau.
  </p>

  {#if phase === 'initial'}
    <Card class="p-0"><EmptyState icon="file-search" title="Keine PDF geladen" subtitle="Wähle eine PDF, um die Extraktions-Pipeline schrittweise zu beobachten." /></Card>
  {:else}
    <div class="flex flex-col gap-4">
      <Card class="p-4">
        <div class="flex items-center gap-2 mb-4">
          <Icon name="file-text" size={14} color={C.textMuted} />
          <span class="text-sm font-mono" style="color:{C.textPrimary}">{fileName}</span>
        </div>
        <div class="flex flex-col gap-0">
          {#each steps as s, i (s.key)}{@render stepRow(s, i === steps.length - 1)}{/each}
        </div>
        {#if ocrActive}
          <div class="mt-4 relative h-1.5 rounded-full overflow-hidden" style="background:{C.elevated}">
            <div class="df-bar-indeterminate" style="background:{C.accent2}"></div>
          </div>
        {/if}
      </Card>

      {#if phase === 'error'}
        <Card class="p-4" style="background:{rgba(C.error, 0.06)}; border-color:{rgba(C.error, 0.3)}">
          <div class="flex items-center gap-2 mb-2"><Icon name="alert-circle" size={16} color={C.error} /><span class="text-sm font-semibold" style="color:{C.error}">Extraktion fehlgeschlagen</span></div>
          <pre class="text-xs font-mono whitespace-pre-wrap" style="color:{rgba(C.error, 0.85)}">OCRError: Backend „Ollama-GPU" nach 120s nicht erreichbar.
  → Prüfe Ollama-Verbindung in den Einstellungen.</pre>
        </Card>
      {/if}

      {#if phase === 'success' && result}
        {@const src = result.source === 'Template' ? C.success : C.accent}
        <Card class="overflow-hidden">
          <div class="flex items-center gap-3 px-4 py-3 flex-wrap" style="border-bottom:1px solid {C.border}">
            <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" style="background:{rgba(src, 0.12)}; color:{src}; border:1px solid {rgba(src, 0.3)}">
              <Icon name={result.source === 'Template' ? 'layout-template' : 'scan-text'} size={13} />
              Quelle: {result.source}
            </span>
            <span class="text-xs font-mono" style="color:{C.textMuted}">{result.pages} Seiten</span>
            <span class="text-xs font-mono px-2 py-0.5 rounded" style="background:{C.elevated}; color:{C.textSecondary}">{result.kind}</span>
          </div>

          <div class="px-4 pt-3">
            <SegTabs size="sm" active={tab} onChange={(v) => (tab = v)} tabs={[
              { key: 'felder', label: 'Extrahierte Felder' },
              { key: 'template', label: 'Template-Vorschau' },
              { key: 'pdftext', label: 'PDF-Text' },
              ...(result.usedOcr ? [{ key: 'ocr', label: 'OCR-Output' }] : []),
            ]} />
          </div>

          <div class="p-4">
            {#if tab === 'felder'}
              <div class="grid grid-cols-2 gap-x-4 gap-y-2.5">
                {#each OCR_FIELDS as f (f.label)}
                  <div class="flex items-center justify-between gap-2 rounded-md px-2.5 py-2" style="background:{C.page}; border:1px solid {C.border}">
                    <div class="min-w-0">
                      <div class="text-[11px]" style="color:{C.textMuted}">{f.label}</div>
                      <div class="text-sm font-mono truncate" style="color:{C.textPrimary}">{f.value}</div>
                    </div>
                    <ConfidenceBadge value={f.conf} />
                  </div>
                {/each}
              </div>
              <div class="mt-4">
                <div class="text-[11px] font-semibold uppercase tracking-wider mb-2" style="color:{C.textMuted}">Positionen</div>
                <div class="rounded-lg overflow-hidden" style="border:1px solid {C.border}">
                  <table class="w-full">
                    <thead><tr style="background:rgba(0,0,0,0.2)">
                      <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:40px">#</th>
                      <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}">Beschreibung</th>
                      <th class="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:80px">Menge</th>
                      <th class="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:130px">Gesamt</th>
                    </tr></thead>
                    <tbody>
                      {#each DOCUMENTS[0].positionen as p (p.nr)}
                        <tr style="border-top:1px solid {C.border}">
                          <td class="px-3 py-2 text-sm font-mono" style="color:{C.textMuted}">{p.nr}</td>
                          <td class="px-3 py-2 text-sm" style="color:{C.textPrimary}">{p.beschreibung}</td>
                          <td class="px-3 py-2 text-sm font-mono text-right" style="color:{C.textSecondary}">{p.menge}</td>
                          <td class="px-3 py-2 text-sm font-mono text-right tabular-nums" style="color:{C.textPrimary}">{p.gesamt}</td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            {:else if tab === 'template'}
              {#if result.usedOcr}
                <EmptyState icon="layout-template" title="Kein Template verwendet" subtitle="Dieses Dokument wurde per OCR-Fallback verarbeitet." />
              {:else}
                <pre class="rounded-lg p-3.5 text-xs font-mono overflow-auto leading-relaxed" style="background:{C.page}; border:1px solid {C.border}; color:{C.textSecondary}; max-height:360px">{OCR_TEMPLATE_YAML}</pre>
              {/if}
            {:else if tab === 'pdftext'}
              {#if result.usedOcr}
                <EmptyState icon="file-text" title="Keine Textebene" subtitle="Bild-PDF ohne eingebetteten Text — siehe OCR-Output." />
              {:else}
                <div class="text-xs font-mono mb-2" style="color:{C.textMuted}">{OCR_PDF_TEXT.length} Zeichen</div>
                <textarea readonly class="w-full rounded-lg p-3.5 text-xs font-mono outline-none resize-none leading-relaxed" style="background:{C.page}; border:1px solid {C.border}; color:{C.textSecondary}; height:300px">{OCR_PDF_TEXT}</textarea>
              {/if}
            {:else if tab === 'ocr'}
              <div class="text-xs font-mono mb-2" style="color:{C.textMuted}">German-OCR · {result.pages} Seiten</div>
              <textarea readonly class="w-full rounded-lg p-3.5 text-xs font-mono outline-none resize-none leading-relaxed" style="background:{C.page}; border:1px solid {C.border}; color:{C.textSecondary}; height:300px">{OCR_PDF_TEXT + '\n\n[OCR-Konfidenz pro Block: 0.88 / 0.91 / 0.77]'}</textarea>
            {/if}
          </div>
        </Card>
      {/if}
    </div>
  {/if}
</div>
