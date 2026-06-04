<script>
  import Icon from '../lib/components/Icon.svelte';
  import Switch from '../lib/components/Switch.svelte';
  import Select from '../lib/components/Select.svelte';
  import TextInput from '../lib/components/TextInput.svelte';
  import TokenCombo from '../lib/components/TokenCombo.svelte';
  import RuleSection from './_RuleSection.svelte';
  import { C } from '../lib/tokens.js';
  import { previewPath, viewToRule } from '../lib/adapters.js';
  import { api } from '../lib/api.js';
  import { RULE_FIELDS, RULE_LOGIC, TOKEN_OPTIONS, TOKEN_CATALOG, operatorsFor } from '../lib/mock.js';

  let { rule, index, sections, isDragging, isOver, example = null, canPickFolder = false,
        onUpdate, onToggle, onDelete, onDragStart, onDragEnter, onDragEnd, onDrop } = $props();

  let grabbable = $state(false);

  const setCond = (i, f) => onUpdate({ conditions: rule.conditions.map((c, j) => (j === i ? { ...c, ...f } : c)) });
  // Feldwechsel: Operator zurücksetzen, falls er für den neuen Feldtyp ungültig ist
  // (sonst bliebe z.B. "enthält" auf dem Zahlen-Feld "Betrag" stehen).
  function setField(i, field) {
    const ops = operatorsFor(field);
    const cur = rule.conditions[i].operator;
    setCond(i, { field, operator: ops.includes(cur) ? cur : ops[0] });
  }
  const addCond = () => onUpdate({ conditions: [...rule.conditions, { logic: 'UND', field: 'Absender', operator: 'enthält', value: '' }] });
  const rmCond = (i) => onUpdate({ conditions: rule.conditions.filter((_, j) => j !== i) });
  const setSub = (i, v) => onUpdate({ subfolders: rule.subfolders.map((s, j) => (j === i ? v : s)) });
  const addSub = () => onUpdate({ subfolders: [...rule.subfolders, '{absender}'] });
  const rmSub = (i) => onUpdate({ subfolders: rule.subfolders.filter((_, j) => j !== i) });
  const setName = (i, v) => onUpdate({ nameParts: rule.nameParts.map((s, j) => (j === i ? v : s)) });
  const addName = () => onUpdate({ nameParts: [...rule.nameParts, '{rechnungsnr}'] });
  const rmName = (i) => onUpdate({ nameParts: rule.nameParts.filter((_, j) => j !== i) });

  // Live-Vorschau: echter Backend-Pfad (inkl. Sanitisierung) via /api/rules/preview,
  // debounced. Offline / Fehler → statische Vorschau aus dem Token-Katalog.
  let preview = $state(previewPath(rule));
  let previewTimer;
  $effect(() => {
    const snap = { b: rule.baseFolder, s: rule.subfolders, n: rule.nameParts, c: rule.conditions }; // Tracking
    void snap;
    clearTimeout(previewTimer);
    previewTimer = setTimeout(async () => {
      try {
        const res = await api.rulePreview(viewToRule(rule, 0), example);
        preview = res?.preview || previewPath(rule);
      } catch {
        preview = previewPath(rule);
      }
    }, 400);
    return () => clearTimeout(previewTimer);
  });

  async function pickFolder() {
    try {
      const folder = await window.pywebview?.api?.pick_folder?.();
      if (folder) onUpdate({ baseFolder: folder });
    } catch { /* Dialog abgebrochen */ }
  }

  let hasOpen = $derived(sections && (sections.wann || sections.wohin || sections.wie));
</script>

<div
  draggable={grabbable}
  ondragstart={onDragStart}
  ondragenter={onDragEnter}
  ondragover={(e) => e.preventDefault()}
  ondragend={() => { grabbable = false; onDragEnd(); }}
  ondrop={onDrop}
  role="listitem"
  class="rounded-xl transition-all"
  style="background:{C.surface}; border:1px solid {isOver ? C.accent : C.border}; opacity:{isDragging ? 0.4 : 1}; box-shadow:{isOver ? `0 0 0 1px ${C.accent}` : 'none'}"
