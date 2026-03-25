# Claude Skills – DocuFlow

Verfügbare Skills für dieses Projekt. Claude ruft sie **automatisch** auf wenn das Thema passt.
Manueller Aufruf: `/skill-name` in Claude Code.

---

## Verfügbare Skills

| Command | Trigger-Muster | Beschreibung |
|---------|---------------|-------------|
| `/nicegui-design` | UI bauen, Seite erstellen, Komponente, Design, Layout, Farben | Design-Tokens, Komponenten-Patterns, Layout-Struktur für DocuFlow |

---

## Schnellreferenz

### UI & Design
```
/nicegui-design    → Design-System, Farb-Konstanten, Komponenten-Patterns
```

---

## Neue Skills anlegen

Wenn Claude eine wiederholbare Aufgabe ohne passendes Skill ausführt:
1. Neue Datei `.claude/commands/[name].md` anlegen
2. Eintrag in dieser Tabelle ergänzen
3. Trigger-Muster in `CLAUDE.md` (Skills-Tabelle) hinzufügen

---

## Skill-Dateien

```
.claude/
├── commands/
│   └── nicegui-design.md
├── CLAUDE.md
├── AGENT_WORKFLOW.md
└── SKILLS.md
```

---

*Letzte Aktualisierung: 2026-03-25*
