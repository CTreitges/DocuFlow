"""DocuFlow Dashboard — Uebersicht, History mit Filter und Undo."""

from __future__ import annotations

from nicegui import ui

from ui import design


def build_dashboard(app_state: dict) -> None:
    """Baut die Dashboard-Seite mit Stats, sortierten Dokumenten und History."""
    db = app_state["db"]

    design.section_header("Dashboard", "dashboard")

    @ui.refreshable
    def stats_section():
        stats = db.get_stats()
        with ui.grid(columns=4).classes('w-full gap-4 mb-6'):
            design.stat_card('Neu / Inbox', str(stats.get("neu", 0)), 'inbox', design.ACCENT)
            design.stat_card('Im Review', str(stats.get("review", 0)), 'rate_review', design.WARNING)
            design.stat_card('Verarbeitet', str(stats.get("verarbeitet", 0)), 'check_circle', design.SUCCESS)
            design.stat_card('Gesamt', str(stats.get("gesamt", 0)), 'folder', design.MUTED)

    stats_section()
    app_state["refresh_stats"] = stats_section.refresh

    @ui.refreshable
    def documents_section():
        from core.models import DocumentStatus
        processed = db.get_documents(DocumentStatus.PROCESSED)

        with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
            ui.label('Sortierte Dokumente').classes(f'text-sm font-semibold {design.TEXT} mb-2')
            if processed:
                row_data = []
                for d in processed[:50]:
                    ext = d.extraction
                    row_data.append({
                        "name": d.file_name,
                        "sender": ext.sender if ext else "",
                        "date": ext.date.isoformat() if ext and ext.date else "",
                        "amount": f"{ext.total_amount:.2f}" if ext and ext.total_amount else "",
                        "sorted_to": d.sorted_path or "—",
                        "processed": d.processed_at.strftime("%d.%m.%Y %H:%M") if d.processed_at else "",
                    })
                ui.aggrid({
                    'defaultColDef': {'sortable': True, 'resizable': True, 'filter': True},
                    'columnDefs': [
                        {'headerName': 'Datei', 'field': 'name', 'flex': 1, 'cellClass': 'font-medium'},
                        {'headerName': 'Absender', 'field': 'sender', 'flex': 1},
                        {'headerName': 'Datum', 'field': 'date', 'width': 110},
                        {'headerName': 'Betrag', 'field': 'amount', 'width': 100, 'type': 'rightAligned'},
                        {'headerName': 'Sortiert nach', 'field': 'sorted_to', 'flex': 2},
                        {'headerName': 'Verarbeitet', 'field': 'processed', 'width': 140},
                    ],
                    'rowData': row_data,
                }).classes('w-full h-64').props('dark')
            else:
                with ui.column().classes('items-center gap-2 py-6 w-full'):
                    ui.icon('inventory_2', size='xl').classes(f'{design.TEXT_MUTED_CLS}')
                    ui.label('Noch keine sortierten Dokumente').classes(f'{design.TEXT_SEC} text-sm')

    documents_section()
    app_state["refresh_documents"] = documents_section.refresh

    # --- History mit Filter und Undo ---
    history_filter = {"value": "alles"}

    @ui.refreshable
    def history_section():
        history = db.get_history_filtered(history_filter["value"], limit=100)
        errors = db.get_error_history(limit=20)

        with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
            with ui.row().classes('items-center justify-between w-full mb-3'):
                ui.label('Aktivitäts-Log').classes(f'text-sm font-semibold {design.TEXT}')

                with ui.button_group().props('flat'):
                    for label, key in [('Heute', 'heute'), ('Woche', 'woche'), ('Alles', 'alles')]:
                        is_active = history_filter["value"] == key
                        color = 'blue-5' if is_active else 'grey-5'

                        def _set_filter(k=key):
                            history_filter["value"] = k
                            history_section.refresh()

                        ui.button(label, on_click=_set_filter) \
                            .props(f'no-caps flat dense color={color}') \
                            .classes('text-xs')

            if history:
                for entry in history:
                    action = entry.get("action", "")
                    doc_id = entry.get("document_id")
                    with ui.row().classes(f'w-full items-center gap-3 py-1.5 {design.BORDER_B}'):
                        _action_icon(action)
                        ui.label(entry.get("file_name", "")).classes(
                            f'text-xs font-medium {design.TEXT} w-44 truncate'
                        )
                        ui.label(entry.get("details", "")).classes(
                            f'text-xs {design.TEXT_SEC} flex-grow truncate'
                        )
                        ts = entry.get("timestamp", "")
                        if ts:
                            ui.label(ts[11:16] if len(ts) > 16 else ts) \
                                .classes(f'text-xs {design.TEXT_MUTED_CLS} w-12')

                        if action == "sorted" and doc_id:
                            def _do_undo(did=doc_id):
                                ok = db.undo_sort(did)
                                if ok:
                                    design.notify_success("Sortierung rückgängig gemacht")
                                    history_section.refresh()
                                    fn = app_state.get("refresh_inbox")
                                    if fn:
                                        fn()
                                    fn2 = app_state.get("refresh_stats")
                                    if fn2:
                                        fn2()
                                else:
                                    design.notify_error("Undo nicht möglich — Datei nicht gefunden")

                            ui.button(icon='undo', on_click=_do_undo) \
                                .props('flat dense round size=xs color=grey-5') \
                                .tooltip('Sortierung rückgängig')
            else:
                ui.label('Keine Aktivitäten im gewählten Zeitraum').classes(
                    f'text-xs {design.TEXT_SEC} italic py-2'
                )

        # --- Fehler-Log ---
        if errors:
            with ui.card().classes(
                f'border border-[{design.ERROR}33] bg-[{design.ERROR}0a] rounded-xl p-4 w-full'
            ).props('flat'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('error_outline', size='sm').classes(f'text-[{design.ERROR}]')
                    ui.label('Fehler-Log').classes(f'text-sm font-semibold text-[{design.ERROR}]')
                for entry in errors:
                    with ui.row().classes(f'w-full items-center gap-3 py-1 {design.BORDER_B}'):
                        ui.icon('error', size='xs').classes(f'text-[{design.ERROR}]')
                        ui.label(entry.get("file_name", "")).classes(
                            f'text-xs font-medium {design.TEXT} w-44 truncate'
                        )
                        ui.label(entry.get("details", "")).classes(
                            f'text-xs text-[{design.ERROR}] flex-grow truncate'
                        )
                        ts = entry.get("timestamp", "")
                        if ts:
                            ui.label(ts[11:16] if len(ts) > 16 else ts) \
                                .classes(f'text-xs {design.TEXT_MUTED_CLS}')

    history_section()
    app_state["refresh_history"] = history_section.refresh


def _action_icon(action: str) -> None:
    icons = {
        "scan": ("search", design.ACCENT),
        "template_match": ("pattern", design.SUCCESS),
        "ocr": ("document_scanner", design.WARNING),
        "sorted": ("check_circle", design.SUCCESS),
        "auto_sorted": ("bolt", design.SUCCESS),
        "confirmed": ("thumb_up", design.SUCCESS),
        "error": ("error", design.ERROR),
        "template_created": ("auto_fix_high", design.ACCENT),
        "undo": ("undo", design.WARNING),
        "correction": ("edit", design.ACCENT),
        "reaktiviert": ("replay", design.ACCENT),
        "ignoriert": ("do_not_disturb", design.MUTED),
    }
    icon_name, color = icons.get(action, ("info", design.MUTED))
    ui.icon(icon_name, size='xs').classes(f'text-[{color}]')
