"""DocuFlow Inbox-Seite — Neue Dokumente sichten, verarbeiten, bestaetigen."""

from __future__ import annotations

from nicegui import ui

from core.models import DocumentStatus
from ui import design


def build_inbox(app_state: dict) -> None:
    """Baut die Inbox-Seite."""
    db = app_state["db"]

    design.section_header("Eingang", "inbox")

    # Toolbar
    with ui.row().classes('w-full gap-3 items-center mb-4'):
        ui.button('Ordner scannen', icon='search', on_click=lambda: _scan(app_state)) \
            .props('no-caps color=primary')
        ui.button('Alle verarbeiten', icon='play_arrow',
                  on_click=lambda: _process_all(app_state)) \
            .props('no-caps outline color=primary')
        ui.space()
        status_label = ui.label('').classes(f'text-sm {design.TEXT_SEC}')
        app_state["inbox_status"] = status_label

    # Sub-Tabs
    with ui.tabs().props('dense align=left').classes(f'mb-0 {design.TEXT}') as sub_tabs:
        tab_eingang = ui.tab('eingang', label='Eingang', icon='inbox')
        tab_ignoriert = ui.tab('ignoriert', label='Ignoriert', icon='do_not_disturb')

    with ui.tab_panels(sub_tabs, value='eingang').classes('w-full'):

        # === Tab: Eingang ===
        with ui.tab_panel('eingang').classes('p-0 pt-3'):

            @ui.refreshable
            def doc_table():
                docs = db.get_documents()
                active = [d for d in docs
                          if d.status.value not in ("verarbeitet", "ignoriert")]

                if not active:
                    with ui.card().classes(
                        f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-8 w-full'
                    ):
                        with ui.column().classes('items-center gap-3 w-full'):
                            ui.icon('inbox', size='xl').classes(design.TEXT_MUTED_CLS)
                            ui.label('Keine neuen Dokumente').classes(
                                f'text-base {design.TEXT_SEC}'
                            )
                            ui.label('Klicke "Ordner scannen" um nach neuen PDFs zu suchen.') \
                                .classes(f'text-sm {design.TEXT_MUTED_CLS}')
                    return

                row_data = []
                for d in active:
                    ext = d.extraction
                    status_display = {
                        "neu": "Neu",
                        "verarbeitung": "In Arbeit",
                        "review": "Review",
                        "fehler": "Fehler",
                    }.get(d.status.value, d.status.value)
                    row_data.append({
                        "id": d.id,
                        "name": d.file_name,
                        "status": status_display,
                        "sender": ext.sender if ext else "",
                        "date": ext.date.isoformat() if ext and ext.date else "",
                        "amount": (
                            f"{ext.total_amount:.2f} {ext.currency}"
                            if ext and ext.total_amount else ""
                        ),
                        "invoice_nr": ext.invoice_number if ext else "",
                        "confidence": _avg_confidence(ext),
                    })

                grid = ui.aggrid({
                    'defaultColDef': {'sortable': True, 'resizable': True},
                    'columnDefs': [
                        {'headerName': 'Dateiname', 'field': 'name', 'flex': 2,
                         'cellStyle': {'fontWeight': '500'}},
                        {'headerName': 'Status', 'field': 'status', 'width': 100,
                         'cellStyle': {
                             'color': 'expression(value == "Review" ? "#60a5fa" : value == "Fehler" ? "#f87171" : "")'
                         }},
                        {'headerName': 'Absender', 'field': 'sender', 'flex': 1},
                        {'headerName': 'Datum', 'field': 'date', 'width': 115},
                        {'headerName': 'Betrag', 'field': 'amount', 'width': 120,
                         'type': 'rightAligned'},
                        {'headerName': 'Re-Nr.', 'field': 'invoice_nr', 'width': 130},
                        {'headerName': 'Konfidenz', 'field': 'confidence', 'width': 90},
                    ],
                    'rowData': row_data,
                    'rowSelection': 'single',
                    'rowHeight': 36,
                    'animateRows': True,
                }).classes('w-full').style('height: 280px').props('dark')

                grid.on('rowClicked', lambda e: _show_detail(e.args['data']['id'], app_state))

                ui.label('Zeile anklicken um Details anzuzeigen') \
                    .classes(f'text-xs {design.TEXT_MUTED_CLS} mt-1')

            doc_table()
            app_state["refresh_inbox"] = doc_table.refresh

            # Detail-Bereich direkt unter der Tabelle im selben Tab
            detail_container = ui.column().classes('w-full mt-2')
            app_state["inbox_detail"] = detail_container

        # === Tab: Ignoriert ===
        with ui.tab_panel('ignoriert').classes('p-0 pt-3'):

            @ui.refreshable
            def ignored_table():
                docs = db.get_documents()
                ignored = [d for d in docs if d.status == DocumentStatus.IGNORED]

                if not ignored:
                    with ui.card().classes(
                        f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-8 w-full'
                    ):
                        with ui.column().classes('items-center gap-3 w-full'):
                            ui.icon('do_not_disturb', size='xl').classes(design.TEXT_MUTED_CLS)
                            ui.label('Keine ignorierten Dokumente').classes(
                                f'text-base {design.TEXT_SEC}'
                            )
                    return

                for d in ignored:
                    with ui.card().classes(
                        f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-3 w-full mb-2'
                    ).props('flat'):
                        with ui.row().classes('items-center w-full gap-3'):
                            ui.icon('description').classes(design.TEXT_MUTED_CLS)
                            ui.label(d.file_name).classes(f'text-sm {design.TEXT} flex-grow')
                            ui.label(d.created_at.strftime('%d.%m.%Y')).classes(
                                f'text-xs {design.TEXT_MUTED_CLS}'
                            )
                            ui.button(
                                'Reaktivieren', icon='undo',
                                on_click=lambda doc=d: _reactivate(
                                    doc.id, app_state, ignored_table.refresh
                                ),
                            ).props('flat no-caps dense color=primary')

            ignored_table()
            app_state["refresh_ignored"] = ignored_table.refresh


