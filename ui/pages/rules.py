"""DocuFlow Sortier-Regeln Editor — Visueller WANN→WOHIN→WIE BENENNEN Editor."""

from __future__ import annotations

from nicegui import ui

from core.file_organizer import preview_target_path
from core.models import (
    ConditionField,
    ConditionOperator,
    ExtractionResult,
    RuleCondition,
    SortRule,
)
from core.rules_store import create_rule, save_rules
from ui import design

# Optionen fuer Dropdowns
FIELD_OPTIONS = {e.value: e.value.replace("_", " ").title() for e in ConditionField}
OPERATOR_OPTIONS = {e.value: e.value.replace("_", " ") for e in ConditionOperator}
PLACEHOLDER_OPTIONS = [
    "{absender}", "{datum}", "{jahr}", "{monat}", "{tag}",
    "{rechnungsnr}", "{betrag}", "{typ}", "{waehrung}",
]


def build_rules_editor(app_state: dict) -> None:
    """Baut den Sortier-Regeln-Editor."""
    design.section_header("Sortier-Regeln", "rule")
    ui.label('Regeln werden von oben nach unten geprueft. Erste passende Regel wird angewendet.') \
        .classes(f'text-sm {design.TEXT_SEC} mb-4')

    @ui.refreshable
    def rules_list():
        rules = app_state.get("rules", [])
        if not rules:
            with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-6 w-full'):
                ui.label('Keine Regeln vorhanden').classes(f'{design.TEXT_SEC}')
            return

        for idx, rule in enumerate(rules):
            _build_rule_card(rule, idx, app_state, rules_list.refresh)

    rules_list()
    app_state["refresh_rules"] = rules_list.refresh

    with ui.row().classes('mt-4'):
        def add_rule():
            rules = app_state.get("rules", [])
            new_rule = create_rule(f"Neue Regel {len(rules) + 1}")
            new_rule.priority = len(rules)
            rules.append(new_rule)
            _save_and_refresh(app_state, rules_list.refresh)

        ui.button('Neue Regel', icon='add', on_click=add_rule) \
            .props('no-caps color=primary')


