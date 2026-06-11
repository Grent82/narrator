# Worldview Data Extraction Design

## Ziel
Term-basierte Wissensextraktion aus Story-Texten, um ein konsistentes Weltwissen fuer die Agenten zu schaffen.

## Konzept

### Was ist Worldview Data?
Weltwissen umfasst implizite Regeln, Normen und Fakten einer Story-Welt:
- **Magische Regeln**: "Zauberer duerfen sich vor Muggeln nicht zeigen"
- **Soziale Normen**: "Adelige gruessen sich mit Verbeugung"
- **Terminologie**: "Ein 'Phial of Light' enthält gefangenes Sternenlicht"
- **Weltfacts**: "Die Nordmauer ist 700 Fuss hoch"

### Unterschied zu Lore Entries
| Lore Entry | Worldview Setting |
|------------|-------------------|
| Charakter, Ort, Item | Regel, Norm, Tatsache |
| Explizit im Text | Oft implizit, muss extrahiert werden |
| Trigger-basiert | Term-basiert |

## Datenmodell

### Neue Tabelle: `worldview_settings`

```sql
CREATE TABLE worldview_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    term VARCHAR(255) NOT NULL,              -- Der Begriff (kann leer sein)
    nature VARCHAR(100) NOT NULL,            -- Kategorie: artifact, norm, fact, rule, etc.
    description TEXT NOT NULL,               -- Ausfuehrliche Beschreibung
    source TEXT NOT NULL,                    -- Woher stammt dies? (Kapitel, Seite)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(story_id, term, nature)
);

CREATE INDEX idx_worldview_settings_story_id ON worldview_settings(story_id);
CREATE INDEX idx_worldview_settings_term ON worldview_settings(term);
CREATE INDEX idx_worldview_settings_nature ON worldview_settings(nature);
```

## Extraktionsprozess (BookWorld-inspiriert)

### Schritt 1: Text-Chunking
- Input: Story-Text oder neue Messages
- Segmentierung in behandelbare Chunks (z.B. 500 Tokens)

### Schritt 2: Atomic Fact Extraction
Pro Chunk wird ein LLM gefragt:
```
Extrahiere atomare Fakten aus diesem Textabschnitt.
Jeder Fakt soll:
- Einen Term haben (wenn anwendbar)
- Eine Kategorie haben (artifact, norm, rule, fact, custom, etc.)
- Eine klare Beschreibung haben
- Den Source-Verweis enthalten

Format: JSON Array
```

### Schritt 3: Filterung
- Entferne Charakter-Actions (sind keine Weltregeln)
- Entferne Common Sense (ist kein spezifisches Weltwissen)
- Behalte nur settings, die die Welt definieren

### Schritt 4: Clustering & Consolidation
- Gleiche/similare Settings zusammenfassen
- Redundanz entfernen
- Beschreibung verfeinern

### Schritt 5: Vektor-Speicherung
- Embeddings fuer semantische Suche
- Retrieval bei relevanten Terms im Prompt

## API-Design

### Endpunkte

```
POST   /stories/{id}/worldview/extract     -- Extrahiere aus Text
GET    /stories/{id}/worldview/settings    -- Alle Settings auflisten
POST   /stories/{id}/worldview/settings    -- Manuelles Setting erstellen
PUT    /stories/{id}/worldview/settings/{id}  -- Update
DELETE /stories/{id}/worldview/settings/{id}  -- Loeschen
GET    /stories/{id}/worldview/retrieve    -- Relevante Settings fuer Query
```

### Request/Response Schemas

```python
class WorldviewSettingIn(BaseModel):
    term: str = ""
    nature: str  # artifact, norm, rule, fact, custom, location_rule, social_custom
    description: str
    source: str = ""

class WorldviewSettingOut(BaseModel):
    id: str
    story_id: str
    term: str
    nature: str
    description: str
    source: str
    created_at: str

class ExtractionRequest(BaseModel):
    text: str
    chunk_size: int = 500
    auto_merge: bool = True

class ExtractionResponse(BaseModel):
    extracted_count: int
    merged_count: int
    settings: List[WorldviewSettingOut]
```

## Prompt-Integration

### System Prompt Erweiterung

```
[WORLDVIEW SETTINGS]
* {term} ({nature}): {description}
* {term} ({nature}): {description}

Nur relevante Settings basierend auf dem aktuellen Kontext verwenden.
```

### Retrieval-Logik
1. Query = aktueller User-Input oder letzte Nachricht
2. Top-K (5-10) relevante Settings aus Vektor-Store
3. In Prompt einfuegen, wenn Query Terms enthält

## Implementierungsphasen

### Phase 1: Basis-Struktur (P1)
- [ ] Datenbank-Migration fuer worldview_settings
- [ ] SQLAlchemy Models
- [ ] CRUD API Routes
- [ ] Manuelle Setting-Erstellung

### Phase 2: Extraktions-Engine (P2)
- [ ] LLM-basierte Fact Extraction Use-Case
- [ ] Chunking-Strategie
- [ ] Filter-Logik
- [ ] Merge/Consolidation

### Phase 3: Prompt-Integration (P3)
- [ ] Vektor-Speicherung (Qdrant)
- [ ] Retrieval-Logik
- [ ] Prompt-Renderer Erweiterung
- [ ] Term-Matching

## LLM-Prompt fuer Extraktion

```
Du bist ein Weltwissen-Analyst. Analysiere den folgenden Textabschnitt aus einer Geschichte und extrahiere alle atomaren Welt-Fakten.

Ein "Welt-Fakt" ist:
- Eine Regel, die in dieser Welt gilt (z.B. "Zauberer duerfen sich vor Nicht-Zauberern nicht zeigen")
- Eine soziale Norm oder ein Brauch (z.B. "Adelige gruessen sich mit Verbeugung")
- Ein spezifisches Objekt oder Artefakt mit besonderen Eigenschaften
- Ein fundamentales Faktum ueber die Welt (z.B. "Die Nordmauer ist 700 Fuss hoch")
- Eine Terminologie-Erklaerung (z.B. "Ein 'Phial of Light' enthält gefangenes Sternenlicht")

NICHT extrahieren:
- Charakter-Actions oder Dialoge
- Allgemeine Common-Sense-Fakten
- Plot-spezifische Ereignisse

Format: JSON Array mit folgenden Feldern:
[
  {
    "term": "Der Begriff (falls vorhanden, sonst leer string)",
    "nature": "artifact|norm|rule|fact|custom|location_rule|social_custom",
    "description": "Klare, neutrale Beschreibung des Fakts",
    "source": "Verweis auf Quelle (Kapitel, Seite, etc.)"
  }
]

Textabschnitt:
{chunk_text}

Antworte NUR mit dem JSON Array, keine weiteren Texte.
```

## Risiken

1. **Over-Extraction**: Zu viele Settings koennen den Prompt ueberladen
2. **Falsche Kategorien**: Inkonsistente nature-Zuordnung
3. **Source-Tracking**: Bei automatischer Extraktion aus Messages kann Source unklar sein

## Metriken

- Settings pro Story
- Durchschnittliche Beschreibungslaenge
- Top-Kategorien (welche nature-Typen dominieren?)
- Retrieval-Trefferquote (wie oft werden Settings im Prompt verwendet?)
