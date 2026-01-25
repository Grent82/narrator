Dieses Projekt konzipiert ein immersives Dark-Fantasy Medieval Text-Adventure, inspiriert von AI Dungeon, bei dem eine zentrale KI als Storyteller fungiert. Der User treibt die Story voran durch freie Chat-Eingaben oder strukturierte Optionen wie "Say" (Dialog führen), "Story" (narrative Beschreibung hinzufügen), "Use" (Gegenstand verwenden), "Do" (Aktion ausführen) oder ähnliche Befehle. Die KI generiert dynamische Erzählungen, Konsequenzen und Weltentwicklungen basierend auf User-Inputs, mit Fokus auf langfristigen Auswirkungen in einer düsteren mittelalterlichen Welt. Im Gegensatz zu einem Prototypen ist dies ein vollwertiges System, das Clean Architecture und Clean Code-Prinzipien anwendet: Die Kernlogik (z. B. Narrative-Steuerung) ist von Anwendungslogik (z. B. Use Cases) und Infrastruktur (z. B. LLM-Aufrufe, DB) entkoppelt, um Testbarkeit, Skalierbarkeit und Wartbarkeit zu gewährleisten. Basierend auf Best Practices aus "Clean Architecture" von Robert C. Martin, angepasst für Python, und Clean Code-Regeln (z. B. kleine Funktionen, SOLID-Prinzipien), wird die Struktur in Entities, Use Cases, Repositories und Adapters unterteilt. Für den privaten Gebrauch ist es auf ein lokales Docker/Docker-Compose-Setup optimiert, das nahtlos auf Hostinger VPS deploybar ist, wo LLMs lokal laufen können (z. B. via Ollama oder llama.cpp für ressourcenschonende Modelle).
Die Motivation ist ein persönliches, erweiterbares Spiel für privaten Nutzen, das KI-Potenziale demonstriert, ohne Cloud-Abhängigkeiten zu maximieren. Halluzinationen werden durch strukturierte Prompts und Verifikationsschritte minimiert, State-Drift durch autoritative DB und Event-Validierung vermieden. Im Vergleich zu AI Dungeon integriert es Multi-LLM-Rollen für tiefere Welt-Simulation, aber mit Fokus auf User-gesteuerte Interaktionen.
Detaillierte Projektbeschreibung
Das Spiel simuliert eine kohärente Welt mit NPCs, Ereignissen und Konsequenzen. Die Storyteller-KI (Player-Facing LLM) interpretiert User-Inputs (freier Text oder Befehle wie "Say: Hallo zum Wirt", "Do: Den Drachen angreifen", "Use: Schwert", "Story: Die Sonne geht unter") und generiert narrative Responses. Background-LLMs treiben die Welt unabhängig voran, z. B. durch NPC-Reaktionen oder Umweltveränderungen. Die Architektur verwendet Event-Triggers als JSON-Objekte (z. B. {"type": "action", "command": "Do", "details": "Schloss betreten"}), die in einem Pub/Sub-Muster verarbeitet werden. Für die UI: Eine webbasierte GUI via NiceGUI mit Chat-Input-Feld, Auswahl-Buttons für Befehle und dynamischen Story-Displays, um die Interaktion intuitiv zu machen.
Die Projektstruktur folgt Clean Architecture: Ein Monorepo mit klarer Hierarchie (src/, tests/, infrastructure/, data/) für bessere Wartung. Entities repräsentieren Kernkonzepte (z. B. NPC mit Beliefs als immutable Dicts), Use Cases handhaben Logik (z. B. ProcessUserInputUseCase), Repositories abstrahieren Datenzugriff, und Adapters verbinden mit externen Systemen (z. B. LLM-Adapter). Logging, Validation und Error-Handling sind integriert, um Clean Code zu gewährleisten.
Features im Detail

Narrative-Design: Die Storyteller-KI erzeugt immersive Texte mit Verzögerungen für Realismus (z. B. Gerüchte-Systeme). Trigger-Ketten: User-Aktion → KI-Interpretation → Background-Simulation → Narrative-Update. User-Auswahlen beeinflussen Pfade, mit Optionen für freie Kreativität.
NPC-Modelle: Reaktive (JSON-States), Antagonisten (mit Zielen wie {"goal": "revenge"}) und vernetzte NPCs (Graph-basierte Beziehungen via NetworkX).
Memory und World Model: Zustände in JSON-Schemas (z. B. {"locations": [...], "npcs": [...]}) mit FAISS für Embeddings; Relevanz-Filterung für Langzeit- vs. Kurzzeit-Memory.
Prompting: Role-spezifische Patterns (narrativ für Storyteller, funktional für Background); Confidence-Thresholds für Validierung.
Technische Optimierungen: Hybrid Echtzeit/Batch via APScheduler; Lokale LLM-Ausführung für Privatnutzung.

