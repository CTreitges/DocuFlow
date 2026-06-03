<script>
  import { confColor, rgba } from '../tokens.js';
  let { value } = $props();
  let col = $derived(confColor(value));
</script>

<span
  class="inline-flex items-center rounded-md px-1.5 py-0.5 text-[11px] font-mono font-medium tabular-nums"
  style="background:{rgba(col, 0.12)}; color:{col}; border:1px solid {rgba(col, 0.27)}"
>{value}%</span>
