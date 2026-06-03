<script>
  import { onMount } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import SegTabs from '../lib/components/SegTabs.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import ConfidenceBadge from '../lib/components/ConfidenceBadge.svelte';
  import { C, rgba } from '../lib/tokens.js';
  import { toast } from '../lib/store.svelte.js';
  import { docToView } from '../lib/adapters.js';
  import { api } from '../lib/api.js';

  // Echte Pipeline-Diagnose: reales Dokument wählen → /process → echte Felder,
  // Konfidenz, Rohtext und abgeleitete Quelle. KEINE Simulation, keine Mock-Felder.
  let docs = $state([]);
  let selectedId = $state(null);
  let phase = $state('initial'); // initial | running | success | error
  let busy = $state(false);
  let scanning = $state(false);
  let result = $state(null);
  let err = $state('');
  let tab = $state('felder');
  let backendOk = $state(true);
  let ocrAvailable = $state(false);

  const FIELD_ORDER = [
    ['absender', 'Absender'], ['datum', 'Datum'], ['rechnungsnr', 'Rechnungsnr.'],
    ['betrag', 'Betrag'], ['iban', 'IBAN'], ['kundennr', 'Kundennr.'],
    ['mwst', 'MwSt'], ['zahlungsziel', 'Zahlungsziel'], ['dokumenttyp', 'Dokumenttyp'],
  ];

  let shownFields = $derived(
    result?.view?.extraction
      ? FIELD_ORDER.map(([k, label]) => ({ label, ...result.view.extraction[k] })).filter((f) => f.value)
      : []
  );

  let srcColor = $derived.by(() => {
    const s = result?.source;
    return s === 'Template' ? C.success : s === 'OCR' ? C.accent : C.textMuted;
  });

  async function loadDocs() {
    try {
      const [list, health] = await Promise.all([api.documents(), api.health().catch(() => null)]);
      docs = list.map((d) => ({ id: d.id, file_name: d.file_name, status: d.status }));
      if (docs.length && selectedId == null) selectedId = docs[0].id;
      backendOk = true;
      if (health) ocrAvailable = !!(health.ocr_available || health.german_ocr_available);
    } catch {
      backendOk = false;
      toast('error', 'Backend nicht erreichbar', 'OCR-Debug benötigt das laufende Backend.');
    }
  }

  onMount(loadDocs);

  async function scanNow() {
    scanning = true;
    try {
      const r = await api.scan();
      await loadDocs();
      toast('success', 'Scan abgeschlossen', `${r.new} neue Datei(en) erkannt.`);
    } catch (e) {
      toast('error', 'Scan fehlgeschlagen', String(e.message || e));
    }
    scanning = false;
  }

  // Quelle ehrlich aus dem realen Verarbeitungsergebnis ableiten.
  function deriveSource(doc) {
    const e = doc.extraction || {};
    const raw = e.raw_text || '';
    const structured = !!(e.sender || e.invoice_number || e.total_amount != null);
    if (doc.template_id) return { source: 'Template', usedOcr: false };
    if (structured && ocrAvailable) return { source: 'OCR', usedOcr: true };
    if (raw) return { source: 'Nur-Text', usedOcr: false };
    return { source: 'Kein Text', usedOcr: false };
  }

  async function run() {
    if (selectedId == null) return;
    busy = true; phase = 'running'; result = null; err = ''; tab = 'felder';
    try {
      const res = await api.process(selectedId);
      const doc = res.document;
      const view = docToView(doc);
      const raw = doc.extraction?.raw_text || '';
      if (doc.status === 'fehler') {
        phase = 'error';
        err = view.error || 'Verarbeitung fehlgeschlagen — Details im Aktivitäts-Log.';
        toast('error', 'Pipeline fehlgeschlagen', doc.file_name);
      } else {
        const { source, usedOcr } = deriveSource(doc);
        result = { doc, view, raw, source, usedOcr, status: doc.status, autoSorted: res.auto_sorted };
        phase = 'success';
        const t = source === 'Template' ? 'Template erkannt' : source === 'OCR' ? 'OCR abgeschlossen' : 'Verarbeitet';
        toast('success', t, doc.file_name + (res.auto_sorted ? ' · auto-sortiert' : ''));
      }
      docs = docs.map((d) => (d.id === selectedId ? { ...d, status: doc.status } : d));
    } catch (e) {
      phase = 'error';
      err = String(e.message || e);
      toast('error', 'Fehler', err);
    }
    busy = false;
  }

  // Reale Stufen-Rekonstruktion aus dem Ergebnis (kein Fake-Timing).
  let steps = $derived.by(() => {
    if (!result) return [];
    const raw = result.raw;
    const isTpl = result.source === 'Template';
    const extract = { label: 'Text-Extraktion', status: raw ? 'done' : 'skipped',
      text: raw ? `${raw.length.toLocaleString('de-DE')} Zeichen aus Textebene` : 'Keine Textebene (Bild-PDF)' };
    const match = { label: 'Template-Match', status: isTpl ? 'done' : 'skipped',
      text: isTpl ? `✓ Template erkannt — ${result.view.konfidenz}% Konfidenz` : 'Kein passendes Template' };
    let ocr;
    if (isTpl) ocr = { label: 'OCR-Fallback', status: 'skipped', text: 'Übersprungen — Template ausreichend.' };
    else if (result.usedOcr) ocr = { label: 'OCR-Fallback', status: 'done', text: '✓ OCR-Extraktion abgeschlossen.' };
    else ocr = { label: 'OCR-Fallback', status: 'skipped', text: ocrAvailable ? 'Nicht benötigt.' : 'OCR-Backend nicht verfügbar — nur Textebene.' };
    return [extract, match, ocr];
  });

  const STEP_META = {
    pending: { color: C.textMuted, icon: null, bg: C.elevated },
    done: { color: C.success, icon: 'check', bg: rgba(C.success, 0.15) },
    skipped: { color: C.textMuted, icon: 'corner-down-right', bg: C.elevated },
    error: { color: C.error, icon: 'x', bg: rgba(C.error, 0.15) },
  };
