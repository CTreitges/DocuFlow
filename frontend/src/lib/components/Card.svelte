<script>
  import { C, clsx } from '../tokens.js';
  let { children, class: klass = '', style = '', ...rest } = $props();
</script>

<div class={clsx('rounded-xl', klass)} style="background:{C.surface}; border:1px solid {C.border}; {style}" {...rest}>
  {@render children?.()}
</div>
