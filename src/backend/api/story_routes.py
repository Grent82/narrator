import logging
import os
import threading
from typing import List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.api.schemas import (
    ExtractionRequest,
    ExtractionResponse,
    LocationIn,
    LocationOut,
    LoreEntryIn,
    LoreEntryOut,
    LoreSuggestionOut,
    LoreSuggestionUpdate,
    StoryGenerateJobResponse,
    StoryGenerateJobStatus,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryCreate,
    StoryOut,
    StorySummary,
    StoryUpdate,
    TravelStart,
    TravelTaskOut,
    WorldviewSettingIn,
    WorldviewSettingOut,
)
from src.backend.application.worldview.extractor import WorldviewExtractor
from src.backend.application.worldview.service import WorldviewService
from src.backend.infrastructure.embeddings import build_lore_text
from src.backend.infrastructure.db import get_db
from src.backend.application.vectorstores.lore_vectorstore import LoreVectorStore
from src.backend.infrastructure.langchain_clients import (
    get_embedding_model,
    get_story_generator_model,
    get_story_generator_repair_model,
)
from src.backend.infrastructure.models import (
    LoreEntryModel,
    LoreSuggestionModel,
    LocationModel,
    StoryMessageModel,
    StoryModel,
    StorySummaryModel,
    TravelTaskModel,
    WorldviewSettingModel,
)
from src.backend.application.summarizer import resolve_summary_prompt_key
from src.backend.application.story_generator import GeneratedStory, generate_story_blueprint
from src.backend.infrastructure.llm_config import active_story_generator_model_name

router = APIRouter(prefix="/stories", tags=["stories"])

_generator_jobs: dict[str, dict] = {}
_TRANSIENT_ASSISTANT_PREFIXES = (
    "[LLM error:",
    "[Ollama error:",
    "[Ollama warning:",
    "Backend error:",
    "Unexpected error:",
)


def _store_job(job_id: str, status: str, result: GeneratedStory | None = None, error: str | None = None) -> None:
    _generator_jobs[job_id] = {
        "status": status,
        "result": result,
        "error": error,
    }


def _job_to_response(job_id: str, job: dict) -> StoryGenerateJobStatus:
    result = job.get("result")
    if isinstance(result, GeneratedStory):
        payload = StoryGenerateResponse(
            title=result.title,
            description=result.description,
            plot_essentials=result.plot_essentials,
            author_note=result.author_note,
            tags=result.tags,
            lore=result.lore,
        )
    else:
        payload = None
    return StoryGenerateJobStatus(
        job_id=job_id,
        status=str(job.get("status", "unknown")),
        result=payload,
        error=job.get("error"),
    )


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


def _normalize_persisted_messages(messages: List) -> List[dict]:
    normalized: List[dict] = []
    for msg in messages:
        role = str(_message_value(msg, "role", "")).strip()
        text = str(_message_value(msg, "text", "") or "")
        stripped_text = text.strip()
        if role == "assistant" and any(stripped_text.startswith(prefix) for prefix in _TRANSIENT_ASSISTANT_PREFIXES):
            continue

        payload = {"role": role, "text": text}
        mode = _message_value(msg, "mode", None)
        if mode:
            payload["mode"] = mode
        normalized.append(payload)
    return normalized


def _is_transient_assistant_message(message: StoryMessageModel) -> bool:
    if (message.role or "").strip() != "assistant":
        return False
    text = (message.text or "").strip()
    return any(text.startswith(prefix) for prefix in _TRANSIENT_ASSISTANT_PREFIXES)


def _cleanup_transient_story_messages(story: StoryModel, db: Session | None = None) -> bool:
    transient_ids = [message.id for message in story.messages if _is_transient_assistant_message(message)]
    if not transient_ids:
        return False

    story.messages = [message for message in story.messages if message.id not in transient_ids]
    for position, message in enumerate(story.messages):
        message.position = position

    summary_record = _ensure_summary(story)
    summary_record.last_position = len(story.messages) - 1 if story.messages else -1

    if db is not None:
        db.commit()
        db.refresh(story)
    return True


def _apply_messages(story: StoryModel, messages: List) -> None:
    normalized_messages = _normalize_persisted_messages(messages)
    story.messages.clear()
    for position, msg in enumerate(normalized_messages):
        story.messages.append(
            StoryMessageModel(
                role=str(_message_value(msg, "role", "")).strip(),
                text=str(_message_value(msg, "text", "") or ""),
                mode=_message_value(msg, "mode", None),
                position=position,
            )
        )
    summary_record = _ensure_summary(story)
    summary_record.last_position = len(normalized_messages) - 1 if normalized_messages else -1


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
    _cleanup_transient_story_messages(story, db)
    return _story_to_out(story)


