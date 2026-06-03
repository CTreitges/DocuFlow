<script>
  import { onMount } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import StatCard from '../lib/components/StatCard.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import SegTabs from '../lib/components/SegTabs.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import { C, rgba, clsx } from '../lib/tokens.js';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/store.svelte.js';
  import { historyToActivity, fmtBetrag } from '../lib/adapters.js';
  import * as MOCK from '../lib/mock.js';

  const ACTION_ICON = {
    scan: { icon: 'search', color: C.info },
    template: { icon: 'layout-template', color: C.accent },
    ocr: { icon: 'scan-text', color: C.accent2 },
    sortiert: { icon: 'check-circle', color: C.success },
    'auto-sortiert': { icon: 'zap', color: C.success },
    'bestätigt': { icon: 'thumbs-up', color: C.success },
    fehler: { icon: 'alert-circle', color: C.error },
    'template-erstellt': { icon: 'wand-2', color: C.accent },
    undo: { icon: 'undo', color: C.muted },
    korrektur: { icon: 'pencil', color: C.warning },
    reaktiviert: { icon: 'rotate-ccw', color: C.info },
    ignoriert: { icon: 'ban', color: C.muted },
  };

  let counts = $state({ neu: 0, review: 0, verarbeitet: 0, total: 0 });
  let sorted = $state([]);
  let log = $state([]);
  let period = $state('heute');

  const periodRank = { heute: 0, woche: 1, alles: 2 };
  let filteredLog = $derived(log.filter((e) => periodRank[e.period] <= periodRank[period]));
  let errors = $derived(log.filter((e) => e.type === 'fehler'));

  function dirOf(p) {
    if (!p) return '';
    const parts = String(p).split(/[\\/]/);
    parts.pop();
    return parts.join('/') + '/';
  }

  function sortedDocToView(d) {
    const e = d.extraction || {};
    return {
      filename: (d.sorted_path ? d.sorted_path.split(/[\\/]/).pop() : d.file_name) || d.file_name,
      absender: e.sender || '—',
      datum: e.date || '—',
      betrag: e.total_amount != null ? fmtBetrag(e.total_amount, e.currency) : '—',
      sortedTo: dirOf(d.sorted_path) || '—',
      processedAt: d.processed_at ? new Date(d.processed_at).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) : '—',
    };
  }

  onMount(async () => {
    try {
      const [stats, sortedDocs, history] = await Promise.all([api.stats(), api.documents('verarbeitet'), api.history(100)]);
      counts = { neu: stats.neu || 0, review: stats.review || 0, verarbeitet: stats.verarbeitet || 0, total: stats.gesamt || 0 };
      sorted = sortedDocs.map(sortedDocToView);
      log = history.map((h) => historyToActivity(h));
    } catch {
      const docs = MOCK.DOCUMENTS;
      counts = {
        neu: docs.filter((d) => d.status === 'neu').length,
        review: docs.filter((d) => d.status === 'review').length,
        verarbeitet: docs.filter((d) => d.status === 'verarbeitet').length,
        total: docs.length,
      };
      sorted = MOCK.SORTED_DOCS;
      log = MOCK.ACTIVITY_LOG;
      toast('info', 'Demo-Daten', 'Backend nicht erreichbar — zeige Design-Beispieldaten.');
    }
  });

  function undo(entry) {
    log = log.map((e) => (e.id === entry.id ? { ...e, undoable: false, type: 'undo', details: 'Sortierung rückgängig gemacht' } : e));
    toast('info', 'Rückgängig gemacht', entry.filename);
  }
</script>

