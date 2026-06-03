<script>
  import { clsx } from '../tokens.js';
  let { color, pulse = false } = $props();
</script>

<span class={clsx('inline-block rounded-full', pulse && 'df-pulse-dot')} style="width:8px; height:8px; background:{color}"></span>