@router.post("/generate", response_model=StoryGenerateJobResponse)
def generate_story(
    payload: StoryGenerateRequest,
    chat_model=Depends(get_story_generator_model),
    repair_model=Depends(get_story_generator_repair_model),
) -> StoryGenerateResponse:
    job_id = str(uuid4())
    _store_job(job_id, "running")
    model_name = active_story_generator_model_name()

    def _run() -> None:
        logger = logging.getLogger("backend")
        try:
            result = generate_story_blueprint(chat_model, payload, logger, repair_model=repair_model, model_name=model_name)
            _store_job(job_id, "done", result=result)
        except Exception as exc:
            logger.exception("story_generator_failed job_id=%s", job_id)
            _store_job(job_id, "error", error=str(exc))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return StoryGenerateJobResponse(job_id=job_id, status="running")


@router.get("/generate/{job_id}", response_model=StoryGenerateJobStatus)
def get_generate_job(job_id: str) -> StoryGenerateJobStatus:
    job = _generator_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_response(job_id, job)


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
    location_to_upsert = None
    is_new_location = False

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
        is_new_location = (suggestion.tag or "").lower() == "location"

    # Create Location entry if this is a Location tag
    if is_new_location:
        existing_location = db.query(LocationModel).filter(
            LocationModel.story_id == story_id,
            LocationModel.name == suggestion.title.strip()
        ).first()
        if not existing_location:
            location = LocationModel(
                story_id=story_id,
                name=suggestion.title.strip(),
                description=suggestion.description or "",
                tag="Location",
                metadata={"source": "lore_suggestion", "suggestion_id": suggestion_id},
            )
            db.add(location)
            location_to_upsert = location

    suggestion.status = "accepted"
    db.delete(suggestion)
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


@router.put("/{story_id}/lore/review/{suggestion_id}", response_model=LoreSuggestionOut)
def update_lore_suggestion(
    story_id: str,
    suggestion_id: str,
    payload: LoreSuggestionUpdate,
    db: Session = Depends(get_db),
) -> LoreSuggestionOut:
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

    suggestion.title = payload.title.strip()
    suggestion.description = payload.description.strip()
    suggestion.tag = payload.tag.strip()
    suggestion.triggers = payload.triggers.strip()
    db.commit()
    db.refresh(suggestion)
    return LoreSuggestionOut(
        id=suggestion.id,
        kind=suggestion.kind,
        status=suggestion.status,
        title=suggestion.title,
        tag=suggestion.tag,
        description=suggestion.description or "",
        triggers=suggestion.triggers or "",
        target_lore_id=suggestion.target_lore_id,
        created_at=suggestion.created_at.isoformat() if suggestion.created_at else None,
    )


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
    db.delete(suggestion)
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


# ============================================================================
# Location Routes
# ============================================================================

def _location_to_out(loc: LocationModel) -> LocationOut:
    return LocationOut(
        id=loc.id,
        story_id=loc.story_id,
        name=loc.name,
        description=loc.description or "",
        tag=loc.tag or "Location",
        metadata=loc.metadata or {},
        parent_location_id=loc.parent_location_id,
        created_at=loc.created_at.isoformat() if loc.created_at else "",
        updated_at=loc.updated_at.isoformat() if loc.updated_at else "",
    )


@router.get("/{story_id}/locations", response_model=List[LocationOut])
def list_locations(story_id: str, db: Session = Depends(get_db)) -> List[LocationOut]:
    locations = db.query(LocationModel).filter(LocationModel.story_id == story_id).order_by(LocationModel.name).all()
    return [_location_to_out(loc) for loc in locations]


