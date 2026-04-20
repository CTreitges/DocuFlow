"""DocuFlow Inbox-Seite — Neue Dokumente sichten, verarbeiten, bestätigen."""

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
                             'color': 'expression(value == "Review" ? "#60a5fa" : '
                                      'value == "Fehler" ? "#f87171" : "")'
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
            with ui.row().classes('items-center justify-between w-full mb-4'):
                with ui.column().classes('gap-0'):
                    ui.label(doc.file_name).classes(f'text-base font-semibold {design.TEXT}')
                    ui.label(doc.file_path).classes(f'text-xs {design.TEXT_MUTED_CLS}')
                design.status_badge(doc.status.value)

            if doc.status == DocumentStatus.ERROR:
                _build_error_view(doc, app_state)
            elif doc.extraction:
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


def _build_error_view(doc, app_state: dict) -> None:
    """Zeigt Fehler-Details und Retry-Button."""
    db = app_state["db"]
    history = db.get_history_filtered("alles", limit=20)
    error_detail = ""
    for entry in history:
        if entry.get("document_id") == doc.id and entry.get("action") == "error":
            error_detail = entry.get("details", "")
            break

    with ui.column().classes('gap-3'):
        with ui.card().classes(
            f'border border-[{design.ERROR}44] bg-[{design.ERROR}0d] rounded-xl p-3 w-full'
        ).props('flat'):
            with ui.row().classes('items-center gap-2 mb-1'):
                ui.icon('error_outline', size='sm').classes(f'text-[{design.ERROR}]')
                ui.label('Verarbeitungsfehler').classes(f'text-sm font-semibold text-[{design.ERROR}]')
            if error_detail:
                ui.label(error_detail).classes(f'text-xs {design.TEXT_SEC} font-mono')

        async def _retry():
            processor = app_state["processor"]
            doc.status = DocumentStatus.NEW
            db.update_document(doc)
            db.add_history(doc.id, "retry", "Erneuter Verarbeitungsversuch")
            await processor.process_document(doc)
            _show_detail(doc.id, app_state)
            fn = app_state.get("refresh_inbox")
            if fn:
                fn()

        with ui.row().classes('gap-2'):
            ui.button('Nochmal versuchen', icon='refresh', on_click=_retry) \
                .props('no-caps color=warning')
            ui.button('Ignorieren', icon='do_not_disturb',
                      on_click=lambda: _ignore_document(doc.id, app_state)) \
                .props('no-caps flat color=grey-5')


def _build_extraction_view(doc, app_state: dict) -> None:
    ext = doc.extraction
    if not ext:
        return

    db = app_state["db"]
    processor = app_state["processor"]

    def _save_field(field: str, new_value: str) -> None:
        """Speichert Feld-Korrektur und aktualisiert Template."""
        from datetime import date as dt_date
        if field == "sender":
            ext.sender = new_value
        elif field == "invoice_number":
            ext.invoice_number = new_value
        elif field == "date":
            try:
                ext.date = dt_date.fromisoformat(new_value)
            except ValueError:
                pass
        elif field == "total_amount":
            try:
                ext.total_amount = float(new_value.replace(",", ".").replace("€", "").strip())
            except ValueError:
                pass
        elif field == "iban":
            ext.iban = new_value
        elif field == "customer_number":
            ext.customer_number = new_value
        elif field == "invoice_number":
            ext.invoice_number = new_value

        db.update_document(doc)
        db.add_history(doc.id, "correction", f"Feld '{field}' korrigiert: {new_value}")

        if ext.sender:
            from core import template_generator
            tpl_path = processor.cfg.get("templates", {}).get("path", "./templates")
            tpl = template_generator.generate_template(ext, ext.raw_text)
            template_generator.save_template(tpl, tpl_path)
            processor.reload_templates()

    with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-3 mb-4'):
        _editable_field("Absender", ext.sender, ext.confidence.get("sender", 0),
                        lambda v: _save_field("sender", v))
        _editable_field("Datum",
                        ext.date.isoformat() if ext.date else "",
                        ext.confidence.get("date", 0),
                        lambda v: _save_field("date", v))
        _editable_field("Rechnungsnr.", ext.invoice_number,
                        ext.confidence.get("invoice_number", 0),
                        lambda v: _save_field("invoice_number", v))
        _editable_field(
            "Betrag",
            f"{ext.total_amount:.2f} {ext.currency}" if ext.total_amount else "",
            ext.confidence.get("total_amount", 0),
            lambda v: _save_field("total_amount", v),
        )
        _editable_field("MwSt-Satz", f"{ext.vat_rate}%" if ext.vat_rate else "", 0)
        _editable_field("IBAN", ext.iban, 0, lambda v: _save_field("iban", v))
        _editable_field("Kundennr.", ext.customer_number, 0,
                        lambda v: _save_field("customer_number", v))
        _editable_field("Zahlungsziel", str(ext.due_date or ""), 0)
        _editable_field("Dokumenttyp", ext.document_type.value, 0)

    if ext.line_items:
        ui.label('Positionen').classes(
            f'text-xs font-semibold {design.TEXT_MUTED_CLS} uppercase tracking-wider mb-1'
        )
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
            result = processor.confirm_and_sort(doc)
            if result:
                design.notify_success(f"Sortiert: {result}")
            else:
                design.notify_info("Bestätigt (keine Sortier-Regel)")
            fn = app_state.get("refresh_inbox")
            if fn:
                fn()
            fn2 = app_state.get("refresh_stats")
            if fn2:
                fn2()
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


