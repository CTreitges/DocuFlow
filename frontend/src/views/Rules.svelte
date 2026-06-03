<script>
  import { onMount, onDestroy } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import ConfirmDialog from '../lib/components/ConfirmDialog.svelte';
  import RuleCard from './RuleCard.svelte';
  import { C } from '../lib/tokens.js';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/store.svelte.js';
  import { ruleToView, viewToRule } from '../lib/adapters.js';
  import * as MOCK from '../lib/mock.js';

  let rules = $state([]);
  let openSections = $state({});
  let dragId = $state(null);
  let overId = $state(null);
  let confirm = $state(null);
  let online = $state(true);
  let saveState = $state('idle'); // idle | saving | saved | error

  // Entprellte Speicher-Timer pro Regel-ID (Feldedits). Strukturelle Aktionen
  // (anlegen, löschen, aktivieren, sortieren) speichern sofort.
  const timers = new Map();
  let savedTimer = null;

  function initSections(list) {
    const o = {};
    list.forEach((r) => { o[r.id] = { wann: true, wohin: false, wie: false }; });
    openSections = o;
  }

  onMount(async () => {
    try {
      const data = await api.rules();
      rules = data.map(ruleToView);
      online = true;
    } catch {
      rules = MOCK.RULES.map((r) => ({ ...r }));
      online = false;
      toast('info', 'Demo-Daten', 'Backend nicht erreichbar — Änderungen werden nicht gespeichert.');
    }
    initSections(rules);
  });

  onDestroy(() => {
    timers.forEach((t) => clearTimeout(t));
    clearTimeout(savedTimer);
  });

  function flashSaved() {
    saveState = 'saved';
    clearTimeout(savedTimer);
    savedTimer = setTimeout(() => { if (saveState === 'saved') saveState = 'idle'; }, 1500);
  }

  async function persistRule(rule) {
    if (!online) return;
    saveState = 'saving';
    try {
      const idx = rules.findIndex((r) => r.id === rule.id);
      await api.updateRule(rule.id, viewToRule(rule, idx < 0 ? 0 : idx));
      flashSaved();
    } catch (e) {
      saveState = 'error';
      toast('error', 'Speichern fehlgeschlagen', String(e.message || e));
    }
  }

  function scheduleSave(rule) {
    if (!online) return;
    clearTimeout(timers.get(rule.id));
    timers.set(rule.id, setTimeout(() => persistRule(rule), 600));
  }

  const toggleSection = (id, key) =>
    (openSections = { ...openSections, [id]: { ...openSections[id], [key]: !openSections[id][key] } });

  function update(id, fields) {
    rules = rules.map((r) => (r.id === id ? { ...r, ...fields } : r));
    const rule = rules.find((r) => r.id === id);
    if (!rule) return;
    // Aktiv/Inaktiv ist eine diskrete Aktion → sofort speichern; Feldedits entprellt.
    if ('enabled' in fields) persistRule(rule);
    else scheduleSave(rule);
  }

  async function addRule() {
    const base = {
      name: 'Neue Regel', enabled: true,
      conditions: [{ logic: 'WENN', field: 'Absender', operator: 'enthält', value: '' }],
      baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}'], nameParts: ['{datum}'],
    };
    if (!online) {
      const id = 'r' + Date.now();
      rules = [...rules, { id, ...base }];
      openSections = { ...openSections, [id]: { wann: true, wohin: true, wie: true } };
      toast('info', 'Regel hinzugefügt', 'Offline — wird nicht gespeichert.');
      return;
    }
    saveState = 'saving';
    try {
      const created = await api.createRule(viewToRule({ id: '', ...base }, rules.length));
      const view = ruleToView(created);
      rules = [...rules, view];
      openSections = { ...openSections, [view.id]: { wann: true, wohin: true, wie: true } };
      flashSaved();
      toast('success', 'Regel hinzugefügt', 'Neue Regel gespeichert.');
    } catch (e) {
      saveState = 'error';
      toast('error', 'Anlegen fehlgeschlagen', String(e.message || e));
    }
  }

  async function deleteRule() {
    const target = confirm;
    confirm = null;
    const prev = rules;
    rules = rules.filter((r) => r.id !== target.id);
    clearTimeout(timers.get(target.id));
    if (!online) { toast('info', 'Regel gelöscht', target.name); return; }
    saveState = 'saving';
    try {
      await api.deleteRule(target.id);
      flashSaved();
      toast('info', 'Regel gelöscht', target.name);
    } catch (e) {
      rules = prev; // Rollback bei Fehler
      saveState = 'error';
      toast('error', 'Löschen fehlgeschlagen', String(e.message || e));
    }
  }

  async function onDrop(targetId) {
    if (!dragId || dragId === targetId) { dragId = null; overId = null; return; }
    const from = rules.findIndex((r) => r.id === dragId);
    const to = rules.findIndex((r) => r.id === targetId);
    const next = [...rules];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    rules = next;
    dragId = null; overId = null;
    if (!online) { toast('info', 'Reihenfolge geändert', 'Offline — wird nicht gespeichert.'); return; }
    saveState = 'saving';
    try {
      await api.reorderRules(next.map((r) => r.id));
      flashSaved();
    } catch (e) {
      saveState = 'error';
      toast('error', 'Sortieren fehlgeschlagen', String(e.message || e));
    }
  }