async def _scan(app_state: dict) -> None:
    processor = app_state["processor"]
    status = app_state.get("inbox_status")
    if status:
        status.set_text("Scanne Ordner…")
    new_docs = processor.scan_input_folders()
    if status:
        status.set_text(f"{len(new_docs)} neue Dokument(e) gefunden")
    fn = app_state.get("refresh_inbox")
    if fn:
        fn()


async def _process_all(app_state: dict) -> None:
    processor = app_state["processor"]
    db = app_state["db"]
    status = app_state.get("inbox_status")

    docs = db.get_documents(DocumentStatus.NEW)
    if not docs:
        design.notify_info("Keine neuen Dokumente zum Verarbeiten")
        return

    if status:
        status.set_text(f"Verarbeite {len(docs)} Dokument(e)…")

    for i, doc in enumerate(docs, 1):
        await processor.process_document(doc)
        if status:
            status.set_text(f"Verarbeitet: {i}/{len(docs)}")

    design.notify_success(f"{len(docs)} Dokument(e) verarbeitet")
    fn = app_state.get("refresh_inbox")
    if fn:
        fn()


def _ignore_document(doc_id: int, app_state: dict) -> None:
    db = app_state["db"]
    doc = db.get_document(doc_id)
    if not doc:
        return
    doc.status = DocumentStatus.IGNORED
    db.update_document(doc)
    db.add_history(doc.id, "ignoriert", f"Dokument ignoriert: {doc.file_name}")
    design.notify_info(f'"{doc.file_name}" ignoriert')
    for key in ("refresh_inbox", "refresh_ignored"):
        fn = app_state.get(key)
        if fn:
            fn()
    container = app_state.get("inbox_detail")
    if container:
        container.clear()


def _reactivate(doc_id: int, app_state: dict, refresh_ignored_fn) -> None:
    db = app_state["db"]
    doc = db.get_document(doc_id)
    if not doc:
        return
    doc.status = DocumentStatus.NEW
    db.update_document(doc)
    db.add_history(doc.id, "reaktiviert", f"Dokument reaktiviert: {doc.file_name}")
    design.notify_success(f'"{doc.file_name}" reaktiviert')
    refresh_ignored_fn()
    fn = app_state.get("refresh_inbox")
    if fn:
        fn()


