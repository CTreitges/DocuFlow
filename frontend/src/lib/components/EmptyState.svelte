<script>
  import Icon from './Icon.svelte';
  import { C } from '../tokens.js';
  let { icon, title, subtitle, action } = $props();
</script>

<div class="flex flex-col items-center justify-center text-center py-16 px-6">
  <div class="flex items-center justify-center rounded-2xl mb-4" style="width:56px; height:56px; background:{C.elevated}; border:1px solid {C.border}">
    <Icon name={icon} size={26} color={C.textMuted} />
  </div>
  <div class="text-sm font-semibold mb-1" style="color:{C.textPrimary}">{title}</div>
  {#if subtitle}<div class="text-xs max-w-xs leading-relaxed" style="color:{C.textMuted}">{subtitle}</div>{/if}
  {#if action}<div class="mt-4">{@render action()}</div>{/if}
</div>
