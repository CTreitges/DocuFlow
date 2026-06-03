# DocuFlow

Lokales Tool zum Einlesen, Extrahieren und automatischen Sortieren deutscher
Rechnungen/Dokumente. Pipeline: PDFs aus überwachten Ordnern → Text-/Template-/OCR-
Extraktion → Prüfung & Korrektur → Sortierung & Umbenennung nach visuellen Regeln.

## Architektur (Stand 2026-06: NiceGUI → Svelte + FastAPI)

| Schicht | Pfad | Beschreibung |
|--------|------|--------------|
| **Core** | `core/` | Unveränderte Python-Logik (PDF, OCR, Templates, Sortierung). Bug-Fixes K1/K2. |
| **Backend** | `backend/` | FastAPI-App (async). Wiederverwendet `core/` als REST-API unter `/api`. |
| **Frontend** | `frontend/` | Svelte 5 + Vite + Tailwind, dunkles „Utility & Precision"-Design (aus Claude Design, Quelle in `frontend/_design/`). |
| **Desktop** | `desktop.py` | pywebview-Shell: startet das Backend und öffnet ein natives Fenster (1280×850). |
| _Legacy_ | `app.py`, `ui/` | Alte NiceGUI-UI — wird durch `frontend/` ersetzt, bleibt vorerst als Referenz. |

## Starten

**Voraussetzungen:** Python 3.12+, Node 20+.

```bash
# Python-Abhängigkeiten
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

### Variante A — Desktop-App (Produktion)
```bash
cd frontend && npm install && npm run build && cd ..
python desktop.py            # FastAPI + natives Fenster
```

### Variante B — Entwicklung (Hot-Reload)
```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload          # http://127.0.0.1:8000

# Terminal 2: Frontend (proxyt /api → :8000)
cd frontend && npm run dev                  # http://127.0.0.1:5173
```

### Variante C — Backend serviert das gebaute Frontend
```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app                    # UI + API auf http://127.0.0.1:8000
```

> Ist das Backend nicht erreichbar, zeigt das Frontend **Design-Beispieldaten**
> (Demo-Modus), damit die Oberfläche nie leer ist.

## Tests

```bash
pytest tests/                 # 19 Tests: K1/K2-Regression + API-Smoke
```

## Behobene Backend-Bugs

- **K1 — Auto-Sortierung war toter Code:** Der Template-Match-Score wurde nie in
  `extraction.confidence['overall']` geschrieben, sodass der Schwellwert-Check
  immer 0 las. Fix in `core/processor.py` (Score wird gesetzt) + portierte
  `process_and_maybe_auto_sort`-Methode. Schwellwert: `auto_confidence_threshold`.
- **K2 — Path-Traversal in `_sanitize_filename`:** Ordner-Segmente aus OCR-Platz-
  haltern (`{absender}` = `../../x`) konnten `shutil.move` aus dem Zielordner
  lenken. Fix in `core/file_organizer.py`: Segment-Sanitisierung + Containment-Check
  (`resolve().is_relative_to(base)`).

## API (Auszug)

`/api/health` · `/api/stats` · `/api/history` · `/api/scan` ·
`/api/documents[/{id}][/process|/confirm|/ignore|/reactivate|/extraction|/preview]` ·
`/api/process-all` · `/api/rules` (GET/PUT) · `/api/templates` (GET/DELETE) ·
`/api/settings` (GET/PUT) · `/api/reset`. Interaktive Doku unter `/docs`.
