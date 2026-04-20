"""DocuFlow Design-Konstanten — Utility & Precision Dark Theme."""

from nicegui import ui

# --- Farben ---
ACCENT = '#3b82f6'      # blue-500
SUCCESS = '#22c55e'     # green-500
WARNING = '#f59e0b'     # amber-500
ERROR = '#ef4444'       # red-500
MUTED = '#6b7280'       # gray-500

_BG_DARK = '#0f172a'        # slate-900
_BG_SURFACE = '#1e293b'     # slate-800
_BG_ELEVATED = '#334155'    # slate-700
_BORDER = 'rgba(255,255,255,0.08)'
_TEXT_PRIMARY = '#f1f5f9'    # slate-100
_TEXT_SECONDARY = '#94a3b8'  # slate-400
_TEXT_MUTED = '#64748b'      # slate-500

# --- Tailwind-Klassen ---
BG = f'bg-[{_BG_DARK}]'
BG_SURFACE = f'bg-[{_BG_SURFACE}]'
BG_ELEVATED = f'bg-[{_BG_ELEVATED}]'
BORDER = f'border border-[{_BORDER}]'
BORDER_B = f'border-b border-b-[{_BORDER}]'
TEXT = f'text-[{_TEXT_PRIMARY}]'
TEXT_SEC = f'text-[{_TEXT_SECONDARY}]'
TEXT_MUTED_CLS = f'text-[{_TEXT_MUTED}]'
TEXT_ACCENT = f'text-[{ACCENT}]'

# --- Status-Farben ---
STATUS_COLORS = {
    'verarbeitet': SUCCESS,
    'review': WARNING,
    'fehler': ERROR,
    'neu': ACCENT,
    'verarbeitung': '#8b5cf6',
}


def apply_theme() -> None:
    """Setzt Quasar-Farbtheme."""
    ui.colors(
        primary=ACCENT,
        secondary=_BG_ELEVATED,
        accent='#8b5cf6',
        dark=_BG_DARK,
        positive=SUCCESS,
        negative=ERROR,
        warning=WARNING,
        info='#38bdf8',
    )


# --- Wiederverwendbare Komponenten ---

def stat_card(label: str, value: str, icon: str, color: str = ACCENT) -> None:
    with ui.card().classes(f'{BG_SURFACE} {BORDER} rounded-xl p-4 gap-3').props('flat'):
        with ui.row().classes('items-center justify-between w-full'):
            ui.label(label).classes(f'text-sm {TEXT_SEC}')
            ui.icon(icon, size='sm').classes(f'text-[{color}]')
        ui.label(value).classes(f'text-2xl font-bold {TEXT}')


def status_badge(status: str) -> ui.label:
    color = STATUS_COLORS.get(status.lower(), MUTED)
    return ui.label(status.capitalize()) \
        .classes('text-xs font-medium px-2 py-0.5 rounded-full') \
        .style(f'background: {color}22; color: {color}; border: 1px solid {color}44')


def dark_input(label: str, **kwargs) -> ui.input:
    return ui.input(label, **kwargs) \
        .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9') \
        .classes('w-full')


def dark_select(label: str, options: list, **kwargs) -> ui.select:
    return ui.select(options, label=label, **kwargs) \
        .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9') \
        .classes('w-full')


def dark_number(label: str, **kwargs) -> ui.number:
    return ui.number(label, **kwargs) \
        .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9') \
        .classes('w-full')


def notify_success(msg: str) -> None:
    ui.notify(msg, type='positive', position='top-right', timeout=3000)


def notify_error(msg: str) -> None:
    ui.notify(msg, type='negative', position='top-right', timeout=5000)


def notify_info(msg: str) -> None:
    ui.notify(msg, type='info', position='top-right', timeout=3000)


def notify_warning(msg: str) -> None:
    ui.notify(msg, type='warning', position='top-right', timeout=5000)


def section_header(title: str, icon: str = '') -> None:
    with ui.row().classes('items-center gap-2 mb-2'):
        if icon:
            ui.icon(icon).classes(f'{TEXT_ACCENT} text-xl')
        ui.label(title).classes(f'text-lg font-semibold {TEXT}')


def confirm_dialog(title: str, body: str, on_confirm) -> None:
    with ui.dialog() as dialog, ui.card().classes(
        f'{BG_SURFACE} {BORDER} rounded-xl p-6 gap-4 min-w-[320px]'
    ):
        ui.label(title).classes(f'text-base font-semibold {TEXT}')
        ui.label(body).classes(f'text-sm {TEXT_SEC}')
        with ui.row().classes('gap-3 justify-end w-full pt-2'):
            ui.button('Abbrechen', on_click=dialog.close) \
                .props('flat no-caps').classes(TEXT_SEC)
            ui.button('Bestaetigen', on_click=lambda: (on_confirm(), dialog.close())) \
                .props('no-caps').classes(f'bg-[{ACCENT}] text-white')
    dialog.open()
