# NiceGUI Design System — DocuFlow

Erstelle oder überarbeite NiceGUI-UI-Komponenten für das DocuFlow-Projekt mit konsistentem Design. Dieses Dokument ist das kanonische Design-System für alle UI-Arbeiten.

## Design-Richtung: "Utility & Precision"

DocuFlow ist ein Power-User-Tool für Dokumentenverarbeitung. Die UI ist:
- **Funktional und dicht** — keine dekorativen Elemente ohne Funktion
- **Dunkel by default** — `dark_mode=True`, Informationen stehen im Vordergrund
- **Klar strukturiert** — Sidebar-Navigation + Content-Bereich
- **Vertrauenswürdig** — gedämpfte Farben, konsistente Abstände, klare Status-Anzeigen

---

## 1. Python Design-Konstanten (`ui/design.py`)

**Dieses Modul MUSS in jedem UI-Build existieren und genutzt werden:**

```python
# ui/design.py — DocuFlow Design-Konstanten
from nicegui import ui

# --- Farben ---
ACCENT   = '#3b82f6'   # blue-500 — primäre Akzentfarbe
SUCCESS  = '#22c55e'   # green-500
WARNING  = '#f59e0b'   # amber-500
ERROR    = '#ef4444'   # red-500
MUTED    = '#6b7280'   # gray-500

_BG_DARK        = '#0f172a'   # slate-900
_BG_SURFACE     = '#1e293b'   # slate-800
_BG_ELEVATED    = '#334155'   # slate-700
_BORDER         = 'rgba(255,255,255,0.08)'
_TEXT_PRIMARY   = '#f1f5f9'   # slate-100
_TEXT_SECONDARY = '#94a3b8'   # slate-400
_TEXT_MUTED     = '#64748b'   # slate-500

# --- Tailwind-Klassen-Fragmente ---
BG              = f'bg-[{_BG_DARK}]'
BG_SURFACE      = f'bg-[{_BG_SURFACE}]'
BG_ELEVATED     = f'bg-[{_BG_ELEVATED}]'
BORDER          = f'border border-[{_BORDER}]'
BORDER_B        = f'border-b border-b-[{_BORDER}]'
TEXT            = f'text-[{_TEXT_PRIMARY}]'
TEXT_SEC        = f'text-[{_TEXT_SECONDARY}]'
TEXT_MUTED_CLS  = f'text-[{_TEXT_MUTED}]'
TEXT_ACCENT     = f'text-[{ACCENT}]'

# Abstände (4px-Raster)
# Nutze Tailwind: gap-1(4px) gap-2(8px) gap-3(12px) gap-4(16px) gap-6(24px) gap-8(32px)
# Padding:        p-2(8px)  p-3(12px)  p-4(16px)   p-6(24px)

# --- Quasar-Farb-Theming (beim App-Start aufrufen) ---
def apply_theme() -> None:
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
```

---

## 2. App-Grundstruktur

```python
@ui.page('/')
def main_page():
    ui.dark_mode(True)
    design.apply_theme()

    # Header
    with ui.header().classes(f'items-center justify-between h-14 px-4 {design.BG_SURFACE} {design.BORDER_B} shadow-none'):
        with ui.row().classes('items-center gap-3'):
            ui.button(icon='menu', on_click=lambda: sidebar.toggle()).props('flat dense color=grey-5')
            ui.label('DocuFlow').classes(f'text-lg font-semibold {design.TEXT}')
        with ui.row().classes('items-center gap-2'):
            ui.label('v0.1').classes(f'text-xs {design.TEXT_MUTED_CLS}')

    # Sidebar
    with ui.left_drawer(value=True).classes(
        f'column no-wrap gap-1 {design.BG_SURFACE} {design.BORDER} pt-4 pb-8'
    ).props('width=220 bordered') as sidebar:
        _build_sidebar()

    # Content
    with ui.column().classes(f'w-full min-h-screen {design.BG} p-6 gap-6'):
        _build_content()
```

---

