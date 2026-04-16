# Clean Architecture Rules

Diese Regeln konkretisieren Schichtentrennung und Verantwortlichkeiten in diesem Repository.

## Grundprinzipien

- Fachliche Regeln gehoeren in fachlich passende Schichten, nicht in technische Randbereiche.
- FastAPI-Routen behandeln HTTP und Orchestrierungsgrenzen, nicht Kernlogik.
- Application-Code steuert Story-, Lore-, Summary- und Turn-Ablaufe.
- Infrastrukturdetails duerfen Fachlogik nicht dominieren.

## Projektkontext

- `src/backend/api/` fuer Routen und Schemagrenzen
- `src/backend/application/` fuer Orchestrierung und Kernablaeufe
- `src/backend/infrastructure/` fuer Datenbank- und Integrationsdetails
- `src/frontend/pages/` fuer Seiten
- `src/frontend/components/` fuer wiederverwendbare UI-Bausteine

## Warnsignale

- gleiche Logik taucht in mehreren Schichten auf
- UI oder Route entscheidet ueber Kernregeln der Story- oder Persistenzlogik
- Integrationsdetails zwingen Application-Code in instabile technische Formen
- neue Loesung ignoriert vorhandene Modulgrenzen ohne bewusste Entscheidung
