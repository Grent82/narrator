


├── .venv/                  # Virtuelle Umgebung
├── src/                    # Quellcode
│   ├── backend/            # Backend: LLM-Logik, Welt-Simulation
│   │   ├── domain/         # Kern-Entities (z.B. NPCs, Events, Triggers)
│   │   │   ├── entities/   # z.B. npc.py, event.py
│   │   │   └── value_objects/ # z.B. relation.py (für soziale Bindungen)
│   │   ├── application/    # Use Cases (z.B. Trigger-Verarbeitung)
│   │   │   └── use_cases/  # z.B. submit_action_use_case.py
│   │   ├── ports/          # Interfaces (z.B. llm_repository.py)
│   │   └── adapters/       # Implementierungen (z.B. ollama_adapter.py, in_memory_state.py)
│   ├── frontend/           # Frontend: Spieler-Interaktion (CLI)
│   │   └── cli/            # z.B. main_cli.py (ruft Backend-Use Cases auf)
├── tests/                  # Tests: Unit für Domain, Integration für Adapters
│   ├── unit/
│   └── integration/
├── data/                   # Speicher für States (z.B. JSON für Memory)
├── tools/                  # Skripte für Setup (z.B. init_db.py)
├── Dockerfile              # Für Containerisierung (optional für Hostinger)
├── docker-compose.yml      # Orchestriert Services (z.B. Ollama-Container)
├── Makefile                # Automatisierung (z.B. make test)
├── requirements.txt        # Abhängigkeiten
├── pyproject.toml          # Konfig für Tools wie uv und Ruff
├── .env                    # Umgebungsvariablen (z.B. LLM-Keys)
└── README.md               # Dokumentation

## Configuration (Environment Variables)

All configuration is read from environment variables (usually via `.env`). Below is a complete list based on `os.getenv(...)` usage in the codebase.

### LLM / Ollama
- `OLLAMA_URL` (default: `http://localhost:11434`)  
  Base URL for Ollama (chat + embeddings).
- `OLLAMA_MODEL` (default: `dolphin-llama3:8b`)  
  Main chat model for story turns.
- `SUMMARY_MODEL` (default: value of `OLLAMA_MODEL`)  
  Model used for story summaries.
- `OLLAMA_NUM_CTX` (default: `16384`)  
  Context length for Ollama requests.
- `OLLAMA_NUM_PREDICT` (default: `1024`)  
  Max tokens to predict per response.
- `OLLAMA_KEEP_ALIVE` (default: `20m`)  
  Keep-alive duration for model loading.
- `OLLAMA_MIN_P` (default: `0.08`)  
  Minimum probability sampling threshold.

### Embeddings / Lore
- `EMBED_MODEL` (default: `nomic-embed-text`)  
  Embedding model for lore retrieval.
- `EMBED_DIM` (default: `768`)  
  Expected embedding vector dimension.
- `LORE_TOP_K` (default: `8`)  
  Number of lore entries retrieved per turn.

### Qdrant (Vector Store)
- `QDRANT_URL` (default: `http://qdrant:6333`)  
  Qdrant service URL.
- `QDRANT_COLLECTION` (default: `lore_vectors`)  
  Collection name for lore vectors.

### Turn History / Summary
- `RECENT_TURN_PAIRS` (default: `3`)  
  Number of recent user+assistant pairs added to the prompt.
- `RECENT_TURN_OVERLAP` (default: `2`)  
  Overlap pairs for sliding window history.
- `SUMMARY_MAX_CHARS` (default: `2400`)  
  Max summary length in characters.

### Backend
- `BACKEND_HOST` (default: `0.0.0.0`)  
  Backend bind host.
- `BACKEND_PORT` (default: `17000`)  
  Backend port.
- `BACKEND_URL` (default: `http://backend:17000`)  
  Backend URL used by the frontend client.

### Frontend
- `FRONTEND_HOST` (default: `0.0.0.0`)  
  Frontend bind host.
- `FRONTEND_PORT` (default: `17080`)  
  Frontend port.
- `FRONTEND_THEME` (default: `default`)  
  Theme name for the UI.

### Database / Redis
- `DB_URL` (default: `sqlite:///./data.db`)  
  SQLAlchemy database URL (Postgres in Docker).
- `REDIS_URL` (default: `redis://localhost:6379`)  
  Redis URL for background tasks or caching.

### Logging
- `LOG_LEVEL` (default: none, falls back to framework defaults)  
  Global log level used when specific logger levels are not set.
- `BACKEND_LOG_LEVEL` (default: none)  
  Log level for the `backend` logger.
- `FRONTEND_LOG_LEVEL` (default: none)  
  Log level for the `frontend` logger.
- `BACKEND_LOG_FILE` (default: `logs/backend.log`)  
  Log file path for backend logs.
- `FRONTEND_LOG_FILE` (default: `logs/frontend.log`)  
  Log file path for frontend logs.
