


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