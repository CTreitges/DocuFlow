"""DocuFlow Settings-Seite — Konfiguration verwalten."""

from __future__ import annotations

import webview
from nicegui import app as nicegui_app
from nicegui import run as nicegui_run
from nicegui import ui

from core import config
from core.ocr_engine import is_available
from ui import design


def build_settings(app_state: dict) -> None:
    """Baut die Settings-Seite."""
    cfg = config.get()

    design.section_header("Einstellungen", "settings")

    # --- Auto-Modus ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.column().classes('gap-0'):
                ui.label('Auto-Sortierung').classes(f'text-sm font-semibold {design.TEXT}')
                ui.label('Bekannte Absender werden automatisch sortiert, nur neue in der Inbox') \
                    .classes(f'text-xs {design.TEXT_SEC}')
            auto_switch = ui.switch(value=cfg.get("auto_mode", False)) \
                .props('color=blue-5')
            auto_switch.on('change', lambda e: _update_auto_mode(e.value))

    # --- Input-Ordner ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        ui.label('Eingabe-Ordner').classes(f'text-sm font-semibold {design.TEXT} mb-2')
        ui.label('Nur aktivierte Ordner werden beim Scannen berücksichtigt.') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-3')

        @ui.refreshable
        def folders_list():
            folders = cfg.get("input_folders", [])
            for i, folder in enumerate(folders):
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    folder_input = design.dark_input('Pfad', value=folder.get("path", "")) \
                        .classes('flex-grow')
                    folder_input.on('change', lambda e, idx=i: _update_folder_path(idx, e.value))

                    ui.button(
                        icon='folder_open',
                        on_click=lambda idx=i: _pick_folder(idx, folders_list.refresh),
                    ).props('flat dense round size=sm color=blue-5') \
                     .tooltip('Ordner auswählen')

                    enabled_sw = ui.switch(value=folder.get("enabled", True)) \
                        .props('dense color=blue-5')
                    enabled_sw.tooltip('Ordner aktiv')
                    enabled_sw.on('change', lambda e, idx=i: _update_folder_enabled(idx, e.value))

                    ui.button(
                        icon='delete',
                        on_click=lambda idx=i: _remove_folder(idx, folders_list.refresh),
                    ).props('flat dense round size=sm color=negative')

            if not folders:
                ui.label('Keine Ordner konfiguriert').classes(f'text-xs {design.TEXT_SEC} italic')

        folders_list()

        ui.button('Ordner hinzufügen', icon='create_new_folder',
                  on_click=lambda: _add_folder_via_dialog(folders_list.refresh)) \
            .props('flat no-caps color=primary').classes('mt-2')

    # --- Ausgabe-Ordner ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        ui.label('Ausgabe').classes(f'text-sm font-semibold {design.TEXT} mb-2')
        with ui.row().classes('w-full items-center gap-2'):
            output_input = design.dark_input(
                'Basis-Ordner', value=cfg.get("output", {}).get("base_path", "./sorted")
            ).classes('flex-grow')
            output_input.on('change', lambda e: _update_output(e.value))
            ui.button(icon='folder_open', on_click=lambda: _pick_output_folder(output_input)) \
                .props('flat dense round size=sm color=blue-5').tooltip('Ordner auswählen')

    # --- Ollama/OCR ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center justify-between w-full mb-2'):
            ui.label('OCR / Ollama').classes(f'text-sm font-semibold {design.TEXT}')
            _ocr_status_badge(cfg)

        ui.label('Wird nur verwendet wenn kein Absender-Template passt.') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-2')

        ollama_cfg = cfg.get("ollama", {})
        with ui.grid(columns=2).classes('w-full gap-3'):
            url_input = design.dark_input('Ollama URL', value=ollama_cfg.get("url", "http://localhost:11434"))
            url_input.on('change', lambda e: _update_ollama("url", e.value))

            model_input = design.dark_input('Modell', value=ollama_cfg.get("model", "glm-ocr"))
            model_input.on('change', lambda e: _update_ollama("model", e.value))

            timeout_input = design.dark_number('Timeout (Sek)', value=ollama_cfg.get("timeout", 120))
            timeout_input.on('change', lambda e: _update_ollama("timeout", int(e.value) if e.value else 120))

        async def check_ocr():
            available = is_available(
                ollama_cfg.get("url", "http://localhost:11434"),
                ollama_cfg.get("model", "glm-ocr"),
            )
            if available:
                design.notify_success("Ollama + GLM-OCR erreichbar")
            else:
                design.notify_error("Ollama oder GLM-OCR nicht erreichbar")

        ui.button('Verbindung testen', icon='wifi_tethering', on_click=check_ocr) \
            .props('flat no-caps color=primary').classes('mt-2')


