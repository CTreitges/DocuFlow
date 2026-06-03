# Chat

_Started 2026-06-02 21:28 UTC_

---

## User

<system-info comment="Only acknowledge these if relevant">
Project title is now "DocuFlow"
Project is currently empty (no files)
Current date is now June 2, 2026
</system-info>

<default aesthetic_system_instructions>
The user has not attached a design system. If they have ALSO not attached references or art direction, and the project is empty, you must ASK the user what visual aesthetic they want. Use the questions_v2 tool to ask about preferred vibe, audience, colors, type, mood, etc. Do NOT just pick your own visual aesthetic without getting the user's aesthetic input -- this is how you get slop!

Once answered, use this guidance when creating designs:
- Choose a type pairing from web-safe set or Google Fonts. Helvetica is a good choice. Avoid hard-to-read or overly stylized fonts. Use 1-3 fonts only.
- Foreground and background: choose a color tone (warm, cool, neutral, something in-between). Use subtly-toned whites and blacks; avoid saturations above 0.02 for whites.
- Accents: choose 0-2 additional accent colors using oklch. All accents should share same chroma and lightness; vary hue.
- NEVER write out an SVG yourself that's more complicated than a square, circle, diamond, etc.
- For imagery, never hand-draw SVGs; use subtly-striped SVG placeholders instead with monospace explainers for what should be dropped there (e.g. “product shot”)

CRITICAL: ignore default aesthetic entirely if given other aesthetic instructions like reference images, design systems or guidance, or if there are files in the project already.
</default aesthetic_system_instructions>