## 3. Sidebar-Navigation

```python
def _build_sidebar():
    # Abschnitts-Label
    ui.label('VERARBEITUNG').classes(f'text-[10px] font-bold tracking-widest px-4 pb-1 {design.TEXT_MUTED_CLS}')

    nav_items = [
        ('inbox', 'Eingang', '/'),
        ('folder_open', 'Sortiert', '/sorted'),
        ('auto_fix_high', 'OCR-Review', '/review'),
    ]
    for icon, label, path in nav_items:
        _nav_button(icon, label, path)

    ui.separator().classes(f'my-3 {design.BORDER}')
    ui.label('SYSTEM').classes(f'text-[10px] font-bold tracking-widest px-4 pb-1 {design.TEXT_MUTED_CLS}')

    for icon, label, path in [('rule', 'Sortier-Regeln', '/rules'), ('settings', 'Einstellungen', '/settings')]:
        _nav_button(icon, label, path)


def _nav_button(icon: str, label: str, path: str) -> None:
    is_active = ui.context.client.sub_pages_router.current_path == path
    active_cls = f'{design.BG_ELEVATED} {design.TEXT_ACCENT}' if is_active else f'text-[{design._TEXT_SECONDARY}]'
    ui.button(label, icon=icon, on_click=lambda p=path: ui.navigate.to(p)) \
        .classes(f'w-full justify-start rounded-lg px-3 py-2 text-sm font-medium {active_cls}') \
        .props('flat no-caps')
```

---

## 4. Stat-Cards (Dashboard)

```python
def stat_card(label: str, value: str, icon: str, color: str = design.ACCENT) -> None:
    with ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-4 gap-3').props('flat'):
        with ui.row().classes('items-center justify-between w-full'):
            ui.label(label).classes(f'text-sm {design.TEXT_SEC}')
            ui.icon(icon, size='sm').classes(f'text-[{color}]')
        ui.label(value).classes(f'text-2xl font-bold {design.TEXT}')

# Verwendung:
with ui.grid(columns=4).classes('w-full gap-4'):
    stat_card('Verarbeitet heute', '42', 'check_circle', design.SUCCESS)
    stat_card('OCR-Queue', '7', 'hourglass_empty', design.WARNING)
    stat_card('Fehler', '2', 'error_outline', design.ERROR)
    stat_card('Gesamt', '1.247', 'folder', design.ACCENT)
```

---

## 5. Dokumenten-Tabelle

```python
def document_table(docs: list[dict]) -> ui.aggrid:
    return ui.aggrid({
        'defaultColDef': {'sortable': True, 'resizable': True, 'filter': True},
        'columnDefs': [
            {'headerName': 'Dateiname', 'field': 'name', 'flex': 2, 'cellClass': 'font-medium'},
            {'headerName': 'Typ',       'field': 'type', 'width': 120},
            {'headerName': 'Datum',     'field': 'date', 'width': 120, 'sort': 'desc'},
            {'headerName': 'Absender',  'field': 'sender', 'flex': 1},
            {'headerName': 'Betrag',    'field': 'amount', 'width': 110, 'type': 'rightAligned'},
            {'headerName': 'Status',    'field': 'status', 'width': 110,
             'cellRenderer': 'agTextCellRenderer'},
        ],
        'rowData': docs,
        'rowSelection': 'single',
    }).classes('w-full').props('dark')
```

---

## 6. Status-Badge

```python
STATUS_COLORS = {
    'verarbeitet': design.SUCCESS,
    'review':      design.WARNING,
    'fehler':      design.ERROR,
    'neu':         design.ACCENT,
}

def status_badge(status: str) -> None:
    color = STATUS_COLORS.get(status.lower(), design.MUTED)
    ui.label(status.capitalize()) \
        .classes(f'text-xs font-medium px-2 py-0.5 rounded-full') \
        .style(f'background: {color}22; color: {color}; border: 1px solid {color}44')
```

---

## 7. Formular-Felder (konsistente Darstellung)