def _editable_field(label: str, value: str, confidence: float,
                    on_save=None) -> None:
    """Zeigt ein Extraktions-Feld mit Confidence-Badge und optionaler Inline-Bearbeitung."""
    if confidence >= 0.9:
        badge_color = design.SUCCESS
        badge_text = f"{confidence:.0%}"
    elif confidence >= 0.7:
        badge_color = design.WARNING
        badge_text = f"{confidence:.0%}"
    elif confidence > 0:
        badge_color = design.ERROR
        badge_text = f"{confidence:.0%}"
    else:
        badge_color = design.MUTED
        badge_text = ""

    with ui.column().classes('gap-0.5'):
        with ui.row().classes('items-center gap-1 mb-0.5'):
            ui.label(label).classes(f'text-xs {design.TEXT_MUTED_CLS}')
            if badge_text:
                ui.label(badge_text) \
                    .classes('text-[10px] font-mono px-1 py-0 rounded leading-4') \
                    .style(
                        f'background: {badge_color}22; color: {badge_color}; '
                        f'border: 1px solid {badge_color}44'
                    )

        if on_save:
            display_row = ui.row().classes('items-center gap-1')
            with display_row:
                value_label = ui.label(value or '—').classes(f'text-sm {design.TEXT}')
                edit_btn = ui.icon('edit', size='xs') \
                    .classes(f'cursor-pointer opacity-40 hover:opacity-100 {design.TEXT_MUTED_CLS}')

            edit_row = ui.row().classes('items-center gap-1 w-full').style('display: none')
            with edit_row:
                edit_input = design.dark_input('', value=value or '') \
                    .classes('flex-grow').props('dense')

                def _save():
                    new_val = edit_input.value
                    on_save(new_val)
                    value_label.set_text(new_val or '—')
                    edit_row.style('display: none')
                    display_row.style('display: flex')

                def _cancel():
                    edit_row.style('display: none')
                    display_row.style('display: flex')

                def _show_edit():
                    display_row.style('display: none')
                    edit_row.style('display: flex')
                    edit_input.set_value(value_label.text if value_label.text != '—' else '')

                edit_btn.on('click', _show_edit)
                ui.button(icon='check', on_click=_save) \
                    .props('flat dense round size=xs color=positive')
                ui.button(icon='close', on_click=_cancel) \
                    .props('flat dense round size=xs color=grey-5')
        else:
            ui.label(value or '—').classes(f'text-sm {design.TEXT}')


def _avg_confidence(ext) -> str:
    if not ext or not ext.confidence:
        return ""
    values = [v for v in ext.confidence.values() if v > 0]
    if not values:
        return ""
    return f"{sum(values) / len(values):.0%}"