def _build_rule_card(rule: SortRule, idx: int, app_state: dict, refresh_fn) -> None:
    """Baut eine einzelne Regel-Karte."""
    rules = app_state.get("rules", [])

    with ui.card().classes(
        f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-3'
    ).props('flat'):
        # Header
        with ui.row().classes('items-center justify-between w-full mb-3'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('drag_indicator').classes(f'{design.TEXT_MUTED_CLS}')
                ui.label(f'#{idx + 1}').classes(f'text-xs {design.TEXT_MUTED_CLS}')
                name_input = design.dark_input('Regelname', value=rule.name) \
                    .classes('w-64')
                name_input.on('change', lambda e, r=rule: _update_rule_name(r, e.value, app_state, refresh_fn))

            with ui.row().classes('gap-1'):
                enabled_switch = ui.switch(value=rule.enabled) \
                    .props('dense color=blue-5')
                enabled_switch.on('change', lambda e, r=rule: _toggle_enabled(r, e.value, app_state, refresh_fn))

                # Hoch/Runter
                if idx > 0:
                    ui.button(icon='arrow_upward',
                              on_click=lambda i=idx: _move_rule(i, -1, app_state, refresh_fn)) \
                        .props('flat dense round size=sm').classes(f'{design.TEXT_SEC}')
                if idx < len(rules) - 1:
                    ui.button(icon='arrow_downward',
                              on_click=lambda i=idx: _move_rule(i, 1, app_state, refresh_fn)) \
                        .props('flat dense round size=sm').classes(f'{design.TEXT_SEC}')

                ui.button(icon='delete',
                          on_click=lambda i=idx: _delete_rule(i, app_state, refresh_fn)) \
                    .props('flat dense round size=sm color=negative')

        # WANN (Bedingungen)
        with ui.expansion('WANN (Bedingungen)', icon='filter_list') \
                .classes(f'w-full {design.TEXT}').props('dense dark'):
            _build_conditions(rule, app_state, refresh_fn)

        # WOHIN (Zielordner)
        with ui.expansion('WOHIN (Zielordner)', icon='folder') \
                .classes(f'w-full {design.TEXT}').props('dense dark'):
            _build_target(rule, app_state, refresh_fn)

        # WIE BENENNEN (Dateiname)
        with ui.expansion('WIE BENENNEN (Dateiname)', icon='edit') \
                .classes(f'w-full {design.TEXT}').props('dense dark'):
            _build_filename(rule, app_state, refresh_fn)

        # Vorschau
        preview = _get_preview(rule)
        ui.label(f'Vorschau: {preview}').classes(f'text-xs {design.TEXT_MUTED_CLS} mt-2 italic')


def _build_conditions(rule: SortRule, app_state: dict, refresh_fn) -> None:
    """Baut den Bedingungen-Editor."""
    for i, cond in enumerate(rule.conditions):
        with ui.row().classes('w-full items-center gap-2 mb-2'):
            if i > 0:
                logic_sel = design.dark_select('', options=['AND', 'OR'], value=cond.logic) \
                    .classes('w-20')
                logic_sel.on('change', lambda e, c=cond: setattr(c, 'logic', e.value) or _save_and_refresh(app_state, refresh_fn))

            field_sel = design.dark_select('Feld', options=FIELD_OPTIONS, value=cond.field.value) \
                .classes('w-36')
            field_sel.on('change', lambda e, c=cond: setattr(c, 'field', ConditionField(e.value)) or _save_and_refresh(app_state, refresh_fn))

            op_sel = design.dark_select('Operator', options=OPERATOR_OPTIONS, value=cond.operator.value) \
                .classes('w-36')
            op_sel.on('change', lambda e, c=cond: setattr(c, 'operator', ConditionOperator(e.value)) or _save_and_refresh(app_state, refresh_fn))

            val_input = design.dark_input('Wert', value=cond.value).classes('flex-grow')
            val_input.on('change', lambda e, c=cond: setattr(c, 'value', e.value) or _save_and_refresh(app_state, refresh_fn))

            ui.button(icon='close',
                      on_click=lambda i=i, r=rule: (r.conditions.pop(i), _save_and_refresh(app_state, refresh_fn))) \
                .props('flat dense round size=sm color=negative')

    def add_cond():
        rule.conditions.append(RuleCondition(
            field=ConditionField.SENDER,
            operator=ConditionOperator.CONTAINS,
            value="",
        ))
        _save_and_refresh(app_state, refresh_fn)

    ui.button('+ Bedingung', icon='add', on_click=add_cond) \
        .props('flat dense no-caps color=primary').classes('mt-1')

    if not rule.conditions:
        ui.label('Keine Bedingungen = Fallback-Regel (passt immer)') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} italic')


def _build_target(rule: SortRule, app_state: dict, refresh_fn) -> None:
    """Baut den Zielordner-Editor."""
    base_input = design.dark_input('Basis-Ordner', value=rule.target_base)
    base_input.on('change', lambda e, r=rule: setattr(r, 'target_base', e.value) or _save_and_refresh(app_state, refresh_fn))

    ui.label('Unterordner (Platzhalter kombinierbar):').classes(f'text-xs {design.TEXT_SEC} mt-2')

    with ui.row().classes('gap-2 flex-wrap items-center'):
        for i, sub in enumerate(rule.target_subfolders):
            if i > 0:
                ui.label('/').classes(f'{design.TEXT_MUTED_CLS}')
            opts = list(PLACEHOLDER_OPTIONS)
            if sub not in opts:
                opts.append(sub)
            sub_sel = ui.select(opts, value=sub) \
                .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9 use-input new-value-mode=add') \
                .classes('w-36')
            sub_sel.on('change', lambda e, idx=i, r=rule: _update_list_item(r.target_subfolders, idx, e.value, app_state, refresh_fn))

            ui.button(icon='close',
                      on_click=lambda idx=i, r=rule: (r.target_subfolders.pop(idx), _save_and_refresh(app_state, refresh_fn))) \
                .props('flat dense round size=xs color=negative')

        def add_sub():
            rule.target_subfolders.append("{jahr}")
            _save_and_refresh(app_state, refresh_fn)

        ui.button(icon='add', on_click=add_sub) \
            .props('flat dense round size=sm color=primary')


