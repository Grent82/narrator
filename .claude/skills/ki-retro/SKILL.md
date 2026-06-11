---
name: ki-retro
description: |
  Session-Retrospektive für Workflow, Zusammenarbeit und Fehler.
  Aktivieren am Ende einer Session oder wenn sich Muster wiederholt haben.
  Analysiert was gut/schlecht lief und bringt Erkenntnisse direkt in
  persistente Artefakte ein (Memory, Rules, AGENTS.md, Skills).
---

# KI-Retro

Führe eine strukturierte Retrospektive dieser Session durch.
**Ziel ist nicht ein Bericht — Ziel ist das sofortige Einschreiben von Erkenntnissen.**

---

## Schritt 1 — Session-Rückblick (kurz)

Nenne in maximal 5 Stichpunkten was in dieser Session gemacht wurde.

---

## Schritt 2 — Workflow & Zusammenarbeit

Beantworte ehrlich und konkret:

**Was hat gut funktioniert?**
- Welche Abläufe, Rollen oder Kommunikationsmuster haben Reibung reduziert?
- Was sollte explizit beibehalten und ggf. als Feedback-Memory gespeichert werden?

**Was hat Reibung erzeugt?**
- Wo gab es Missverständnisse, Korrekturrunden oder Hin-und-her?
- Welche Annahmen wurden getroffen statt nachgefragt?
- Welche Rolle fehlte oder wurde falsch gewählt?

---

## Schritt 3 — Fehler-Analyse

Liste jeden konkreten Fehler dieser Session:

| Fehler | Ursache | Wie oft korrigiert? |
|--------|---------|---------------------|
| ...    | Annahme statt Nachfragen / fehlende Regel / falsches Scope / ... | ... |

Sei ehrlich — auch kleinere Korrekturen zählen.

---

## Schritt 4 — Maßnahmen bestimmen und sofort ausführen

Ordne jede Erkenntnis einer konkreten Maßnahme zu:

| Erkenntnis | Maßnahme | Wo |
|------------|----------|----|
| Feedback das sich wiederholt hat | `feedback_*.md` schreiben/aktualisieren | `.claude/memory/` |
| Neue Projektinformation | `project_*.md` schreiben | `.claude/memory/` |
| Wiederkehrender Fehler ohne Regel | neue Rule anlegen | `.claude/rules/` |
| Rollenrouting war falsch | AGENTS.md-Abschnitt anpassen | `AGENTS.md` |
| Skill fehlt oder ist unvollständig | Skill anlegen/ergänzen | `.claude/skills/` |
| Offene technische Schuld | `bd create ...` | Beads |

**Führe jede Maßnahme direkt jetzt aus — nicht nur auflisten.**

Prüfe bei Memory-Einträgen:
- Gibt es einen bestehenden Eintrag der aktualisiert werden sollte?
- Füge neue Einträge in `MEMORY.md` ein.

---

## Schritt 5 — Abschluss

Bestätige konkret:
- Welche Dateien wurden erstellt oder geändert?
- Was gilt explizit für die nächste Session?
- Was bleibt als offenes Risiko?
