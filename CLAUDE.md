# ⚡ PFLICHTAKTIONEN – IMMER ZUERST, KEINE AUSNAHME

## RLM-Gedächtnis (100% automatisch, bei JEDEM Prompt)

| Zeitpunkt | Aktion | Tool |
|-----------|--------|------|
| **Gesprächsstart** | Relevante Erkenntnisse laden | `mcp__rlm-claude__rlm_recall` (project=DocuFlow) |
| **Fund/Bug/Entscheidung** | Sofort speichern, NICHT warten | `mcp__rlm-claude__rlm_remember` |
| **Gesprächsende** | Session-Zusammenfassung | `mcp__rlm-claude__rlm_chunk` (chunk_type=session, project=DocuFlow) |

**Regel:** `rlm_recall` ist der ERSTE Tool-Aufruf jeder Session – noch vor jeder anderen Aktion.
**Regel:** `rlm_remember` wird ausgeführt SOBALD etwas Wichtiges passiert – nie am Ende gesammelt.

## Skills (100% automatisch)

Wenn Aufgabe: wiederholbar + >3 Schritte + kein passender Skill → **Skill-Datei sofort anlegen** (`.claude/commands/[name].md`), in `SKILLS.md` eintragen, Trigger in CLAUDE.md ergänzen. Kein Nachfragen.

---

# DocuFlow — Claude Code Kontext

Intelligentes Dokumenten-Management-Tool: PDFs/Bilder → OCR → Template-Matching → automatische Sortierung & Umbenennung.

## Kerndateien (werden erst nach Projektstart befüllt)

| Datei | Inhalt |
|-------|--------|
| `main.py` | NiceGUI App-Einstieg, Routing, Dark-Mode-Setup |
| `ui/` | NiceGUI-Seiten und -Komponenten |
| `ui/design.py` | Design-Konstanten (Farben, Tailwind-Klassen) |
| `core/processor.py` | Dreistufige Verarbeitungs-Pipeline |
| `core/ocr.py` | GLM-OCR via Ollama |
| `core/templates.py` | Template-Matching und -Verwaltung |
| `core/rules.py` | Sortier-Regeln (WANN→WOHIN→WIE BENENNEN) |
| `db/models.py` | Pydantic-Modelle + SQLite-Schema |
| `config.yaml` | App-Konfiguration via ruamel.yaml |

## Umgebung

- **Shell:** Bash (Unix-Syntax), **Python:** `python` (3.13 global)
- **App starten:** `python main.py` (nur bei explizitem Bedarf)
- **IDE:** PyCharm

## Arbeitsregeln

- Große Dateien **nie komplett lesen** – immer erst Grep, dann Read mit offset/limit
- Binärdateien (PDF, Bilder) nie mit Read öffnen
- `config.yaml` und JSON-Configs immer valide halten
- Minimale, fokussierte Änderungen – kein Refactoring ohne Auftrag
- Alle UI-Handler die I/O machen: `async def`
- Listen die sich nach OCR-Verarbeitung aktualisieren: `@ui.refreshable`
- Keine Inline-Farben — immer `ui/design.py` Konstanten nutzen
- `ui.aggrid` statt `ui.table` für Dokumentenlisten

---

## MCP-Tool-Einsatz (Pflicht)

Bei jeder Aufgabe **immer zuerst** den passenden MCP-Server nutzen, bevor auf Bash-Fallbacks zurückgegriffen wird:

| Aufgabe | Pflicht-MCP | Wann |
|---------|-------------|------|
| Excel-Datei lesen / analysieren | `mcp__excel__excel_read_sheet`, `mcp__excel__excel_describe_sheets` | Immer bei `.xlsx`-Dateien statt Bash |
| Git-Status / Log / Diff | `mcp__git__git_status`, `mcp__git__git_log`, `mcp__git__git_diff_unstaged` | Bei allen Git-Operationen |
| Git-Commit / Add | `mcp__git__git_commit`, `mcp__git__git_add` | Statt `git`-Bash-Befehlen |
| Verzeichnisse auflisten | `mcp__filesystem__list_directory` | Ergänzend zu Glob/Grep |
| Library-Dokumentation nachschlagen | `mcp__context7__query-docs` | Bei unbekannten APIs (NiceGUI, PyMuPDF, Ollama...) |
| **Gedächtnis speichern** | `mcp__rlm-claude__rlm_remember`, `mcp__rlm-claude__rlm_chunk` | Erkenntnisse, Entscheidungen, Fehlerursachen |
| **Gedächtnis abrufen** | `mcp__rlm-claude__rlm_recall`, `mcp__rlm-claude__rlm_search` | Beim Gesprächsstart + bei bekannten Themen |
| **Große Dateien analysieren** | `mcp__rlm__rlm_load_file`, `mcp__rlm__rlm_execute_code` | Statt vollständigem Read bei großen Dateien |
| **Web-Suche** | `mcp__brave-search__brave_web_search` | Bei Fehlermeldungen, unbekannten Problemen, aktuellen Infos |

**Konkrete Regeln:**
- **Excel:** Niemals XLSX mit `Read` öffnen – immer `mcp__excel__excel_describe_sheets` + `mcp__excel__excel_read_sheet`
- **Git:** `mcp__git__*` bevorzugen; Bash `git`-Befehle nur wenn MCP nicht ausreicht
- **NiceGUI-Docs:** Bei Fragen zu NiceGUI, Quasar, PyMuPDF → `mcp__context7__query-docs`

---

## Skills – Automatischer Einsatz (Pflicht)

Claude **muss** Skills automatisch via `Skill`-Tool aufrufen, sobald eine Anfrage zu einem der folgenden Muster passt:

| Erkennungsmuster (Nutzer sagt...) | Skill |
|-----------------------------------|-------|
| "UI bauen", "Seite erstellen", "Komponente", "Design", "Layout", "Farben" | `nicegui-design` |

---

## Skills – Automatische Erstellung

Wenn Claude eine **komplexe, wiederholbare Aufgabe** ausführt, die:
- mehr als 3 Schritte umfasst
- kein passendes Skill in `.claude/commands/` hat
- wahrscheinlich wieder gebraucht wird

→ **Automatisch** eine neue Skill-Datei erstellen:
1. Datei schreiben: `.claude/commands/[name].md`
2. Skill in `.claude/SKILLS.md` eintragen (Tabelle + Schnellreferenz)
3. Trigger-Muster in `.claude/CLAUDE.md` (Skills-Tabelle) ergänzen

---

## Design-System

Siehe `.claude/commands/nicegui-design.md` — bei JEDER UI-Arbeit als Referenz nutzen.
Design-Richtung: **"Utility & Precision"** — dunkles Theme, funktional-dicht, slate-Farben, blauer Akzent.

## Architektur-Phasen

1. **Core**: OCR-Pipeline, Template-System, Sortier-Regeln, Basis-UI
2. **Suche/Dashboard/Duplikate**
3. **Verträge/Lieferscheine/DATEV**
4. **System Tray/Email/API**

## Dokumentation

- `.claude/AGENT_WORKFLOW.md` – Tool-Einsatz, Loops, Token-Optimierung
- `.claude/SKILLS.md` – Übersicht aller verfügbaren Skills
- `.claude/commands/nicegui-design.md` – NiceGUI Design-System
