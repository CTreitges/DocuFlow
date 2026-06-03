<script>
  import { onMount } from 'svelte';
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import SectionHeader from '../lib/components/SectionHeader.svelte';
  import EmptyState from '../lib/components/EmptyState.svelte';
  import TextInput from '../lib/components/TextInput.svelte';
  import ConfirmDialog from '../lib/components/ConfirmDialog.svelte';
  import { C, rgba, clsx } from '../lib/tokens.js';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/store.svelte.js';
  import * as MOCK from '../lib/mock.js';

  let rows = $state([]);
  let editId = $state(null);
  let draft = $state(null);
  let confirm = $state(null);
  let reloading = $state(false);

  function toView(t) {
    return {
      id: t.id,
      absender: t.sender_name || t.id,
      muster: (t.sender_patterns || []).length,
      felder: Object.keys(t.field_patterns || {}).length,
      schwelle: Math.round((t.confidence_threshold ?? 0.9) * 100),
      verwendet: t.times_used || 0,
    };
  }

  async function load(showToastOnMock = true) {
    try {
      const tpls = await api.templates();
      rows = tpls.map(toView);
    } catch {
      rows = MOCK.TEMPLATES;
      if (showToastOnMock) toast('info', 'Demo-Daten', 'Backend nicht erreichbar — zeige Design-Beispieldaten.');
    }
  }
  onMount(() => load());

  function startEdit(t) { editId = t.id; draft = { ...t }; }
  function saveEdit() {
    rows = rows.map((r) => (r.id === editId ? draft : r));
    editId = null;
    toast('success', 'Template gespeichert', `${draft.absender} (lokal — Persistenz via Löschen/Neu-Lernen)`);
  }
  async function reload() {
    reloading = true;
    await load(false);
    reloading = false;
    toast('info', 'Templates neu geladen', `${rows.length} Muster aktualisiert.`);
  }
  async function doDelete() {
    const t = confirm;
    confirm = null;
    try {
      await api.deleteTemplate(t.id);
      rows = rows.filter((r) => r.id !== t.id);
      toast('info', 'Template gelöscht', t.absender);
    } catch (e) {
      toast('error', 'Löschen fehlgeschlagen', String(e.message || e));
    }
  }
</script>

<div>
  <SectionHeader icon="wand-2" title="Templates">
    {#snippet right()}
      <Button variant="flat" icon={reloading ? undefined : 'refresh-cw'} onclick={reload} disabled={reloading}>
        {#if reloading}<span class="flex items-center gap-2"><Icon name="loader" size={14} class="df-spin" />Lädt…</span>{:else}Templates neu laden{/if}
      </Button>
    {/snippet}
  </SectionHeader>

  <p class="text-sm mb-4" style="color:{C.textSecondary}">Automatisch generierte Muster für bekannte Absender.</p>

  {#if rows.length === 0}
    <Card class="p-0"><EmptyState icon="wand-2" title="Keine Templates vorhanden" subtitle="Templates werden automatisch erstellt, wenn Dokumente bestätigt werden." /></Card>
  {:else}
    <Card class="overflow-hidden p-0">
      <table class="w-full">
        <thead>
          <tr style="border-bottom:1px solid {C.border}">
            {#each [{ l: 'Absender' }, { l: 'Muster', r: true }, { l: 'Felder', r: true }, { l: 'Schwelle', r: true }, { l: 'Verwendet', r: true }, { l: 'ID' }, { l: '', w: 90 }] as h}
              <th class={clsx('px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider', h.r ? 'text-right' : 'text-left')} style="color:{C.textMuted}; {h.w ? `width:${h.w}px` : ''}">{h.l}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each rows as t (t.id)}
            {@const editing = editId === t.id}
            <tr style="border-bottom:1px solid {C.border}">
              <td class="px-3 py-2.5 text-sm font-semibold" style="color:{C.textPrimary}">
                {#if editing}<TextInput value={draft.absender} onChange={(v) => (draft = { ...draft, absender: v })} class="w-full" />{:else}{t.absender}{/if}
              </td>
              <td class="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style="color:{C.textSecondary}">{t.muster}</td>
              <td class="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style="color:{C.textSecondary}">{t.felder}</td>
              <td class="px-3 py-2.5 text-right">
                {#if editing}
                  <input type="number" value={draft.schwelle} oninput={(e) => (draft = { ...draft, schwelle: +e.currentTarget.value })} class="w-16 rounded-md px-2 py-1 text-sm font-mono text-right outline-none" style="background:{C.page}; border:1px solid {C.accent}; color:{C.textPrimary}" />
                {:else}<span class="text-sm font-mono tabular-nums" style="color:{C.textSecondary}">{t.schwelle}%</span>{/if}
              </td>
              <td class="px-3 py-2.5 text-sm font-mono text-right tabular-nums" style="color:{C.textSecondary}">{t.verwendet}</td>
              <td class="px-3 py-2.5 text-xs font-mono" style="color:{rgba(C.textMuted, 0.6)}">{t.id}</td>
              <td class="px-3 py-2.5">
                <div class="flex items-center justify-end gap-1">
                  {#if editing}
                    <button onclick={saveEdit} title="Speichern" class="p-1.5 rounded-md" style="background:{rgba(C.success, 0.14)}; color:{C.success}"><Icon name="check" size={14} /></button>
                    <button onclick={() => (editId = null)} title="Abbrechen" class="p-1.5 rounded-md" style="background:{C.elevated}; color:{C.textSecondary}"><Icon name="x" size={14} /></button>
                  {:else}
                    <button onclick={() => startEdit(t)} title="Bearbeiten" class="p-1.5 rounded-md hover:bg-white/5" style="color:{C.textSecondary}"><Icon name="pencil" size={14} /></button>
                    <button onclick={() => (confirm = t)} title="Löschen" class="p-1.5 rounded-md hover:bg-white/5" style="color:{C.error}"><Icon name="trash" size={14} /></button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </Card>
  {/if}

  <ConfirmDialog
    open={!!confirm}
    title="Template löschen?"
    body={confirm ? `Das Template „${confirm.absender}" wird entfernt. Bereits sortierte Dokumente bleiben unverändert.` : ''}
    confirmLabel="Löschen"
    danger
    onConfirm={doDelete}
    onCancel={() => (confirm = null)}
  />
</div>
