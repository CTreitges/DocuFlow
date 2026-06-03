<script>
  import Icon from './Icon.svelte';
  import { C, rgba, clsx } from '../tokens.js';

  let { children, variant = 'flat', size = 'md', icon, onclick, disabled = false, class: klass = '', title, style = '' } = $props();

  const variants = {
    primary: { background: C.accent, color: '#fff', border: '1px solid transparent' },
    success: { background: C.success, color: '#04210f', border: '1px solid transparent' },
    amber: { background: C.warning, color: '#241803', border: '1px solid transparent' },
    danger: { background: 'transparent', color: C.error, border: `1px solid ${rgba(C.error, 0.4)}` },
    flat: { background: C.elevated, color: C.textPrimary, border: `1px solid ${C.border}` },
    ghost: { background: 'transparent', color: C.textSecondary, border: '1px solid transparent' },
  };
  const hoverBg = { primary: '#2563eb', success: '#16a34a', amber: '#d97706', danger: rgba(C.error, 0.12), flat: '#3e4c63', ghost: 'rgba(255,255,255,0.06)' };

  let hover = $state(false);
  let v = $derived(variants[variant]);
  let pad = $derived(size === 'sm' ? 'px-2.5 py-1.5 text-xs' : 'px-3.5 py-2 text-sm');
  let bg = $derived(hover && !disabled ? hoverBg[variant] : v.background);
</script>

<button
  {title}
  {disabled}
  {onclick}
  onmouseenter={() => (hover = true)}
  onmouseleave={() => (hover = false)}
  class={clsx('inline-flex items-center gap-2 rounded-lg font-medium transition-colors select-none whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed', pad, klass)}
  style="background:{bg}; color:{v.color}; border:{v.border}; {style}"
>
  {#if icon}<Icon name={icon} size={size === 'sm' ? 14 : 16} />{/if}
  {@render children?.()}
</button>
