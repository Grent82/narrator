from typing import List, Optional

from pydantic import BaseModel, Field


class LoreEntryIn(BaseModel):
    id: Optional[str] = None
    title: str
    description: str = ""
    tag: str
    triggers: str = ""


class LoreEntryOut(BaseModel):
    id: str
    title: str
    description: str = ""
    tag: str
    triggers: str = ""


class LoreSuggestionOut(BaseModel):
    id: str
    kind: str
    status: str
    title: str
    tag: str
    description: str = ""
    triggers: str = ""
    target_lore_id: Optional[str] = None
    created_at: Optional[str] = None


class LoreSuggestionUpdate(BaseModel):
    title: str
    description: str = ""
    tag: str
    triggers: str = ""


# Location schemas
class LocationIn(BaseModel):
    name: str
    description: str = ""
    tag: str = "Location"
    metadata: dict = {}
    parent_location_id: str | None = None


class LocationOut(BaseModel):
    id: str
    story_id: str
    name: str
    description: str = ""
    tag: str = "Location"
    metadata: dict = {}
    parent_location_id: str | None = None
    created_at: str
    updated_at: str


# Travel schemas
class TravelStart(BaseModel):
    character_name: str
    from_location_id: str | None = None
    to_location_id: str
    distance: int = 1


class TravelTaskOut(BaseModel):
    id: str
    story_id: str
    character_name: str
    from_location_id: str | None = None
    to_location_id: str
    distance: int
    remaining_turns: int
    started_at: str
    completed_at: str | None = None
    status: str


# Worldview Setting schemas
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
    updated_at: str


# Location connection schemas (distance network)
class LocationConnectionIn(BaseModel):
    from_location_id: str
    to_location_id: str
    distance: int = 1
    travel_time_hours: float | None = None
    difficulty: str = "normal"  # easy, normal, dangerous, impossible


class LocationConnectionOut(BaseModel):
    id: str
    story_id: str
    from_location_id: str
    to_location_id: str
    distance: int
    travel_time_hours: float | None = None
    difficulty: str
    created_at: str


class LocationConnectionUpdate(BaseModel):
    distance: int | None = None
    travel_time_hours: float | None = None
    difficulty: str | None = None


# Event schemas (Intervention/Event system)
class EventIn(BaseModel):
    event_type: str = "global_event"  # global_event, environment_interaction, world_state_change
    title: str
    description: str = ""
    intervention: str = ""
    is_active: bool = True
    priority: int = 0
    location_id: str | None = None


class EventOut(BaseModel):
    id: str
    story_id: str
    event_type: str
    title: str
    description: str
    intervention: str
    is_active: bool
    priority: int
    location_id: str | None
    created_at: str
    updated_at: str
    started_at: str | None
    ended_at: str | None


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    intervention: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    location_id: str | None = None


class ExtractionRequest(BaseModel):
    text: str
    chunk_size: int = 500
    auto_merge: bool = True


class ExtractionResponse(BaseModel):
    extracted_count: int
    merged_count: int
    settings: list[WorldviewSettingOut] = []


class ChatMessage(BaseModel):
    role: str
    text: str = ""
    mode: Optional[str] = None


class StoryBase(BaseModel):
    title: str
    ai_instruction_key: str
    ai_instructions: str
    summary_prompt_key: str = "neutral"
    plot_summary: str = ""
    plot_essentials: str = ""
    author_note: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    lore: List[LoreEntryIn] = Field(default_factory=list)
    messages: List[ChatMessage] = Field(default_factory=list)


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    ai_instruction_key: Optional[str] = None
    ai_instructions: Optional[str] = None
    summary_prompt_key: Optional[str] = None
    plot_summary: Optional[str] = None
    plot_essentials: Optional[str] = None
    author_note: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    lore: Optional[List[LoreEntryIn]] = None
    messages: Optional[List[ChatMessage]] = None


class StoryOut(StoryBase):
    id: str
    lore: List[LoreEntryOut] = Field(default_factory=list)
    lore_review: List[LoreSuggestionOut] = Field(default_factory=list)


class StorySummary(BaseModel):
    id: str
    title: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)


class StoryGenerateRequest(BaseModel):
    ai_instruction_key: str
    role: str
    name: str
    gender: str = ""
    age: str = ""
    traits: str
    world_input: str
    start_template: str = ""
    start_custom: str = ""


class StoryGenerateResponse(BaseModel):
    title: str
    description: str
    plot_essentials: str
    author_note: str = ""
    tags: List[str] = Field(default_factory=list)
    lore: List[LoreEntryIn] = Field(default_factory=list)


class StoryGenerateJobResponse(BaseModel):
    job_id: str
    status: str


class StoryGenerateJobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[StoryGenerateResponse] = None
    error: Optional[str] = None


# Character schemas
class CharacterIn(BaseModel):
    name: str
    nickname: Optional[str] = None
    is_player: bool = False
    profile: str = ""
    relation: str = ""
    goal: str = ""
    status: str = ""
    motivation: str = ""
    location_id: Optional[str] = None
    activity: float = 1.0
    metadata: dict = {}


class CharacterOut(BaseModel):
    id: str
    story_id: str
    name: str
    nickname: Optional[str] = None
    is_player: bool
    profile: str
    relation: str
    goal: str
    status: str
    motivation: str
    location_id: Optional[str] = None
    activity: float
    metadata: dict
    created_at: str
    updated_at: str


class CharacterUpdate(BaseModel):
    nickname: Optional[str] = None
    profile: Optional[str] = None
    relation: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    motivation: Optional[str] = None
    location_id: Optional[str] = None
    activity: Optional[float] = None
    metadata: Optional[dict] = None
