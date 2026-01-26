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


class StoryBase(BaseModel):
    title: str
    ai_instruction_key: str
    ai_instructions: str
    plot_summary: str = ""
    plot_essentials: str = ""
    author_note: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    lore: List[LoreEntryIn] = Field(default_factory=list)


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    ai_instruction_key: Optional[str] = None
    ai_instructions: Optional[str] = None
    plot_summary: Optional[str] = None
    plot_essentials: Optional[str] = None
    author_note: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    lore: Optional[List[LoreEntryIn]] = None


class StoryOut(StoryBase):
    id: str
    lore: List[LoreEntryOut] = Field(default_factory=list)


class StorySummary(BaseModel):
    id: str
    title: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str
    text: str = ""
    mode: Optional[str] = None


class SummaryRecomputeRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)


class SummaryRecomputeResponse(BaseModel):
    plot_summary: str