Architektur & Rollen

Zentraler Orchestrator (Backend) als Game Engine: Handhabt Turn-Loop, State-Logik und API.
Logische Rollen (in Clean Architecture als Use Cases und Adapters implementiert):
Storyteller-LLM (ehemals PF-LLM): Zentrale KI für Narration, Intent-Interpretation und User-Interaktion (großes Modell wie Llama3 via Ollama lokal auf Hostinger).
World-Manager-LLM: Globale Logik und Meta-Plot.
NPC-Agent-LLMs: Für NPC-Gruppen/Fraktionen.
Event-Generator-LLM: Systemische Ereignisse (z. B. Kriege, Wetter).
Memory/State-Layer: Abstrakte Repository für DB + Embeddings.

Alle Rollen als modulare Komponenten im Backend, entkoppelt für Testbarkeit.

Kommunikation & Orchestrierung

Turn-basiertes Modell: Pro User-Input (Chat oder Befehl) ein Ablauf (Storyteller → Events → Background-LLMs → State-Update → Narration).
Direkte Funktionsaufrufe im Orchestrator; Redis als Event-Bus (Pub/Sub) für asynchrone Events und Background-Ticks.
Clean Code: Kleine Funktionen, die jeweils nur eine einzige Aufgabe erfüllen, für jeden einzelnen Schritt.

Synchronisation & Konsistenz

Autoritativer Zustand in zentraler DB (Single-Source-of-Truth).
Pro Turn: Transaktionale Isolation (Laden → Vorschläge → Validierung → Commit).
Konfliktregeln: User-Aktionen priorisieren, dann NPCs, dann Events; World-Manager erzwingt Konsistenz.
Keine CRDTs nötig für privaten Gebrauch.

Projektstruktur (High-Level)

Backend-Projekt:
API-Layer: FastAPI für Endpunkte wie /input.
Orchestrations-Layer: Use Cases für Turn-Loop, Events, Konflikte.
Agent-Layer: Adapters für LLMs.
State/Memory-Layer: Repositories für DB und Embeddings.

Separate Ordner: Infrastructure (Docker, Logs), Tests (Unit/Integration).
Frontend: NiceGUI-Integration für webbasierte UI.

Datenhaltung & Memory

PostgreSQL als DB mit JSONB-Feldern für Flexibilität und pgvector für Embeddings.
Tabellen: Entities, Relations, Events, Rumors, Quest-Status, NPC-State.
Embeddings: pgvector für Vektor-Suchen; FAISS als Fallback.

LLM-Strategie

Storyteller-LLM: Starkes lokales Modell (z. B. Llama3 via Ollama auf Hostinger) für Narration und Inputs.
Background-LLMs: Kleinere Modelle (z. B. Phi-3 lokal) für strukturierte Outputs.
Lokale Ausführung priorisiert für Privatnutzung; Optionale Cloud-Fallback.

Messaging & Background Processing

Redis als Cache und Event-Bus für Ticks und Jobs.
Periodische Scheduler (APScheduler) für Welt-Simulation.

Hosting & Deployment

Lokales Setup: Docker/Docker-Compose für Backend, Redis, PostgreSQL und Ollama (LLMs).
Docker-Compose.yml: Services für app (FastAPI), db (PostgreSQL), redis, ollama (lokale LLMs).
Hostinger VPS: Kompatibel mit Docker; 4 vCPU, 8 GB RAM empfohlen für parallele LLMs.
Deployment: docker-compose up; NiceGUI exponiert via Port für lokalen Zugriff.

Technologie-Stack (konkrete Entscheidungen)

Sprache/Framework: Python 3.10+ mit FastAPI; Clean Code durch Pydantic-Validation und MyPy-Typing.
DB: PostgreSQL mit pgvector.
Memory/Embeddings: pgvector; FAISS für lokale Tests.
Cache/Messaging: Redis.
LLM-Zugriff: Ollama für lokale Modelle; HTTP-Client für Optionale Cloud.
UI: NiceGUI für interaktive Web-Frontend.
Containerisierung: Docker/Docker-Compose für Setup und Deployment.






-------



Brain storming.
Now i have the story I like to see the last story history in the chat.
Also i like to have the possibilty to see all characters (with there story, items, ... for the llm), all places (with description for the llm), all races (description for llm), 