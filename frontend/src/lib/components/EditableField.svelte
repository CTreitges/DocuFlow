<script>
  import Icon from './Icon.svelte';
  import ConfidenceBadge from './ConfidenceBadge.svelte';
  import { C, rgba, clsx } from '../tokens.js';

  let { label, value, confidence = null, mono = false, onSave, readOnly = false } = $props();

  let editing = $state(false);
  let draft = $state(value);
  let inputEl = $state(null);

  $effect(() => { draft = value; });

  function startEdit() {
    if (readOnly) return;
    editing = true;
    draft = value;
    queueMicrotask(() => { inputEl?.focus(); inputEl?.select(); });
  }
  function commit() { onSave?.(draft); editing = false; }
  function cancel() { draft = value; editing = false; }
</script>

<div class="min-w-0">
  <div class="flex items-center gap-2 mb-1">
    <span class="text-xs" style="color:{C.textMuted}">{label}</span>
    {#if confidence != null}<ConfidenceBadge value={confidence} />{/if}
    {#if readOnly}<span class="text-[10px] uppercase tracking-wider" style="color:{C.textMuted}">read-only</span>{/if}
  </div>

  {#if editing}
    <div class="flex items-center gap-1.5">
      <input
        bind:this={inputEl}
        bind:value={draft}
        onkeydown={(e) => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') cancel(); }}
        class={clsx('flex-1 min-w-0 rounded-md px-2 py-1.5 text-sm outline-none', mono && 'font-mono')}
        style="background:{C.page}; border:1px solid {C.accent}; color:{C.textPrimary}"
      />
      <button onclick={commit} title="Speichern" class="p-1.5 rounded-md" style="background:{rgba(C.success, 0.14)}; color:{C.success}"><Icon name="check" size={15} /></button>
      <button onclick={cancel} title="Abbrechen" class="p-1.5 rounded-md" style="background:{C.elevated}; color:{C.textSecondary}"><Icon name="x" size={15} /></button>
    </div>
  {:else}
    <div
      class={clsx('group flex items-center justify-between gap-2 rounded-md px-2 py-1.5', !readOnly && 'cursor-text')}
      style="background:{C.page}; border:1px solid {C.border}"
      onclick={startEdit}
      role="button"
      tabindex="0"
      onkeydown={(e) => { if (e.key === 'Enter') startEdit(); }}
    >
      <span class={clsx('text-sm truncate', mono && 'font-mono')} style="color:{value && value !== '—' ? C.textPrimary : C.textMuted}">{value || '—'}</span>
      {#if !readOnly}<Icon name="pencil" size={13} class="opacity-40 group-hover:opacity-100 transition-opacity shrink-0" color={C.textSecondary} />{/if}
    </div>
  {/if}
</div>
