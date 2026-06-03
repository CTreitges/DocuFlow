<script>
  import Icon from './Icon.svelte';
  import { ui, dismiss } from '../store.svelte.js';
  import { C, rgba } from '../tokens.js';

  const STYLE = {
    success: { color: C.success, icon: 'check-circle' },
    info: { color: C.info, icon: 'alert-circle' },
    error: { color: C.error, icon: 'alert-circle' },
    warning: { color: C.warning, icon: 'alert-triangle' },
  };
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2" style="width:320px">
  {#each ui.toasts as t (t.id)}
    {@const st = STYLE[t.kind] || STYLE.info}
    <div class="df-toast-in flex items-start gap-2.5 rounded-lg px-3.5 py-3" style="background:{C.surface}; border:1px solid {rgba(st.color, 0.4)}; box-shadow:0 8px 30px rgba(0,0,0,0.4)">
      <Icon name={st.icon} size={17} color={st.color} class="mt-px" />
      <div class="flex-1 min-w-0">
        {#if t.title}<div class="text-sm font-medium" style="color:{C.textPrimary}">{t.title}</div>{/if}
        {#if t.body}<div class="text-xs mt-0.5" style="color:{C.textSecondary}">{t.body}</div>{/if}
      </div>
      <button onclick={() => dismiss(t.id)} class="opacity-50 hover:opacity-100 transition-opacity"><Icon name="x" size={14} color={C.textSecondary} /></button>
    </div>
  {/each}
</div>