<div>
  <SectionHeader icon="layout-dashboard" title="Dashboard" />

  <div class="grid grid-cols-4 gap-4 mb-4">
    <StatCard label="Neu / Inbox" value={counts.neu} icon="inbox" color={C.accent} />
    <StatCard label="Im Review" value={counts.review} icon="pencil" color={C.warning} />
    <StatCard label="Verarbeitet" value={counts.verarbeitet} icon="check-circle" color={C.success} />
    <StatCard label="Gesamt" value={counts.total} icon="database" color={C.muted} />
  </div>

  <div class="grid grid-cols-2 gap-4">
    <!-- Sortierte Dokumente -->
    <Card class="p-0 overflow-hidden">
      <div class="px-4 py-3 flex items-center gap-2" style="border-bottom:1px solid {C.border}">
        <Icon name="check-circle" size={15} color={C.success} />
        <span class="text-sm font-semibold" style="color:{C.textPrimary}">Sortierte Dokumente</span>
      </div>
      {#if sorted.length === 0}
        <EmptyState icon="box" title="Noch keine sortierten Dokumente" subtitle="Bestätigte Dokumente erscheinen hier mit Zielpfad." />
      {:else}
        <div class="overflow-auto" style="max-height:360px">
          <table class="w-full">
            <thead class="sticky top-0" style="background:{C.surface}">
              <tr style="border-bottom:1px solid {C.border}">
                {#each ['Datei', 'Absender', 'Datum', 'Betrag', 'Sortiert nach', 'Verarbeitet'] as h, i}
                  <th class={clsx('px-3 py-2 text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap', i === 3 ? 'text-right' : 'text-left')} style="color:{C.textMuted}">{h}</th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each sorted as d, i (i)}
                <tr style="border-bottom:1px solid {C.border}">
                  <td class="px-3 py-2 text-sm font-mono truncate" style="color:{C.textPrimary}; max-width:140px">{d.filename}</td>
                  <td class="px-3 py-2 text-sm truncate" style="color:{C.textSecondary}; max-width:120px">{d.absender}</td>
                  <td class="px-3 py-2 text-sm font-mono whitespace-nowrap" style="color:{C.textSecondary}">{d.datum}</td>
                  <td class="px-3 py-2 text-sm font-mono text-right tabular-nums whitespace-nowrap" style="color:{C.textPrimary}">{d.betrag}</td>
                  <td class="px-3 py-2 text-xs font-mono truncate" style="color:{C.info}; max-width:150px">{d.sortedTo}</td>
                  <td class="px-3 py-2 text-xs font-mono whitespace-nowrap" style="color:{C.textMuted}">{d.processedAt}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>

    <!-- Aktivitäts-Log -->
    <Card class="p-0 overflow-hidden flex flex-col">
      <div class="px-4 py-3 flex items-center justify-between" style="border-bottom:1px solid {C.border}">
        <div class="flex items-center gap-2">
          <Icon name="list-filter" size={15} color={C.accent} />
          <span class="text-sm font-semibold" style="color:{C.textPrimary}">Aktivitäts-Log</span>
        </div>
        <SegTabs size="sm" active={period} onChange={(v) => (period = v)} tabs={[{ key: 'heute', label: 'Heute' }, { key: 'woche', label: 'Woche' }, { key: 'alles', label: 'Alles' }]} />
      </div>
      {#if filteredLog.length === 0}
        <div class="py-12 text-center text-sm italic" style="color:{C.textMuted}">Keine Aktivitäten im Zeitraum</div>
      {:else}
        <div class="overflow-auto" style="max-height:360px">
          {#each filteredLog as e (e.id)}
            {@const a = ACTION_ICON[e.type] || ACTION_ICON.scan}
            <div class="flex items-start gap-3 px-4 py-2.5" style="border-top:1px solid {C.border}">
              <div class="flex items-center justify-center rounded-md shrink-0 mt-0.5" style="width:26px; height:26px; background:{rgba(a.color, 0.12)}">
                <Icon name={a.icon} size={14} color={a.color} />
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate" style="color:{C.textPrimary}">{e.filename}</div>
                <div class="text-xs mt-0.5" style="color:{C.textMuted}">{e.details}</div>
              </div>
              <div class="flex flex-col items-end gap-1 shrink-0">
                <span class="text-xs font-mono whitespace-nowrap" style="color:{C.textMuted}">{e.time}</span>
                {#if e.undoable}
                  <button onclick={() => undo(e)} class="text-xs flex items-center gap-1 hover:underline" style="color:{C.accent}"><Icon name="undo" size={12} />Undo</button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </Card>
  </div>

  {#if errors.length > 0}
    <Card class="mt-4 p-0 overflow-hidden" style="border-color:{rgba(C.error, 0.3)}; background:{rgba(C.error, 0.05)}">
      <div class="px-4 py-3 flex items-center gap-2" style="border-bottom:1px solid {rgba(C.error, 0.2)}">
        <Icon name="alert-circle" size={15} color={C.error} />
        <span class="text-sm font-semibold" style="color:{C.error}">Fehler-Log</span>
        <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background:{rgba(C.error, 0.15)}; color:{C.error}">{errors.length}</span>
      </div>
      <div>
        {#each errors as e (e.id)}
          <div class="flex items-center justify-between px-4 py-2.5" style="border-top:1px solid {rgba(C.error, 0.12)}">
            <div class="min-w-0">
              <div class="text-sm font-mono truncate" style="color:{C.textPrimary}">{e.filename}</div>
              <div class="text-xs mt-0.5" style="color:{rgba(C.error, 0.8)}">{e.details}</div>
            </div>
            <span class="text-xs font-mono shrink-0" style="color:{C.textMuted}">{e.time}</span>
          </div>
        {/each}
      </div>
    </Card>
  {/if}
</div>
