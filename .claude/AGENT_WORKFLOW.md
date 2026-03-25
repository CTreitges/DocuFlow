# Agent Workflow – DocuFlow (Claude Code)

Dieses Dokument optimiert den Einsatz von Claude Code für das Projekt **DocuFlow**. Es dient dem Kontext-Management, der Token-Optimierung und klaren Agentic Loops.

---

## 1. Projektüberblick

| Was | Beschreibung |
|-----|--------------|
| **Zweck** | PDF/Bild-Dokumente → OCR (GLM-OCR via Ollama) → Template-Matching → automatische Sortierung & Umbenennung |
| **UI** | NiceGUI (Python) + Tailwind CSS + Quasar, Dark-Theme |
| **Einstieg** | `main.py` (App), `core/processor.py` (Pipeline), `ui/` (Seiten), `ui/design.py` (Designsystem) |
| **Konfiguration** | `config.yaml` (ruamel.yaml), SQLite-DB via `db/models.py` |

**Wichtig:** Alle Nutzerdaten und Dokumente bleiben lokal; keine Uploads ins Internet.

---

## 2. Kontext-Management

### 2.1 Große Dateien nie vollständig laden

- Dateien >300 Zeilen: Erst **Grep** nutzen um relevante Stellen zu finden, dann `Read` mit `offset`/`limit`.
- Für sehr große Dateien: `mcp__rlm__rlm_load_file` statt Read.

**Regel:** Vor dem Öffnen großer Dateien immer zuerst mit Grep suchen (Funktions-/Klassennamen, eindeutige Strings), dann nur den relevanten Bereich laden.

### 2.2 Was nicht in den Kontext soll

- **Binärdateien:** PDF, Bilder, XLSX – nie mit Read öffnen (nur Pfade/Existenz prüfen)
- **Ordner mit Nutzerdaten:** `inbox/`, `sorted/`, `temp/`, `exports/` – Inhalte nicht einlesen
- **Venv/Cache:** `venv/`, `__pycache__/` – ignorieren

### 2.3 Was gezielt in den Kontext soll

- **Konkrete Funktionen/Klassen**, die für die Aufgabe relevant sind
- **`ui/design.py`** bei allen UI-Änderungen — Designkonstanten immer referenzieren
- **`config.yaml`-Struktur** bei Einstellungsänderungen
- **DB-Schema** (`db/models.py`) bei Datenbankänderungen

---

## 3. Tool-Einsatz

### 3.1 MCP-Server (Pflicht – immer zuerst prüfen)

| Aufgabe | MCP-Tool | Statt |
|---------|----------|-------|
| Excel lesen/analysieren | `mcp__excel__excel_describe_sheets` + `mcp__excel__excel_read_sheet` | Read (verboten für XLSX) |
| Git Status/Log/Diff | `mcp__git__git_status`, `mcp__git__git_log`, `mcp__git__git_diff_unstaged` | `Bash git ...` |
| Git Add/Commit | `mcp__git__git_add`, `mcp__git__git_commit` | `Bash git add/commit` |
| Verzeichnis auflisten | `mcp__filesystem__list_directory` | `Bash ls` |
| NiceGUI/PyMuPDF/Ollama-Docs | `mcp__context7__query-docs` | WebSearch |
| Große Datei analysieren | `mcp__rlm__rlm_load_file`, `mcp__rlm__rlm_execute_code` | Read mit offset/limit |

**Regel:** MCPs vor Bash. Bash nur wenn kein MCP die Aufgabe erfüllen kann.

### 3.2 Suche

| Tool | Wann | Wie |
|------|------|-----|
| **Grep** | Funktionsnamen, Konstanten, eindeutige Strings | `pattern: "process_document"`, optional `path` begrenzen |
| **Glob** | Dateien nach Typ finden | `pattern: "*.py"` oder `"**/*.yaml"` |
| **Agent (Explore)** | Offene, unbekannte Suche über viele Dateien | Wenn Grep allein nicht ausreicht |

**Ablauf:** Erst suchen (Grep/Glob), dann gezielt lesen (Read mit Bereich). So bleibt der Kontext klein.

### 3.3 Lesen & Bearbeiten