<pasted_text name="Pasted text (167 lines)">
 Du bist ein Senior Product Designer und Frontend-Engineer. Baue ein interaktives, klickbares High-Fidelity-Mockup der
  Desktop-App „DocuFlow" als ein einzelnes React-Artifact mit Tailwind (Dark Theme). Alle 6 Screens müssen über die
  Sidebar navigierbar sein, mit realistischen deutschen Mock-Daten und umschaltbaren Zuständen (leer / lädt / Fehler /
  Erfolg). Verwende lucide-react für Icons. Kein Backend — alles mit lokalem React-State und Mock-Daten. Halte die
  Komponentenstruktur sauber und framework-neutral (keine exotischen React-Only-Tricks), weil das Ganze später 1:1 in
  Svelte 5 umgesetzt wird.

  ## Kontext / Produkt
  DocuFlow ist ein lokales Power-User-Tool für die Verwaltung deutscher Rechnungen/Dokumente. Pipeline: PDFs aus
  überwachten Ordnern → OCR-/Template-Extraktion → Prüfung & Korrektur durch den Nutzer → automatische Sortierung &
  Umbenennung nach visuellen Regeln. Läuft als Desktop-Fenster (~1280×850, kein Browser-Chrome). Nutzer = eine Person,
  die viele Rechnungen verarbeitet und maximale Kontrolle + Geschwindigkeit + Übersicht will. Es ist KEIN verspieltes
  Consumer-Tool — Informationsdichte und Präzision schlagen Dekoration.

  ## Design-Sprache: „Utility & Precision"
  Dunkel, dicht, funktional, vertrauenswürdig. Keine dekorativen Elemente ohne Funktion.

  Farben (exakt):
  - Hintergründe: Page #0f172a (slate-900) · Surface/Cards/Sidebar/Header #1e293b (slate-800) · Elevated/aktiver
  Nav/Code #334155 (slate-700)
  - Akzent (primär: Buttons, Links, aktiver Nav-Text) #3b82f6 (blue-500) · Sekundär-Akzent #8b5cf6 (Status „in Arbeit")
  - Semantik: Success #22c55e · Warning #f59e0b · Error #ef4444 · Muted #6b7280 · Info #38bdf8
  - Text: primär #f1f5f9 · sekundär #94a3b8 · muted #64748b
  - Border: rgba(255,255,255,0.08), 1px (Cards border-only, kein Schatten)

  Raster (4px-Basis): Sidebar 220px (kollabierbar) · Header 56px · Seiten-Padding 24px · Card-Abstand 16px ·
  Card-Padding 16px · Card-Radius 12px · Button-Radius 8px · Nav-Icon 20px.

  Typografie: Sektions-Header text-lg semibold + Akzent-Icon · Card-Titel text-sm semibold · Sidebar-Sektions-Label
  text-[10px] bold tracking-widest UPPERCASE muted · Werte text-sm primär · Labels/Hints text-xs muted · Monospace für
  Pfade, IBAN, Rohtext, Logs, Konfidenz-%.

  Status-Farb-Mapping: neu→Akzent · review→Warning · verarbeitet→Success · fehler→Error · in Arbeit→Sekundär-Akzent
  (Purple) · ignoriert→Muted.

  ## App-Shell
  - Header (56px, slate-800, untere Border): links Menu-Toggle (klappt Sidebar) + Dokument-Icon + Wortmarke „DocuFlow";
  rechts Versions-Label „v0.1" (muted).
  - Sidebar (220px, slate-800, kollabierbar) mit zwei beschrifteten Sektionen:
    - VERARBEITUNG: Eingang (inbox), Dashboard (layout-dashboard), Templates (wand-2)
    - SYSTEM (Separator davor): Sortier-Regeln (list-filter), Einstellungen (settings), OCR-Debug (bug)
    - Aktiver Eintrag: slate-700 Hintergrund + blauer Text; inaktiv: sekundär-grauer Text. Voll-breite,
  links-ausgerichtete Buttons, rounded-lg.
  - Echtes Routing/Screen-Switching (nicht nur Tab-Panels) — die Sidebar wechselt den aktiven Screen, aktiver Zustand
  klar markiert.
  - Content: slate-900, Padding 24px, scrollbar; pro Screen oben ein Sektions-Header (Icon + Titel).

  ## Wiederverwendbare Komponenten (zentral definieren, überall nutzen)
  1. StatCard(label, value, icon, color): Surface-Card, oben [Label sekundär | Icon farbig], darunter großer Wert
  text-2xl bold.
  2. StatusBadge(status): Pill rounded-full text-xs; Style = Farbe@12% Hintergrund / Farbe Text / Farbe@27% Border.
  3. ConfidenceBadge(value): kleines Mono-Pill mit %-Wert. EIN einheitliches Schema (nicht 3 verschiedene): ≥90% grün ·
  ≥70% amber · <70% rot. Konsistent auf allen Screens.
  4. EditableField(label, value, confidence?): Label + optional ConfidenceBadge, Anzeige-Wert + Stift-Icon (Opacity 40%,
  hover 100%); Klick → Inline-Input + Check(grün)/Close(grau); Cancel verwirft.
  5. RuleCard: Surface-Card mit Header (Drag-Handle + #Nr + Regelname-Input + Enabled-Switch + Löschen) und 3
  aufklappbaren Abschnitten (WANN/WOHIN/WIE BENENNEN) + Live-Vorschau-Zeile.
  6. ConfirmDialog(title, body, onConfirm): zentrierter Surface-Dialog min-w 320px, Abbrechen (flat) + Bestätigen
  (Akzent).
  7. Toast/Notification: oben rechts, Success/Info 3s, Error/Warning 5s.

  ## Die 6 Screens

  ### 1) Eingang (Inbox) — Default-Screen, wichtigste & dichteste Oberfläche
  - Toolbar: Buttons „Ordner scannen" + „Alle verarbeiten" + Status-Label rechts (z.B. „3 neue Dokumente gefunden",
  „Verarbeite 2/3…").
  - Sub-Tabs: „Eingang" und „Ignoriert".
  - Tabelle (dichte Datentabelle, dark, sortier-/filterbar, Single-Select, Zeilen-Klick): Spalten Dateiname (semibold) |
  Status (StatusBadge) | Absender | Datum (ISO) | Betrag (rechtsbündig, „1.234,56 EUR") | Re-Nr. | Konfidenz (%). Zeigt
  nur Docs ≠ verarbeitet/ignoriert.
  - Detail-/Review-Panel unter der Tabelle (erscheint bei Zeilen-Klick), Header = Dateiname + Pfad (mono, muted) +
  StatusBadge. Drei Varianten:
    - Unverarbeitet: Hinweis „Noch nicht verarbeitet" + Buttons „Jetzt verarbeiten" / „Ignorieren".
    - Extraktion (Kern!): 2-Spalten-Grid mit 9 Feldern — editierbar: Absender, Datum, Rechnungsnr., Betrag, IBAN,
  Kundennr.; read-only: MwSt-Satz, Zahlungsziel, Dokumenttyp. Nur Absender/Datum/Rechnungsnr./Betrag tragen eine
  ConfidenceBadge. Darunter Positionen-Tabelle (# | Beschreibung | Menge | Gesamt). Buttons: „Bestätigen & Sortieren"
  (grün) | „Ignorieren" | „Schließen".
    - Fehler: rote Fehlerkarte mit Detail (mono) + Buttons „Nochmal versuchen" (amber) / „Ignorieren".
  - Ignoriert-Tab: Karten je Dokument (Datei-Icon + Name + Datum + „Reaktivieren").
  - States: Leer-Eingang (zentrierte Card, Inbox-Icon, „Keine neuen Dokumente", Subtext „Klicke ‚Ordner scannen'…") ·
  Leer-Ignoriert · Lade-Status im Label · Erfolg-Toast · Fehlerkarte.

  ### 2) Dashboard
  - 4 StatCards (Grid): „Neu / Inbox" (accent) | „Im Review" (warning) | „Verarbeitet" (success) | „Gesamt" (muted).
  - Card „Sortierte Dokumente": Tabelle (Datei | Absender | Datum | Betrag rechtsbündig | „Sortiert nach" = Zielpfad |
  „Verarbeitet" = Zeitstempel).
  - Card „Aktivitäts-Log": Zeitfilter-Button-Group (Heute / Woche / Alles) + Liste: Action-Icon (farbig je Typ) +
  Dateiname (truncate) + Details + Uhrzeit; bei Action „sortiert" ein Undo-Button pro Zeile.
    - Icon-Mapping: scan→search, template→layout-template, ocr→scan-text, sortiert→check-circle, auto-sortiert→zap,
  bestätigt→thumbs-up, fehler→alert-circle, template-erstellt→wand-2, undo→undo, korrektur→pencil,
  reaktiviert→rotate-ccw, ignoriert→ban.
  - Fehler-Log-Card (nur wenn Fehler vorhanden, rot getönt).
  - States: Leer-Sortierte (box-Icon + „Noch keine sortierten Dokumente") · Leer-Log (kursiv „Keine Aktivitäten im
  Zeitraum") · Undo-Toast.

  ### 3) Templates
  - Beschreibungszeile „Automatisch generierte Muster für bekannte Absender."
  - Tabelle: Absender (semibold) | Muster (Anzahl) | Felder (Anzahl) | Schwelle (%) | Verwendet (Anzahl) | ID (klein,
  halbtransparent).
  - Button „Templates neu laden". Pro Zeile Bearbeiten + Löschen.
  - State: Leer (wand-2-Icon + „Keine Templates vorhanden", Subtext „werden automatisch erstellt, wenn Dokumente
  bestätigt werden").

  ### 4) Sortier-Regeln — visueller Editor
  - Hinweiszeile „Regeln werden von oben nach unten geprüft. Erste passende gewinnt."
  - Liste von RuleCards. Pro Card 3 aufklappbare Abschnitte:
    - WANN (Bedingungen): pro Bedingung [ab der 2.: Logik-Select AND/OR] + Feld-Select
  (Absender/Betrag/Inhalt/Dokumenttyp/Rechnungsnr.) + Operator-Select (enthält/ist/beginnt mit/größer als/kleiner als) +
  Wert-Input + Entfernen-X. „+ Bedingung". Leer = „Keine Bedingungen = Fallback-Regel (passt immer)".
    - WOHIN (Zielordner): Basis-Ordner-Input + Unterordner-Chips (Selects, „/"-getrennt, Platzhalter kombinierbar) +
  Hinzufügen.
    - WIE BENENNEN: Dateiname-Bausteine als Chip-Selects („_"-getrennt) + „.pdf"-Suffix + Hinzufügen. Platzhalter:
  {absender} {datum} {jahr} {monat} {tag} {rechnungsnr} {betrag} {typ} {waehrung}.
    - Live-Vorschau-Zeile (kursiv, muted) mit Beispieldaten, z.B. D:/Rechnungen/2026/Amazon/2026-03-15_INV-12345.pdf.
  - Echtes Drag-&-Drop-Reorder der RuleCards (Handle funktional).
  - State: Leer („Keine Regeln vorhanden" + „Neue Regel").

  ### 5) Einstellungen
  - Optionale Warn-Card oben (amber): nicht existierende aktivierte Ordner / fehlender Ausgabe-Ordner.
  - Card „Ordner-Überwachung": Live-Status (grüner Punkt + „Aktiv — N Ordner überwacht" + Pfadliste mono, oder grauer
  Punkt + „Inaktiv") + Button „Neu starten".
  - Card „Auto-Sortierung": Switch + Beschreibung + Konfidenz-Schwellwert-Slider 50–100% (Schritt 5) + Live-%-Anzeige
  (mono, accent) + Hinweis „Dokumente unterhalb dieser Schwelle gehen immer in die Inbox."
  - Card „Eingabe-Ordner": Liste je Ordner (Pfad-Input + Ordner-Picker-Button + Aktiv-Switch + Löschen) + „Ordner
  hinzufügen".
  - Card „Ausgabe": Basis-Ordner-Input + Picker-Button.
  - Card „German-OCR" (Badge „Primär"): Beschreibung + Aktiviert-Switch + Backend-Select (Ollama-GPU / HuggingFace-CPU /
  LlamaCPP-GGUF) + 3-Status-Badge (Nicht installiert=rot / Installiert·Modell nicht geladen=amber / Geladen·Aktiv=grün)
  + kontextabhängige Aktions-Buttons + ausblendbares Live-Install-Log (mono).
  - Card „Ollama" (Badge „Fallback" + Live-Verbindungs-Badge): URL-Input + Modell-Input + Timeout-Number + „Verbindung
  testen".
  - Card „Datenbank zurücksetzen": Beschreibung + „Alles löschen" (rot, outline) → ConfirmDialog (einzige destruktive
  Aktion).
  - States: Warn-Card bedingt · Watchdog aktiv/inaktiv · OCR-3-Status · Lade-Spinner + Live-Log während Install/Download
  · Ollama Prüfe…/Verbunden/Offline.

  ### 6) OCR-Debug — Diagnose
  - Hinweiszeile „PDF auswählen → Pipeline läuft → Extrahierte Daten + Template-Vorschau".
  - Aktionen: „PDF auswählen" + „Leeren".
  - Pipeline-Status als sichtbarer Stepper/Progress: Text-Extraktion → Template-Match → OCR-Fallback, mit Status-Texten
  („Lese <name>…", „N Seiten, M Zeichen. Prüfe Templates…", „Kein Template — German-OCR läuft… (30–120 s)", „✓ Template:
  <Absender>") + animiertem Fortschrittsbalken während OCR.
  - Ergebnis-Kopf: Quelle-Badge (Template=grün / OCR=blau) + Seitenzahl + „Text-PDF"/„Bild-PDF".
  - Ergebnis-Tabs: Extrahierte Felder (10 Felder je ConfidenceBadge + Positionen) | Template-Vorschau (YAML-Code-Block)
  | PDF-Text (Zeichenzahl + readonly Mono-Textarea) | OCR-Output (nur wenn OCR genutzt).
  - States: Initial „Keine PDF geladen" · Lädt (Stepper + Progress + Status) · Erfolg (Badge + Tabs) · Fehler (rotes
  Status-Label + Toast) · Tab-Leer-States.

  ## Verbesserungen ggü. dem alten NiceGUI-UI (bewusst einbauen)
  1. Echtes Routing statt versteckter Single-Page-Tabs.
  2. Echtes Drag-&-Drop beim Regel-Reorder (Alt-UI hatte nur ein Deko-Icon).
  3. EIN einheitliches Konfidenz-Badge-Schema (Alt-UI hatte 3 widersprüchliche).
  4. Templates editier-/löschbar (Alt-UI read-only).
  5. Generell mehr „Atem" + klarere Hierarchie, ohne Informationsdichte zu opfern.

  ## Mock-Daten (deutsch, realistisch)
  - Absender: „Amazon EU S.à r.l.", „Telekom Deutschland GmbH", „Müller Dachbau GmbH", „Schneider Elektro",
  „Stadtwerke".
  - Beträge im deutschen Format („1.234,56 EUR", „89,90 EUR"), ISO-Daten, Re-Nrn („INV-2026-0412", „RG-88231"), eine
  IBAN, gemischte Status (neu/review/verarbeitet/fehler), Konfidenzen 62–98%, ein paar Positionen je Rechnung, ein
  gefülltes Aktivitäts-Log mit verschiedenen Action-Typen.

  ## Liefer-Anforderung
  Ein lauffähiges React-Artifact, alle 6 Screens per Sidebar navigierbar, dark, mit den exakten Farben/Abständen oben,
  realistischen Mock-Daten und durchklickbaren Interaktionen (Zeile wählen → Detail-Panel, Inline-Edit, Regel
  auf-/zuklappen + Drag-Reorder, Tab-Wechsel, ConfirmDialog, Toasts, Empty-States umschaltbar). Sauber komponentisiert
  für die spätere Svelte-5-Portierung
</pasted_text>


<system-reminder>Auto-injected reminder (ignore if not relevant): do not recreate copyrighted or branded UI unless the user's email domain matches that company. Create original designs instead.</system-reminder>

## Assistant

_[tool: update_todos]_

This is a wonderfully detailed spec — exact colors, spacing, components, all 6 screens, and mock data. That's everything I need, so I'll build directly rather than asking questions. Let me lay out a plan and get started.

_[tool: write_file]_

Starting with the HTML shell. I'll use IBM Plex Sans + IBM Plex Mono — a precise, technical pairing that fits the "Utility & Precision" language better than a generic UI font.

_[tool: write_file]_

Now the mock data and shared design tokens.

_[tool: write_file]_

Now the reusable components and an icon helper.

_[tool: write_file]_

Now the Inbox screen — the densest and most important. It owns the table, sortable columns, the three review-panel variants, and the ignored-tab cards.

_[tool: str_replace_edit]_

Dashboard needs the `StatCard` component — let me add it to the shared components file first.

_[tool: str_replace_edit]_

_[tool: write_file]_

_[tool: write_file]_

Now Templates — editable/deletable table with empty state.

_[tool: write_file]_

Now the visual rule editor with real drag-and-drop reorder and the three collapsible sections per rule.

_[tool: write_file]_

Settings — folders, watchdog, auto-sort slider, the 3-state OCR card with live install log, Ollama, and the destructive reset confirm.

_[tool: str_replace_edit]_

I left a stray undefined `r` reference in the warning text. Let me fix it.

_[tool: write_file]_

Finally OCR-Debug — the diagnostic pipeline stepper with animated progress and result tabs. I'll cycle template→OCR→error across runs so all states are reachable from the one button.

_[tool: write_file]_

Now the app shell — header, collapsible sidebar, routing, and toast host — wiring it all together.Let me verify it loads cleanly.

_[tool: show_html]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: read_file]_

A German quote is breaking the JSX attribute parse. Let me look at the exact line.

_[tool: grep]_

Found it — the closing quote after "scannen" is a straight `"`, which terminates the JSX attribute early. Let me find all German-quote usages to fix any mismatches.

_[tool: str_replace_edit]_

Only `screen_inbox.jsx:133` is broken — it's inside a JSX double-quoted attribute. The data/template-literal cases are fine. Let me fix it with proper German curly quotes.

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: eval_js]_

Two real bugs: the lucide global name is wrong, and I called my 2-arg `rgba()` helper with CSS-style 4-arg `rgba(0,0,0,...)`. Let me check the lucide global name and find the bad rgba calls.

_[tool: eval_js]_

_[tool: str_replace_edit]_

`LucideReact` loaded but is empty — that UMD build doesn't expose icons usefully. Let me switch to the vanilla `lucide` package (icon node data) and render SVGs from it in React. First let me load it and inspect the structure.

_[tool: show_html]_

_[tool: eval_js]_

_[tool: str_replace_edit]_

The format is `["svg", attrs, children]`. Let me rewrite the `Icon` component to build the SVG in React, and fix the `rgba()` calls where I wrongly passed CSS 4-arg form.

_[tool: str_replace_edit]_

Now fix the bad `rgba(0,0,0,...)` / `rgba(255,255,255,...)` CSS-style calls that break my 2-arg helper.

_[tool: grep]_

_[tool: str_replace_edit]_

Most string-literal ones are fine. The broken function calls are the `rgba(0,0,0,0.x)` and `rgba(255,255,255,0.06)` ones. I'll make the helper defensive AND fix the explicit calls.

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: save_screenshot]_

Clean. Let me screenshot to check the visuals across screens.

_[tool: view_image]_

_[tool: eval_js]_

Shell looks great, but the main content is empty. Let me check what's actually in the DOM.

_[tool: save_screenshot]_

Content is all there (68KB DOM, tables, headings) — the first capture was just before mount finished. Let me re-screenshot.

_[tool: view_image]_

_[tool: eval_js]_

Still black despite content in DOM. Let me check the computed visibility/position of the content.

_[tool: str_replace_edit]_

The `.df-fade-in` wrapper is stuck at opacity 0 because CSS animations are frozen in my backgrounded iframe — it animates fine in the user's focused tab, but it's risky (blank content in print/PDF). Let me remove it from the persistent route wrapper so primary content never depends on the animation.

_[tool: grep]_

Let me check what else uses the fade so I can force it visible during verification screenshots.

_[tool: show_html]_

These are all click-triggered/transient and animate fine in a focused tab. For my verification I'll force them visible. Let me reload and capture all six screens.

_[tool: save_screenshot]_

_[tool: view_image]_

_[tool: eval_js]_

Inbox table looks excellent. The review panel for the selected row should be below it — let me verify it's rendering.

_[tool: save_screenshot]_

The CSS animation overrides inline opacity while frozen — I need to disable the animation itself for the capture. (In the user's live tab these animate fine.) Let me re-capture.

_[tool: view_image]_

_[tool: save_screenshot]_

The review panel is spot-on. Let me verify the other five screens. I'll navigate via the sidebar and capture each.

_[tool: view_image]_

_[tool: save_screenshot]_

Dashboard is excellent. Let me check rules and settings.

_[tool: view_image]_

_[tool: eval_js]_

Rules screen structure looks great. But the field/operator dropdowns may be showing wrong values (rule #2 should be Betrag/größer als). Let me verify the select values.

_[tool: save_screenshot]_

The select *values* are all correct (Dokumenttyp/ist, Betrag/größer als) — the screenshot tool just doesn't render native `<select>` text accurately. The app is correct. Let me check settings and OCR.

_[tool: view_image]_

_[tool: save_screenshot]_

Settings looks great. Two minor wrap issues: the watchdog status line and "Ordner hinzufügen" wrap awkwardly. Let me see the lower settings cards first.

_[tool: view_image]_

_[tool: eval_js]_

_[tool: save_screenshot]_

_[tool: view_image]_

_[tool: str_replace_edit]_

The save_screenshot captures from the top regardless of scroll, but eval confirms the OCR/Ollama/reset cards all exist. Let me fix the two text-wrap issues I spotted (watchdog status + "Ordner hinzufügen") and check the OCR screen.

_[tool: show_html]_

Now let me check the OCR-Debug screen by running its pipeline.

_[tool: save_screenshot]_

_[tool: view_image]_

_[tool: str_replace_edit]_

The stepper works. The section title "OCR-Debug" is wrapping ("OCR-"/"Debug") — let me fix `SectionHeader` to nowrap. Then I'll re-check the OCR result card after full completion.

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: view_image]_

_[tool: update_todos]_

All six screens render correctly. Let me mark the todos complete and do the final handoff.Let me clean up the screenshot files and hand off.

_[tool: delete_file]_

_[tool: done]_

_[tool: fork_verifier_agent]_

**DocuFlow** ist fertig — ein durchklickbares High-Fidelity-Mockup als React-Artifact, sauber in einzelne Dateien zerlegt (Daten · Komponenten · 6 Screens · App-Shell), bereit für die spätere Svelte-5-Portierung.

**Drin ist alles aus dem Brief:**
- **Echtes Routing** über die kollabierbare Sidebar (Verarbeitung / System), aktiver Zustand klar markiert
- **Eingang** — dichte, sortierbare Tabelle + Review-Panel in 3 Varianten (unverarbeitet / Extraktion mit Inline-Edit + Konfidenz-Badges + Positionen / Fehler), Ignoriert-Tab, „Scannen"/„Alle verarbeiten" mit Live-Status
- **Dashboard** — 4 StatCards (live aus dem geteilten State), sortierte Dokumente, Aktivitäts-Log mit Zeitfilter + Undo, bedingte Fehler-Log-Card
- **Templates** editier-/löschbar mit ConfirmDialog
- **Sortier-Regeln** — visueller Editor mit **echtem Drag-&-Drop-Reorder**, WANN/WOHIN/WIE-Sektionen, Live-Pfad-Vorschau
- **Einstellungen** — Watchdog, Auto-Sort-Slider, Ordnerlisten, 3-Status German-OCR mit Live-Install-Log, Ollama-Verbindungstest, destruktiver Reset
- **OCR-Debug** — animierter Pipeline-Stepper + Ergebnis-Tabs (zyklisch Template → OCR → Fehler durchklickbar)
- **Ein** einheitliches Konfidenz-Schema (≥90 grün / ≥70 amber / <70 rot), exakte Slate-Farben, Toasts, IBM Plex Sans/Mono für die Utility-Anmutung.

Ein paar Hinweise: Schriftarten/Tailwind/Icons laden per CDN (Internet nötig). Die Mock-Daten leben rein im React-State — ein Reset oder Reload setzt alles zurück. Sag Bescheid, wenn ich Farben, Dichte oder einzelne Flows anpassen soll.