>
  <div class="flex items-center gap-3 px-4 py-3" style="border-bottom:{hasOpen ? `1px solid ${C.border}` : 'none'}">
    <div
      onmousedown={() => (grabbable = true)}
      onmouseup={() => (grabbable = false)}
      title="Ziehen zum Sortieren"
      role="button"
      tabindex="-1"
      class="cursor-grab active:cursor-grabbing p-1 -ml-1 rounded hover:bg-white/5"
      style="color:{C.textMuted}"
    >
      <Icon name="grip-vertical" size={16} />
    </div>
    <span class="text-xs font-mono px-1.5 py-0.5 rounded shrink-0" style="background:{C.elevated}; color:{C.textMuted}">#{index}</span>
    <input value={rule.name} oninput={(e) => onUpdate({ name: e.currentTarget.value })} class="flex-1 min-w-0 bg-transparent text-sm font-semibold outline-none rounded px-1 py-0.5 focus:bg-black/20" style="color:{C.textPrimary}" />
    <div class="flex items-center gap-3 shrink-0">
      <div class="flex items-center gap-1.5">
        <span class="text-xs" style="color:{C.textMuted}">Aktiv</span>
        <Switch checked={rule.enabled} onChange={(v) => onUpdate({ enabled: v })} />
      </div>
      <button onclick={onDelete} title="Regel löschen" class="p-1.5 rounded-md hover:bg-white/5" style="color:{C.error}"><Icon name="trash" size={15} /></button>
    </div>
  </div>

  <RuleSection label="WANN — Bedingungen" open={sections.wann} onToggle={() => onToggle('wann')}>
    {#if rule.conditions.length === 0}
      <div class="text-xs italic px-1 py-2" style="color:{C.textMuted}">Keine Bedingungen = Fallback-Regel (passt immer)</div>
    {:else}
      <div class="flex flex-col gap-2">
        {#each rule.conditions as c, i (i)}
          <div class="flex items-center gap-2 flex-wrap">
            {#if i === 0}
              <span class="text-xs font-mono font-semibold px-2 py-1.5" style="color:{C.accent}">WENN</span>
            {:else}
              <Select value={c.logic} onChange={(v) => setCond(i, { logic: v })} options={RULE_LOGIC} style="width:80px" />
            {/if}
            <Select value={c.field} onChange={(v) => setField(i, v)} options={RULE_FIELDS} />
            <Select value={c.operator} onChange={(v) => setCond(i, { operator: v })} options={operatorsFor(c.field)} />
            <TextInput value={c.value} onChange={(v) => setCond(i, { value: v })} placeholder="Wert…" class="flex-1 min-w-[120px]" />
            <button onclick={() => rmCond(i)} class="p-1.5 rounded-md hover:bg-white/5" style="color:{C.textMuted}"><Icon name="x" size={15} /></button>
          </div>
        {/each}
      </div>
    {/if}
    <button onclick={addCond} class="mt-2 text-xs flex items-center gap-1.5 hover:underline" style="color:{C.accent}"><Icon name="plus" size={13} />Bedingung</button>
  </RuleSection>

  <RuleSection label="WOHIN — Zielordner" open={sections.wohin} onToggle={() => onToggle('wohin')}>
    <div class="flex items-center gap-2 mb-2">
      <span class="text-xs w-20 shrink-0" style="color:{C.textMuted}">Basis-Ordner</span>
      <TextInput value={rule.baseFolder} onChange={(v) => onUpdate({ baseFolder: v })} mono class="flex-1" />
      {#if canPickFolder}
        <button onclick={pickFolder} title="Ordner auswählen" class="shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-md hover:bg-white/5" style="border:1px solid {C.border}; color:{C.textSecondary}"><Icon name="folder-open" size={14} />Durchsuchen</button>
      {/if}
    </div>
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-xs w-20 shrink-0" style="color:{C.textMuted}">Unterordner</span>
      {#each rule.subfolders as s, i (i)}
        <div class="flex items-center">
          <TokenCombo value={s} onChange={(v) => setSub(i, v)} tokens={TOKEN_CATALOG} />
          <button onclick={() => rmSub(i)} class="p-1 rounded hover:bg-white/5" style="color:{C.textMuted}"><Icon name="x" size={13} /></button>
          {#if i < rule.subfolders.length - 1}<span class="font-mono mx-0.5" style="color:{C.textMuted}">/</span>{/if}
        </div>
      {/each}
      <button onclick={addSub} class="text-xs flex items-center gap-1 px-2 py-1.5 rounded-md hover:bg-white/5" style="color:{C.accent}"><Icon name="plus" size={13} />Hinzufügen</button>
    </div>
  </RuleSection>

  <RuleSection label="WIE BENENNEN — Dateiname" open={sections.wie} onToggle={() => onToggle('wie')}>
    <div class="flex items-center gap-1.5 flex-wrap">
      {#each rule.nameParts as s, i (i)}
        <div class="flex items-center">
          <Select value={s} onChange={(v) => setName(i, v)} options={TOKEN_OPTIONS} />
          <button onclick={() => rmName(i)} class="p-1 rounded hover:bg-white/5" style="color:{C.textMuted}"><Icon name="x" size={13} /></button>
          {#if i < rule.nameParts.length - 1}<span class="font-mono mx-0.5" style="color:{C.textMuted}">_</span>{/if}
        </div>
      {/each}
      <span class="font-mono text-sm px-1" style="color:{C.textMuted}">.pdf</span>
      <button onclick={addName} class="text-xs flex items-center gap-1 px-2 py-1.5 rounded-md hover:bg-white/5" style="color:{C.accent}"><Icon name="plus" size={13} />Baustein</button>
    </div>
  </RuleSection>

  <div class="px-4 py-2.5 flex items-center gap-2" style="border-top:1px solid {C.border}; background:rgba(0,0,0,0.15)">
    <Icon name="corner-down-right" size={13} color={C.textMuted} class="shrink-0" />
    <span class="text-xs font-mono italic truncate" style="color:{C.info}">{preview}</span>
  </div>
</div>