```python
# Standard-Input für dunkles Theme
def dark_input(label: str, **kwargs) -> ui.input:
    return ui.input(label, **kwargs) \
        .props(f'dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9') \
        .classes('w-full')

# Standard-Select
def dark_select(label: str, options: list, **kwargs) -> ui.select:
    return ui.select(options, label=label, **kwargs) \
        .props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9') \
        .classes('w-full')
```

---

## 8. Notifications & Feedback

```python
# Konsistente Notification-Aufrufe
def notify_success(msg: str) -> None:
    ui.notify(msg, type='positive', position='top-right', timeout=3000)

def notify_error(msg: str) -> None:
    ui.notify(msg, type='negative', position='top-right', timeout=5000)

def notify_info(msg: str) -> None:
    ui.notify(msg, type='info', position='top-right', timeout=3000)
```

---

## 9. Dialog-Pattern

```python
def confirm_dialog(title: str, body: str, on_confirm: callable) -> None:
    with ui.dialog() as dialog, ui.card().classes(f'{design.BG_SURFACE} {design.BORDER} rounded-xl p-6 gap-4 min-w-[320px]'):
        ui.label(title).classes(f'text-base font-semibold {design.TEXT}')
        ui.label(body).classes(f'text-sm {design.TEXT_SEC}')
        with ui.row().classes('gap-3 justify-end w-full pt-2'):
            ui.button('Abbrechen', on_click=dialog.close).props('flat no-caps').classes(design.TEXT_SEC)
            ui.button('Bestätigen', on_click=lambda: (on_confirm(), dialog.close())) \
                .props('no-caps').classes(f'bg-[{design.ACCENT}] text-white')
    dialog.open()
```

---

## 10. Abstands- und Größen-Regeln

| Element            | Klasse           | Pixel |
|--------------------|------------------|-------|
| Sidebar-Breite     | `props='width=220'` | 220px |
| Header-Höhe        | `h-14`           | 56px  |
| Seiten-Padding     | `p-6`            | 24px  |
| Karten-Abstand     | `gap-4`          | 16px  |
| Inneres Padding    | `p-4`            | 16px  |
| Border-Radius Card | `rounded-xl`     | 12px  |
| Border-Radius Btn  | `rounded-lg`     | 8px   |
| Icon-Größe Nav     | `size='sm'`      | 20px  |
| Trennlinie         | `rgba(255,255,255,0.08)` | — |

---

## 11. Wichtige NiceGUI-Fallstricke

- **Dark-Mode Tailwind**: `bg-[#hex] dark:bg-[#hex]` — funktioniert NUR wenn `ui.dark_mode(True)` aktiv
- **Quasar `props('dark')`**: Tabellen, Inputs, Selects brauchen explizit `.props('dark')` für dunkle Darstellung
- **`.classes()` vs `.props()`**: Tailwind-Klassen → `.classes()`, Quasar-Props → `.props()`
- **Karten haben keinen Schatten by default**: `.props('flat')` für border-only, ohne für Schatten
- **`ui.aggrid` statt `ui.table`**: Für Dokumentenlisten — mehr Features, virtuelles Scrolling
- **Sidebar-Toggle**: `ui.left_drawer(value=True)` + Variable speichern + `.toggle()` aufrufen
- **`@ui.refreshable`**: Für Dokumentenlisten die sich nach OCR-Verarbeitung aktualisieren
- **`async def`**: Für alle Handler die I/O machen (Datei lesen, DB-Query, OCR-Aufruf)

---

## Checkliste vor jedem UI-Commit

- [ ] `design.apply_theme()` wird beim App-Start aufgerufen
- [ ] `ui.dark_mode(True)` gesetzt
- [ ] Alle Inputs haben `.props('dark outlined dense ...')`
- [ ] Tabellen haben `.props('dark')`
- [ ] Abstände folgen dem 4px-Raster
- [ ] Status-Badges nutzen `status_badge()` Helper
- [ ] Keine Inline-Hex-Farben außerhalb von `design.py`
