import logging
import os
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
from src.backend.infrastructure.embeddings import build_lore_text
from src.backend.infrastructure.db import get_db
from src.backend.application.vectorstores.lore_vectorstore import LoreVectorStore
from src.backend.infrastructure.langchain_clients import get_embedding_model
from src.backend.infrastructure.models import (
    LoreEntryModel,
    LoreSuggestionModel,
    StoryMessageModel,
    StoryModel,
    StorySummaryModel,
)
from src.backend.application.summarizer import resolve_summary_prompt_key

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
        "description": entry.description or "",
        "triggers": entry.triggers or "",
    }


def _story_to_out(story: StoryModel) -> StoryOut:
    return StoryOut(
        id=story.id,
        title=story.title,
        ai_instruction_key=story.ai_instruction_key,
        ai_instructions=story.ai_instructions,
        summary_prompt_key=story.summary_prompt_key,
        plot_summary=story.plot_summary or "",
        plot_essentials=story.plot_essentials or "",
        author_note=story.author_note or "",
        description=story.description or "",
        tags=list(story.tags or []),
        messages=[msg.to_payload() for msg in (story.messages or [])],
        lore=[_lore_to_out(entry) for entry in story.lore_entries],
        lore_review=[
            {
                "id": item.id,
                "kind": item.kind,
                "status": item.status,
                "title": item.title,
                "tag": item.tag,
                "description": item.description or "",
                "triggers": item.triggers or "",
                "target_lore_id": item.target_lore_id,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in story.lore_suggestions
            if item.status == "pending"
        ],
    )


def _compute_lore_vector(entry_id: str, story_id: str, text: str, metadata: dict) -> None:
    logger = logging.getLogger("backend")
    try:
        embedder = get_embedding_model()
        embedding = embedder.embed_query(text)
        if not embedding:
            logger.warning("lore_vector_embedding_failed entry_id=%s", entry_id)
            return
        expected_dim = int(os.getenv("EMBED_DIM", "768"))
        if embedding and len(embedding) != expected_dim:
            logger.error( "Lore Embeddings Dimension mismatch: got %d, expected %d", len(embedding), expected_dim)
            embedding = None
            return
    except Exception:
        logger.exception("Lore Embeddings Failed entry_id=%s", entry_id)
        return
    payload = {
        "story_id": story_id,
        "content": text,
        "metadata": metadata,
    }
    logger.debug( "lore_qdrant_upsert   entry_id=%s story_id=%s title=%s content_len=%d", entry_id, story_id, metadata.get("title", ""), len(text or ""), )
    store = LoreVectorStore(embedder, story_id, vector_size=int(os.getenv("EMBED_DIM", "768")))
    store.upsert_lore(entry_id, embedding, payload)


def _queue_vector(background_tasks: BackgroundTasks | None, entry_id: str, story_id: str, text: str, metadata: dict) -> None:
    if background_tasks is None:
        return
    background_tasks.add_task(_compute_lore_vector, entry_id, story_id, text, metadata)


def _apply_lore(story: StoryModel, lore: List[LoreEntryIn], db: Session) -> List[tuple[str, str, dict]]:
    existing_ids = {entry.id for entry in story.lore_entries}
    story.lore_entries.clear()
    tasks: List[tuple[str, str, dict]] = []
    new_ids: set[str] = set()
    for entry in lore:
        entry_id = entry.id or str(uuid4())
        new_ids.add(entry_id)
        text = build_lore_text(
            entry.title,
            entry.tag,
            entry.triggers or "",
            entry.description or "",
        )
        metadata = {
            "lore_id": entry_id,
            "title": entry.title,
            "tag": entry.tag,
            "description": entry.description or "",
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
    removed_ids = existing_ids - new_ids
    if removed_ids and story.id:
        store = LoreVectorStore(get_embedding_model(), story.id, vector_size=int(os.getenv("EMBED_DIM", "768")))
        for lore_id in removed_ids:
            store.delete_by_lore_id(lore_id)
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
    summary_prompt_key = payload.summary_prompt_key or resolve_summary_prompt_key(payload.ai_instruction_key)
    story = StoryModel(
        title=payload.title.strip() or "Untitled Story",
        ai_instruction_key=payload.ai_instruction_key,
        ai_instructions=payload.ai_instructions,
        summary_prompt_key=summary_prompt_key,
        plot_essentials=payload.plot_essentials or "",
        author_note=payload.author_note or "",
        description=payload.description or "",
        tags=list(payload.tags or []),
    )
    _ensure_summary(story, payload.plot_summary or "")
    if payload.messages:
        _apply_messages(story, payload.messages)
    tasks = _apply_lore(story, payload.lore or [], db)
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


@router.post("/{story_id}/lore/sync", status_code=status.HTTP_204_NO_CONTENT)
def sync_story_lore(story_id: str, db: Session = Depends(get_db)) -> None:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    if not story.lore_entries:
        return None
    embedder = get_embedding_model()
    store = LoreVectorStore(embedder, story_id, vector_size=int(os.getenv("EMBED_DIM", "768")))
    texts: list[str] = []
    metadatas: list[dict] = []
    for entry in story.lore_entries:
        texts.append(build_lore_text(entry.title, entry.tag, entry.triggers or "", entry.description or ""))
        metadatas.append(_lore_metadata(entry))
    store.add_texts(texts, metadatas=metadatas)


@router.post("/{story_id}/lore/review/{suggestion_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_lore_suggestion(
    story_id: str,
    suggestion_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> None:
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    suggestion = (
        db.query(LoreSuggestionModel)
        .filter(
            LoreSuggestionModel.id == suggestion_id,
            LoreSuggestionModel.story_id == story_id,
            LoreSuggestionModel.status == "pending",
        )
        .first()
    )
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    entry_to_upsert = None
    if suggestion.kind == "UPDATE" and suggestion.target_lore_id:
        target = (
            db.query(LoreEntryModel)
            .filter(LoreEntryModel.story_id == story_id, LoreEntryModel.id == suggestion.target_lore_id)
            .first()
        )
        if target:
            if suggestion.description and suggestion.description not in (target.description or ""):
                target.description = (target.description or "").rstrip() + "\n" + suggestion.description
            if suggestion.triggers:
                existing = {t.strip() for t in (target.triggers or "").split(",") if t.strip()}
                incoming = {t.strip() for t in suggestion.triggers.split(",") if t.strip()}
                target.triggers = ", ".join(sorted(existing.union(incoming)))
            entry_to_upsert = target
        else:
            entry = LoreEntryModel(
                title=suggestion.title,
                description=suggestion.description or "",
                tag=suggestion.tag,
                triggers=suggestion.triggers or "",
            )
            story.lore_entries.append(entry)
            entry_to_upsert = entry
    else:
        entry = LoreEntryModel(
            title=suggestion.title,
            description=suggestion.description or "",
            tag=suggestion.tag,
            triggers=suggestion.triggers or "",
        )
        story.lore_entries.append(entry)
        entry_to_upsert = entry
    suggestion.status = "accepted"
    db.commit()
    db.refresh(story)

    if entry_to_upsert:
        text = build_lore_text(
            entry_to_upsert.title,
            entry_to_upsert.tag,
            entry_to_upsert.triggers or "",
            entry_to_upsert.description or "",
        )
        _queue_vector(background_tasks, entry_to_upsert.id, story_id, text, _lore_metadata(entry_to_upsert))
    return None


@router.post("/{story_id}/lore/review/{suggestion_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_lore_suggestion(
    story_id: str,
    suggestion_id: str,
    db: Session = Depends(get_db),
) -> None:
    suggestion = (
        db.query(LoreSuggestionModel)
        .filter(
            LoreSuggestionModel.id == suggestion_id,
            LoreSuggestionModel.story_id == story_id,
            LoreSuggestionModel.status == "pending",
        )
        .first()
    )
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    suggestion.status = "rejected"
    db.commit()
    return None


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
    if payload.summary_prompt_key is not None:
        story.summary_prompt_key = payload.summary_prompt_key
    elif payload.ai_instruction_key is not None:
        story.summary_prompt_key = resolve_summary_prompt_key(payload.ai_instruction_key)
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
        tasks = _apply_lore(story, payload.lore, db)
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
    text = build_lore_text(
        payload.title,
        payload.tag,
        payload.triggers or "",
        payload.description or "",
    )
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
    text = build_lore_text(
        payload.title,
        payload.tag,
        payload.triggers or "",
        payload.description or "",
    )
    _queue_vector(background_tasks, entry.id, story_id, text, _lore_metadata(entry))
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
    store = LoreVectorStore(get_embedding_model(), story_id, vector_size=int(os.getenv("EMBED_DIM", "768")))
    store.delete_by_lore_id(entry_id)
    db.delete(entry)
    db.commit()
