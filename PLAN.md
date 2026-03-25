# DocuFlow - Intelligentes Dokumenten-Management

## Context

Ziel ist ein lokales Tool, das Rechnungen (und später andere Dokumente) aus Ordnern liest, relevante Daten extrahiert, und die Dateien automatisch sortiert/umbenennt. Das Tool soll erweiterbar sein und ein UI haben. PDF-Parsing soll KI-gestützt mit lokalem Fallback auf Muster erfolgen.

**Hardware:** GTX 1080 Ti (11 GB VRAM), Ollama 0.11.10 installiert, Python 3.13, Windows 11

## Architektur-Entscheidungen

### 1. OCR/Parsing: GLM-OCR via Ollama

**Ollama + GLM-OCR** ist die beste Wahl:

- **Modell:** GLM-OCR (0.9B Parameter, 1.6–2.2 GB)
- **Benchmark:** 94.6 auf OmniDocBench V1.5 — Rang #1, schlaegt kommerzielle Loesungen
- **Precision Mode:** bis 99.9% Genauigkeit fuer Finanzdokumente
- **VRAM:** ~2–3 GB (GTX 1080 Ti hat 11 GB — reichlich Luft)
- **Ollama:** Offizielles Modell (`ollama pull glm-ocr`)

**GLM-OCR ist ideal** weil:
- Nur 0.9B Parameter, laeuft muehelos auf der 1080 Ti
- Spezialisiert auf Rechnungen, Tabellen, Finanz-Dokumente
- Direkt in Ollama verfuegbar: `ollama pull glm-ocr`
- Extrahiert strukturiert: Rechnungsnummer, Datum, Betrag, Absender, Positionen
- 128K Context Window - auch fuer lange Dokumente

### 2. Dreistufige Parsing-Strategie

```
PDF einlesen
    |
    v
[Stufe 1] Text-Extraktion (PyMuPDF/pdfplumber)
    |-- Hat der PDF eingebetteten Text? --> Regex-Muster pruefen
    |
    v
[Stufe 2] Muster-Matching (Templates)
    |-- Bekannter Absender? --> Template anwenden, fertig
    |
    v
[Stufe 3] GLM-OCR via Ollama
    |-- KI-Extraktion --> Ergebnis + automatisch Template generieren
```

**Vorteile:**
- Bekannte Rechnungen werden sofort per Muster erkannt (schnell, keine GPU)
- KI nur bei neuen/unbekannten Rechnungen (ressourcenschonend)
- Jede erfolgreiche KI-Extraktion erzeugt ein neues Template fuer die Zukunft

### 3. Auto-Template-Erzeugung ("Einmal pruefen, dann automatisch")

**Workflow:**
1. Neue Rechnung → KI-Extraktion → User prueft/korrigiert im UI → Klick "Sortieren"
2. Bei Bestaetigung: Absender wird als "bekannt" markiert + Template wird generiert
3. Ab dann: Rechnungen vom selben Absender werden **automatisch** sortiert (kein UI noetig)
4. User kann im UI sehen was automatisch sortiert wurde (Log/History)

**Globaler Auto-Modus Toggle:**
- In den Settings: Schalter "Auto-Sortierung" AN/AUS
- AUS = alle Dokumente landen in der Inbox zur manuellen Pruefung (Test-Phase)
- AN = bekannte Absender werden automatisch sortiert, nur neue in der Inbox
- Default: AUS (sicher fuer den Anfang)

**Template-Generierung:**
1. Absender-Identifikation (z.B. "Amazon", "Telekom")
2. Position der extrahierten Felder im Text merken (Regex-Pattern ableiten)
3. Template als YAML speichern
4. Konfidenz-Schwelle: Auto-Sortierung nur wenn Template-Match > 90%

### 4. Extrahierte Felder (Erweitertes Set)

- Absender (Firmenname)
- Datum (Rechnungsdatum)
- Rechnungsnummer
- Gesamtbetrag + Waehrung
- Einzelpositionen (Beschreibung, Menge, Einzelpreis)
- MwSt-Satz / MwSt-Betrag
- Zahlungsziel / Faelligkeitsdatum
- IBAN / Bankverbindung
- Kundennummer