</script>

<div>
  <SectionHeader icon="list-filter" title="Sortier-Regeln">
    {#snippet right()}
      <div class="flex items-center gap-3">
        {#if !online}
          <span class="text-xs flex items-center gap-1.5" style="color:{C.warning}"><Icon name="alert-triangle" size={13} />Demo (offline)</span>
        {:else if saveState === 'saving'}
          <span class="text-xs flex items-center gap-1.5" style="color:{C.textMuted}"><Icon name="loader" size={13} class="df-spin" />Speichert…</span>
        {:else if saveState === 'error'}
          <span class="text-xs flex items-center gap-1.5" style="color:{C.error}"><Icon name="alert-circle" size={13} />Nicht gespeichert</span>
        {:else if saveState === 'saved'}
          <span class="text-xs flex items-center gap-1.5" style="color:{C.success}"><Icon name="check" size={13} />Gespeichert</span>
        {:else}
          <span class="text-xs flex items-center gap-1.5" style="color:{C.textMuted}"><Icon name="check" size={13} color={C.success} />Automatisch gespeichert</span>
        {/if}
        <Button variant="primary" icon="plus" onclick={addRule}>Neue Regel</Button>
      </div>
    {/snippet}
  </SectionHeader>

  <p class="text-sm mb-4 flex items-center gap-2" style="color:{C.textSecondary}">
    <Icon name="arrow-right" size={14} color={C.textMuted} />
    Regeln werden von oben nach unten geprüft. Erste passende gewinnt. Änderungen werden automatisch gespeichert.
  </p>

  {#if rules.length === 0}
    <Card class="p-0">
      <EmptyState icon="list-filter" title="Keine Regeln vorhanden" subtitle="Lege Regeln an, um Dokumente automatisch in Zielordner zu sortieren.">
        {#snippet action()}<Button variant="primary" icon="plus" onclick={addRule}>Neue Regel</Button>{/snippet}
      </EmptyState>
    </Card>
  {:else}
    <div class="flex flex-col gap-4" role="list">
      {#each rules as rule, idx (rule.id)}
        <RuleCard
          {rule}
          index={idx + 1}
          sections={openSections[rule.id]}
          isDragging={dragId === rule.id}
          isOver={overId === rule.id && dragId !== rule.id}
          onUpdate={(f) => update(rule.id, f)}
          onToggle={(k) => toggleSection(rule.id, k)}
          onDelete={() => (confirm = rule)}
          onDragStart={() => (dragId = rule.id)}
          onDragEnter={() => (overId = rule.id)}
          onDragEnd={() => { dragId = null; overId = null; }}
          onDrop={() => onDrop(rule.id)}
        />
      {/each}
    </div>
  {/if}

  <ConfirmDialog open={!!confirm} title="Regel löschen?" body={confirm ? `Die Regel „${confirm.name}“ wird dauerhaft entfernt.` : ''} confirmLabel="Löschen" danger onConfirm={deleteRule} onCancel={() => (confirm = null)} />
</div>
