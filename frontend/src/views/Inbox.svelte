<script>
  import { onMount } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import StatusBadge from '../lib/components/StatusBadge.svelte';
  import ConfidenceBadge from '../lib/components/ConfidenceBadge.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import SegTabs from '../lib/components/SegTabs.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import ReviewPanel from './ReviewPanel.svelte';
  import { C, rgba, clsx } from '../lib/tokens.js';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/store.svelte.js';
  import { docToView, applyEdit } from '../lib/adapters.js';
  import * as MOCK from '../lib/mock.js';

  let docs = $state([]);
  let live = $state(true);
  let tab = $state('eingang');
  let selectedId = $state(null);
  let sort = $state({ key: 'datum', dir: 'desc' });
  let scanLabel = $state({ text: '', busy: false });

  const cols = [
    { key: 'filename', label: 'Dateiname', w: '24%' },
    { key: 'status', label: 'Status', w: '110px' },
    { key: 'absender', label: 'Absender', w: '20%' },
    { key: 'datum', label: 'Datum', w: '110px' },
    { key: 'betrag', label: 'Betrag', w: '130px', right: true },
    { key: 'reNr', label: 'Re-Nr.', w: '130px' },
    { key: 'konfidenz', label: 'Konfidenz', w: '100px', right: true },
  ];

  let inboxDocs = $derived(docs.filter((d) => d.status !== 'verarbeitet' && d.status !== 'ignoriert'));
  let ignoredDocs = $derived(docs.filter((d) => d.status === 'ignoriert'));
  let selected = $derived(docs.find((d) => d.id === selectedId));
  let selectedVisible = $derived(selected && selected.status !== 'verarbeitet' && selected.status !== 'ignoriert');

  let sorted = $derived.by(() => {
    const arr = [...inboxDocs];
    arr.sort((a, b) => {
      let av = a[sort.key] ?? '', bv = b[sort.key] ?? '';
      if (sort.key === 'konfidenz') { av = a.konfidenz; bv = b.konfidenz; }
      if (av < bv) return sort.dir === 'asc' ? -1 : 1;
      if (av > bv) return sort.dir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  });
  const toggleSort = (key) => (sort = { key, dir: sort.key === key && sort.dir === 'asc' ? 'desc' : 'asc' });

  function patchLocal(id, fields) { docs = docs.map((d) => (d.id === id ? { ...d, ...fields } : d)); }
  function selectNextAfter(id) {
    const next = inboxDocs.find((x) => x.id !== id);
    selectedId = next ? next.id : null;
  }

  function synthExtraction(d) {
    const k = d.konfidenz || 71;
    return {
      absender: { value: d.absender !== '—' ? d.absender : 'Unbekannt', conf: k },
      datum: { value: d.datum !== '—' ? d.datum : '2026-03-18', conf: Math.max(60, k - 4) },
      rechnungsnr: { value: d.reNr !== '—' ? d.reNr : 'RG-00000', conf: Math.max(60, k - 8) },
      betrag: { value: d.betrag !== '—' ? d.betrag : '0,00 EUR', conf: Math.max(60, k - 6) },
      iban: { value: 'DE—' }, kundennr: { value: '—' }, mwst: { value: '19 %' },
      zahlungsziel: { value: '14 Tage netto' }, dokumenttyp: { value: 'Rechnung' },
    };
  }

  async function reload(selectFirst = false) {
    const data = await api.documents();
    docs = data.map(docToView);
    live = true;
    if (selectFirst || (selectedId && !docs.find((d) => d.id === selectedId))) {
      const first = docs.find((d) => d.status !== 'verarbeitet' && d.status !== 'ignoriert');
      if (selectFirst) selectedId = first ? first.id : null;
    }
  }

  onMount(async () => {
    try {
      await reload(true);
    } catch {
      docs = MOCK.DOCUMENTS.map((d) => ({ ...d }));
      live = false;
      selectedId = 'd1';
      scanLabel = { text: '3 neue Dokumente gefunden', busy: false };
      toast('info', 'Demo-Daten', 'Backend nicht erreichbar — zeige Design-Beispieldaten.');
    }
  });

  async function scanFolder() {
    scanLabel = { text: 'Scanne Ordner…', busy: true };
    if (live) {
      try {
        const r = await api.scan();
        await reload();
        scanLabel = { text: `${r.new} neue(s) Dokument(e) gefunden`, busy: false };
        toast('info', 'Scan abgeschlossen', 'Überwachte Ordner geprüft.');
      } catch (e) { scanLabel = { text: 'Scan fehlgeschlagen', busy: false }; toast('error', 'Fehler', String(e.message || e)); }
    } else {
      setTimeout(() => { scanLabel = { text: `${inboxDocs.length} Dokumente im Eingang`, busy: false }; toast('info', 'Scan abgeschlossen', 'Überwachte Ordner geprüft (Demo).'); }, 1200);
    }
  }

  async function processAll() {
    const queue = inboxDocs.filter((d) => d.status === 'neu');
    if (!queue.length) { toast('info', 'Nichts zu verarbeiten', 'Keine neuen Dokumente im Eingang.'); return; }
    scanLabel = { text: `Verarbeite ${queue.length}…`, busy: true };
    if (live) {
      try { const r = await api.processAll(); await reload(); scanLabel = { text: `${r.processed} Dokumente verarbeitet`, busy: false }; toast('success', 'Verarbeitung fertig', `${r.processed} Dokumente bereit zur Prüfung.`); }
      catch (e) { scanLabel = { text: 'Fehler', busy: false }; toast('error', 'Fehler', String(e.message || e)); }
    } else {
      let i = 0;
      const step = () => {
        i++; scanLabel = { text: `Verarbeite ${i}/${queue.length}…`, busy: true };
        const d = queue[i - 1];
        patchLocal(d.id, { status: 'review', extraction: synthExtraction(d), positionen: d.positionen || [{ nr: 1, beschreibung: 'Position 1', menge: '1', gesamt: d.betrag !== '—' ? d.betrag : '0,00 EUR' }] });
        if (i < queue.length) setTimeout(step, 600);
        else setTimeout(() => { scanLabel = { text: `${queue.length} Dokumente verarbeitet`, busy: false }; toast('success', 'Verarbeitung fertig', `${queue.length} Dokumente bereit zur Prüfung.`); }, 600);
      };
      setTimeout(step, 300);
    }
  }

  async function processOne(d) {
    scanLabel = { text: `Verarbeite ${d.filename}…`, busy: true };
    if (live) {
      try { await api.process(d._raw.id); await reload(); scanLabel = { text: '1 Dokument verarbeitet', busy: false }; toast('success', 'Verarbeitet', `${d.filename} bereit zur Prüfung.`); }
      catch (e) { scanLabel = { text: 'Fehler', busy: false }; toast('error', 'Fehler', String(e.message || e)); }
    } else {
      setTimeout(() => { patchLocal(d.id, { status: 'review', extraction: synthExtraction(d), positionen: [{ nr: 1, beschreibung: 'Position 1', menge: '1', gesamt: d.betrag !== '—' ? d.betrag : '0,00 EUR' }] }); scanLabel = { text: '1 Dokument verarbeitet', busy: false }; toast('success', 'Verarbeitet', `${d.filename} bereit zur Prüfung.`); }, 1300);
    }
  }

  async function retry(d) {
    if (live) return processOne(d);
    scanLabel = { text: `Neuer Versuch: ${d.filename}…`, busy: true };
    setTimeout(() => { patchLocal(d.id, { status: 'review', error: undefined, extraction: synthExtraction({ ...d, konfidenz: 74 }), positionen: [{ nr: 1, beschreibung: 'Erkannte Position', menge: '1', gesamt: '142,00 EUR' }] }); scanLabel = { text: 'Erneut verarbeitet', busy: false }; toast('success', 'Erfolg', 'OCR-Fallback hat funktioniert.'); }, 1600);
  }

  async function confirmSort(d) {
    if (live) {
      try { await api.confirm(d._raw.id); await reload(); toast('success', 'Bestätigt & sortiert', d.filename); selectNextAfter(d.id); }
      catch (e) { toast('error', 'Fehler', String(e.message || e)); }
    } else { patchLocal(d.id, { status: 'verarbeitet' }); toast('success', 'Bestätigt & sortiert', `${d.filename} → D:/Rechnungen/2026/…`); selectNextAfter(d.id); }
  }

  async function ignore(d) {
    if (live) { try { await api.ignore(d._raw.id); await reload(); } catch (e) { toast('error', 'Fehler', String(e.message || e)); return; } }
    else patchLocal(d.id, { status: 'ignoriert' });
    toast('info', 'Ignoriert', d.filename); selectNextAfter(d.id);
  }

  async function reactivate(d) {
    if (live) { try { await api.reactivate(d._raw.id); await reload(); } catch (e) { toast('error', 'Fehler', String(e.message || e)); return; } }
    else patchLocal(d.id, { status: 'neu' });
    toast('success', 'Reaktiviert', d.filename);
  }

  async function editField(d, key, value) {
    if (live) {
      try { const ext = applyEdit(d._raw, key, value); await api.updateExtraction(d._raw.id, ext); await reload(); toast('success', 'Feld aktualisiert', `${key}: ${value}`); }
      catch (e) { toast('error', 'Speichern fehlgeschlagen', String(e.message || e)); }
    } else {
      docs = docs.map((x) => (x.id === d.id ? { ...x, extraction: { ...x.extraction, [key]: { ...x.extraction[key], value } } } : x));
      toast('success', 'Feld aktualisiert', `${key}: ${value}`);
    }
  }
</script>

<div>
  <SectionHeader icon="inbox" title="Eingang">
    {#snippet right()}
      <div class="flex items-center gap-2">
        <Button variant="flat" icon="search" onclick={scanFolder} disabled={scanLabel.busy}>Ordner scannen</Button>
        <Button variant="primary" icon="zap" onclick={processAll} disabled={scanLabel.busy}>Alle verarbeiten</Button>
      </div>
    {/snippet}
  </SectionHeader>

  <div class="flex items-center justify-between mb-3">
    <SegTabs active={tab} onChange={(v) => (tab = v)} tabs={[
      { key: 'eingang', label: 'Eingang', icon: 'inbox', count: inboxDocs.length },
      { key: 'ignoriert', label: 'Ignoriert', icon: 'ban', count: ignoredDocs.length },
    ]} />
    <div class="flex items-center gap-2 text-xs font-mono" style="color:{scanLabel.busy ? C.accent : C.textMuted}">
      {#if scanLabel.busy}<Icon name="loader" size={13} class="df-spin" />{/if}
      {scanLabel.text}
    </div>
  </div>

  {#if tab === 'eingang'}
    {#if inboxDocs.length === 0}
      <Card class="p-0">
        <EmptyState icon="inbox" title="Keine neuen Dokumente" subtitle="Klicke auf »Ordner scannen«, um überwachte Ordner nach neuen PDFs zu durchsuchen.">
          {#snippet action()}<Button variant="flat" icon="search" onclick={scanFolder}>Ordner scannen</Button>{/snippet}
        </EmptyState>
      </Card>
    {:else}
      <Card class="overflow-hidden p-0">
        <table class="w-full border-collapse">
          <thead>
            <tr style="border-bottom:1px solid {C.border}">
              {#each cols as c (c.key)}
                <th onclick={() => toggleSort(c.key)} class={clsx('px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider cursor-pointer select-none', c.right ? 'text-right' : 'text-left')} style="color:{C.textMuted}; width:{c.w}">
                  <span class={clsx('inline-flex items-center gap-1', c.right && 'flex-row-reverse')}>
                    {c.label}
                    {#if sort.key === c.key}<Icon name="chevron-down" size={12} color={C.accent} class={sort.dir === 'asc' ? 'rotate-180' : ''} />{/if}
                  </span>
                </th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each sorted as d (d.id)}
              {@const on = d.id === selectedId}
              <tr
                onclick={() => (selectedId = d.id)}
                class="cursor-pointer transition-colors"
                style="border-bottom:1px solid {C.border}; background:{on ? rgba(C.accent, 0.1) : 'transparent'}; box-shadow:{on ? `inset 2px 0 0 ${C.accent}` : 'none'}"
              >
                <td class="px-3 py-2.5 text-sm font-semibold truncate" style="color:{C.textPrimary}; max-width:0">
                  <span class="flex items-center gap-2"><Icon name="file-text" size={14} color={C.textMuted} class="shrink-0" /><span class="truncate">{d.filename}</span></span>
                </td>
                <td class="px-3 py-2.5"><StatusBadge status={d.status} /></td>
                <td class="px-3 py-2.5 text-sm truncate" style="color:{C.textSecondary}; max-width:0">{d.absender}</td>
                <td class="px-3 py-2.5 text-sm font-mono" style="color:{C.textSecondary}">{d.datum}</td>
                <td class="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style="color:{String(d.betrag).startsWith('−') ? C.error : C.textPrimary}">{d.betrag}</td>
                <td class="px-3 py-2.5 text-sm font-mono" style="color:{C.textSecondary}">{d.reNr}</td>
                <td class="px-3 py-2.5 text-right">{#if d.konfidenz > 0}<ConfidenceBadge value={d.konfidenz} />{:else}<span class="text-xs font-mono" style="color:{C.textMuted}">—</span>{/if}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </Card>
    {/if}
  {:else if ignoredDocs.length === 0}
    <Card class="p-0"><EmptyState icon="ban" title="Keine ignorierten Dokumente" subtitle="Dokumente, die du ignorierst, landen hier und können jederzeit reaktiviert werden." /></Card>
  {:else}
    <div class="grid grid-cols-2 gap-4">
      {#each ignoredDocs as d (d.id)}
        <Card class="p-4 flex items-center gap-3">
          <div class="flex items-center justify-center rounded-lg shrink-0" style="width:38px; height:38px; background:{C.elevated}">
            <Icon name="file-text" size={18} color={C.textMuted} />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-semibold truncate" style="color:{C.textPrimary}">{d.filename}</div>
            <div class="text-xs font-mono mt-0.5" style="color:{C.textMuted}">{d.datum}</div>
          </div>
          <Button variant="flat" size="sm" icon="rotate-ccw" onclick={() => reactivate(d)}>Reaktivieren</Button>
        </Card>
      {/each}
    </div>
  {/if}

  {#if tab === 'eingang' && selectedVisible}
    {#key selected.id}
      <ReviewPanel
        doc={selected}
        onEditField={(k, v) => editField(selected, k, v)}
        onConfirm={() => confirmSort(selected)}
        onIgnore={() => ignore(selected)}
        onClose={() => (selectedId = null)}
        onProcess={() => processOne(selected)}
        onRetry={() => retry(selected)}
      />
    {/key}
  {/if}
</div>
