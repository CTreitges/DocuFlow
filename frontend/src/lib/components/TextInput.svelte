<script>
  import { C, clsx } from '../tokens.js';
  let { value, onChange, placeholder = '', mono = false, class: klass = '', style = '', onkeydown, type = 'text' } = $props();
</script>

<input
  {value}
  {type}
  {placeholder}
  {onkeydown}
  oninput={(e) => onChange(e.currentTarget.value)}
  class={clsx('rounded-md px-2.5 py-1.5 text-sm outline-none', mono && 'font-mono', klass)}
  style="background:{C.page}; border:1px solid {C.border}; color:{C.textPrimary}; {style}"
/>
