import logging
from typing import List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
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
from src.backend.infrastructure.db import SessionLocal
from src.backend.infrastructure.langchain_clients import get_embedding_model
from src.backend.infrastructure.models import (
    LoreEntryModel,
    LoreVectorModel,
    StoryMessageModel,
    StoryModel,
    StorySummaryModel,
)

router = APIRouter(prefix="/stories", tags=["stories"])


def _lore_to_out(entry: LoreEntryModel) -> LoreEntryOut:
    return LoreEntryOut(
        id=entry.id,
        title=entry.title,
        description=entry.description or "",
        tag=entry.tag,
        triggers=entry.triggers or "",
    )


def _lore_metadata(entry: LoreEntryModel) -> dict:
    return {
        "lore_id": entry.id,
        "title": entry.title,
        "tag": entry.tag,
        "triggers": entry.triggers or "",
    }


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
        messages=[msg.to_payload() for msg in (story.messages or [])],
        lore=[_lore_to_out(entry) for entry in story.lore_entries],
    )


def _compute_lore_vector(entry_id: str, story_id: str, text: str, metadata: dict) -> None:
    logger = logging.getLogger("backend")
    try:
        embedder = get_embedding_model()
        embedding = embedder.embed_query(text)
        if not embedding:
            logger.warning("lore_vector_embedding_failed entry_id=%s", entry_id)
            return
    except Exception:
        logger.exception("lore_vector_embedding_failed entry_id=%s", entry_id)
        return
    db = SessionLocal()
    try:
        if not metadata:
            entry = db.query(LoreEntryModel).filter(LoreEntryModel.id == entry_id).first()
            if entry:
                metadata = _lore_metadata(entry)
        existing = db.query(LoreVectorModel).filter(LoreVectorModel.lore_id == entry_id).first()
        if existing:
            existing.story_id = story_id
            existing.content = text
            existing.metadata_ = metadata
            existing.embedding = embedding
        else:
            db.add(
                LoreVectorModel(
                    story_id=story_id,
                    lore_id=entry_id,
                    content=text,
                    metadata_=metadata,
                    embedding=embedding,
                )
            )
        db.commit()
    finally:
        db.close()


def _queue_vector(background_tasks: BackgroundTasks | None, entry_id: str, story_id: str, text: str, metadata: dict) -> None:
    if background_tasks is None:
        return
    background_tasks.add_task(_compute_lore_vector, entry_id, story_id, text, metadata)


def _apply_lore(story: StoryModel, lore: List[LoreEntryIn]) -> List[tuple[str, str, dict]]:
    story.lore_entries.clear()
    tasks: List[tuple[str, str, dict]] = []
    for entry in lore:
        entry_id = entry.id or str(uuid4())
        text = entry.description or ""
        metadata = {
            "lore_id": entry_id,
            "title": entry.title,
            "tag": entry.tag,
            "triggers": entry.triggers or "",
        }
        story.lore_entries.append(
            LoreEntryModel(
                id=entry_id,
                title=entry.title,
                description=entry.description or "",
                tag=entry.tag,
                triggers=entry.triggers or "",
            )
        )
        tasks.append((entry_id, text, metadata))
    return tasks


def _message_value(msg, key: str, default=None):
    if hasattr(msg, key):
        return getattr(msg, key)
    if isinstance(msg, dict):
        return msg.get(key, default)
    return default


def _ensure_summary(story: StoryModel, summary: str | None = None) -> StorySummaryModel:
    if story.summary_record is None:
        story.summary_record = StorySummaryModel(summary=(summary or "").strip(), last_position=-1)
    elif summary is not None:
        story.summary_record.summary = (summary or "").strip()
    return story.summary_record