def _show_detail(doc_id: int, app_state: dict) -> None:
    db = app_state["db"]
    doc = db.get_document(doc_id)
    if not doc:
        return

    container = app_state.get("inbox_detail")
    if not container:
        return
    container.clear()

    with container:
        with ui.card().classes(
            f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-5 w-full'
        ):
            # Header
            with ui.row().classes('items-center justify-between w-full mb-4'):
                with ui.column().classes('gap-0'):
                    ui.label(doc.file_name).classes(f'text-base font-semibold {design.TEXT}')
                    ui.label(doc.file_path).classes(f'text-xs {design.TEXT_MUTED_CLS}')
                design.status_badge(doc.status.value)

            if doc.extraction:
                _build_extraction_view(doc, app_state)
            else:
                with ui.column().classes('gap-3'):
                    ui.label('Noch nicht verarbeitet').classes(f'text-sm {design.TEXT_SEC}')

                    async def process_single():
                        processor = app_state["processor"]
                        await processor.process_document(doc)
                        _show_detail(doc_id, app_state)
                        fn = app_state.get("refresh_inbox")
                        if fn:
                            fn()

                    with ui.row().classes('gap-2'):
                        ui.button('Jetzt verarbeiten', icon='play_arrow',
                                  on_click=process_single).props('no-caps color=primary')
                        ui.button('Ignorieren', icon='do_not_disturb',
                                  on_click=lambda: _ignore_document(doc_id, app_state)) \
                            .props('no-caps flat color=grey-5')


def _build_extraction_view(doc, app_state: dict) -> None:
    ext = doc.extraction
    if not ext:
        return

    with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-2 mb-4'):
        _confidence_field("Absender", ext.sender, ext.confidence.get("sender", 0))
        _confidence_field("Datum", str(ext.date or ""), ext.confidence.get("date", 0))
        _confidence_field("Rechnungsnr.", ext.invoice_number,
                          ext.confidence.get("invoice_number", 0))
        _confidence_field(
            "Betrag",
            f"{ext.total_amount:.2f} {ext.currency}" if ext.total_amount else "",
            ext.confidence.get("total_amount", 0),
        )
        _confidence_field("MwSt-Satz", f"{ext.vat_rate}%" if ext.vat_rate else "", 0)
        _confidence_field("IBAN", ext.iban, 0)
        _confidence_field("Kundennr.", ext.customer_number, 0)
        _confidence_field("Zahlungsziel", str(ext.due_date or ""), 0)
        _confidence_field("Dokumenttyp", ext.document_type.value, 0)

    if ext.line_items:
        ui.label('Positionen').classes(f'text-xs font-semibold {design.TEXT_MUTED_CLS} uppercase tracking-wider mb-1')
        items_data = [
            {"#": i + 1, "beschreibung": item.description,
             "menge": item.quantity or "", "gesamt": item.total or ""}
            for i, item in enumerate(ext.line_items)
        ]
        ui.aggrid({
            'columnDefs': [
                {'headerName': '#', 'field': '#', 'width': 45},
                {'headerName': 'Beschreibung', 'field': 'beschreibung', 'flex': 2},
                {'headerName': 'Menge', 'field': 'menge', 'width': 75},
                {'headerName': 'Gesamt', 'field': 'gesamt', 'width': 95},
            ],
            'rowData': items_data,
        }).classes('w-full').style('height: 120px').props('dark')

    ui.separator().classes(f'my-3 {design.BORDER}')

    with ui.row().classes('gap-2'):
        def do_confirm():
            processor = app_state["processor"]
            result = processor.confirm_and_sort(doc)
            if result:
                design.notify_success(f"Sortiert: {result}")
            else:
                design.notify_info("Bestätigt (keine Sortier-Regel)")
            fn = app_state.get("refresh_inbox")
            if fn:
                fn()
            c = app_state.get("inbox_detail")
            if c:
                c.clear()

        ui.button('Bestätigen & Sortieren', icon='check',
                  on_click=do_confirm).props('no-caps color=positive')
        ui.button('Ignorieren', icon='do_not_disturb',
                  on_click=lambda: _ignore_document(doc.id, app_state)) \
            .props('no-caps flat color=grey-5')
        ui.button('Schließen', icon='close',
                  on_click=lambda: app_state.get("inbox_detail", ui.column()).clear()) \
            .props('no-caps flat color=grey-5')


def _confidence_field(label: str, value: str, confidence: float) -> None:
    if confidence >= 0.8:
        color = design.SUCCESS
    elif confidence >= 0.5:
        color = design.WARNING
    elif confidence > 0:
        color = design.ERROR
    else:
        color = design.MUTED

    with ui.column().classes('gap-0'):
        with ui.row().classes('items-center gap-1'):
            ui.label(label).classes(f'text-xs {design.TEXT_MUTED_CLS}')
            if confidence > 0:
                ui.icon('circle', size='8px').classes(f'text-[{color}]')
        ui.label(value or '—').classes(f'text-sm {design.TEXT}')


def _avg_confidence(ext) -> str:
    if not ext or not ext.confidence:
        return ""
    values = [v for v in ext.confidence.values() if v > 0]
    if not values:
        return ""
    return f"{sum(values) / len(values):.0%}"
