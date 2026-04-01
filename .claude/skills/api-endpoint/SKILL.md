---
name: api-endpoint
description: Implementiert oder erweitert FastAPI-Endpunkte, Pydantic-Schemas und zugehoerige Validierung in diesem Projekt.
---

# API Endpoint

Nutze diesen Skill fuer Aenderungen in `src/backend/api/` und angrenzenden Application-Layern.

## Fokus

- FastAPI-Routen und Dependencies
- Request-/Response-Modelle mit Pydantic
- Fehlerbehandlung und Statuscodes
- Streaming-Endpunkte
- saubere Anbindung an Use Cases und Repositories

## Lies zuerst

- `README.md`
- `guideline.md`
- `status.md`
- relevante Routen in `src/backend/api/`
- betroffene Use Cases in `src/backend/application/`

## Regeln

- Route bleibt duenn; Logik geht in Application- oder Service-Code.
- Request-/Response-Shapes explizit halten.
- Fehlerfaelle bewusst modellieren.
- API-Aenderungen nur mit Blick auf Frontend und Persistenz durchfuehren.

## Validierung

- `pytest`
- `ruff check .`
- gezielte API-Smoke-Tests, wenn noetig