| Tool | Wann |
|------|------|
| **Read** | Gezielte Bereiche mit `offset`/`limit`; niemals große Dateien komplett; nie Binärdateien |
| **Edit** | Exakten Block ersetzen; ausreichend Kontext (eindeutiger String), um nur eine Stelle zu treffen |
| **Write** | Nur für neue, kleine Dateien |
| **Bash** | Shell-Befehle — Git und Excel via MCP bevorzugen |

### 3.4 Mehrschrittige Aufgaben

- **Agent (general-purpose):** Für komplexe, mehrstufige Aufgaben, die mehrere Suchen und Reads kombinieren.
- **Parallele Tool-Calls:** Unabhängige Reads/Greps/MCP-Calls immer parallel ausführen.

---

## 4. Token-Optimierung

- Große Dateien: **niemals** komplett lesen; immer `offset` und `limit` nutzen
- Edit: Genau den zu ändernden Block ersetzen; keine unnötigen Großrefactorings
- Keine vollständigen Dateien in Antworten kopieren
- Keine langen Logs oder Binärdaten ausgeben
- `config.yaml` und DB-Schemas: nur betroffene Keys anfassen; Validität erhalten

---

## 5. Agentic Loops

### 5.1 Standard-Loop: Aufgabe → Lösung

1. **Verstehen:** Aufgabe klar eingrenzen (welche Datei, welche Funktion, welches Verhalten)
2. **Lokalisieren:** Mit Grep/Glob die relevante Stelle finden
3. **Einlesen:** Nur den gefundenen Bereich mit Read (offset/limit) laden
4. **Ändern:** Minimale, fokussierte Änderung mit Edit
5. **Prüfen:** App starten oder Unit-Test nur wenn explizit nötig
6. **Abschluss:** Kurz zusammenfassen was geändert wurde

### 5.2 Wann abbrechen / Rückfrage

- Anforderungen unklar oder widersprüchlich → **eine** kurze Rückfrage, statt viel Code zu raten
- Änderung betrifft viele Stellen (DB-Schema, Pipeline-Interface) → Bestätigung einholen

### 5.3 Keine unnötigen Loops

- Kein wiederholtes vollständiges Einlesen großer Dateien
- Kein mehrfaches Suchen derselben Sache ohne neue Information
- Nach erfolgreicher Änderung und kurzer Verifikation: Loop beenden

### 5.4 Beispiel: Neue UI-Seite hinzufügen

**Aufgabe:** „Neue Seite für Sortier-Regeln-Editor bauen."

1. **Design laden:** `.claude/commands/nicegui-design.md` — Farbkonstanten, Layout-Pattern referenzieren
2. **Vorhandene Seiten prüfen:** Grep nach `@ui.page` in `main.py` → Routing-Muster verstehen
3. **Read:** Nur relevanter Bereich aus `main.py` + `ui/design.py`
4. **Neue Datei erstellen:** `ui/rules_editor.py` mit korrekten Design-Klassen
5. **Route registrieren:** Edit `main.py` → neue Route einbinden
6. **Abschluss:** Kurz beschreiben welche Klassen aus `design.py` genutzt wurden

---

## 6. Projekt-Karte (schnelle Orientierung)

