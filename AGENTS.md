# AGENTS.md

## Zweck

Dieses Repository nutzt Codex mit rollenbasierten Agents und Skills.
Diese Datei definiert die gemeinsamen, dauerhaften Projektregeln fuer alle Agents.

Arbeite praezise, minimal-invasiv und orientiere dich an der bestehenden Struktur, den vorhandenen Modulen und den tatsaechlichen Projektzielen.

---

## Projektkontext

Stack:
- Backend: Python, FastAPI, Pydantic
- Frontend: NiceGUI
- Persistenz: SQLAlchemy, Alembic, PostgreSQL
- KI-Integration: Ollama, LangChain
- Retrieval: Qdrant
- Infrastruktur: Docker Compose, Redis

Ziel:
- saubere, wartbare und testbare Software
- kleine, sichere und nachvollziehbare Aenderungen
- keine stillschweigenden Architekturbrueche
- konsistente Story-, Lore- und Zustandslogik fuer das Narrator-Projekt

---

## Lies zuerst

Bevor du Aenderungen vorschlaegst oder umsetzt, pruefe in dieser Reihenfolge, sofern vorhanden:

1. `README.md`
2. `guideline.md`
3. `status.md`
4. relevante Dateien in `src/backend/`, `src/frontend/` und `src/shared/`
5. relevante Datenbank- und Infrastrukturdateien (`alembic/`, `docker-compose.yml`, `tools/`)
6. relevante bestehende Tests in `tests/`

Wenn Anforderungen, Akzeptanzkriterien oder Architektur unklar oder widerspruechlich sind:
- keine Annahmen treffen
- nicht raten und nicht verdeckt weitermachen
- konkret benennen, was fehlt oder kollidiert
- gezielt nachfragen, welche Information gebraucht wird
- bei groesseren Konzeptfragen an `requirements-engineer` oder `architect` eskalieren

---

## Allgemeine Arbeitsregeln

- Kleine, gezielte Aenderungen vor grossem Refactoring bevorzugen.
- Bestehende Patterns, Modulgrenzen und Benennungen zuerst wiederverwenden.
- Keine Architekturgrundsaetze stillschweigend aendern.
- Keine Anforderungen erfinden.
- Root Cause analysieren, bevor Bugs gefixt werden.
- Wichtige technische Entscheidungen kurz und klar dokumentieren.
- Diffs klein, nachvollziehbar und rueckverfolgbar halten.
- Wenn Implementierung, Projektbeschreibung und Code voneinander abweichen, die Abweichung explizit benennen.

Methodische Leitplanken koennen zusaetzlich ueber `.claude/rules/` konkretisiert werden. Diese Rules ergaenzen die Rollenarbeit, ersetzen aber weder fachliches Urteil noch projektspezifische Analyse.

---

## Architekturregeln

### Backend

- FastAPI-Routen in `src/backend/api/` fuer HTTP- und Schema-Grenzen nutzen.
- Fach- und Orchestrierungslogik in `src/backend/application/` halten.
- Infrastrukturzugriffe in `src/backend/infrastructure/` kapseln.
- Pydantic-Modelle und Request-/Response-Shapes konsistent halten.
- Streaming-Endpunkte und LLM-Aufrufe nur so weit kapseln, dass Verantwortlichkeiten klar bleiben.

### Frontend

- NiceGUI-Seiten in `src/frontend/pages/` und wiederverwendbare UI-Bausteine in `src/frontend/components/` halten.
- Keine ad-hoc UI-Logik in Startdateien verstecken, wenn sie als Komponente oder Seite gehoert.
- Interaktive Elemente semantisch und zugaenglich umsetzen.
- Zustandslogik moeglichst klar zwischen UI-State, Frontend-State und Backend-Persistenz trennen.

### Persistenz und Integrationen

- SQLAlchemy-Modelle, Queries und Alembic-Migrationen konsistent halten.
- Datenmodell- oder API-Aenderungen nur mit Blick auf Frontend, Persistenz und bestehende Stories durchfuehren.
- Ollama-, Qdrant- und Redis-Anbindungen nicht unkontrolliert ueber neue Einstiegspunkte verstreuen.
- Externe Abhaengigkeiten ueber bestehende Adapter, Config-Module und Factory-Funktionen anbinden.

---

## UI- und UX-Grundsaetze

- Accessibility ist Pflicht, mindestens WCAG-AA-orientiert.
- Semantisches HTML bzw. semantisch sinnvolle NiceGUI-Komponenten verwenden.
- Keine klickbaren Container statt echter Controls.
- Keine Inputs ohne zugaenglichen Namen.
- Focus-Indikatoren nicht ohne gleichwertige Alternative entfernen.
- Mobile und kleinere Viewports mitdenken, auch wenn die UI serverseitig gebaut wird.

---

