<script>
  import { onMount } from 'svelte';
  import Icon from './lib/components/Icon.svelte';
  import ToastHost from './lib/components/ToastHost.svelte';
  import Inbox from './views/Inbox.svelte';
  import Dashboard from './views/Dashboard.svelte';
  import Templates from './views/Templates.svelte';
  import Rules from './views/Rules.svelte';
  import Settings from './views/Settings.svelte';
  import OcrDebug from './views/OcrDebug.svelte';
  import { ui, setRoute, toggleSidebar } from './lib/store.svelte.js';
  import { C, rgba, clsx } from './lib/tokens.js';
  import { api } from './lib/api.js';
  import * as MOCK from './lib/mock.js';

  const NAV = [
    { section: 'Verarbeitung', items: [
      { key: 'eingang', label: 'Eingang', icon: 'inbox' },
      { key: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
      { key: 'templates', label: 'Templates', icon: 'wand-2' },
    ] },
    { section: 'System', items: [
      { key: 'regeln', label: 'Sortier-Regeln', icon: 'list-filter' },
      { key: 'einstellungen', label: 'Einstellungen', icon: 'settings' },
      { key: 'ocr', label: 'OCR-Debug', icon: 'bug' },
    ] },
  ];

  const SCREENS = { eingang: Inbox, dashboard: Dashboard, templates: Templates, regeln: Rules, einstellungen: Settings, ocr: OcrDebug };
  let Current = $derived(SCREENS[ui.route] ?? Inbox);

  let inboxCount = $state(0);
  async function refreshCount() {
    try { const s = await api.stats(); inboxCount = s.neu || 0; }
    catch { inboxCount = MOCK.DOCUMENTS.filter((d) => d.status === 'neu').length; }
  }
  onMount(refreshCount);
  // Nach Navigation neu zählen (Inbox-Aktionen ändern die Anzahl).
  $effect(() => { ui.route; refreshCount(); });
</script>

<div class="flex flex-col h-full" style="background:{C.page}">
  <!-- Header -->
  <header class="flex items-center justify-between px-3 shrink-0" style="height:56px; background:{C.surface}; border-bottom:1px solid {C.border}">
    <div class="flex items-center gap-2">
      <button onclick={toggleSidebar} title="Sidebar ein-/ausklappen" class="p-2 rounded-lg hover:bg-white/5 transition-colors" style="color:{C.textSecondary}">
        <Icon name="menu" size={18} />
      </button>
      <div class="flex items-center gap-2 ml-1">
        <div class="flex items-center justify-center rounded-lg" style="width:28px; height:28px; background:{rgba(C.accent, 0.15)}">
          <Icon name="file-text" size={16} color={C.accent} />
        </div>
        <span class="text-base font-semibold tracking-tight" style="color:{C.textPrimary}">DocuFlow</span>
      </div>
    </div>
    <span class="text-xs font-mono mr-2" style="color:{C.textMuted}">v0.2</span>
  </header>

  <div class="flex flex-1 min-h-0">
    <!-- Sidebar -->
    <aside class="shrink-0 flex flex-col py-3 transition-all duration-200" style="width:{ui.collapsed ? 60 : 220}px; background:{C.surface}; border-right:1px solid {C.border}">
      {#each NAV as group, gi (group.section)}
        <div class={gi > 0 ? 'mt-1' : ''}>
          {#if gi > 0}<div class="mx-3 my-2" style="border-top:1px solid {C.border}"></div>{/if}
          {#if !ui.collapsed}<div class="px-4 pt-1 pb-1.5 text-[10px] font-bold uppercase tracking-widest" style="color:{C.textMuted}">{group.section}</div>{/if}
          <nav class="px-2 flex flex-col gap-0.5">
            {#each group.items as item (item.key)}
              {@const on = ui.route === item.key}
              <button
                onclick={() => setRoute(item.key)}
                title={ui.collapsed ? item.label : undefined}
                class={clsx('flex items-center rounded-lg transition-colors w-full', ui.collapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-3 py-2')}
                style="background:{on ? C.elevated : 'transparent'}; color:{on ? C.accent : C.textSecondary}"
                onmouseenter={(e) => { if (!on) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
                onmouseleave={(e) => { if (!on) e.currentTarget.style.background = 'transparent'; }}
              >
                <Icon name={item.icon} size={20} class="shrink-0" strokeWidth={on ? 2.2 : 2} />
                {#if !ui.collapsed}<span class="text-sm font-medium flex-1 text-left">{item.label}</span>{/if}
                {#if !ui.collapsed && item.key === 'eingang' && inboxCount > 0}
                  <span class="text-[10px] font-mono font-semibold rounded-full px-1.5 py-0.5" style="background:{rgba(C.accent, 0.18)}; color:{C.accent}">{inboxCount}</span>
                {/if}
              </button>
            {/each}
          </nav>
        </div>
      {/each}
    </aside>

    <!-- Content -->
    <main class="flex-1 min-w-0 overflow-auto" style="background:{C.page}">
      <div class="p-6">
        {#key ui.route}
          <Current />
        {/key}
      </div>
    </main>
  </div>

  <ToastHost />
</div>
