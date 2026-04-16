# Projekt-Instruktionen

**Version:** 1.0 | **Stack:** Python · FastAPI · NiceGUI · SQLAlchemy · Alembic · PostgreSQL · Ollama · Qdrant · Redis

---

## Projektstruktur

| Verzeichnis | Zweck |
|---|---|
| `src/backend/` | FastAPI, Anwendungslogik, Persistenz und Integrationen |
| `src/frontend/` | NiceGUI-Frontend fuer Story-Interaktion und Verwaltung |
| `src/shared/` | Gemeinsame Utilities wie Logging |
| `alembic/` | Datenbankmigrationen |
| `tests/` | Projektweite Tests |
| `tools/` | Hilfsskripte fuer lokale Entwicklung und Betrieb |
| `data/` | Lokale Daten und Volumes |

---

## Kernkontext

Dieses Repository ist kein React/Django-Monorepo. Es ist ein Python-Projekt fuer ein narratives, LLM-getriebenes Story-System.

Wichtige Bausteine:
- **Backend:** FastAPI-Endpunkte, Story-Turn-Orchestrierung, Lore- und Summary-Logik
- **Frontend:** NiceGUI-Seiten und Komponenten fuer Chat, Story-Header, Side Panels und Lore-Ansichten
- **Persistenz:** PostgreSQL ueber SQLAlchemy, Migrationen ueber Alembic
- **LLM- und Retrieval-Schicht:** Ollama, LangChain, Qdrant
- **Infrastruktur:** Docker Compose, Redis, lokale `.env`-Konfiguration

Ziel:
- konsistente Story-Sessions ohne Kontextverlust
- wartbare Trennung zwischen API, Use Cases, Infrastruktur und UI
- kleine, sichere und gut validierte Aenderungen

---

## Lies zuerst

Bevor du Aenderungen vorschlaegst oder umsetzt, pruefe – sofern vorhanden:
1. `README.md`
2. `guideline.md`
3. `status.md`
4. relevante Implementierungen in `src/backend/`, `src/frontend/` und `src/shared/`
5. relevante Datenbank- oder Infrastrukturdateien (`alembic/`, `docker-compose.yml`, `tools/`)
6. vorhandene Tests in `tests/`

Wenn Anforderungen oder Architektur unklar sind: keine Annahmen treffen, den Widerspruch oder die Luecke konkret benennen und gezielt nachfragen.

---

## Backend-Regeln

**Stack:** FastAPI · Pydantic · SQLAlchemy · Alembic · PostgreSQL · LangChain · Ollama · Qdrant

### Architektur

- API-Grenzen in `src/backend/api/` halten.
- Orchestrierung und Use Cases in `src/backend/application/` halten.
- Infrastruktur und externe Clients in `src/backend/infrastructure/` kapseln.
- Datenbankzugriff und Migrationslogik konsistent halten.
- Keine fachliche Kernlogik direkt in FastAPI-Routen verstecken.

### Konventionen

- Request-/Response-Modelle klar und stabil halten.
- Fehlerfaelle explizit behandeln.
- Externe Integrationen ueber bestehende Adapter oder Factory-Funktionen anbinden.
- Streaming-Verhalten und Langlaufoperationen nur aendern, wenn die Auswirkungen auf UI und Persistenz mitgedacht werden.

---

## Frontend-Regeln

**Stack:** NiceGUI · Python

### Struktur

- Seiten in `src/frontend/pages/`
- Wiederverwendbare UI-Bausteine in `src/frontend/components/`
- Konfiguration in `src/frontend/config.py` und angrenzenden Modulen

### Grundprinzipien

- Accessibility ist Pflicht.
- Semantische Controls und zugaengliche Beschriftungen verwenden.
- Keine ueberladene UI-Logik in einzelnen Page-Funktionen.
- Bestehende Komponenten erweitern, bevor neue, parallele Muster entstehen.
- Story-, Lore- und Seitenzustand konsistent zur Backend-Persistenz halten.

---

## Datenmodell und Integrationen

- Alembic-Migrationen nicht manuell "quick-fixen", wenn das Modell oder die Query-Logik unklar ist.
- Datenmodell- und API-Aenderungen nur mit Blick auf bestehende Story-, Message-, Summary- und Lore-Flows vornehmen.
- Qdrant und Embeddings nicht als stillschweigende Nebenwirkung divergieren lassen.
- Ollama- und LangChain-Konfiguration ueber bestehende Settings und Infrastrukturdateien respektieren.

---

## Agents

Spezialisierte Sub-Agenten in `.claude/agents/`:

| Agent | Wann aktiviert |
|---|---|
| `requirements-engineer` | Anforderungen fehlen, sind unklar oder widerspruechlich |
| `architect` | Architektur, API-Design, Datenmodell, Integrationsgrenzen |
| `investigator` | Root-Cause-Analyse, Befundsammlung, Analyse unklarer Fehlerbilder |
| `developer` | Features implementieren, Bugs fixen, Refactorings |
| `fixer` | Minimal-invasive Bugfixes bei bereits verstandener Ursache |
| `test-writer` | Automatisierte Tests schreiben oder anpassen |
| `tester` | Tests, QA, Reproduktion und Verifikation |
| `code-reviewer` | Review von Risiken, Regressionen, Wartbarkeit und A11y |
| `technical-writer` | Technische Doku, Runbooks und Handovers pflegen |
| `devops` | Docker Compose, lokale Services, `.env`, Ports, Migrationen, Betriebsfragen |

Typischer Workflow:
`requirements-engineer` -> `architect` -> `developer` -> `test-writer` -> `tester` -> `code-reviewer`

Fuer Bugs:
`investigator` -> `fixer` -> `test-writer` -> `tester`

---

## Skills

Spezialisierte Skill-Anweisungen in `.claude/skills/`:

| Skill | Zweck |
|---|---|
| `accessibility` | A11y fuer NiceGUI-Seiten und Web-Interaktionen |
| `api-endpoint` | FastAPI-Endpunkte, Pydantic-Schemas, Streaming, Validierung |
| `frontend-components` | Wiederverwendbare NiceGUI-Komponenten und Seitenstruktur |

Ergaenzende methodische Leitplanken liegen unter `.claude/rules/`, z. B. fuer Clean Code, Architektur, Git-Sicherheit, Security und risikobasiertes Testing.

---

## Validierung

Bevorzuge passende, projektbezogene Checks:
- `pytest`
- `ruff check .`
- `python -m compileall src`
- gezielte lokale Smoke-Tests fuer Backend oder Frontend

Wenn Checks nicht gelaufen sind, benenne das klar und nenne das Restrisiko.

---

## Betrieb und Delivery

- Lokale Entwicklung kann direkt ueber Python-Module oder Docker Compose erfolgen.
- `docker-compose.yml` ist der zentrale Einstiegspunkt fuer lokale Mehr-Service-Setups.
- Datenbankmigrationen und produktionsnahe Eingriffe nicht stillschweigend ausfuehren.
- Branching und Delivery klein und pruefbar halten.

---

## Erwartetes Antwortformat bei Aenderungen

Kurze Zusammenfassung am Ende:
- betroffene Dateien
- wichtigste Aenderungen
- Test-/Validierungsstatus
- offene Risiken oder Fragen

**Ende CLAUDE.md**