### 5. UI: NiceGUI mit visuellem Regel-Editor

**Warum NiceGUI statt Streamlit:**
- Echtes Multi-Page-Routing (wichtig fuer spaetere Features)
- Kein Script-Rerun bei jeder Interaktion (stabiler fuer Datei-Operationen)
- Tailwind CSS fuer ansprechende UI
- Laeuft als Desktop-App oder im Browser
- Besser erweiterbar als Streamlit/Gradio

**Mehrere Input-Ordner:**
- User kann beliebig viele Inbox-Ordner konfigurieren
- z.B. "D:/Downloads", "D:/Scans", "D:/Email-Anhaenge"
- Jeder Ordner wird ueberwacht, neue PDFs werden erkannt

**Sortier-Regeln im UI (visueller Editor):**

Jede Regel besteht aus 3 Teilen: WANN → WOHIN → WIE BENENNEN

```
┌─ Regel: "Amazon Rechnungen" ─────────────────────────────┐
│                                                           │
│ WANN (Bedingung):                                         │
│   Feld: [Absender ▼]  Operator: [enthaelt ▼]             │
│   Wert: [Amazon                              ]           │
│   [+ Bedingung]                                           │
│                                                           │
│ WOHIN (Zielordner):                                       │
│   Basis: [D:/Rechnungen          ] [Ordner]               │
│   Unterordner: [jahr ▼] / [absender ▼]  [+ Feld]         │
│                                                           │
│ WIE BENENNEN (Dateiname):                                 │
│   [datum ▼] _ [rechnungsnr ▼]  [+ Feld]  .pdf            │
│                                                           │
│ Vorschau:                                                 │
│   D:/Rechnungen/2026/Amazon/2026-03-15_INV-12345.pdf      │
└───────────────────────────────────────────────────────────┘
```

**Bedingungen (WANN):**
- Absender enthaelt/ist/beginnt mit "..."
- Betrag groesser/kleiner als X
- Inhalt enthaelt "..." (Freitext-Suche im Dokument)
- Dokumenttyp ist Rechnung/Vertrag/Lieferschein
- Mehrere Bedingungen kombinierbar (UND/ODER)

**Verfuegbare Bausteine fuer Ordner + Dateiname:**
- {absender} - Firmenname
- {datum} - Rechnungsdatum (YYYY-MM-DD)
- {jahr} / {monat} / {tag}
- {rechnungsnr} - Rechnungsnummer
- {betrag} - Gesamtbetrag
- {typ} - Dokumenttyp (Rechnung, Vertrag, etc.)
- Freier Text dazwischen moeglich (z.B. Unterstriche, Bindestriche)

**Regel-Reihenfolge:**
- Regeln werden von oben nach unten geprueft
- Erste passende Regel wird angewendet
- Fallback-Regel am Ende fuer alles was nirgends passt
- Regeln per Drag & Drop umsortierbar

**Beispiele:**
1. Absender enthaelt "Amazon" → D:/Rechnungen/{jahr}/Amazon/{datum}_{rechnungsnr}.pdf
2. Absender enthaelt "Telekom" → D:/Rechnungen/{jahr}/Telekom/{datum}_{betrag}EUR.pdf
3. Betrag > 1000 → D:/Rechnungen/{jahr}/Gross/{absender}_{datum}.pdf
4. Fallback → D:/Rechnungen/{jahr}/Sonstige/{absender}_{datum}.pdf

### 6. Projekt-Struktur

```
DocuFlow/
├── app.py                    # NiceGUI Entry-Point
├── config.yaml               # Konfiguration (Ordner-Pfade, Regeln)
├── requirements.txt
│
├── core/
│   ├── __init__.py
│   ├── pdf_reader.py          # PDF Text-Extraktion (PyMuPDF)
│   ├── ocr_engine.py          # GLM-OCR via Ollama Integration
│   ├── template_matcher.py    # Muster-basierte Extraktion
│   ├── template_generator.py  # Auto-Template aus KI-Ergebnissen
│   ├── file_organizer.py      # Dateien sortieren/umbenennen
│   └── models.py              # Datenmodelle (Invoice, Document)
│
├── templates/                 # YAML-Templates pro Absender
│   └── beispiel_amazon.yaml
│
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── dashboard.py       # Uebersicht
│   │   ├── inbox.py           # Neue Dokumente sichten
│   │   ├── templates.py       # Templates verwalten
│   │   └── settings.py        # Einstellungen
│   └── components/
│       ├── document_card.py   # Dokument-Vorschau
│       └── extraction_view.py # Extrahierte Daten anzeigen/korrigieren
│
└── tests/
```

