# Narrator

Narrator ist ein lokales Storytelling-System fuer interaktive, KI-gestuetzte Text-Adventures. Der aktuelle Stand setzt auf FastAPI im Backend, ein separates Vite/React/TypeScript-Frontend, PostgreSQL fuer Persistenz, Qdrant fuer Lore-Retrieval und Ollama fuer lokale Modelle.

## Aktueller Techstack

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- Frontend: Vite, React, TypeScript
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
  shared/             Gemeinsame Utilities
frontend/             Vite App (React + TypeScript)
alembic/              Migrationen
tools/                Hilfsskripte
```

Hinweis: Aeltere Doku-Teile im Projekt beschrieben eine staerker ausdifferenzierte Clean-Architecture-Struktur mit `domain/`, CLI-Frontend, Redis-Event-Bus, FAISS und pgvector. Das entspricht nicht dem aktuellen Code-Stand. Das fruehere NiceGUI-Frontend liegt noch im Repository, ist aber nicht mehr der aktive Laufzeitpfad.

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

Lokaler Frontend-Start ohne Docker:

```bash
cd frontend
npm install
npm run dev
```

## Wichtige Umgebungsvariablen

### Backend / Frontend

- `BACKEND_HOST` / `BACKEND_PORT`
- `FRONTEND_ORIGINS`
- `VITE_API_BASE_URL` (optional for direct browser-to-backend access)
- `VITE_BACKEND_PROXY_TARGET` (for local/Compose dev via Vite proxy)

### Datenbank

- `DB_URL`

### Ollama / LLM

- `LLM_PROVIDER` (`ollama` or `openai_compatible`; defaults to `ollama`)
- `LLM_MODEL` (optional provider-neutral override for the main chat model)
- `LLM_BASE_URL` / `LLM_API_KEY` for OpenAI-compatible AI hubs
- `OLLAMA_URL`
- `OLLAMA_MODEL` (kept as the local Ollama default when `LLM_MODEL` is unset)
- `MODEL_PROFILE`
- `SUMMARY_MODEL`
- `SUMMARY_MODEL_PROFILE`
- `STORY_GEN_MODEL`
- `STORY_GEN_REPAIR_MODEL`
- Model profiles describe prompt behavior independently from provider/model IDs. Current profile classes include `local_small_instruct`, `balanced_reasoning`, and `reasoning_strong`.

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
- `LOG_LEVEL`
- `BACKEND_LOG_LEVEL`

## Aktueller funktionaler Umfang

- Story-Turns per Streaming ueber `/turn/stream`
- Story-Verwaltung mit gespeicherten Messages und Summary
- Lore-Verwaltung pro Story
- Lore-Retrieval ueber Qdrant
- Lore-Suggestions aus Story-Turns
- Story-Generierung fuer neue Geschichten
- Browser-Frontend als getrennte Vite-App mit eigenem Build- und Dev-Server
