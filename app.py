"""DocuFlow — Intelligentes Dokumenten-Management.

NiceGUI App mit Sidebar-Navigation, Dark-Theme und Tab-Panels.
"""

from __future__ import annotations

from nicegui import ui

from core import config
from core.database import Database
from core.processor import Processor
from core.rules_store import load_rules
from ui import design
from ui.pages.dashboard import build_dashboard
from ui.pages.inbox import build_inbox
from ui.pages.rules import build_rules_editor
from ui.pages.settings import build_settings
from ui.pages.templates_page import build_templates

cfg = config.load()
db = Database(cfg.get("database", {}).get("path", "./data/docuflow.db"))
db.connect()


@ui.page("/")
def main_page():
    ui.dark_mode(True)
    design.apply_theme()

    rules = load_rules()
    processor = Processor(db)
    processor.set_rules(rules)

    app_state = {
        "db": db,
        "processor": processor,
        "rules": rules,
        "cfg": cfg,
    }

    # Navigations-Buttons merken fuer aktive Hervorhebung
    nav_buttons: dict[str, ui.button] = {}

    # --- Header ---
    with ui.header().classes(
        f"items-center justify-between h-14 px-4 {design.BG_SURFACE} {design.BORDER_B} shadow-none"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.button(icon="menu", on_click=lambda: sidebar.toggle()) \
                .props("flat dense color=grey-5")
            ui.icon("description").classes(f"{design.TEXT_ACCENT} text-xl")
            ui.label("DocuFlow").classes(f"text-lg font-semibold {design.TEXT}")
        with ui.row().classes("items-center gap-2"):
            ui.label("v0.1").classes(f"text-xs {design.TEXT_MUTED_CLS}")

    # --- Sidebar ---
    with ui.left_drawer(value=True).classes(
        f"column no-wrap gap-1 {design.BG_SURFACE} {design.BORDER} pt-4 pb-8"
    ).props("width=220 bordered") as sidebar:

        def navigate(tab_name: str):
            tabs.set_value(tab_name)
            _update_nav_active(tab_name, nav_buttons)

        ui.label("VERARBEITUNG").classes(
            f"text-[10px] font-bold tracking-widest px-4 pb-1 pt-2 {design.TEXT_MUTED_CLS}"
        )

        for icon, label, tab in [
            ("inbox", "Eingang", "inbox"),
            ("dashboard", "Dashboard", "dashboard"),
            ("auto_fix_high", "Templates", "templates"),
        ]:
            btn = ui.button(label, icon=icon, on_click=lambda t=tab: navigate(t)) \
                .classes(f"w-full justify-start rounded-lg px-3 py-2 text-sm font-medium") \
                .props("flat no-caps")
            nav_buttons[tab] = btn

        ui.separator().classes(f"my-3 {design.BORDER}")
        ui.label("SYSTEM").classes(
            f"text-[10px] font-bold tracking-widest px-4 pb-1 {design.TEXT_MUTED_CLS}"
        )

        for icon, label, tab in [
            ("rule", "Sortier-Regeln", "rules"),
            ("settings", "Einstellungen", "settings"),
        ]:
            btn = ui.button(label, icon=icon, on_click=lambda t=tab: navigate(t)) \
                .classes(f"w-full justify-start rounded-lg px-3 py-2 text-sm font-medium") \
                .props("flat no-caps")
            nav_buttons[tab] = btn

        _update_nav_active("inbox", nav_buttons)

    # --- Content ---
    with ui.column().classes(f"w-full min-h-screen {design.BG} p-6 gap-0"):
        tabs = ui.tabs().classes("hidden")
        with tabs:
            for name in ["inbox", "dashboard", "templates", "rules", "settings"]:
                ui.tab(name)

        with ui.tab_panels(tabs, value="inbox") \
                .classes(f"w-full {design.BG}") \
                .style("box-shadow: none; background: transparent;"):
            with ui.tab_panel("inbox").classes("p-0"):
                build_inbox(app_state)
            with ui.tab_panel("dashboard").classes("p-0"):
                build_dashboard(app_state)
            with ui.tab_panel("templates").classes("p-0"):
                build_templates(app_state)
            with ui.tab_panel("rules").classes("p-0"):
                build_rules_editor(app_state)
            with ui.tab_panel("settings").classes("p-0"):
                build_settings(app_state)


def _update_nav_active(active_tab: str, nav_buttons: dict[str, ui.button]) -> None:
    """Aktualisiert die Hervorhebung der Sidebar-Buttons."""
    for tab_name, btn in nav_buttons.items():
        if tab_name == active_tab:
            btn.classes(replace=f"w-full justify-start rounded-lg px-3 py-2 text-sm font-medium "
                                f"{design.BG_ELEVATED} {design.TEXT_ACCENT}")
        else:
            btn.classes(replace=f"w-full justify-start rounded-lg px-3 py-2 text-sm font-medium "
                                f"{design.TEXT_SEC}")


from nicegui import app as nicegui_app

nicegui_app.native.window_args["text"] = "DocuFlow"

ui.run(
    title="DocuFlow",
    dark=True,
    favicon="📄",
    reload=False,
    native=True,
    window_size=(1280, 850),
)
