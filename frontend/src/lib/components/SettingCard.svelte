<script>
  import Icon from './Icon.svelte';
  import Card from './Card.svelte';
  import { C, rgba } from '../tokens.js';
  let { title, badge, badgeColor, right, icon, iconColor, children } = $props();
</script>

<Card class="overflow-hidden">
  <div class="flex items-center justify-between px-4 py-3" style="border-bottom:1px solid {C.border}">
    <div class="flex items-center gap-2">
      {#if icon}<Icon name={icon} size={15} color={iconColor || C.accent} />{/if}
      <span class="text-sm font-semibold" style="color:{C.textPrimary}">{title}</span>
      {#if badge}<span class="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded" style="background:{rgba(badgeColor, 0.14)}; color:{badgeColor}; border:1px solid {rgba(badgeColor, 0.3)}">{badge}</span>{/if}
    </div>
    {@render right?.()}
  </div>
  <div class="p-4">{@render children?.()}</div>
</Card>