def _build_filename(rule: SortRule, app_state: dict, refresh_fn) -> None:
    """Baut den Dateiname-Editor."""
    ui.label('Dateiname-Bausteine (werden mit _ verbunden):').classes(f'text-xs {design.TEXT_SEC}')

    with ui.row().classes('gap-2 flex-wrap items-center'):
        for i, part in enumerate(rule.filename_parts):
            if i > 0:
                ui.label('_').classes(f'{design.TEXT_MUTED_CLS} font-bold')
            opts = list(PLACEHOLDER_OPTIONS)
            if part not in opts:
                opts.append(part)
            part_sel = ui.select(opts, value=part) \
                .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9 use-input new-value-mode=add') \
                .classes('w-36')
            part_sel.on('change', lambda e, idx=i, r=rule: _update_list_item(r.filename_parts, idx, e.value, app_state, refresh_fn))

            ui.button(icon='close',
                      on_click=lambda idx=i, r=rule: (r.filename_parts.pop(idx), _save_and_refresh(app_state, refresh_fn))) \
                .props('flat dense round size=xs color=negative')

        ui.label('.pdf').classes(f'{design.TEXT_MUTED_CLS}')

        def add_part():
            rule.filename_parts.append("{datum}")
            _save_and_refresh(app_state, refresh_fn)

        ui.button(icon='add', on_click=add_part) \
            .props('flat dense round size=sm color=primary')


def _get_preview(rule: SortRule) -> str:
    """Erstellt eine Vorschau mit Beispiel-Daten."""
    from datetime import date
    example = ExtractionResult(
        sender="Amazon",
        date=date(2026, 3, 15),
        invoice_number="INV-12345",
        total_amount=99.99,
        currency="EUR",
    )
    return preview_target_path(example, rule)


def _update_rule_name(rule: SortRule, name: str, app_state: dict, refresh_fn) -> None:
    rule.name = name
    _save_and_refresh(app_state, None)


def _toggle_enabled(rule: SortRule, enabled: bool, app_state: dict, refresh_fn) -> None:
    rule.enabled = enabled
    _save_and_refresh(app_state, None)


def _move_rule(idx: int, direction: int, app_state: dict, refresh_fn) -> None:
    rules = app_state.get("rules", [])
    new_idx = idx + direction
    if 0 <= new_idx < len(rules):
        rules[idx], rules[new_idx] = rules[new_idx], rules[idx]
        for i, r in enumerate(rules):
            r.priority = i
        _save_and_refresh(app_state, refresh_fn)


def _delete_rule(idx: int, app_state: dict, refresh_fn) -> None:
    rules = app_state.get("rules", [])
    if 0 <= idx < len(rules):
        rules.pop(idx)
        for i, r in enumerate(rules):
            r.priority = i
        _save_and_refresh(app_state, refresh_fn)


def _update_list_item(lst: list, idx: int, value: str, app_state: dict, refresh_fn) -> None:
    if 0 <= idx < len(lst):
        lst[idx] = value
        _save_and_refresh(app_state, refresh_fn)


def _save_and_refresh(app_state: dict, refresh_fn=None) -> None:
    rules = app_state.get("rules", [])
    save_rules(rules)
    if refresh_fn:
        refresh_fn()