</script>

{#snippet stepRow(step, last)}
  {@const meta = STEP_META[step.status] ?? STEP_META.pending}
  <div class="flex gap-3">
    <div class="flex flex-col items-center">
      <div class="flex items-center justify-center rounded-full shrink-0" style="width:26px; height:26px; background:{meta.bg}; border:1px solid {rgba(meta.color, 0.3)}">
        {#if meta.icon}<Icon name={meta.icon} size={14} color={meta.color} />
        {:else}<span class="rounded-full" style="width:6px; height:6px; background:{meta.color}"></span>{/if}
      </div>
      {#if !last}<div style="width:2px; flex:1; min-height:18px; background:{C.border}; margin:2px 0"></div>{/if}
    </div>
    <div class="pb-4 min-w-0">
      <div class="text-sm font-medium" style="color:{step.status === 'skipped' ? C.textMuted : C.textPrimary}">{step.label}</div>
      {#if step.text}<div class="text-xs font-mono mt-0.5" style="color:{step.status === 'error' ? C.error : C.textMuted}">{step.text}</div>{/if}
    </div>
  </div>
{/snippet}

<div>
  <SectionHeader icon="bug" title="OCR-Debug">
    {#snippet right()}
      <div class="flex items-center gap-2">
        <Button variant="flat" icon={scanning ? undefined : 'search'} onclick={scanNow} disabled={scanning || !backendOk}>
          {#if scanning}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Scannt…</span>{:else}Ordner scannen{/if}
        </Button>
        <Button variant="primary" icon={busy ? undefined : 'scan-text'} onclick={run} disabled={busy || selectedId == null}>
          {#if busy}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Verarbeite…</span>{:else}Verarbeiten{/if}
        </Button>
      </div>
    {/snippet}
  </SectionHeader>
  <p class="text-sm mb-4 flex items-center gap-2" style="color:{C.textSecondary}">
    <Icon name="arrow-right" size={14} color={C.textMuted} />
    Dokument wählen → echte Pipeline läuft → extrahierte Daten, Konfidenz und Quelle.
  </p>

  {#if !backendOk}
    <Card class="p-0"><EmptyState icon="server" title="Backend nicht erreichbar" subtitle="Starte das Backend (uvicorn backend.main:app), um die echte Extraktions-Pipeline zu testen." /></Card>
  {:else if docs.length === 0}
    <Card class="p-0">
      <EmptyState icon="file-search" title="Keine Dokumente" subtitle="Lege PDFs in einen Eingangs-Ordner und klicke „Ordner scannen“.">
        {#snippet action()}<Button variant="primary" icon="search" onclick={scanNow} disabled={scanning}>Ordner scannen</Button>{/snippet}
      </EmptyState>
    </Card>
  {:else}
    <Card class="p-4 mb-4">
      <div class="flex items-center gap-3 flex-wrap">
        <Icon name="file-text" size={15} color={C.textMuted} />
        <select
          value={selectedId}
          onchange={(e) => (selectedId = +e.currentTarget.value)}
          class="appearance-none rounded-md pl-2.5 pr-7 py-1.5 text-sm font-mono outline-none cursor-pointer flex-1 min-w-[240px]"
          style="background:{C.page}; border:1px solid {C.border}; color:{C.textPrimary}"
        >
          {#each docs as d (d.id)}<option value={d.id} style="background:{C.surface}">{d.file_name} · {d.status}</option>{/each}
        </select>
        <span class="text-xs" style="color:{C.textMuted}">{docs.length} Dokument(e)</span>
      </div>
    </Card>
  {/if}

  {#if busy}
    <Card class="p-4">
      <div class="flex items-center gap-2 mb-3">
        <Icon name="loader" size={14} class="df-spin" color={C.accent} />
        <span class="text-sm" style="color:{C.textPrimary}">Pipeline läuft — Text → Template → OCR…</span>
      </div>
      <div class="relative h-1.5 rounded-full overflow-hidden" style="background:{C.elevated}">
        <div class="df-bar-indeterminate" style="background:{C.accent2}"></div>
      </div>
    </Card>
  {:else if phase === 'error'}
    <Card class="p-4" style="background:{rgba(C.error, 0.06)}; border-color:{rgba(C.error, 0.3)}">
      <div class="flex items-center gap-2 mb-2"><Icon name="alert-circle" size={16} color={C.error} /><span class="text-sm font-semibold" style="color:{C.error}">Extraktion fehlgeschlagen</span></div>
      <pre class="text-xs font-mono whitespace-pre-wrap" style="color:{rgba(C.error, 0.85)}">{err}</pre>
    </Card>
  {:else if phase === 'success' && result}
    <div class="flex flex-col gap-4">
      <Card class="p-4">
        <div class="flex flex-col gap-0">
          {#each steps as s, i (s.label)}{@render stepRow(s, i === steps.length - 1)}{/each}
        </div>
      </Card>

      <Card class="overflow-hidden">
        <div class="flex items-center gap-3 px-4 py-3 flex-wrap" style="border-bottom:1px solid {C.border}">
          <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" style="background:{rgba(srcColor, 0.12)}; color:{srcColor}; border:1px solid {rgba(srcColor, 0.3)}">
            <Icon name={result.source === 'Template' ? 'layout-template' : 'scan-text'} size={13} />
            Quelle: {result.source}
          </span>
          <span class="text-xs font-mono px-2 py-0.5 rounded" style="background:{C.elevated}; color:{C.textSecondary}">Status: {result.status}</span>
          {#if result.autoSorted}<span class="text-xs font-mono px-2 py-0.5 rounded" style="background:{rgba(C.success, 0.12)}; color:{C.success}">auto-sortiert</span>{/if}
        </div>

        <div class="px-4 pt-3">
          <SegTabs size="sm" active={tab} onChange={(v) => (tab = v)} tabs={[
            { key: 'felder', label: 'Extrahierte Felder' },
            { key: 'pdftext', label: 'PDF-Text' },
            ...(result.doc.template_id ? [{ key: 'template', label: 'Template' }] : []),
          ]} />
        </div>

        <div class="p-4">
          {#if tab === 'felder'}
            {#if shownFields.length}
              <div class="grid grid-cols-2 gap-x-4 gap-y-2.5">
                {#each shownFields as f (f.label)}
                  <div class="flex items-center justify-between gap-2 rounded-md px-2.5 py-2" style="background:{C.page}; border:1px solid {C.border}">
                    <div class="min-w-0">
                      <div class="text-[11px]" style="color:{C.textMuted}">{f.label}</div>
                      <div class="text-sm font-mono truncate" style="color:{C.textPrimary}">{f.value}</div>
                    </div>
                    {#if f.conf != null}<ConfidenceBadge value={f.conf} />{/if}
                  </div>
                {/each}
              </div>
              {#if result.view.positionen?.length}
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
                        {#each result.view.positionen as p (p.nr)}
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
              {/if}
            {:else}
              <EmptyState icon="scan-text" title="Keine strukturierten Felder" subtitle="Nur Rohtext erkannt (kein Template, OCR nicht verfügbar). Siehe Tab „PDF-Text“." />
            {/if}
          {:else if tab === 'pdftext'}
            {#if result.raw}
              <div class="text-xs font-mono mb-2" style="color:{C.textMuted}">{result.raw.length.toLocaleString('de-DE')} Zeichen</div>
              <textarea readonly class="w-full rounded-lg p-3.5 text-xs font-mono outline-none resize-none leading-relaxed" style="background:{C.page}; border:1px solid {C.border}; color:{C.textSecondary}; height:320px">{result.raw}</textarea>
            {:else}
              <EmptyState icon="file-text" title="Keine Textebene" subtitle="Bild-PDF ohne eingebetteten Text." />
            {/if}
          {:else if tab === 'template'}
            <div class="rounded-lg p-3.5" style="background:{C.page}; border:1px solid {C.border}">
              <div class="flex items-center gap-2 mb-1"><Icon name="layout-template" size={14} color={C.success} /><span class="text-sm font-semibold" style="color:{C.textPrimary}">Erkannt per Muster-Match</span></div>
              <div class="text-xs font-mono" style="color:{C.textSecondary}">Template-ID: {result.doc.template_id}</div>
              <div class="text-xs mt-1" style="color:{C.textMuted}">Konfidenz: {result.view.konfidenz}% · Templates verwaltest du im Tab „Templates".</div>
            </div>
          {/if}
        </div>
      </Card>
    </div>
  {/if}
</div>
