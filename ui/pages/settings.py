"""DocuFlow Settings-Seite — Konfiguration verwalten."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from nicegui import run as nicegui_run
from nicegui import ui

from core import config
from core.ocr_engine import is_available, is_german_ocr_available, is_model_loaded, preload_model
from core.watchdog_service import watchdog_service
from ui import design


def build_settings(app_state: dict) -> None:
    """Baut die Settings-Seite."""
    cfg = config.get()

    design.section_header("Einstellungen", "settings")

    # --- Config-Warnungen ---
    _build_config_warnings(cfg)

    # --- Watchdog-Status ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center justify-between w-full mb-2'):
            with ui.row().classes('items-center gap-2'):
                ui.label('Ordner-Überwachung').classes(f'text-sm font-semibold {design.TEXT}')
                ui.badge('Watchdog', color='grey-6').props('rounded')

        @ui.refreshable
        def watchdog_status():
            watched = watchdog_service.get_watched_folders()
            if watchdog_service.is_running and watched:
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('fiber_manual_record', size='xs').classes('text-[#22c55e]')
                    ui.label(f'Aktiv — {len(watched)} Ordner überwacht').classes(f'text-xs {design.TEXT_SEC}')
                for p in watched:
                    ui.label(p).classes(f'text-xs font-mono {design.TEXT_MUTED_CLS} ml-5')
            else:
                with ui.row().classes('items-center gap-2'):
                    ui.icon('fiber_manual_record', size='xs').classes(f'text-[{design.MUTED}]')
                    ui.label('Inaktiv — keine Ordner konfiguriert').classes(f'text-xs {design.TEXT_SEC}')

        watchdog_status()
        app_state["refresh_watchdog_status"] = watchdog_status.refresh

        async def restart_watchdog():
            current_cfg = config.get()
            watchdog_service.restart(current_cfg.get("input_folders", []))
            watchdog_status.refresh()
            design.notify_success("Watchdog neu gestartet")

        ui.button('Neu starten', icon='refresh', on_click=restart_watchdog) \
            .props('flat no-caps color=primary').classes('mt-2')

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

        ui.separator().classes(f'my-3 {design.BORDER}')
        ui.label('Konfidenz-Schwellwert').classes(f'text-xs {design.TEXT_SEC} mb-1')
        ui.label('Dokumente unterhalb dieser Schwelle gehen immer in die Inbox.') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-2')
        threshold_val = cfg.get("auto_confidence_threshold", 0.9)
        threshold_label = ui.label(f'{threshold_val:.0%}').classes(f'text-xs font-mono {design.TEXT_ACCENT}')

        def _on_threshold_change(e):
            val = float(e.value) / 100
            threshold_label.set_text(f'{val:.0%}')
            c = config.get()
            c["auto_confidence_threshold"] = val
            config.save()

        ui.slider(min=50, max=100, step=5, value=int(threshold_val * 100)) \
            .props('color=blue-5 label-always') \
            .classes('w-full mt-1') \
            .on('change', _on_threshold_change)

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

    # --- German-OCR (HuggingFace, primär) ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        german_ocr_cfg = cfg.get("german_ocr", {})

        with ui.row().classes('items-center justify-between w-full mb-1'):
            with ui.row().classes('items-center gap-2'):
                ui.label('German-OCR').classes(f'text-sm font-semibold {design.TEXT}')
                ui.badge('Primär', color='blue-5').props('rounded')

        ui.label('Keyven/german-ocr — Qwen2-VL-2B, auf deutschen Rechnungen trainiert. '
                 'Läuft lokal im Python-Prozess, kein Server nötig.') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-1')
        ui.label('Beim ersten Aufruf: ~4,4 GB Modell-Download von HuggingFace (einmalig).') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-3')

        # Toggle + Backend
        with ui.grid(columns=2).classes('w-full gap-3 mb-3'):
            with ui.row().classes('items-center gap-3 col-span-1'):
                ui.label('Aktiviert').classes(f'text-xs {design.TEXT_SEC}')
                german_ocr_switch = ui.switch(
                    value=german_ocr_cfg.get("enabled", True)
                ).props('color=blue-5')
                german_ocr_switch.on('change', lambda e: _update_german_ocr("enabled", e.value))

            backend_select = ui.select(
                options={
                    "ollama": "Ollama (german-ocr-turbo, GPU)",
                    "huggingface": "HuggingFace (CPU, kein Install nötig)",
                    "llamacpp": "LlamaCPP (GGUF, CUDA Build nötig)",
                },
                value=german_ocr_cfg.get("backend", "ollama"),
                label="Backend",
            ).props('dark dense filled options-dark').classes('col-span-1')
            backend_select.on('update:model-value', lambda e: _update_german_ocr("backend", e.value))

        # Status + Aktionen als refreshable Block
        action_spinner = ui.spinner(size='sm', color='blue-5').classes('hidden')
        action_status = ui.label('').classes(f'text-xs {design.TEXT_SEC}')
        install_log = ui.log(max_lines=8) \
            .classes(f'w-full text-xs font-mono rounded {design.BG_ELEVATED} mt-2 hidden') \
            .style('height: 130px')

        @ui.refreshable
        def german_ocr_actions():
            with ui.row().classes('items-center gap-2 w-full mb-2'):
                # Status-Badge
                if not is_german_ocr_available():
                    ui.badge('Nicht installiert', color='negative').props('rounded')
                elif is_model_loaded():
                    ui.badge('Geladen · Aktiv', color='positive').props('rounded')
                else:
                    ui.badge('Installiert · Modell nicht geladen', color='warning').props('rounded')

            with ui.row().classes('items-center gap-2 w-full flex-wrap'):
                if not is_german_ocr_available():
                    ui.button('Paket installieren', icon='download',
                              on_click=install_german_ocr) \
                        .props('flat no-caps color=primary')
                elif not is_model_loaded():
                    ui.button('Modell vorladen', icon='cloud_download',
                              on_click=preload_german_ocr) \
                        .props('flat no-caps color=primary')
                    ui.button('Abhängigkeiten installieren', icon='build',
                              on_click=install_deps) \
                        .props('flat no-caps color=grey-5') \
                        .tooltip('pip install german-ocr[llamacpp] mit CUDA-Support')

        async def install_german_ocr():
            action_spinner.classes(remove='hidden')
            action_status.set_text('Installiere german-ocr…')
            install_log.classes(remove='hidden')
            install_log.clear()

            def _run_pip():
                return subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', 'german-ocr'],
                    capture_output=True, text=True,
                )

            proc = await asyncio.get_running_loop().run_in_executor(None, _run_pip)
            action_spinner.classes(add='hidden')

            for line in (proc.stdout + proc.stderr).splitlines():
                if line.strip():
                    install_log.push(line)

            if proc.returncode == 0:
                action_status.set_text('Paket installiert — App-Neustart empfohlen')
                design.notify_success('german-ocr installiert')
            else:
                action_status.set_text('Installation fehlgeschlagen — Details im Log')
                design.notify_error('pip install fehlgeschlagen')

            german_ocr_actions.refresh()

        async def install_deps():
            import traceback
            action_spinner.classes(remove='hidden')
            action_status.set_text('Installiere Abhängigkeiten…')
            install_log.classes(remove='hidden')
            install_log.clear()
            install_log.push('Installiere: torch transformers accelerate qwen-vl-utils huggingface_hub')

            # LlamaCPP mit CUDA für GTX 1080 Ti (Pascal, CUDA 6.1)
            env = {'CMAKE_ARGS': '-DGGML_CUDA=on', **__import__('os').environ}

            def _run():
                return subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', 'german-ocr[llamacpp]'],
                    capture_output=True, text=True, env=env,
                )

            proc = await asyncio.get_running_loop().run_in_executor(None, _run)
            action_spinner.classes(add='hidden')

            for line in (proc.stdout + proc.stderr).splitlines():
                if line.strip():
                    install_log.push(line)

            if proc.returncode == 0:
                action_status.set_text('Abhängigkeiten installiert — jetzt Modell vorladen')
                design.notify_success('Abhängigkeiten installiert')
            else:
                action_status.set_text('Installation fehlgeschlagen — Details im Log')
                design.notify_error('Abhängigkeiten-Installation fehlgeschlagen')

        async def preload_german_ocr():
            import traceback
            action_spinner.classes(remove='hidden')
            action_status.set_text('Lade Modell… (4,4 GB Download, bitte warten)')
            install_log.classes(remove='hidden')
            install_log.clear()
            install_log.push('Starte Modell-Download von HuggingFace (Keyven/german-ocr)…')
            try:
                g_cfg = cfg.get("german_ocr", {})
                await preload_model(
                    backend=g_cfg.get("backend", "llamacpp"),
                    n_gpu_layers=g_cfg.get("n_gpu_layers", -1),
                )
                action_status.set_text('Modell geladen — bereit')
                install_log.push('✓ Modell erfolgreich geladen')
                design.notify_success('German-OCR Modell geladen')
            except Exception as e:
                tb = traceback.format_exc()
                action_status.set_text(f'Fehler beim Laden — Details im Log')
                for line in tb.splitlines():
                    install_log.push(line)
                design.notify_error('Modell-Laden fehlgeschlagen — Details im Log')
            finally:
                action_spinner.classes(add='hidden')
            german_ocr_actions.refresh()

        german_ocr_actions()

        with ui.row().classes('items-center gap-2 mt-1'):
            action_spinner
            action_status

        install_log

    # --- Ollama (Fallback) ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.label('Ollama').classes(f'text-sm font-semibold {design.TEXT}')
            ui.badge('Fallback', color='grey-6').props('rounded')
            ollama_status_badge = ui.badge('Prüfe...', color='grey-6').props('rounded')

        ui.label('Wird verwendet wenn German-OCR deaktiviert ist oder fehlschlägt.') \
            .classes(f'text-xs {design.TEXT_MUTED_CLS} mb-2')

        ollama_cfg = cfg.get("ollama", {})
        with ui.grid(columns=2).classes('w-full gap-3'):
            url_input = design.dark_input('Ollama URL', value=ollama_cfg.get("url", "http://localhost:11434"))
            url_input.on('change', lambda e: _update_ollama("url", e.value))

            model_input = design.dark_input('Fallback-Modell', value=ollama_cfg.get("model", "minicpm-v"))
            model_input.on('change', lambda e: _update_ollama("model", e.value))

            timeout_input = design.dark_number('Timeout (Sek)', value=ollama_cfg.get("timeout", 120))
            timeout_input.on('change', lambda e: _update_ollama("timeout", int(e.value) if e.value else 120))

        async def check_ocr():
            available = is_available(
                ollama_cfg.get("url", "http://localhost:11434"),
                ollama_cfg.get("model", "minicpm-v"),
            )
            if available:
                design.notify_success("OCR-Backend erreichbar")
            else:
                design.notify_error("Kein OCR-Backend verfügbar")

        ui.button('Verbindung testen', icon='wifi_tethering', on_click=check_ocr) \
            .props('flat no-caps color=primary').classes('mt-2')

    async def _check_ollama_status():
        try:
            cfg = config.get()
            url = cfg.get('ollama', {}).get('url', 'http://localhost:11434')
            model = cfg.get('ollama', {}).get('model', 'minicpm-v')
            loop = asyncio.get_running_loop()
            available = await loop.run_in_executor(None, lambda: is_available(url, model))
            ollama_status_badge.set_text('Verbunden' if available else 'Offline')
            ollama_status_badge.props(f'color={"positive" if available else "negative"}')
        except Exception:
            ollama_status_badge.set_text('Fehler')
            ollama_status_badge.props('color=negative')

    asyncio.create_task(_check_ollama_status())

    # --- Datenbank zurücksetzen ---
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 w-full mb-4').props('flat'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.column().classes('gap-0'):
                ui.label('Datenbank zurücksetzen').classes(f'text-sm font-semibold {design.TEXT}')
                ui.label('Alle Dokumente und History-Einträge löschen. Konfiguration bleibt erhalten.') \
                    .classes(f'text-xs {design.TEXT_SEC}')

            async def do_clear():
                db = app_state["db"]
                db.clear_all()
                for key in ("refresh_inbox", "refresh_ignored",
                            "refresh_stats", "refresh_documents", "refresh_history"):
                    fn = app_state.get(key)
                    if fn:
                        fn()
                design.notify_success("Datenbank geleert")

            ui.button('Alles löschen', icon='delete_forever',
                      on_click=lambda: design.confirm_dialog(
                          'Datenbank löschen?',
                          'Alle Dokumente und History-Einträge werden unwiderruflich gelöscht.',
                          do_clear,
                      )).props('no-caps color=negative outline')


def _open_folder_dialog() -> str | None:
    """Öffnet nativen Windows-Ordner-Dialog via PowerShell (kein GUI-Thread-Konflikt)."""
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
        "$d.Description = 'Ordner auswählen'; "
        "$d.ShowNewFolderButton = $true; "
        "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }"
    )
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    result = subprocess.run(
        ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
        capture_output=True, text=True, timeout=120,
        creationflags=flags,
    )
    path = result.stdout.strip()
    return path if path else None


async def _pick_folder(idx: int, refresh_fn) -> None:
    """Öffnet OS-Ordner-Dialog und aktualisiert den Pfad."""
    path = await nicegui_run.io_bound(_open_folder_dialog)
    if path:
        _update_folder_path(idx, path)
        refresh_fn()


async def _add_folder_via_dialog(refresh_fn) -> None:
    """Öffnet OS-Ordner-Dialog und fügt neuen Ordner hinzu."""
    path = await nicegui_run.io_bound(_open_folder_dialog)
    if path:
        cfg = config.get()
        folders = cfg.get("input_folders", [])
        folders.append({"path": path, "enabled": True})
        config.save()
        refresh_fn()


async def _pick_output_folder(output_input) -> None:
    """Öffnet OS-Ordner-Dialog für den Ausgabe-Ordner."""
    path = await nicegui_run.io_bound(_open_folder_dialog)
    if path:
        output_input.set_value(path)
        _update_output(path)


def _ocr_status_badge(cfg: dict) -> None:
    ollama_cfg = cfg.get("ollama", {})
    available = is_available(
        ollama_cfg.get("url", "http://localhost:11434"),
        ollama_cfg.get("model", "minicpm-v"),
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


def _update_german_ocr(key: str, value) -> None:
    cfg = config.get()
    if "german_ocr" not in cfg:
        cfg["german_ocr"] = {}
    cfg["german_ocr"][key] = value
    config.save()


def _build_config_warnings(cfg: dict) -> None:
    """Zeigt Warnungen für ungültige Konfigurationswerte."""
    warnings = []

    for folder in cfg.get("input_folders", []):
        p = Path(folder.get("path", ""))
        if folder.get("enabled", True) and not p.exists():
            warnings.append(f"Eingabe-Ordner nicht gefunden: {p}")

    output_path = Path(cfg.get("output", {}).get("base_path", ""))
    if output_path and not output_path.exists():
        warnings.append(f"Ausgabe-Ordner nicht gefunden: {output_path}")

    if not warnings:
        return

    with ui.card().classes(
        f'border border-[{design.WARNING}44] bg-[{design.WARNING}11] rounded-xl p-4 w-full mb-4'
    ).props('flat'):
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('warning', size='sm').classes(f'text-[{design.WARNING}]')
            ui.label('Konfigurationswarnungen').classes(f'text-sm font-semibold text-[{design.WARNING}]')
        for msg in warnings:
            ui.label(f'• {msg}').classes(f'text-xs {design.TEXT_SEC}')
