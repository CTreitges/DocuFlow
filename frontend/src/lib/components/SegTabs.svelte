<script>
  import Icon from './Icon.svelte';
  import { C, clsx } from '../tokens.js';
  let { tabs, active, onChange, size = 'md' } = $props();
  let pad = $derived(size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm');
</script>

<div class="inline-flex rounded-lg p-0.5 gap-0.5" style="background:{C.page}; border:1px solid {C.border}">
  {#each tabs as t}
    {@const on = active === t.key}
    <button
      onclick={() => onChange(t.key)}
      class={clsx('rounded-md font-medium transition-colors flex items-center gap-1.5', pad)}
      style="background:{on ? C.elevated : 'transparent'}; color:{on ? C.textPrimary : C.textSecondary}"
    >
      {#if t.icon}<Icon name={t.icon} size={14} />{/if}
      {t.label}
      {#if t.count != null}<span class="text-[10px] font-mono px-1 rounded" style="background:{on ? C.surface : 'transparent'}; color:{C.textMuted}">{t.count}</span>{/if}
    </button>
  {/each}
</div>