## Kern-Features (Phase 1)

1. **Mehrere Input-Ordner** - Beliebig viele Inbox-Ordner konfigurierbar
2. **Automatische Extraktion** - Dreistufig (Text -> Muster -> KI)
3. **Ergebnisse pruefen** - UI zeigt extrahierte Daten (erweitert), User korrigiert
4. **Visueller Regel-Editor** - Sortier-Regeln: WANN -> WOHIN -> WIE BENENNEN
5. **Sortieren & Umbenennen** - Nach konfigurierten Regeln
6. **Template-Lernen** - Einmal bestaetigen, danach automatisch
7. **Auto-Sortierung** - Toggle AN/AUS (Default: AUS fuer Testphase)
8. **History/Log** - Uebersicht was sortiert wurde
9. **OCR-Feedback-Loop** - Korrekturen verbessern zukuenftige Extraktion
   - Confidence-Score pro Feld (rot/gelb/gruen)
   - Korrekturen fliessen in Template-Verbesserung ein
   - Bei wiederholten Korrekturen: Template automatisch anpassen

## Spaetere Erweiterungen

### Phase 2 — Suche & Uebersicht
- Volltextsuche ueber alle Dokumente (SQLite FTS)
- Dashboard mit Statistiken (Ausgaben pro Absender, Zeitverlauf)
- Duplikat-Erkennung (gleiche Rechnungsnr / Betrag+Datum+Absender)
- Tags / Kategorien (manuell + automatisch)

### Phase 3 — Weitere Dokumenttypen
- Vertraege (Laufzeit, Kuendigungsfrist → Erinnerungen)
- Lieferscheine (Abgleich mit Rechnung)
- Briefe / Behoerdenpost
- Garantie-Belege (Ablaufdatum tracken)
- Export: CSV/Excel, DATEV-Format fuer Steuerberater

### Phase 4 — Automatisierung & Integration
- Hintergrund-Dienst (System Tray, Desktop-Notifications)
- Email-Integration (IMAP → Anhaenge automatisch in Inbox)
- Dokumenten-Verkuepfung (Rechnung ↔ Lieferschein ↔ Bestellung)
- REST API fuer externe Tools
- Multi-User / Netzwerk-Ordner
- Backup & Archiv (ZIP pro Monat, Checksummen, Papierkorb mit Undo)

## Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Sprache | Python 3.13 |
| UI | NiceGUI |
| PDF-Text | PyMuPDF (fitz) |
| OCR/KI | GLM-OCR via Ollama (ollama Python SDK) |
| Templates | YAML (ruamel.yaml) |
| Datenbank | SQLite (via sqlite3) fuer Dokument-Index |
| Config | YAML |

## Dependencies

```
nicegui
pymupdf
ollama
ruamel.yaml
pydantic
watchdog
```

## Implementierungsreihenfolge

1. Projekt-Setup (venv, Dependencies, Grundstruktur)
2. `models.py` - Pydantic-Modelle fuer Dokumente
3. `pdf_reader.py` - Text aus PDFs extrahieren
4. `ocr_engine.py` - GLM-OCR via Ollama anbinden
5. `template_matcher.py` + `template_generator.py` - Muster-System
6. `file_organizer.py` - Sortieren/Umbenennen
7. UI aufbauen (Dashboard, Inbox, Regel-Editor, Settings)
8. OCR-Feedback-Loop
9. Integration & Tests

## Verifizierung

1. Ollama starten, `ollama pull glm-ocr` ausfuehren
2. Test-Rechnung (PDF) in Inbox-Ordner legen
3. App starten, pruefen ob Rechnung erkannt wird
4. Extrahierte Daten im UI kontrollieren
5. Sortierung/Umbenennung pruefen
6. Zweite Rechnung vom selben Absender -> Template sollte greifen
