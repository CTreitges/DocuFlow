"""DocuFlow Dashboard — Uebersicht und History."""

from __future__ import annotations

from nicegui import ui

from ui import design


def build_dashboard(app_state: dict) -> None:
    """Baut die Dashboard/Sortiert-Seite mit Stats und History."""
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

    @ui.refreshable
    def history_section():
        history = db.get_history(limit=30)
        with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full').props('flat'):
            ui.label('Aktivitäts-Log').classes(f'text-sm font-semibold {design.TEXT} mb-2')
            if history:
                for entry in history:
                    with ui.row().classes(f'w-full items-center gap-3 py-1 {design.BORDER_B}'):
                        _action_icon(entry.get("action", ""))
                        ui.label(entry.get("file_name", "")).classes(f'text-xs font-medium {design.TEXT} w-48')
                        ui.label(entry.get("details", "")).classes(f'text-xs {design.TEXT_SEC} flex-grow')
                        ts = entry.get("timestamp", "")
                        if ts:
                            ui.label(ts[11:16] if len(ts) > 16 else ts) \
                                .classes(f'text-xs {design.TEXT_MUTED_CLS}')
            else:
                ui.label('Noch keine Aktivitäten').classes(f'text-xs {design.TEXT_SEC} italic')

    history_section()
    app_state["refresh_history"] = history_section.refresh


def _action_icon(action: str) -> None:
    icons = {
        "scan": ("search", design.ACCENT),
        "template_match": ("pattern", design.SUCCESS),
        "ocr": ("document_scanner", design.WARNING),
        "sorted": ("check_circle", design.SUCCESS),
        "confirmed": ("thumb_up", design.SUCCESS),
        "error": ("error", design.ERROR),
        "template_created": ("auto_fix_high", design.ACCENT),
    }
    icon_name, color = icons.get(action, ("info", design.MUTED))
    ui.icon(icon_name, size='xs').classes(f'text-[{color}]')
