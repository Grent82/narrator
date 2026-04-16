================================================================
AKTUELLER UMFANG (IMPLEMENTIERT, IST-STAND)
================================================================

1) Kernfunktionalitaet
- Ein zentraler Storyteller-LLM generiert die Narration.
- Eingabemodi: Say / Do / Story / Continue.
- NiceGUI Frontend mit Chat-Log, Story-Steuerung und Side Panel.
- Lore-Verwaltung mit Karten und Review-Flow fuer Vorschlaege.
- Story-Generierung fuer neue Geschichten.

2) Architektur (heutiger Stand)
- FastAPI Backend mit Streaming-Endpunkt `/turn/stream`.
- Geschichtete Struktur mit `api`, `application`, `infrastructure`, `frontend`.
- Turn-Logik ueber `TurnUseCase` und `turn_service`.
- LLM-Anbindung via LangChain Community + Ollama.

3) Datenhaltung
- PostgreSQL als Primary DB.
- Tabellen: `stories`, `story_messages`, `story_summaries`, `lore_entries`, `lore_suggestions`.
- `story_messages` speichert Chat-Verlauf mit `position` fuer stabile Reihenfolge.
- `story_summaries` speichert Summary und `last_position` fuer inkrementelle Updates.

4) Lore + Vektor-Suche
- Qdrant als produktiver Vector Store fuer Lore Retrieval.
- Embeddings via `OllamaEmbeddings`.
- Lore-Embeddings liegen in Qdrant

1) Frontend/Backend-Kommunikation
- Klassische JSON-Requests fuer CRUD-Flows.
- Streaming fuer Story-Turns via HTTP-Stream.

================================================================
TECH STACK
================================================================

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- NiceGUI
- PostgreSQL
- Qdrant
- Ollama
- LangChain Community
- Docker Compose

================================================================
OFFENE TECHNISCHE LUECKEN
================================================================

P0
- Tooling-Konfiguration in `pyproject.toml` fehlte bisher.
- Doku und Abhaengigkeiten muessen auf den realen Code-Stand konsolidiert werden.

P1
- Message-Persistenz und Summary-Konsistenz fuer Edit-/Retry-/Erase-Flows absichern.
- Lore-/Qdrant-Synchronitaet haerter absichern.
- Typisierung im Frontend-State verbessern.

P2
- Characters / Places / Races als persistente Weltmodelle einfuehren.
- Quest-System als eigener Fachbereich.

P3
- Bewusste Entscheidung, ob Redis/Jobs/Eventing ueberhaupt gebraucht werden.
- Spaetere Bewertung, ob LangChain fuer den schmalen Einsatz noch gerechtfertigt ist.

================================================================
DEPENDENCIES
================================================================

- fastapi
- pydantic
- sqlalchemy
- alembic
- nicegui
- httpx
- ollama
- langchain-core
- langchain-community
- qdrant-client
- psycopg2-binary
- python-dotenv
- uvicorn

================================================================
ROADMAP (NAECHSTE SCHRITTE)
================================================================

1) Repo konsolidieren
- Doku korrigieren
- Tooling konfigurieren
- Abhaengigkeiten auditieren

1) Qualitaet absichern
- erste Tests fuer TurnUseCase, Prompt-Building und Summary-Flow
- Linting/Formatierung verbindlich machen

1) Funktionale Erweiterungen
- Chat-Historie dauerhaft und robust editierbar machen
- Weltmodelle fuer Characters, Places und Races aufbauen
- Quest-System schrittweise einfuehren

================================================================
BRAINSTORMING (IDEEN)
================================================================

- Chat-Historie immer sichtbar.
- Ubersicht fur Charaktere/Orte/Rassen inkl. LLM-relevanter Infos.

================================================================
TODO: QUEST-SYSTEM (DETAILLIERT)
================================================================

Ziel
- Aktive Quests / Missionen aus dem Story-Text extrahieren und dauerhaft pflegen.
- Open / Completed / Failed / Abandoned Status verfolgen.
- Quests in den Prompt einspeisen, damit Ziele nicht verloren gehen.

A) Datenmodell
1) Neue Tabelle: quest_items
- id (UUID, PK)
- story_id (FK -> stories, index)
- title (string)
- description (text)
- status (enum: open/completed/failed/abandoned)
- objectives (JSON list, optional)
- tags (JSON list, optional)
- embedding (Qdrant, optional)
- last_update_position (int)
- created_at / updated_at (timestamps)

2) Alembic Migration
- Tabelle anlegen + Indizes
- Optional: Qdrant embedding Store

B) API / Backend
1) Endpunkte
- GET /stories/{id}/quests
- POST /stories/{id}/quests (manuelles Hinzufugen)
- PUT /stories/{id}/quests/{quest_id} (Update)
- DELETE /stories/{id}/quests/{quest_id}

2) Service / Use-Case
- QuestExtractUseCase (arbeitet nach jedem Turn)
- QuestUpdateUseCase (DB-Updates + status change)

C) LLM-Extraktion (Quest-Analyzer)
1) Input
- Letzter User-Input + letzter Assistant-Output
- Optional: plot_summary (nur kurz, 1-2 Saetze)

2) Output (JSON)
- {
    "new": [ {"title":..., "description":..., "objectives":[...]} ],
    "update": [ {"id":..., "status":..., "objectives":...} ],
    "complete": [ {"id":...} ]
  }

3) Regeln
- Nur Quests erzeugen wenn konkrete Aufgabe/Goal vorliegt.
- Keine Plot-Atmosphare oder lose Hinweise als Quest.
- Quests kurz halten, neutral formulieren.

D) Prompt-Integration
- Neuer Abschnitt [QUESTS]
- Nur offene und relevante Quests laden (top-k nach embeddings)
- Beispiel:
  [QUESTS]
  - (open) Find the registry ledger in Valdor.
  - (open) Deliver the sealed letter to Borin.

E) Embeddings
- Optional: Quest embedding fur Retrieval
- Query = aktueller User-Input oder Summary

F) UI (optional, aber sinnvoll)
- Side Panel: Quest-Liste
- Filter nach Status
- Editierbar (manual override)

G) Tests
- Unit Tests fur JSON-Parser
- Integration Test fur Quest-Lifecycle (new -> open -> completed)
