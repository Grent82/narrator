================================================================
AKTUELLER UMFANG (IMPLEMENTIERT, IST-STAND)
================================================================

1) Kernfunktionalitat
- Ein zentraler Storyteller-LLM generiert die Narration.
- Eingabemodi: Say / Do / Story / Continue (MODE-Block im Prompt).
- NiceGUI Frontend mit Chat-Log, Story-Steuerung und Side Panel.
- Lore-Verwaltung mit Karten (Create/Edit/Duplicate/Delete).
- Lore Review (Vorschlage) im Story-Header (Accept/Reject).

2) Architektur (heutiger Stand)
- FastAPI Backend mit /turn/stream.
- Use-Case Layer (TurnUseCase) fur Turn-Logik (stream).
- Repositories fur Story-, Lore- und Message-Zugriff.
- LLM Anbindung via LangChain (ChatModel) + Ollama.

3) Datenhaltung
- PostgreSQL als Primary DB.
- Tabellen: stories, story_messages, story_summaries, lore_entries, lore_suggestions.
- story_messages speichert Chat-Verlauf mit position fur stabile Reihenfolge.
- story_summaries speichert Summary + last_position.

4) Lore + Vektor-Suche
- Qdrant als Vector Store fur Lore Retrieval.
- Embeddings via LangChain OllamaEmbeddings.
- Lore Embeddings werden in Qdrant gespeichert (nicht in lore_entries).
- Lore Retrieval nutzt Top-K aus Qdrant.

5) Summary
- Inkrementelle Summary pro Turn (update_story_summary).
- Summary wird in story_summaries gespeichert.
- last_position wird fur inkrementelles Fortschreiben genutzt.

================================================================
PLANNED / OFFEN (ROADMAP)
================================================================

1) Persistenz der Messages im Frontend
- Sicherstellen, dass alle Chat-Nachrichten nach jedem Turn in story_messages persistiert werden.
- Recompute Summary, wenn Messages geloescht/retired werden (Erase/Retry).

2) Welt- und NPC-Modelle
- UI/Struktur fur Characters, Places, Races (LLM-Descriptions).
- Persistente Datenmodelle fur diese Entitaten.

3) Summary-Gating
- Optionaler LLM-Check, ob Summary-Update notwendig ist.
- Heuristiken (z.B. minimale Textlaenge).

4) Erweiterte Simulation (optional)
- Multi-LLM Rollen.
- Event-Bus / Background-Simulation.
- Scheduler und Welt-Ticks.

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

================================================================
TECH STACK (AKTUELL)
================================================================

- Backend: FastAPI (Python)
- LLM: Ollama (lokal) + LangChain Wrapper
- DB: PostgreSQL
- Vector Store: Qdrant
- Frontend: NiceGUI
- Docker/Docker-Compose fur lokales Setup

================================================================
BRAINSTORMING (IDEEN)
================================================================

- Chat-Historie immer sichtbar.
- Ubersicht fur Charaktere/Orte/Rassen inkl. LLM-relevanter Infos.

================================================================
PRIORISIERUNG (NAECHSTE SCHRITTE)
================================================================

P0 (MUSS, stabile Sessions)
- Chat-Messages zuverlaessig persistieren (kein Kontextverlust).
- Summary-Recompute konsistent bei Erase/Retry.
- Embedding/Lore-Flow stabilisieren (Qdrant sync + fehlende Embeddings).

P1 (HOCH, aber nicht blockierend)
- Lore Review Edit-Flow verdrahten.
- UI-Consistency/UX Fixes (Dialoge, Mode-Input, Buttons).

P2 (MITTEL)
- Quest-System (minimaler Start).
- Summary-Gating (Heuristiken oder LLM-Check).

P3 (SPAETER / OPTIONAL)
- NPC/World-Modelle.
- Multi-LLM Rollen, Scheduler, Event-Bus.
