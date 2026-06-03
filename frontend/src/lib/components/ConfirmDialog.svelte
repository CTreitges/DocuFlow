<script>
  import Button from './Button.svelte';
  import { C } from '../tokens.js';
  let { open = false, title, body, confirmLabel = 'Bestätigen', danger = false, onConfirm, onCancel } = $props();
</script>

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center df-fade-in" style="background:rgba(2,6,23,0.6)" onclick={onCancel} role="presentation">
    <div class="df-dialog-in rounded-xl p-5" style="background:{C.surface}; border:1px solid {C.border}; min-width:360px; max-width:440px; box-shadow:0 20px 60px rgba(0,0,0,0.5)" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <h3 class="text-base font-semibold mb-2" style="color:{C.textPrimary}">{title}</h3>
      <p class="text-sm leading-relaxed mb-5" style="color:{C.textSecondary}">{body}</p>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" onclick={onCancel}>Abbrechen</Button>
        <Button variant={danger ? 'danger' : 'primary'} onclick={onConfirm}>{confirmLabel}</Button>
      </div>
    </div>
  </div>
{/if}