async def _pick_folder(idx: int, refresh_fn) -> None:
    """Öffnet OS-Ordner-Dialog und aktualisiert den Pfad."""
    try:
        result = await nicegui_run.io_bound(
            nicegui_app.native.main_window.create_file_dialog,
            webview.FOLDER_DIALOG,
        )
        if result:
            _update_folder_path(idx, result[0])
            refresh_fn()
    except Exception:
        design.notify_error("Ordner-Dialog konnte nicht geöffnet werden")


async def _add_folder_via_dialog(refresh_fn) -> None:
    """Öffnet OS-Ordner-Dialog und fügt neuen Ordner hinzu."""
    try:
        result = await nicegui_run.io_bound(
            nicegui_app.native.main_window.create_file_dialog,
            webview.FOLDER_DIALOG,
        )
        if result:
            cfg = config.get()
            folders = cfg.get("input_folders", [])
            folders.append({"path": result[0], "enabled": True})
            config.save()
            refresh_fn()
    except Exception:
        design.notify_error("Ordner-Dialog konnte nicht geöffnet werden")


async def _pick_output_folder(output_input) -> None:
    """Öffnet OS-Ordner-Dialog für den Ausgabe-Ordner."""
    try:
        result = await nicegui_run.io_bound(
            nicegui_app.native.main_window.create_file_dialog,
            webview.FOLDER_DIALOG,
        )
        if result:
            output_input.set_value(result[0])
            _update_output(result[0])
    except Exception:
        design.notify_error("Ordner-Dialog konnte nicht geöffnet werden")


def _ocr_status_badge(cfg: dict) -> None:
    ollama_cfg = cfg.get("ollama", {})
    available = is_available(
        ollama_cfg.get("url", "http://localhost:11434"),
        ollama_cfg.get("model", "glm-ocr"),
    )
    if available:
        ui.badge('Verbunden', color='positive').props('rounded')
    else:
        ui.badge('Offline', color='negative').props('rounded')


def _update_auto_mode(enabled: bool) -> None:
    cfg = config.get()
    cfg["auto_mode"] = enabled
    config.save()
    design.notify_info(f"Auto-Sortierung {'aktiviert' if enabled else 'deaktiviert'}")


def _update_folder_path(idx: int, path: str) -> None:
    cfg = config.get()
    folders = cfg.get("input_folders", [])
    if 0 <= idx < len(folders):
        folders[idx]["path"] = path
        config.save()


def _update_folder_enabled(idx: int, enabled: bool) -> None:
    cfg = config.get()
    folders = cfg.get("input_folders", [])
    if 0 <= idx < len(folders):
        folders[idx]["enabled"] = enabled
        config.save()


def _remove_folder(idx: int, refresh_fn) -> None:
    cfg = config.get()
    folders = cfg.get("input_folders", [])
    if 0 <= idx < len(folders):
        folders.pop(idx)
        config.save()
        refresh_fn()


def _update_output(path: str) -> None:
    cfg = config.get()
    if "output" not in cfg:
        cfg["output"] = {}
    cfg["output"]["base_path"] = path
    config.save()


def _update_ollama(key: str, value) -> None:
    cfg = config.get()
    if "ollama" not in cfg:
        cfg["ollama"] = {}
    cfg["ollama"][key] = value
    config.save()
