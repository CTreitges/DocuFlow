"""DocuFlow Debug-Seite — PDF testen, OCR Pipeline, Template-Vorschau."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from nicegui import run as nicegui_run
from nicegui import ui

from core import ocr_engine, pdf_reader, template_generator, template_matcher
from ui import design


def build_debug(app_state: dict) -> None:
    """Baut die Debug/Test-Seite."""
    design.section_header("OCR Debug", "bug_report")

    # Hinweis
    with ui.row().classes('items-center gap-2 mb-4'):
        ui.icon('info_outline').classes(f'text-sm {design.TEXT_MUTED_CLS}')
        ui.label('PDF auswählen → Pipeline läuft → Extrahierte Daten + Template-Vorschau') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS}')

    # Aktions-Zeile
    with ui.row().classes('items-center gap-3 mb-3'):
        ui.button('PDF auswählen', icon='upload_file',
                  on_click=lambda: _pick_and_process(app_state, status_label, spinner,
                                                     progress_bar, result_container)) \
            .props('no-caps color=primary')
        ui.button('Leeren', icon='clear_all',
                  on_click=lambda: _clear(status_label, spinner, progress_bar, result_container)) \
            .props('no-caps flat color=grey-5')

    # Status + Spinner
    with ui.row().classes('items-center gap-2 mb-1'):
        spinner = ui.spinner('dots', size='sm', color='blue-5')
        spinner.set_visibility(False)
        status_label = ui.label('Keine PDF geladen').classes(f'text-sm {design.TEXT_SEC}')

    # Fortschrittsbalken
    progress_bar = ui.linear_progress(value=0, show_value=False) \
        .props('color=blue-5 rounded').classes('w-full mb-4')
    progress_bar.set_visibility(False)

    # Ergebnis
    result_container = ui.column().classes('w-full gap-4')


def _open_pdf_dialog() -> str | None:
    """Öffnet nativen Windows-Datei-Dialog via PowerShell (kein GUI-Thread-Konflikt mit pywebview)."""
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.OpenFileDialog; "
        "$d.Filter = 'PDF-Dateien (*.pdf)|*.pdf|Alle Dateien (*.*)|*.*'; "
        "$d.Title = 'PDF auswählen'; "
        "$d.Multiselect = $false; "
        "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.FileName }"
    )
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    result = subprocess.run(
        ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
        capture_output=True, text=True, timeout=120,
        creationflags=flags,
    )
    path = result.stdout.strip()
    return path if path else None


def _clear(status_label, spinner, progress_bar, result_container) -> None:
    result_container.clear()
    status_label.set_text('Keine PDF geladen')
    spinner.set_visibility(False)
    progress_bar.set_visibility(False)
    progress_bar.set_value(0)


async def _pick_and_process(app_state, status_label, spinner, progress_bar, result_container) -> None:
    """Datei-Dialog öffnen und PDF verarbeiten."""
    path_str = await nicegui_run.io_bound(_open_pdf_dialog)
    if not path_str:
        return
    await _process_pdf(Path(path_str), app_state, status_label, spinner, progress_bar, result_container)


async def _process_pdf(
    pdf_path: Path,
    app_state: dict,
    status_label,
    spinner,
    progress_bar,
    result_container,
) -> None:
    """Verarbeitet eine PDF durch die komplette Pipeline."""
    spinner.set_visibility(True)
    progress_bar.set_visibility(True)
    progress_bar.set_value(0.05)
    status_label.set_text(f'Lese {pdf_path.name}…')
    result_container.clear()

    try:
        processor = app_state['processor']
        cfg = app_state['cfg']

        # Stufe 1: Text-Extraktion
        has_text = pdf_reader.has_text(pdf_path)
        raw_text = pdf_reader.extract_text(pdf_path) if has_text else ''
        page_count = pdf_reader.get_page_count(pdf_path)
        progress_bar.set_value(0.2)
        status_label.set_text(
            f'{pdf_path.name} — {page_count} Seite(n), {len(raw_text)} Zeichen. Prüfe Templates…'
        )

        # Stufe 2: Template-Matching
        templates = processor._templates
        matched_tpl, tpl_score = (
            template_matcher.match_template(raw_text, templates)
            if raw_text else (None, 0.0)
        )
        progress_bar.set_value(0.35)

        if matched_tpl:
            extraction = template_matcher.extract_with_template(raw_text, matched_tpl)
            source = f'Template: {matched_tpl.sender_name} ({tpl_score:.0%})'
            used_ocr = False
            progress_bar.set_value(0.95)
            status_label.set_text(f'✓ Template: {matched_tpl.sender_name}')
        else:
            status_label.set_text('Kein Template — Ollama OCR läuft… (kann 30–120 Sek. dauern)')

            # Fortschritt animieren während OCR läuft
            ocr_running = True

            async def advance():
                steps = [0.42, 0.5, 0.58, 0.65, 0.72, 0.79, 0.85, 0.89]
                for v in steps:
                    await asyncio.sleep(10)
                    if ocr_running:
                        progress_bar.set_value(v)

            asyncio.ensure_future(advance())

            ollama_cfg = cfg.get('ollama', {})
            extraction = await ocr_engine.extract_from_pdf(
                pdf_path,
                ollama_url=ollama_cfg.get('url', 'http://localhost:11434'),
                model=ollama_cfg.get('model', 'glm-ocr'),
                timeout=ollama_cfg.get('timeout', 120),
            )
            ocr_running = False
            source = 'Ollama GLM-OCR'
            used_ocr = True
            status_label.set_text(
                f'✓ OCR fertig — Absender: {extraction.sender or "unbekannt"}'
            )

        progress_bar.set_value(1.0)
        spinner.set_visibility(False)

        with result_container:
            _render_results(extraction, source, raw_text, page_count, has_text, used_ocr)

        await asyncio.sleep(0.5)
        progress_bar.set_visibility(False)

    except Exception as ex:
        status_label.set_text(f'Fehler: {ex}')
        spinner.set_visibility(False)
        progress_bar.set_visibility(False)
        design.notify_error(str(ex))


def _render_results(extraction, source: str, raw_text: str,
                    page_count: int, has_text: bool, used_ocr: bool) -> None:

    with ui.row().classes('items-center gap-3 mb-1'):
        ui.badge('GLM-OCR' if used_ocr else 'Template',
                 color='blue' if used_ocr else 'positive').props('rounded')
        ui.label(source).classes(f'text-sm font-medium {design.TEXT}')
        ui.label(f'{page_count} Seite(n)').classes(f'text-xs {design.TEXT_MUTED_CLS}')
        ui.label('Text-PDF' if has_text else 'Bild-PDF').classes(f'text-xs {design.TEXT_MUTED_CLS}')

    with ui.tabs().props('dense align=left').classes(f'{design.TEXT}') as result_tabs:
        ui.tab('felder', label='Extrahierte Felder', icon='data_object')
        ui.tab('template', label='Template-Vorschau', icon='code')
        ui.tab('rohtext', label='Rohtext', icon='article')

    with ui.tab_panels(result_tabs, value='felder').classes('w-full'):

        with ui.tab_panel('felder').classes('p-0'):
            with ui.card().classes(
                f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full'
            ).props('flat'):
                with ui.grid(columns=2).classes('w-full gap-x-6 gap-y-3'):
                    _field('Absender', extraction.sender, extraction.confidence.get('sender'))
                    _field('Datum', str(extraction.date or ''), extraction.confidence.get('date'))
                    _field('Rechnungsnr.', extraction.invoice_number,
                           extraction.confidence.get('invoice_number'))
                    _field('Betrag',
                           f'{extraction.total_amount:.2f} {extraction.currency}'
                           if extraction.total_amount else '',
                           extraction.confidence.get('total_amount'))
                    _field('MwSt-Satz', f'{extraction.vat_rate}%' if extraction.vat_rate else '', None)
                    _field('MwSt-Betrag',
                           f'{extraction.vat_amount:.2f}' if extraction.vat_amount else '', None)
                    _field('IBAN', extraction.iban, None)
                    _field('Kundennr.', extraction.customer_number, None)
                    _field('Zahlungsziel', str(extraction.due_date or ''), None)
                    _field('Dokumenttyp', extraction.document_type.value, None)

                if extraction.line_items:
                    ui.separator().classes(f'my-3 {design.BORDER}')
                    ui.label('Positionen').classes(
                        f'text-xs font-semibold {design.TEXT_MUTED_CLS} uppercase tracking-wider mb-1'
                    )
                    for i, item in enumerate(extraction.line_items):
                        with ui.row().classes(
                            f'w-full gap-4 py-1 {"border-t " + design.BORDER if i > 0 else ""}'
                        ):
                            ui.label(item.description).classes(f'text-sm {design.TEXT} flex-grow')
                            if item.quantity:
                                ui.label(f'× {item.quantity}').classes(f'text-xs {design.TEXT_SEC}')
                            if item.total:
                                ui.label(f'{item.total:.2f}').classes(f'text-sm font-medium {design.TEXT}')

        with ui.tab_panel('template').classes('p-0'):
            with ui.card().classes(
                f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full'
            ).props('flat'):
                if extraction.sender:
                    tpl = template_generator.generate_template(extraction, raw_text)
                    ui.label('Dieses Template würde beim Bestätigen gespeichert:') \
                        .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-2')
                    ui.code(_template_to_yaml(tpl), language='yaml').classes('w-full text-xs')
                else:
                    ui.label('Kein Absender → kein Template generierbar') \
                        .classes(f'text-sm {design.TEXT_SEC}')

        with ui.tab_panel('rohtext').classes('p-0'):
            with ui.card().classes(
                f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full'
            ).props('flat'):
                if raw_text:
                    ui.label(f'{len(raw_text)} Zeichen').classes(
                        f'text-xs {design.TEXT_MUTED_CLS} mb-2'
                    )
                    ui.textarea(value=raw_text) \
                        .props('readonly outlined dense dark') \
                        .classes('w-full font-mono text-xs') \
                        .style('min-height: 280px')
                else:
                    ui.label('Kein Rohtext (Bild-PDF → direkt an OCR)') \
                        .classes(f'text-sm {design.TEXT_SEC}')


def _field(label: str, value: str, confidence: float | None) -> None:
    if confidence is not None:
        if confidence >= 0.8:
            color, badge = design.SUCCESS, f'{confidence:.0%} ✓'
        elif confidence >= 0.5:
            color, badge = design.WARNING, f'{confidence:.0%} ~'
        else:
            color, badge = design.ERROR, f'{confidence:.0%} ✗'
    else:
        color, badge = design.MUTED, ''

    with ui.column().classes('gap-0'):
        with ui.row().classes('items-center justify-between w-full'):
            ui.label(label).classes(f'text-xs {design.TEXT_MUTED_CLS}')
            if badge:
                ui.label(badge).classes(f'text-[10px] font-mono text-[{color}]')
        ui.label(value or '—').classes(f'text-sm {design.TEXT} break-all')


def _template_to_yaml(tpl) -> str:
    lines = [f'id: {tpl.id}', f'sender_name: "{tpl.sender_name}"', 'sender_patterns:']
    for p in tpl.sender_patterns:
        lines.append(f'  - "{p}"')
    lines.append('field_patterns:')
    for k, v in tpl.field_patterns.items():
        lines.append(f'  {k}: "{v}"')
    lines.append(f'confidence_threshold: {tpl.confidence_threshold}')
    return '\n'.join(lines)
