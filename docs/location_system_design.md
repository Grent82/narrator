# Location System Design

## Ziel
Ein einfaches, geographisches System für Story-Orte, das räumliche Kohärenz und Travel-Mechaniken ermöglicht.

## Datenmodell

### Neue Tabelle: `locations`

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    tag VARCHAR(100) NOT NULL DEFAULT 'Location',  -- Location, Settlement, Landmark, etc.
    metadata JSONB NOT NULL DEFAULT '{}',          -- Optional: terrain, climate, NPCs, etc.
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(story_id, name)
);

CREATE INDEX idx_locations_story_id ON locations(story_id);
```

### Erweiterung: `story_messages`

```sql
ALTER TABLE story_messages 
ADD COLUMN location_id UUID REFERENCES locations(id) ON DELETE SET NULL;

CREATE INDEX idx_story_messages_location_id ON story_messages(location_id);
```

### Travel-Mechanik (optional, Phase 2)

```sql
CREATE TABLE travel_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    character_name VARCHAR(255) NOT NULL,  -- Name des reisenden Charakters
    from_location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    to_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    distance INT NOT NULL DEFAULT 1,       -- Travel duration in turns
    remaining_turns INT NOT NULL DEFAULT 1,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',  -- in_progress, completed, cancelled
    
    INDEX idx_travel_tasks_story_id(story_id),
    INDEX idx_travel_tasks_status(status)
);
```

## API-Endpunkte

### Locations CRUD

```
GET    /stories/{story_id}/locations           # Alle Locations auflisten
POST   /stories/{story_id}/locations           # Neue Location erstellen
GET    /stories/{story_id}/locations/{id}      # Single Location Details
PUT    /stories/{story_id}/locations/{id}      # Location updaten
DELETE /stories/{story_id}/locations/{id}      # Location loeschen
```

### Travel (Phase 2)

```
POST   /stories/{story_id}/travel              # Reise starten
GET    /stories/{story_id}/travel/active       # Aktive Reisen auflisten
PUT    /stories/{story_id}/travel/{id}/cancel  # Reise abbrechen
```

## Prompt-Integration

### System Prompt Erweiterung

```
[LOCATIONS]
* {name} - {description}
* {name} - {description}

[CURRENT LOCATION]
Die aktuelle Szene findet statt in: {location_name}
{location_description}
```

### Travel State im Prompt

```
[TRAVEL STATUS]
* {character} ist unterwegs nach {destination} ({remaining} Turns verbleibend)
```

## Implementierungsphasen

### Phase 1: Basis-Location-System (P1)
- [ ] Datenbank-Migration fuer Locations
- [ ] SQLAlchemy Models
- [ ] CRUD Routes
- [ ] Location-Tracking in Messages

### Phase 2: Travel-Mechanik (P2)
- [ ] Travel-Tasks Tabelle
- [ ] Travel-Start API
- [ ] Turn-Service Integration (Turn-Abhaenge Travel)
- [ ] Travel-Status im Prompt

### Phase 3: Worldview Enhancement (P3)
- [ ] Location-Typen (Settlement, Wildernis, etc.)
- [ ] Location-spezifische Regeln
- [ ] Auto-Extraction aus Story-Text

## Abhaengigkeiten

- Keine neuen Abhaengigkeiten
- Nutzt bestehende SQLAlchemy/Pydantic-Infrastruktur
- Optional: Qdrant Integration fuer Location-Embeddings (Phase 3)

## Risiken

1. **Breaking Changes**: `story_messages.location_id` kann NULL sein (SET NULL)
2. **Migration Safety**: Existing Stories haben keine Locations (Backfill optional)
3. **Prompt Complexity**: Zu viele Locations koennen den Prompt ueberladen (Top-K Retrieval)
