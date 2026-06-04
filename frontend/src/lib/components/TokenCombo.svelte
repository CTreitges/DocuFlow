<script>
  import Icon from './Icon.svelte';
  import { C } from '../tokens.js';

  // Freitext-Eingabe für ein Ordner-Segment PLUS Platzhalter-Menü. Erlaubt eigene
  // Ordnernamen ("Rechnungen") UND Tokens ("{jahr}") — Tokens werden mit
  // Klartext-Label + Beispielwert angeboten, gespeichert wird das rohe Token.
  let { value, onChange, tokens = [], width = '130px' } = $props();

  let open = $state(false);
  let root;

  function pick(token) {
    onChange(token);
    open = false;
  }

  function onWindowClick(e) {
    if (open && root && !root.contains(e.target)) open = false;
  }
</script>

<svelte:window onclick={onWindowClick} />

<div class="relative inline-flex items-center" bind:this={root}>
  <input
    {value}
    oninput={(e) => onChange(e.currentTarget.value)}
    class="rounded-l-md px-2 py-1.5 text-sm font-mono outline-none"
    style="width:{width}; background:{C.page}; border:1px solid {C.border}; border-right:none; color:{C.textPrimary}"
  />
  <button
    onclick={() => (open = !open)}
    title="Platzhalter einfügen"
    class="px-1.5 py-1.5 rounded-r-md hover:bg-white/5"
    style="background:{C.page}; border:1px solid {C.border}; color:{C.accent}"
  >
    <Icon name="wand-2" size={14} />
  </button>

  {#if open}
    <div
      class="absolute z-30 left-0 top-full mt-1 py-1 rounded-md df-fade-in max-h-64 overflow-auto"
      style="min-width:180px; background:{C.surface}; border:1px solid {C.border}; box-shadow:0 8px 24px rgba(0,0,0,0.4)"
    >
      {#each tokens as t}
        <button
          onclick={() => pick(t.token)}
          class="w-full flex items-center justify-between gap-3 px-3 py-1.5 text-left hover:bg-white/5"
        >
          <span class="text-sm" style="color:{C.textPrimary}">{t.label}</span>
          <span class="text-xs font-mono" style="color:{C.textMuted}">{t.beispiel}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>
