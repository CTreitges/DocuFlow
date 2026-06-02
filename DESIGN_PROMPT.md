# Claude-Design-Prompt — DocuFlow UI (interaktives Mockup)

> Diesen Prompt in **claude.ai** (Artifacts) einfügen. Erzeugt ein klickbares High-Fidelity-Mockup als **React + Tailwind**-Artifact. Look-&-Feel-Target; produktive Umsetzung später in **Svelte 5** (Vite-SPA + FastAPI + pywebview). Komponenten daher sauber/framework-neutral halten.

---

Du bist ein Senior Product Designer **und** Frontend-Engineer. Baue ein **interaktives, klickbares High-Fidelity-Mockup** der Desktop-App **„DocuFlow"** als **ein einzelnes React-Artifact mit Tailwind** (Dark Theme). Alle 6 Screens müssen über die Sidebar navigierbar sein, mit realistischen deutschen Mock-Daten und umschaltbaren Zuständen (leer / lädt / Fehler / Erfolg). Verwende `lucide-react` für Icons. Kein Backend — alles mit lokalem React-State und Mock-Daten. Halte die Komponentenstruktur sauber und framework-neutral (keine exotischen React-Only-Tricks), weil das Ganze später 1:1 in **Svelte 5** umgesetzt wird.

## Kontext / Produkt

DocuFlow ist ein **lokales Power-User-Tool** für die Verwaltung deutscher Rechnungen/Dokumente. Pipeline: PDFs aus überwachten Ordnern → OCR-/Template-Extraktion → Prüfung & Korrektur durch den Nutzer → automatische Sortierung & Umbenennung nach visuellen Regeln. Läuft als **Desktop-Fenster** (~1280×850, kein Browser-Chrome). Nutzer = **eine Person**, die viele Rechnungen verarbeitet und maximale **Kontrolle + Geschwindigkeit + Übersicht** will. Es ist KEIN verspieltes Consumer-Tool — Informationsdichte und Präzision schlagen Dekoration.

## Design-Sprache: „Utility & Precision"

Dunkel, dicht, funktional, vertrauenswürdig. Keine dekorativen Elemente ohne Funktion.

