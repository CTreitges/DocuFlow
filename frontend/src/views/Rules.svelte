<script>
  import { onMount } from 'svelte';
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
  let saving = $state(false);

  function initSections(list) {
    const o = {};
    list.forEach((r) => { o[r.id] = { wann: true, wohin: false, wie: false }; });
    openSections = o;
  }

  onMount(async () => {
    try {
      const data = await api.rules();
      rules = data.map(ruleToView);
    } catch {
      rules = MOCK.RULES.map((r) => ({ ...r }));
      toast('info', 'Demo-Daten', 'Backend nicht erreichbar — zeige Design-Beispieldaten.');
    }
    initSections(rules);
  });

  const update = (id, fields) => (rules = rules.map((r) => (r.id === id ? { ...r, ...fields } : r)));
  const toggleSection = (id, key) => (openSections = { ...openSections, [id]: { ...openSections[id], [key]: !openSections[id][key] } });

  function addRule() {
    const id = 'r' + Date.now();
    rules = [...rules, { id, name: 'Neue Regel', enabled: true, conditions: [{ logic: 'WENN', field: 'Absender', operator: 'enthält', value: '' }], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}'], nameParts: ['{datum}'] }];
    openSections = { ...openSections, [id]: { wann: true, wohin: true, wie: true } };
    toast('success', 'Regel hinzugefügt', 'Neue Regel ans Ende gestellt. „Speichern" nicht vergessen.');
  }

  function deleteRule() {
    rules = rules.filter((r) => r.id !== confirm.id);
    toast('info', 'Regel gelöscht', confirm.name);
    confirm = null;
  }

  function onDrop(targetId) {
    if (!dragId || dragId === targetId) { dragId = null; overId = null; return; }
    const from = rules.findIndex((r) => r.id === dragId);
    const to = rules.findIndex((r) => r.id === targetId);
    const next = [...rules];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    rules = next;
    dragId = null; overId = null;
    toast('info', 'Reihenfolge geändert', 'Regeln werden von oben nach unten geprüft.');
  }

  async function save() {
    saving = true;
    try {
      const payload = rules.map((r, i) => viewToRule(r, i));
      await api.saveRules(payload);
      toast('success', 'Regeln gespeichert', `${payload.length} Regel(n) übernommen.`);
    } catch (e) {
      toast('error', 'Speichern fehlgeschlagen', String(e.message || e));
    }
    saving = false;
  }
</script>

<div>
  <SectionHeader icon="list-filter" title="Sortier-Regeln">
    {#snippet right()}
      <div class="flex items-center gap-2">
        <Button variant="flat" icon={saving ? undefined : 'check'} onclick={save} disabled={saving}>
          {#if saving}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Speichert…</span>{:else}Speichern{/if}
        </Button>
        <Button variant="primary" icon="plus" onclick={addRule}>Neue Regel</Button>
      </div>
    {/snippet}
  </SectionHeader>

  <p class="text-sm mb-4 flex items-center gap-2" style="color:{C.textSecondary}">
    <Icon name="arrow-right" size={14} color={C.textMuted} />
    Regeln werden von oben nach unten geprüft. Erste passende gewinnt.
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

  <ConfirmDialog open={!!confirm} title="Regel löschen?" body={confirm ? `Die Regel „${confirm.name}" wird dauerhaft entfernt.` : ''} confirmLabel="Löschen" danger onConfirm={deleteRule} onCancel={() => (confirm = null)} />
</div>
