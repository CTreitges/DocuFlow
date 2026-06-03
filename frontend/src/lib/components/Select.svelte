<script>
  import Icon from './Icon.svelte';
  import { C, clsx } from '../tokens.js';
  let { value, onChange, options, class: klass = '', style = '' } = $props();
</script>

<div class="relative inline-flex">
  <select
    {value}
    onchange={(e) => onChange(e.currentTarget.value)}
    class={clsx('appearance-none rounded-md pl-2.5 pr-7 py-1.5 text-sm outline-none cursor-pointer', klass)}
    style="background:{C.page}; border:1px solid {C.border}; color:{C.textPrimary}; {style}"
  >
    {#each options as o}<option value={o} style="background:{C.surface}">{o}</option>{/each}
  </select>
  <Icon name="chevron-down" size={14} class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" color={C.textMuted} />
</div>
