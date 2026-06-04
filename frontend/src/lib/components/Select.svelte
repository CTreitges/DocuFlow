<script>
  import Icon from './Icon.svelte';
  import { C, clsx } from '../tokens.js';
  let { value, onChange, options, class: klass = '', style = '' } = $props();

  // Optionen dürfen String ODER { value, label } sein — Label wird angezeigt,
  // value gespeichert (z.B. "Jahr · 2026" anzeigen, "{jahr}" speichern).
  const norm = (o) => (typeof o === 'string' ? { value: o, label: o } : o);
</script>

<div class="relative inline-flex">
  <select
    {value}
    onchange={(e) => onChange(e.currentTarget.value)}
    class={clsx('appearance-none rounded-md pl-2.5 pr-7 py-1.5 text-sm outline-none cursor-pointer', klass)}
    style="background:{C.page}; border:1px solid {C.border}; color:{C.textPrimary}; {style}"
  >
    {#each options as o}{@const opt = norm(o)}<option value={opt.value} style="background:{C.surface}">{opt.label}</option>{/each}
  </select>
  <Icon name="chevron-down" size={14} class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" color={C.textMuted} />
</div>