## Python- und Code-Qualitaet

- Typisierung ernst nehmen; keine vermeidbaren ungetypten Schnittstellen.
- Kleine, lesbare Funktionen mit klarer Verantwortung bevorzugen.
- Keine tote Konfiguration, keine verdeckten Side Effects.
- Kommentare nur dort, wo der Code sonst unnoetig schwer zu verstehen waere.
- Logging gezielt einsetzen, ohne Rauschen oder sensible Daten zu erzeugen.

---

## Testing und Validierung

Jede nicht triviale Aenderung soll validiert werden.

Bevorzuge:
- bestehende Tests erweitern
- neue Tests nah an der geaenderten Funktionalitaet ergaenzen
- Happy Path, Edge Cases und Fehlerfaelle beruecksichtigen

Fuehre, sofern sinnvoll und im Projekt vorhanden, passende Checks aus, z. B.:
- `pytest`
- `ruff check .`
- `python -m compileall src`
- relevante lokale Smoke-Tests fuer Backend oder Frontend

Wenn etwas nicht ausgefuehrt wurde:
- klar benennen
- kurz begruenden
- Restrisiko nennen

Keine Abschlussaussage ohne zur Behauptung passende frische Verifikation.

---

## Dokumentation aktualisieren

Aktualisiere bei Bedarf mit der Implementierung auch:
- `README.md`
- `guideline.md`
- `status.md`
- relevante Architektur- oder Betriebsnotizen im Repository

Dokumentation und Code sollen konsistent bleiben.

---

## Zusammenarbeit mit Rollen

Nutze die spezialisierten Agents passend:

- `requirements-engineer`
  - fuer unklare, fehlende oder widerspruechliche Anforderungen
- `architect`
  - fuer Architektur, API-Design, Datenmodell, Integrationsgrenzen und technische Entscheidungen
- `investigator`
  - fuer Root-Cause-Analyse, Befundsammlung und Trennung zwischen Symptom und Ursache
- `developer`
  - fuer Implementierung und Refactoring
- `fixer`
  - fuer gezielte, minimal-invasive Bugfixes bei verstandener Ursache
- `test-writer`
  - fuer neue oder angepasste automatisierte Tests
- `tester`
  - fuer Teststrategie, Testfaelle, QA und Verifikation
- `code-reviewer`
  - fuer Risiko- und Qualitaetsreviews mit Fokus auf Regressionen, Architektur und A11y
- `technical-writer`
  - fuer technische Dokumentation, Runbooks und Handovers
- `devops`
  - fuer lokale Umgebung, Docker Compose, Konfiguration, Migrationen und Betriebsfragen

Rollen sollen ihre Verantwortung nicht stillschweigend ueberschreiten.

---

## Skills

Wenn passende Skills vorhanden sind, nutze sie bevorzugt, insbesondere:
- `accessibility`
- `api-endpoint`
- `frontend-components`

Wenn ein Skill besser geeignet ist als freie Ausfuehrung, nutze den Skill.

---

## Code Review

Wenn ein Review angefragt ist:
- primaer Bugs, Risiken, Regressionen, Integrations- und A11y-Probleme finden
- Implementierung gegen reale Projektziele und bestehende Architektur pruefen
- Abweichungen von Architektur oder Datenfluss explizit benennen und einordnen
- Findings nach Schwere sortieren
- Datei- und moeglichst Zeilenbezug nennen
- nicht zuerst zusammenfassen, sondern zuerst die relevanten Befunde liefern

Wenn keine Findings vorliegen:
- explizit sagen
- verbleibende Risiken oder Testluecken trotzdem nennen

---

## Deployment und Betrieb

- Lokale Entwicklung laeuft ueber Python-Starts oder Docker Compose.
- Shared oder produktionsnahe Umgebungen duerfen nicht stillschweigend durch Migrationen oder Datenbankeingriffe veraendert werden.
- `alembic upgrade head` nur dort ausfuehren, wo das fuer die Aufgabe wirklich vorgesehen und abgestimmt ist.
- Deployment- oder Betriebsanpassungen minimal-invasiv und mit Blick auf vorhandene `docker-compose.yml`-, `.env`- und Service-Konfigurationen vornehmen.

---

## Git und Delivery

- Nicht direkt auf geschuetzten Standard-Branches arbeiten.
- Kleine, pruefbare Aenderungen bevorzugen.
- Kurz beschreiben:
  - was geaendert wurde
  - warum es geaendert wurde
  - wie es validiert wurde
  - welche Risiken offen bleiben

---

## Erwartetes Antwortformat bei Aenderungen

Wenn du Aenderungen gemacht oder vorgeschlagen hast, fasse am Ende knapp zusammen:
- betroffene Dateien
- wichtigste Aenderungen
- Test-/Validierungsstatus
- offene Risiken oder offene Fragen
