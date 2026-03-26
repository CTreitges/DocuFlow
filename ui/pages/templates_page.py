"""DocuFlow Templates-Seite — Verwaltung der erkannten Absender-Templates."""

from __future__ import annotations

from pathlib import Path

from nicegui import ui

from core import config
from core.template_matcher import load_templates
from ui import design


def build_templates(app_state: dict) -> None:
    """Baut die Template-Verwaltungsseite."""
    cfg = config.get()
    tpl_dir = cfg.get("templates", {}).get("path", "./templates")

    design.section_header("Templates", "auto_fix_high")
    ui.label('Automatisch generierte Muster fuer bekannte Absender.') \
        .classes(f'text-sm {design.TEXT_SEC} mb-4')

    @ui.refreshable
    def templates_list():
        templates = load_templates(tpl_dir)

        if not templates:
            with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-6 w-full'):
                with ui.column().classes('items-center gap-2 w-full'):
                    ui.icon('auto_fix_high', size='xl').classes(f'{design.TEXT_MUTED_CLS}')
                    ui.label('Keine Templates vorhanden').classes(f'{design.TEXT_SEC}')
                    ui.label('Templates werden automatisch erstellt wenn Dokumente bestaetigt werden.') \
                        .classes(f'text-xs {design.TEXT_MUTED_CLS}')
            return

        row_data = []
        for tpl in templates:
            row_data.append({
                "id": tpl.id,
                "sender": tpl.sender_name,
                "patterns": len(tpl.sender_patterns),
                "fields": len(tpl.field_patterns),
                "threshold": f"{tpl.confidence_threshold:.0%}",
                "used": tpl.times_used,
            })

        ui.aggrid({
            'defaultColDef': {'sortable': True, 'resizable': True},
            'columnDefs': [
                {'headerName': 'Absender', 'field': 'sender', 'flex': 2, 'cellClass': 'font-medium'},
                {'headerName': 'Muster', 'field': 'patterns', 'width': 90},
                {'headerName': 'Felder', 'field': 'fields', 'width': 90},
                {'headerName': 'Schwelle', 'field': 'threshold', 'width': 100},
                {'headerName': 'Verwendet', 'field': 'used', 'width': 100},
                {'headerName': 'ID', 'field': 'id', 'flex': 1, 'cellClass': 'text-xs opacity-50'},
            ],
            'rowData': row_data,
            'rowSelection': 'single',
        }).classes('w-full h-64').props('dark')

    templates_list()

    with ui.row().classes('mt-3'):
        ui.button('Templates neu laden', icon='refresh',
                  on_click=templates_list.refresh) \
            .props('flat no-caps color=primary')
