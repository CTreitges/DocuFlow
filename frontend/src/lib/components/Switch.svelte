<script>
  import { C } from '../tokens.js';
  let { checked = false, onChange, disabled = false } = $props();
</script>

<button
  role="switch"
  aria-checked={checked}
  {disabled}
  onclick={() => !disabled && onChange?.(!checked)}
  class="relative inline-flex items-center rounded-full transition-colors shrink-0 disabled:opacity-40"
  style="width:38px; height:22px; background:{checked ? C.accent : C.elevated}; border:1px solid {C.border}"
>
  <span class="inline-block rounded-full bg-white transition-transform" style="width:16px; height:16px; transform:translateX({checked ? 18 : 3}px)"></span>
</button>
