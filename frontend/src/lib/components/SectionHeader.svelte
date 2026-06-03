<script>
  import Icon from './Icon.svelte';
  import { C } from '../tokens.js';
  let { icon, title, right } = $props();
</script>

<div class="flex items-center justify-between mb-5">
  <div class="flex items-center gap-2.5">
    <Icon name={icon} size={20} color={C.accent} />
    <h1 class="text-lg font-semibold whitespace-nowrap" style="color:{C.textPrimary}">{title}</h1>
  </div>
  {@render right?.()}
</div>
