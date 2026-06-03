<script>
  import Card from '../lib/components/Card.svelte';
  import Icon from '../lib/components/Icon.svelte';
  import Button from '../lib/components/Button.svelte';
  import StatusBadge from '../lib/components/StatusBadge.svelte';
  import EditableField from '../lib/components/EditableField.svelte';
  import { C, rgba } from '../lib/tokens.js';

  let { doc, onEditField, onConfirm, onIgnore, onClose, onProcess, onRetry } = $props();

  let variant = $derived(doc.status === 'fehler' ? 'error' : doc.extraction ? 'extraction' : 'unprocessed');
  const ex = (k) => doc.extraction?.[k] || { value: '' };
</script>

<Card class="mt-4 df-fade-in overflow-hidden">
  <div class="flex items-center justify-between px-4 py-3" style="border-bottom:1px solid {C.border}; background:rgba(0,0,0,0.15)">
    <div class="min-w-0">
      <div class="flex items-center gap-2.5">
        <Icon name="file-text" size={16} color={C.accent} />
        <span class="text-sm font-semibold" style="color:{C.textPrimary}">{doc.filename}</span>
        <StatusBadge status={doc.status} />
      </div>
      <div class="text-xs font-mono mt-1 ml-6 truncate" style="color:{C.textMuted}">{doc.path}</div>
    </div>
    <button onclick={onClose} class="p-1.5 rounded-md hover:bg-white/5"><Icon name="x" size={16} color={C.textSecondary} /></button>
  </div>

  <div class="p-4">
    {#if variant === 'unprocessed'}
      <div class="flex flex-col items-center text-center py-6">
        <Icon name="file-search" size={26} color={C.textMuted} class="mb-3" />
        <div class="text-sm font-medium mb-1" style="color:{C.textPrimary}">Noch nicht verarbeitet</div>
        <div class="text-xs mb-4" style="color:{C.textMuted}">Starte die Extraktion, um Felder zu erkennen.</div>
        <div class="flex gap-2">
          <Button variant="primary" icon="zap" onclick={onProcess}>Jetzt verarbeiten</Button>
          <Button variant="ghost" icon="ban" onclick={onIgnore}>Ignorieren</Button>
        </div>
      </div>
    {:else if variant === 'error'}
      <div>
        <div class="rounded-lg p-4 mb-4" style="background:{rgba(C.error, 0.08)}; border:1px solid {rgba(C.error, 0.3)}">
          <div class="flex items-center gap-2 mb-2">
            <Icon name="alert-circle" size={16} color={C.error} />
            <span class="text-sm font-semibold" style="color:{C.error}">Verarbeitung fehlgeschlagen</span>
          </div>
          <pre class="text-xs font-mono whitespace-pre-wrap leading-relaxed" style="color:{rgba(C.error, 0.85)}">{doc.error || 'Unbekannter Fehler.'}</pre>
        </div>
        <div class="flex gap-2">
          <Button variant="amber" icon="rotate-cw" onclick={onRetry}>Nochmal versuchen</Button>
          <Button variant="ghost" icon="ban" onclick={onIgnore}>Ignorieren</Button>
        </div>
      </div>
    {:else}
      <div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3">
          <EditableField label="Absender" value={ex('absender').value} confidence={ex('absender').conf} onSave={(v) => onEditField('absender', v)} />
          <EditableField label="Datum" value={ex('datum').value} confidence={ex('datum').conf} mono onSave={(v) => onEditField('datum', v)} />
          <EditableField label="Rechnungsnr." value={ex('rechnungsnr').value} confidence={ex('rechnungsnr').conf} mono onSave={(v) => onEditField('rechnungsnr', v)} />
          <EditableField label="Betrag" value={ex('betrag').value} confidence={ex('betrag').conf} mono onSave={(v) => onEditField('betrag', v)} />
          <EditableField label="IBAN" value={ex('iban').value} mono onSave={(v) => onEditField('iban', v)} />
          <EditableField label="Kundennr." value={ex('kundennr').value} mono onSave={(v) => onEditField('kundennr', v)} />
          <EditableField label="MwSt-Satz" value={ex('mwst').value} readOnly />
          <EditableField label="Zahlungsziel" value={ex('zahlungsziel').value} readOnly />
          <EditableField label="Dokumenttyp" value={ex('dokumenttyp').value} readOnly />
        </div>

        {#if doc.positionen && doc.positionen.length > 0}
          <div class="mt-5">
            <div class="text-[11px] font-semibold uppercase tracking-wider mb-2" style="color:{C.textMuted}">Positionen</div>
            <div class="rounded-lg overflow-hidden" style="border:1px solid {C.border}">
              <table class="w-full">
                <thead><tr style="background:rgba(0,0,0,0.2)">
                  <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:40px">#</th>
                  <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}">Beschreibung</th>
                  <th class="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:80px">Menge</th>
                  <th class="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wider" style="color:{C.textMuted}; width:130px">Gesamt</th>
                </tr></thead>
                <tbody>
                  {#each doc.positionen as p (p.nr)}
                    <tr style="border-top:1px solid {C.border}">
                      <td class="px-3 py-2 text-sm font-mono" style="color:{C.textMuted}">{p.nr}</td>
                      <td class="px-3 py-2 text-sm" style="color:{C.textPrimary}">{p.beschreibung}</td>
                      <td class="px-3 py-2 text-sm font-mono text-right" style="color:{C.textSecondary}">{p.menge}</td>
                      <td class="px-3 py-2 text-sm font-mono text-right tabular-nums" style="color:{C.textPrimary}">{p.gesamt}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}

        <div class="flex items-center gap-2 mt-5">
          <Button variant="success" icon="check-circle" onclick={onConfirm}>Bestätigen &amp; Sortieren</Button>
          <Button variant="ghost" icon="ban" onclick={onIgnore}>Ignorieren</Button>
          <Button variant="ghost" icon="x" onclick={onClose}>Schließen</Button>
        </div>
      </div>
    {/if}
  </div>
</Card>