def _apply_messages(story: StoryModel, messages: List) -> None:
    story.messages.clear()
    for position, msg in enumerate(messages):
        story.messages.append(
            StoryMessageModel(
                role=str(_message_value(msg, "role", "")).strip(),
                text=str(_message_value(msg, "text", "") or ""),
                mode=_message_value(msg, "mode", None),
                position=position,
            )
        )
    summary_record = _ensure_summary(story)
    summary_record.last_position = len(messages) - 1 if messages else -1


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
def create_story(
    payload: StoryCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> StoryOut:
    story = StoryModel(
        title=payload.title.strip() or "Untitled Story",
        ai_instruction_key=payload.ai_instruction_key,
        ai_instructions=payload.ai_instructions,
        plot_essentials=payload.plot_essentials or "",
        author_note=payload.author_note or "",
        description=payload.description or "",
        tags=list(payload.tags or []),
    )
    _ensure_summary(story, payload.plot_summary or "")
    if payload.messages:
        _apply_messages(story, payload.messages)
    tasks = _apply_lore(story, payload.lore or [])
    db.add(story)
    db.commit()
    db.refresh(story)
    for entry_id, text, metadata in tasks:
        _queue_vector(background_tasks, entry_id, story.id, text, metadata)
    return _story_to_out(story)


@router.get("/{story_id}", response_model=StoryOut)
def get_story(
    story_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> StoryOut:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return _story_to_out(story)


@router.put("/{story_id}", response_model=StoryOut)
def update_story(
    story_id: str,
    payload: StoryUpdate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> StoryOut:
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
        _ensure_summary(story, payload.plot_summary)
    if payload.plot_essentials is not None:
        story.plot_essentials = payload.plot_essentials
    if payload.author_note is not None:
        story.author_note = payload.author_note
    if payload.description is not None:
        story.description = payload.description
    if payload.tags is not None:
        story.tags = list(payload.tags)
    if payload.messages is not None:
        _apply_messages(story, payload.messages)
    if payload.lore is not None:
        tasks = _apply_lore(story, payload.lore)
    else:
        tasks = []
    db.commit()
    db.refresh(story)
    for entry_id, text, metadata in tasks:
        _queue_vector(background_tasks, entry_id, story.id, text, metadata)
    return _story_to_out(story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: str, db: Session = Depends(get_db)) -> None:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    db.delete(story)
    db.commit()


@router.get("/{story_id}/lore", response_model=List[LoreEntryOut])
def list_lore(
    story_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> List[LoreEntryOut]:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return [_lore_to_out(entry) for entry in story.lore_entries]


@router.post("/{story_id}/lore", response_model=LoreEntryOut, status_code=status.HTTP_201_CREATED)
def add_lore(
    story_id: str,
    payload: LoreEntryIn,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> LoreEntryOut:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    text = payload.description or ""
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
    _queue_vector(background_tasks, entry.id, story.id, text, _lore_metadata(entry))
    return _lore_to_out(entry)


@router.put("/{story_id}/lore/{entry_id}", response_model=LoreEntryOut)
def update_lore(
    story_id: str,
    entry_id: str,
    payload: LoreEntryIn,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> LoreEntryOut:
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
    text = payload.description or ""
    _queue_vector(background_tasks, entry.id, story_id, text, _lore_metadata(entry))
    return _lore_to_out(entry)


@router.post("/{story_id}/lore/reindex", status_code=status.HTTP_202_ACCEPTED)
def reindex_lore(
    story_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> dict:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    queued = 0
    for entry in story.lore_entries:
        text = entry.description or ""
        _queue_vector(background_tasks, entry.id, story.id, text, _lore_metadata(entry))
        queued += 1
    return {"status": "queued", "count": queued}


@router.delete("/{story_id}/lore/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lore(story_id: str, entry_id: str, db: Session = Depends(get_db)) -> None:
    entry = (
        db.query(LoreEntryModel)
        .filter(LoreEntryModel.story_id == story_id, LoreEntryModel.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lore entry not found")
    db.query(LoreVectorModel).filter(LoreVectorModel.lore_id == entry_id).delete(synchronize_session=False)
    db.delete(entry)
    db.commit()