**Farben (exakt):**
- Hintergründe: Page `#0f172a` (slate-900) · Surface/Cards/Sidebar/Header `#1e293b` (slate-800) · Elevated/aktiver Nav/Code `#334155` (slate-700)
- Akzent (primär: Buttons, Links, aktiver Nav-Text) `#3b82f6` (blue-500) · Sekundär-Akzent `#8b5cf6` (Status „in Arbeit")
- Semantik: Success `#22c55e` · Warning `#f59e0b` · Error `#ef4444` · Muted `#6b7280` · Info `#38bdf8`
- Text: primär `#f1f5f9` · sekundär `#94a3b8` · muted `#64748b`
- Border: `rgba(255,255,255,0.08)`, 1px (Cards border-only, **kein** Schatten)

**Raster (4px-Basis):** Sidebar 220px (kollabierbar) · Header 56px · Seiten-Padding 24px · Card-Abstand 16px · Card-Padding 16px · Card-Radius 12px · Button-Radius 8px · Nav-Icon 20px.

**Typografie:** Sektions-Header `text-lg` semibold + Akzent-Icon · Card-Titel `text-sm` semibold · Sidebar-Sektions-Label `text-[10px]` bold tracking-widest UPPERCASE muted · Werte `text-sm` primär · Labels/Hints `text-xs` muted · **Monospace** für Pfade, IBAN, Rohtext, Logs, Konfidenz-%.

**Status-Farb-Mapping:** neu→Akzent · review→Warning · verarbeitet→Success · fehler→Error · in Arbeit→Sekundär-Akzent (Purple) · ignoriert→Muted.

## App-Shell

- **Header** (56px, slate-800, untere Border): links Menu-Toggle (klappt Sidebar) + Dokument-Icon + Wortmarke „DocuFlow"; rechts Versions-Label „v0.1" (muted).
- **Sidebar** (220px, slate-800, kollabierbar) mit zwei beschrifteten Sektionen:
  - **VERARBEITUNG:** Eingang (inbox), Dashboard (layout-dashboard), Templates (wand-2)
  - **SYSTEM** (Separator davor): Sortier-Regeln (list-filter / rule), Einstellungen (settings), OCR-Debug (bug)
  - Aktiver Eintrag: slate-700 Hintergrund + blauer Text; inaktiv: sekundär-grauer Text. Voll-breite, links-ausgerichtete Buttons, rounded-lg.
- **Echtes Routing/Screen-Switching** (nicht nur Tab-Panels) — die Sidebar wechselt den aktiven Screen, aktiver Zustand klar markiert.
- **Content:** slate-900, Padding 24px, scrollbar; pro Screen oben ein Sektions-Header (Icon + Titel).

## Wiederverwendbare Komponenten (zentral definieren, überall nutzen)

1. **StatCard**(label, value, icon, color): Surface-Card, oben [Label sekundär | Icon farbig], darunter großer Wert `text-2xl` bold.
2. **StatusBadge**(status): Pill rounded-full `text-xs`; Style = Farbe@12% Hintergrund / Farbe Text / Farbe@27% Border.
3. **ConfidenceBadge**(value): kleines Mono-Pill mit %-Wert. **EIN einheitliches Schema** (nicht wie im Alt-UI 3 verschiedene): ≥90% grün · ≥70% amber · <70% rot. Konsistent auf allen Screens.
4. **EditableField**(label, value, confidence?): Label + optional ConfidenceBadge, Anzeige-Wert + Stift-Icon (Opacity 40%, hover 100%); Klick → Inline-Input + Check(grün)/Close(grau); Cancel verwirft.
5. **RuleCard**: Surface-Card mit Header (Drag-Handle + #Nr + Regelname-Input + Enabled-Switch + Löschen) und 3 aufklappbaren Abschnitten (WANN/WOHIN/WIE BENENNEN) + Live-Vorschau-Zeile.
6. **ConfirmDialog**(title, body, onConfirm): zentrierter Surface-Dialog min-w 320px, Abbrechen (flat) + Bestätigen (Akzent).
7. **Toast/Notification**: oben rechts, Success/Info 3s, Error/Warning 5s.

## Die 6 Screens

### 1) Eingang (Inbox) — Default-Screen, wichtigste & dichteste Oberfläche
- **Toolbar:** Buttons „Ordner scannen" + „Alle verarbeiten" + Status-Label rechts (z.B. „3 neue Dokumente gefunden", „Verarbeite 2/3…").
- **Sub-Tabs:** „Eingang" und „Ignoriert".
- **Tabelle** (dichte Datentabelle, dark, sortier-/filterbar, Single-Select, Zeilen-Klick): Spalten **Dateiname** (semibold) | **Status** (StatusBadge) | **Absender** | **Datum** (ISO) | **Betrag** (rechtsbündig, „1.234,56 EUR") | **Re-Nr.** | **Konfidenz** (%). Zeigt nur Docs ≠ verarbeitet/ignoriert.
- **Detail-/Review-Panel** unter der Tabelle (erscheint bei Zeilen-Klick), Header = Dateiname + Pfad (mono, muted) + StatusBadge. **Drei Varianten:**
  - **Unverarbeitet:** Hinweis „Noch nicht verarbeitet" + Buttons „Jetzt verarbeiten" / „Ignorieren".
  - **Extraktion (Kern!):** 2-Spalten-Grid mit 9 Feldern — **editierbar:** Absender, Datum, Rechnungsnr., Betrag, IBAN, Kundennr.; **read-only:** MwSt-Satz, Zahlungsziel, Dokumenttyp. Nur Absender/Datum/Rechnungsnr./Betrag tragen eine ConfidenceBadge. Darunter **Positionen-Tabelle** (# | Beschreibung | Menge | Gesamt). Buttons: **„Bestätigen & Sortieren"** (grün) | „Ignorieren" | „Schließen".
  - **Fehler:** rote Fehlerkarte mit Detail (mono) + Buttons „Nochmal versuchen" (amber) / „Ignorieren".
- **Ignoriert-Tab:** Karten je Dokument (Datei-Icon + Name + Datum + „Reaktivieren").
- **States:** Leer-Eingang (zentrierte Card, Inbox-Icon, „Keine neuen Dokumente", Subtext „Klicke ‚Ordner scannen'…") · Leer-Ignoriert · Lade-Status im Label · Erfolg-Toast · Fehlerkarte.

### 2) Dashboard
- **4 StatCards** (Grid): „Neu / Inbox" (accent) | „Im Review" (warning) | „Verarbeitet" (success) | „Gesamt" (muted).
- **Card „Sortierte Dokumente":** Tabelle (Datei | Absender | Datum | Betrag rechtsbündig | „Sortiert nach" = Zielpfad | „Verarbeitet" = Zeitstempel).
- **Card „Aktivitäts-Log":** Zeitfilter-Button-Group (Heute / Woche / Alles) + Liste: Action-Icon (farbig je Typ) + Dateiname (truncate) + Details + Uhrzeit; bei Action „sortiert" ein **Undo-Button** pro Zeile.
  - Icon-Mapping: scan→search, template→layout-template, ocr→scan-text, sortiert→check-circle, auto-sortiert→zap, bestätigt→thumbs-up, fehler→alert-circle, template-erstellt→wand-2, undo→undo, korrektur→pencil, reaktiviert→rotate-ccw, ignoriert→ban.
- **Fehler-Log-Card** (nur wenn Fehler vorhanden, rot getönt).
- **States:** Leer-Sortierte (box-Icon + „Noch keine sortierten Dokumente") · Leer-Log (kursiv „Keine Aktivitäten im Zeitraum") · Undo-Toast.

### 3) Templates
- Beschreibungszeile „Automatisch generierte Muster für bekannte Absender."
- Tabelle: **Absender** (semibold) | **Muster** (Anzahl) | **Felder** (Anzahl) | **Schwelle** (%) | **Verwendet** (Anzahl) | **ID** (klein, halbtransparent).
- Button „Templates neu laden". **Neu vs. Alt-UI:** pro Zeile **Bearbeiten + Löschen** ergänzen (Alt-UI war read-only).
- **State:** Leer (wand-2-Icon + „Keine Templates vorhanden", Subtext „werden automatisch erstellt, wenn Dokumente bestätigt werden").

### 4) Sortier-Regeln — visueller Editor
- Hinweiszeile „Regeln werden von oben nach unten geprüft. Erste passende gewinnt."
- Liste von **RuleCards**. Pro Card 3 aufklappbare Abschnitte:
  - **WANN (Bedingungen):** pro Bedingung [ab der 2.: Logik-Select AND/OR] + Feld-Select (Absender/Betrag/Inhalt/Dokumenttyp/Rechnungsnr.) + Operator-Select (enthält/ist/beginnt mit/größer als/kleiner als) + Wert-Input + Entfernen-X. „+ Bedingung". Leer = „Keine Bedingungen = Fallback-Regel (passt immer)".
  - **WOHIN (Zielordner):** Basis-Ordner-Input + Unterordner-Chips (Selects, „/"-getrennt, Platzhalter kombinierbar) + Hinzufügen.
  - **WIE BENENNEN:** Dateiname-Bausteine als Chip-Selects („_"-getrennt) + „.pdf"-Suffix + Hinzufügen. Platzhalter: `{absender} {datum} {jahr} {monat} {tag} {rechnungsnr} {betrag} {typ} {waehrung}`.
  - **Live-Vorschau-Zeile** (kursiv, muted) mit Beispieldaten, z.B. `D:/Rechnungen/2026/Amazon/2026-03-15_INV-12345.pdf`.
- **Neu vs. Alt-UI: echtes Drag-&-Drop-Reorder** der RuleCards (Handle funktional, nicht nur dekorativ).
- **State:** Leer („Keine Regeln vorhanden" + „Neue Regel").

### 5) Einstellungen
- Optionale **Warn-Card** oben (amber): nicht existierende aktivierte Ordner / fehlender Ausgabe-Ordner.
- **Card „Ordner-Überwachung":** Live-Status (grüner Punkt + „Aktiv — N Ordner überwacht" + Pfadliste mono, oder grauer Punkt + „Inaktiv") + Button „Neu starten".
- **Card „Auto-Sortierung":** Switch + Beschreibung + **Konfidenz-Schwellwert-Slider** 50–100% (Schritt 5) + Live-%-Anzeige (mono, accent) + Hinweis „Dokumente unterhalb dieser Schwelle gehen immer in die Inbox."
- **Card „Eingabe-Ordner":** Liste je Ordner (Pfad-Input + Ordner-Picker-Button + Aktiv-Switch + Löschen) + „Ordner hinzufügen".
- **Card „Ausgabe":** Basis-Ordner-Input + Picker-Button.
- **Card „German-OCR" (Badge „Primär"):** Beschreibung + Aktiviert-Switch + Backend-Select (Ollama-GPU / HuggingFace-CPU / LlamaCPP-GGUF) + **3-Status-Badge** (Nicht installiert=rot / Installiert·Modell nicht geladen=amber / Geladen·Aktiv=grün) + kontextabhängige Aktions-Buttons + ausblendbares **Live-Install-Log** (mono).
- **Card „Ollama" (Badge „Fallback" + Live-Verbindungs-Badge):** URL-Input + Modell-Input + Timeout-Number + „Verbindung testen".
- **Card „Datenbank zurücksetzen":** Beschreibung + „Alles löschen" (rot, outline) → **ConfirmDialog** (einzige destruktive Aktion).
- **States:** Warn-Card bedingt · Watchdog aktiv/inaktiv · OCR-3-Status · Lade-Spinner + Live-Log während Install/Download · Ollama Prüfe…/Verbunden/Offline.

### 6) OCR-Debug — Diagnose
- Hinweiszeile „PDF auswählen → Pipeline läuft → Extrahierte Daten + Template-Vorschau".
- Aktionen: „PDF auswählen" + „Leeren".
- **Pipeline-Status als sichtbarer Stepper/Progress:** Text-Extraktion → Template-Match → OCR-Fallback, mit Status-Texten („Lese <name>…", „N Seiten, M Zeichen. Prüfe Templates…", „Kein Template — German-OCR läuft… (30–120 s)", „✓ Template: <Absender>") + animiertem Fortschrittsbalken während OCR.
- **Ergebnis-Kopf:** Quelle-Badge (Template=grün / OCR=blau) + Seitenzahl + „Text-PDF"/„Bild-PDF".
- **Ergebnis-Tabs:** Extrahierte Felder (10 Felder je ConfidenceBadge + Positionen) | Template-Vorschau (YAML-Code-Block) | PDF-Text (Zeichenzahl + readonly Mono-Textarea) | OCR-Output (nur wenn OCR genutzt).
- **States:** Initial „Keine PDF geladen" · Lädt (Stepper + Progress + Status) · Erfolg (Badge + Tabs) · Fehler (rotes Status-Label + Toast) · Tab-Leer-States.

## Verbesserungen ggü. dem alten NiceGUI-UI (bewusst einbauen)
1. **Echtes Routing** statt versteckter Single-Page-Tabs.
2. **Echtes Drag-&-Drop** beim Regel-Reorder (Alt-UI hatte nur ein Deko-Icon).
3. **EIN einheitliches Konfidenz-Badge-Schema** (Alt-UI hatte 3 widersprüchliche).
4. Templates editier-/löschbar (Alt-UI read-only).
5. Generell mehr „Atem" + klarere Hierarchie, ohne Informationsdichte zu opfern.

## Mock-Daten (deutsch, realistisch)
- Absender: „Amazon EU S.à r.l.", „Telekom Deutschland GmbH", „Müller Dachbau GmbH", „Schneider Elektro", „Stadtwerke".
- Beträge im deutschen Format („1.234,56 EUR", „89,90 EUR"), ISO-Daten, Re-Nrn („INV-2026-0412", „RG-88231"), eine IBAN, gemischte Status (neu/review/verarbeitet/fehler), Konfidenzen 62–98%, ein paar Positionen je Rechnung, ein gefülltes Aktivitäts-Log mit verschiedenen Action-Typen.

## Liefer-Anforderung
Ein **lauffähiges React-Artifact**, alle 6 Screens per Sidebar navigierbar, dark, mit den exakten Farben/Abständen oben, realistischen Mock-Daten und durchklickbaren Interaktionen (Zeile wählen → Detail-Panel, Inline-Edit, Regel auf-/zuklappen + Drag-Reorder, Tab-Wechsel, ConfirmDialog, Toasts, Empty-States umschaltbar). Sauber komponentisiert für die spätere Svelte-5-Portierung.
