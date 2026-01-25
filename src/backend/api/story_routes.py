from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.api.schemas import (
    LoreEntryIn,
    LoreEntryOut,
    StoryCreate,
    StoryOut,
    StorySummary,
    StoryUpdate,
)
from src.backend.infrastructure.db import get_db
from src.backend.infrastructure.models import LoreEntryModel, StoryModel

router = APIRouter(prefix="/stories", tags=["stories"])


def _lore_to_out(entry: LoreEntryModel) -> LoreEntryOut:
    return LoreEntryOut(
        id=entry.id,
        title=entry.title,
        description=entry.description or "",
        tag=entry.tag,
        triggers=entry.triggers or "",
    )


def _story_to_out(story: StoryModel) -> StoryOut:
    return StoryOut(
        id=story.id,
        title=story.title,
        ai_instruction_key=story.ai_instruction_key,
        ai_instructions=story.ai_instructions,
        plot_summary=story.plot_summary or "",
        plot_essentials=story.plot_essentials or "",
        author_note=story.author_note or "",
        description=story.description or "",
        tags=list(story.tags or []),
        lore=[_lore_to_out(entry) for entry in story.lore_entries],
    )


def _apply_lore(story: StoryModel, lore: List[LoreEntryIn]) -> None:
    story.lore_entries.clear()
    for entry in lore:
        story.lore_entries.append(
            LoreEntryModel(
                id=entry.id or str(uuid4()),
                title=entry.title,
                description=entry.description or "",
                tag=entry.tag,
                triggers=entry.triggers or "",
            )
        )


@router.get("", response_model=List[StorySummary])
def list_stories(db: Session = Depends(get_db)) -> List[StorySummary]:
    stories = db.query(StoryModel).order_by(StoryModel.updated_at.desc()).all()
    return [
        StorySummary(
            id=story.id,
            title=story.title,
            description=story.description or "",
            tags=list(story.tags or []),
        )
        for story in stories
    ]


@router.post("", response_model=StoryOut, status_code=status.HTTP_201_CREATED)
def create_story(payload: StoryCreate, db: Session = Depends(get_db)) -> StoryOut:
    story = StoryModel(
        title=payload.title.strip() or "Untitled Story",
        ai_instruction_key=payload.ai_instruction_key,
        ai_instructions=payload.ai_instructions,
        plot_summary=payload.plot_summary or "",
        plot_essentials=payload.plot_essentials or "",
        author_note=payload.author_note or "",
        description=payload.description or "",
        tags=list(payload.tags or []),
    )
    _apply_lore(story, payload.lore or [])
    db.add(story)
    db.commit()
    db.refresh(story)
    return _story_to_out(story)


@router.get("/{story_id}", response_model=StoryOut)
def get_story(story_id: str, db: Session = Depends(get_db)) -> StoryOut:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return _story_to_out(story)


@router.put("/{story_id}", response_model=StoryOut)
def update_story(story_id: str, payload: StoryUpdate, db: Session = Depends(get_db)) -> StoryOut:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    if payload.title is not None:
        story.title = payload.title.strip() or "Untitled Story"
    if payload.ai_instruction_key is not None:
        story.ai_instruction_key = payload.ai_instruction_key
    if payload.ai_instructions is not None:
        story.ai_instructions = payload.ai_instructions
    if payload.plot_summary is not None:
        story.plot_summary = payload.plot_summary
    if payload.plot_essentials is not None:
        story.plot_essentials = payload.plot_essentials
    if payload.author_note is not None:
        story.author_note = payload.author_note
    if payload.description is not None:
        story.description = payload.description
    if payload.tags is not None:
        story.tags = list(payload.tags)
    if payload.lore is not None:
        _apply_lore(story, payload.lore)
    db.commit()
    db.refresh(story)
    return _story_to_out(story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: str, db: Session = Depends(get_db)) -> None:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    db.delete(story)
    db.commit()


@router.get("/{story_id}/lore", response_model=List[LoreEntryOut])
def list_lore(story_id: str, db: Session = Depends(get_db)) -> List[LoreEntryOut]:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return [_lore_to_out(entry) for entry in story.lore_entries]


@router.post("/{story_id}/lore", response_model=LoreEntryOut, status_code=status.HTTP_201_CREATED)
def add_lore(story_id: str, payload: LoreEntryIn, db: Session = Depends(get_db)) -> LoreEntryOut:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    entry = LoreEntryModel(
        id=payload.id or str(uuid4()),
        title=payload.title,
        description=payload.description or "",
        tag=payload.tag,
        triggers=payload.triggers or "",
        story=story,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _lore_to_out(entry)


@router.put("/{story_id}/lore/{entry_id}", response_model=LoreEntryOut)
def update_lore(story_id: str, entry_id: str, payload: LoreEntryIn, db: Session = Depends(get_db)) -> LoreEntryOut:
    entry = (
        db.query(LoreEntryModel)
        .filter(LoreEntryModel.story_id == story_id, LoreEntryModel.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lore entry not found")
    entry.title = payload.title
    entry.description = payload.description or ""
    entry.tag = payload.tag
    entry.triggers = payload.triggers or ""
    db.commit()
    db.refresh(entry)
    return _lore_to_out(entry)


@router.delete("/{story_id}/lore/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lore(story_id: str, entry_id: str, db: Session = Depends(get_db)) -> None:
    entry = (
        db.query(LoreEntryModel)
        .filter(LoreEntryModel.story_id == story_id, LoreEntryModel.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lore entry not found")
    db.delete(entry)
    db.commit()
