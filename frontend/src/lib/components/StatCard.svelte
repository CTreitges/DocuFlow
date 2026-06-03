<script>
  import Icon from './Icon.svelte';
  import Card from './Card.svelte';
  import { C, rgba } from '../tokens.js';
  let { label, value, icon, color } = $props();
</script>

<Card class="p-4">
  <div class="flex items-center justify-between mb-3">
    <span class="text-xs font-medium" style="color:{C.textSecondary}">{label}</span>
    <div class="flex items-center justify-center rounded-lg" style="width:30px; height:30px; background:{rgba(color, 0.12)}">
      <Icon name={icon} size={16} color={color} />
    </div>
  </div>
  <div class="text-2xl font-bold tabular-nums" style="color:{C.textPrimary}">{value}</div>
</Card>