@router.post("/{story_id}/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(story_id: str, payload: LocationIn, db: Session = Depends(get_db)) -> LocationOut:
    # Check if location with same name exists
    existing = db.query(LocationModel).filter(
        LocationModel.story_id == story_id,
        LocationModel.name == payload.name.strip()
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location with this name already exists")

    # Validate parent_location_id if provided
    parent_location_id = payload.parent_location_id
    if parent_location_id:
        parent = db.query(LocationModel).filter(
            LocationModel.id == parent_location_id,
            LocationModel.story_id == story_id
        ).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent location not found")

    location = LocationModel(
        story_id=story_id,
        name=payload.name.strip(),
        description=payload.description.strip(),
        tag=payload.tag.strip() or "Location",
        metadata=payload.metadata or {},
        parent_location_id=parent_location_id,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return _location_to_out(location)


@router.get("/{story_id}/locations/{location_id}", response_model=LocationOut)
def get_location(story_id: str, location_id: str, db: Session = Depends(get_db)) -> LocationOut:
    location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.story_id == story_id
    ).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return _location_to_out(location)


@router.put("/{story_id}/locations/{location_id}", response_model=LocationOut)
def update_location(story_id: str, location_id: str, payload: LocationIn, db: Session = Depends(get_db)) -> LocationOut:
    location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.story_id == story_id
    ).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    # Check for name collision
    existing = db.query(LocationModel).filter(
        LocationModel.story_id == story_id,
        LocationModel.name == payload.name.strip(),
        LocationModel.id != location_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location with this name already exists")

    # Validate parent_location_id if provided
    parent_location_id = payload.parent_location_id
    if parent_location_id:
        parent = db.query(LocationModel).filter(
            LocationModel.id == parent_location_id,
            LocationModel.story_id == story_id
        ).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent location not found")

    location.name = payload.name.strip()
    location.description = payload.description.strip()
    location.tag = payload.tag.strip() or "Location"
    location.metadata = payload.metadata or {}
    location.parent_location_id = parent_location_id
    db.commit()
    db.refresh(location)
    return _location_to_out(location)


@router.delete("/{story_id}/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(story_id: str, location_id: str, db: Session = Depends(get_db)) -> None:
    location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.story_id == story_id
    ).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    db.delete(location)
    db.commit()


# ============================================================================
# Travel Routes
# ============================================================================

def _travel_to_out(task: TravelTaskModel) -> TravelTaskOut:
    return TravelTaskOut(
        id=task.id,
        story_id=task.story_id,
        character_name=task.character_name,
        from_location_id=task.from_location_id,
        to_location_id=task.to_location_id,
        distance=task.distance,
        remaining_turns=task.remaining_turns,
        started_at=task.started_at.isoformat() if task.started_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        status=task.status,
    )


@router.post("/{story_id}/travel", response_model=TravelTaskOut, status_code=status.HTTP_201_CREATED)
def start_travel(story_id: str, payload: TravelStart, db: Session = Depends(get_db)) -> TravelTaskOut:
    # Validate to_location exists
    to_location = db.query(LocationModel).filter(
        LocationModel.id == payload.to_location_id,
        LocationModel.story_id == story_id
    ).first()
    if not to_location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination location not found")

    # Validate from_location if provided
    from_location_id = payload.from_location_id
    if payload.from_location_id:
        from_location = db.query(LocationModel).filter(
            LocationModel.id == payload.from_location_id,
            LocationModel.story_id == story_id
        ).first()
        if not from_location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="From location not found")

    task = TravelTaskModel(
        story_id=story_id,
        character_name=payload.character_name.strip(),
        from_location_id=from_location_id,
        to_location_id=payload.to_location_id,
        distance=payload.distance,
        remaining_turns=payload.distance,
        status="in_progress",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _travel_to_out(task)


@router.get("/{story_id}/travel/active", response_model=List[TravelTaskOut])
def list_active_travel(story_id: str, db: Session = Depends(get_db)) -> List[TravelTaskOut]:
    tasks = db.query(TravelTaskModel).filter(
        TravelTaskModel.story_id == story_id,
        TravelTaskModel.status == "in_progress"
    ).order_by(TravelTaskModel.started_at).all()
    return [_travel_to_out(task) for task in tasks]


@router.put("/{story_id}/travel/{task_id}/cancel", response_model=TravelTaskOut)
def cancel_travel(story_id: str, task_id: str, db: Session = Depends(get_db)) -> TravelTaskOut:
    task = db.query(TravelTaskModel).filter(
        TravelTaskModel.id == task_id,
        TravelTaskModel.story_id == story_id,
        TravelTaskModel.status == "in_progress"
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active travel task not found")

    task.status = "cancelled"
    db.commit()
    db.refresh(task)
    return _travel_to_out(task)


# ============================================================================
# Worldview Setting Routes
# ============================================================================

def _worldview_to_out(setting: WorldviewSettingModel) -> WorldviewSettingOut:
    return WorldviewSettingOut(
        id=setting.id,
        story_id=setting.story_id,
        term=setting.term,
        nature=setting.nature,
        description=setting.description or "",
        source=setting.source or "",
        created_at=setting.created_at.isoformat() if setting.created_at else "",
        updated_at=setting.updated_at.isoformat() if setting.updated_at else "",
    )


@router.get("/{story_id}/worldview/settings", response_model=List[WorldviewSettingOut])
def list_worldview_settings(story_id: str, db: Session = Depends(get_db)) -> List[WorldviewSettingOut]:
    settings = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.story_id == story_id
    ).order_by(WorldviewSettingModel.nature, WorldviewSettingModel.term).all()
    return [_worldview_to_out(s) for s in settings]


@router.post("/{story_id}/worldview/settings", response_model=WorldviewSettingOut, status_code=status.HTTP_201_CREATED)
def create_worldview_setting(story_id: str, payload: WorldviewSettingIn, db: Session = Depends(get_db)) -> WorldviewSettingOut:
    # Check for duplicate
    existing = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.story_id == story_id,
        WorldviewSettingModel.term == payload.term.strip(),
        WorldviewSettingModel.nature == payload.nature.strip()
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setting with this term and nature already exists")

    setting = WorldviewSettingModel(
        story_id=story_id,
        term=payload.term.strip(),
        nature=payload.nature.strip(),
        description=payload.description.strip(),
        source=payload.source.strip(),
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return _worldview_to_out(setting)


@router.get("/{story_id}/worldview/settings/{setting_id}", response_model=WorldviewSettingOut)
def get_worldview_setting(story_id: str, setting_id: str, db: Session = Depends(get_db)) -> WorldviewSettingOut:
    setting = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.id == setting_id,
        WorldviewSettingModel.story_id == story_id
    ).first()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worldview setting not found")
    return _worldview_to_out(setting)


@router.put("/{story_id}/worldview/settings/{setting_id}", response_model=WorldviewSettingOut)
def update_worldview_setting(story_id: str, setting_id: str, payload: WorldviewSettingIn, db: Session = Depends(get_db)) -> WorldviewSettingOut:
    setting = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.id == setting_id,
        WorldviewSettingModel.story_id == story_id
    ).first()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worldview setting not found")

    # Check for duplicate (excluding self)
    existing = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.story_id == story_id,
        WorldviewSettingModel.term == payload.term.strip(),
        WorldviewSettingModel.nature == payload.nature.strip(),
        WorldviewSettingModel.id != setting_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setting with this term and nature already exists")

    setting.term = payload.term.strip()
    setting.nature = payload.nature.strip()
    setting.description = payload.description.strip()
    setting.source = payload.source.strip()
    db.commit()
    db.refresh(setting)
    return _worldview_to_out(setting)


@router.delete("/{story_id}/worldview/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worldview_setting(story_id: str, setting_id: str, db: Session = Depends(get_db)) -> None:
    setting = db.query(WorldviewSettingModel).filter(
        WorldviewSettingModel.id == setting_id,
        WorldviewSettingModel.story_id == story_id
    ).first()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worldview setting not found")
    db.delete(setting)
    db.commit()


@router.post("/{story_id}/worldview/extract", response_model=ExtractionResponse)
def extract_worldview_settings(
    story_id: str,
    payload: ExtractionRequest,
    db: Session = Depends(get_db),
) -> ExtractionResponse:
    """Extract worldview settings from text using LLM.

    This endpoint uses an LLM to analyze the provided text and extract
    worldview settings like rules, norms, artifacts, and facts.
    """
    # Verify story exists
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")

    # Create extractor with LLM
    from src.backend.infrastructure.langchain_clients import get_story_generator_model

    llm = get_story_generator_model()
    extractor = WorldviewExtractor(llm)
    service = WorldviewService(db, extractor)

    # Extract and save
    result = service.extract_and_save(
        story_id=story_id,
        text=payload.text,
        chunk_size=payload.chunk_size,
        auto_merge=payload.auto_merge,
    )

    # Get saved settings
    settings = service.get_settings(story_id)

    return ExtractionResponse(
        extracted_count=result["extracted_count"],
        merged_count=result["merged_count"],
        settings=[_worldview_to_out(s) for s in settings],
    )


@router.get("/{story_id}/worldview/retrieve")
def retrieve_worldview_settings(story_id: str, query: str, top_k: int = 5, db: Session = Depends(get_db)):
    """Retrieve worldview settings relevant to a query.

    Currently returns all settings limited by top_k. Future implementation
    will use embedding-based retrieval.
    """
    # Verify story exists
    story = db.query(StoryModel).filter(StoryModel.id == story_id).first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")

    service = WorldviewService(db)
    settings = service.get_relevant_settings(story_id, query, top_k)

    return {
        "query": query,
        "top_k": top_k,
        "count": len(settings),
        "settings": [_worldview_to_out(s) for s in settings],
    }