| Bereich | Inhalt | Hinweis |
|---------|--------|---------|
| **main.py** | App-Start, Routing, Dark-Mode, Theme | Nur Routing-Bereich laden bei Seiten-Aufgaben |
| **ui/design.py** | Farb-Konstanten, Tailwind-Klassen-Fragmente | IMMER bei UI-Änderungen referenzieren |
| **ui/*.py** | NiceGUI-Seiten, je Seite eine Datei | Gezielt nach Seiten-Name laden |
| **core/processor.py** | Dreistufige Pipeline (Extraktion→Template→OCR) | Bei Verarbeitungs-Bugs hier starten |
| **core/ocr.py** | GLM-OCR via Ollama HTTP-API | Bei OCR-Problemen; Ollama-Docs via Context7 |
| **core/templates.py** | Template-Matching, Confidence-Scores | Bei Erkennungsproblemen |
| **core/rules.py** | Sortier-Regeln-Engine | Bei Sortierungs-Bugs |
| **db/models.py** | Pydantic-Modelle + SQLite via aiosqlite | Bei DB-Änderungen Schema und Migration prüfen |
| **config.yaml** | App-Einstellungen (ruamel.yaml) | Kommentare erhalten; YAML-Validität wahren |

---

## 7. Umgebung & Befehle

- **Shell:** Bash (Unix-Syntax auch auf Windows)
- **Python:** `python` (3.13 global)
- **App starten:** `python main.py` (nur bei explizitem Bedarf)
- **NiceGUI-Docs:** `mcp__context7__query-docs` mit query "nicegui ..."

---

## 8. NiceGUI Design-System

Vollständige Referenz: `.claude/commands/nicegui-design.md` — **immer laden bei UI-Arbeit**.

### Design-Richtung: "Utility & Precision"
Dunkles Theme (immer an), funktional-dicht, slate-Farben, blauer Akzent `#3b82f6`.

### Pflicht: `ui/design.py` Konstanten-Modul

Alle Farben und Tailwind-Klassen als Python-Variablen zentralisieren — **keine Inline-Hex-Farben** im UI-Code:

```python
# Kernfarben
ACCENT = '#3b82f6'   # blue-500
SUCCESS = '#22c55e'  # green-500
WARNING = '#f59e0b'  # amber-500
ERROR   = '#ef4444'  # red-500

# Hintergründe (slate-Palette)
BG         = 'bg-[#0f172a]'   # slate-900
BG_SURFACE = 'bg-[#1e293b]'   # slate-800
BG_ELEVATED= 'bg-[#334155]'   # slate-700

# Text & Borders
TEXT     = 'text-[#f1f5f9]'
TEXT_SEC = 'text-[#94a3b8]'
BORDER   = 'border border-[rgba(255,255,255,0.08)]'
```

### App-Start (immer)

```python
ui.dark_mode(True)
design.apply_theme()  # Quasar-Farben setzen
```

### Layout-Struktur

```
ui.header()        → h-14, BG_SURFACE, BORDER_B
ui.left_drawer()   → width=220, BG_SURFACE, BORDER
ui.column()        → BG, p-6, gap-6  ← Content-Bereich
```

### Komponenten-Regeln

| Komponente | Regel |
|------------|-------|
| Inputs/Selects | `.props('dark outlined dense color=blue-5 label-color=grey-5 bg-color=grey-9')` |
| Tabellen | `ui.aggrid` mit `.props('dark')` — **nicht** `ui.table` |
| Cards | `.classes('BG_SURFACE BORDER rounded-xl p-4')` + `.props('flat')` |
| Buttons Nav | `.props('flat no-caps')` + `.classes('w-full justify-start rounded-lg')` |
| Status-Badge | Inline-Style: `background: {color}22; color: {color}; border: 1px solid {color}44` |

### Abstands-Raster (4px-Basis)

`gap-1`=4px · `gap-2`=8px · `gap-3`=12px · `gap-4`=16px · `gap-6`=24px · `p-4`=16px · `p-6`=24px

### Wichtige Fallstricke

- `dark:` Tailwind-Varianten funktionieren **nur** wenn `ui.dark_mode(True)` aktiv ist
- Quasar-Komponenten (Inputs, Selects, Tabellen) brauchen **explizit** `.props('dark')`
- `.classes()` → Tailwind, `.props()` → Quasar-Properties, `.style()` → Inline-CSS
- Sidebar-Toggle: Variable speichern (`as sidebar`), dann `sidebar.toggle()`
- Async: **alle** Handler mit I/O als `async def`
- Refreshable: Dokumentenlisten mit `@ui.refreshable` dekorieren

---

## 9. Kurz-Checkliste vor dem Abschluss

- [ ] Nur relevante Dateibereiche gelesen (keine kompletten Riesen-Dateien)?
- [ ] `ui/design.py` Konstanten genutzt (keine Inline-Hex-Farben)?
- [ ] Änderungen minimal und auf die Aufgabe beschränkt?
- [ ] YAML/JSON gültig und Schema-Kommentare erhalten?
- [ ] Kurze Zusammenfassung für den Nutzer formuliert?

---

*Optimiert für Claude Code. Letzte Anpassung: 2026-03-25.*
