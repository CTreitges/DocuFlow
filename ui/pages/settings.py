"""DocuFlow Settings-Seite — Konfiguration verwalten."""

from __future__ import annotations

from pathlib import Path

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

        @ui.refreshable
        def folders_list():
            folders = cfg.get("input_folders", [])
            for i, folder in enumerate(folders):
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    folder_input = design.dark_input('Pfad', value=folder.get("path", "")) \
                        .classes('flex-grow')
                    folder_input.on('change', lambda e, idx=i: _update_folder_path(idx, e.value))

                    enabled_sw = ui.switch(value=folder.get("enabled", True)) \
                        .props('dense color=blue-5')
                    enabled_sw.on('change', lambda e, idx=i: _update_folder_enabled(idx, e.value))

                    watch_sw = ui.switch(value=folder.get("watch", True)) \
                        .props('dense color=amber-5')
                    watch_sw.tooltip('Ordner ueberwachen')

                    ui.button(icon='delete',
                              on_click=lambda idx=i: _remove_folder(idx, folders_list.refresh)) \
                        .props('flat dense round size=sm color=negative')

            if not folders:
                ui.label('Keine Ordner konfiguriert').classes(f'text-xs {design.TEXT_SEC} italic')

        folders_list()

        def add_folder():
            folders = cfg.get("input_folders", [])
            folders.append({"path": "./inbox_new", "enabled": True, "watch": True})
            config.save()
            folders_list.refresh()

        ui.button('Ordner hinzufuegen', icon='create_new_folder', on_click=add_folder) \
            .props('flat no-caps color=primary').classes('mt-2')

    # --- Ausgabe-Ordner ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        ui.label('Ausgabe').classes(f'text-sm font-semibold {design.TEXT} mb-2')
        output_input = design.dark_input('Basis-Ordner', value=cfg.get("output", {}).get("base_path", "./sorted"))
        output_input.on('change', lambda e: _update_output(e.value))

    # --- Ollama/OCR ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center justify-between w-full mb-2'):
            ui.label('OCR / Ollama').classes(f'text-sm font-semibold {design.TEXT}')
            _ocr_status_badge(cfg)

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
