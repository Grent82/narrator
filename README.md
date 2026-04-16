# Narrator

Narrator ist ein lokales Storytelling-System fuer interaktive, KI-gestuetzte Text-Adventures. Der aktuelle Stand setzt auf ein Python-only Setup mit FastAPI im Backend, NiceGUI im Frontend, PostgreSQL fuer Persistenz, Qdrant fuer Lore-Retrieval und Ollama fuer lokale Modelle.

## Aktueller Techstack

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- Frontend: NiceGUI
- LLM: Ollama, angebunden ueber LangChain Community
- Persistenz: PostgreSQL
- Vektor-Suche: Qdrant
- Infrastruktur: Docker Compose

## Projektstruktur

```text
src/
  backend/
    api/              HTTP-Endpunkte und API-Schemas
    application/      Use Cases, Prompting, Summary, Retrieval
    infrastructure/   DB, ORM-Modelle, Ollama/LangChain-Clients
  frontend/
    components/       Wiederverwendbare NiceGUI-Bausteine
    pages/            Seiten
    services/         Backend-Zugriffe und Streaming
  shared/             Gemeinsame Utilities
alembic/              Migrationen
tools/                Hilfsskripte
```

Hinweis: Aeltere Doku-Teile im Projekt beschrieben eine staerker ausdifferenzierte Clean-Architecture-Struktur mit `domain/`, CLI-Frontend, Redis-Event-Bus, FAISS und pgvector. Das entspricht nicht dem aktuellen Code-Stand.

## Lokaler Start

```bash
docker-compose up --build
```

Danach sind typischerweise erreichbar:

- Frontend: `http://localhost:17080`
- Backend: `http://localhost:17000`
- Adminer: `http://localhost:18080`
- Ollama: `http://localhost:11435`
- Qdrant: `http://localhost:16333`

## Wichtige Umgebungsvariablen

### Backend / Frontend

- `BACKEND_HOST` / `BACKEND_PORT`
- `FRONTEND_HOST` / `FRONTEND_PORT`
- `BACKEND_URL`

### Datenbank

- `DB_URL`

### Ollama / LLM

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `SUMMARY_MODEL`
- `STORY_GEN_MODEL`
- `STORY_GEN_REPAIR_MODEL`

### Retrieval / Embeddings

- `EMBED_MODEL`
- `EMBED_DIM`
- `LORE_TOP_K`
- `QDRANT_URL`
- `QDRANT_COLLECTION`

### Turn-Kontext / Summary

- `RECENT_TURN_PAIRS`
- `RECENT_TURN_OVERLAP`
- `SUMMARY_MAX_CHARS`

### Logging

- `BACKEND_LOG_FILE`
- `FRONTEND_LOG_FILE`
- `LOG_LEVEL`
- `BACKEND_LOG_LEVEL`
- `FRONTEND_LOG_LEVEL`

## Aktueller funktionaler Umfang

- Story-Turns per Streaming ueber `/turn/stream`
- Story-Verwaltung mit gespeicherten Messages und Summary
- Lore-Verwaltung pro Story
- Lore-Retrieval ueber Qdrant
- Lore-Suggestions aus Story-Turns
- Story-Generierung fuer neue Geschichten

