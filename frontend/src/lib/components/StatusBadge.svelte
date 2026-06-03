<script>
  import { STATUS, rgba } from '../tokens.js';
  let { status } = $props();
  let s = $derived(STATUS[status] || STATUS.neu);
</script>

<span
  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap"
  style="background:{rgba(s.color, 0.12)}; color:{s.color}; border:1px solid {rgba(s.color, 0.27)}"
>{s.label}</span>
