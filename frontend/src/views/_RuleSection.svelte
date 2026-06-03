<script>
  import Icon from '../lib/components/Icon.svelte';
  import { C } from '../lib/tokens.js';
  let { label, open, onToggle, children } = $props();
</script>

<div style="border-bottom:1px solid {C.border}">
  <button onclick={onToggle} class="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/[0.02]">
    <Icon name={open ? 'chevron-down' : 'chevron-right'} size={14} color={C.textMuted} />
    <span class="text-[11px] font-bold uppercase tracking-wider" style="color:{C.textSecondary}">{label}</span>
  </button>
  {#if open}<div class="px-4 pb-3.5 pt-0.5 df-fade-in">{@render children?.()}</div>{/if}
</div>
