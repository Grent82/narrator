from __future__ import annotations

import os
import threading
import time
from typing import Callable, Iterator

from src.backend.application.ports import ChatModelProtocol, LoggerProtocol

from src.backend.application.input_formatting import format_user_for_summary
from src.backend.application.llm_settings import DEFAULT_OPTIONS, MODE_OPTIONS
from src.backend.application.prompt_builder import build_chat_messages
from src.backend.application.use_cases.turn_models import TurnContext
from src.backend.application.lore_suggester import extract_suggestions, save_suggestions
from src.backend.infrastructure.db import SessionLocal
from src.backend.infrastructure.langchain_clients import get_chat_model
from src.backend.infrastructure.models import LoreEntryModel


def stream_turn(
    context: TurnContext,
    chat_model: ChatModelProtocol,
    model: str,
    logger: LoggerProtocol,
    commit: Callable[[], None] | None = None,
    summary_model: str | None = None,
    summary_max_chars: int | None = None,
    recent_pairs: int = 3,
    overlap_pairs: int = 0,
) -> Iterator[str]:
    start = time.monotonic()
    buffer = ""
    last_usage = None
    try:
        messages = build_chat_messages(
            context.story,
            context.text,
            mode=context.mode,
            lore_entries=context.lore_entries,
            recent_pairs=recent_pairs,
            overlap_pairs=overlap_pairs,
            logger=logger,
        )
        logger.debug("ollama_stream_request messages=%s", messages)
        options = MODE_OPTIONS.get(context.mode, DEFAULT_OPTIONS)
        logger.debug("ollama_stream_options %s", options)
        bound = chat_model.bind(model=model, **options)
        for part in bound.stream(messages):
            token = getattr(part, "content", "") or ""
            usage = getattr(part, "response_metadata", {}).get("usage")
            if usage:
                last_usage = usage
            if token:
                buffer += token
                yield token
        logger.debug("ollama_stream_completed duration_ms=%d", int((time.monotonic() - start) * 1000))
        if last_usage:
            logger.debug("ollama_usage %s", last_usage)
        if context.story and commit and summary_model and summary_max_chars is not None:
            from src.backend.application.summarizer import update_story_summary

            update_story_summary(
                client=chat_model,
                model=summary_model,
                story=context.story,
                user_input=format_user_for_summary(context.mode, context.text),
                assistant_text=buffer,
                max_chars=summary_max_chars,
                logger=logger,
            )
            commit()
            _schedule_lore_suggestions(context.story.id, context.text, buffer, model, logger)
        else:
            logger.debug("story_summary_skipped no_story_or_commit")
    except Exception as exc:
        logger.exception("ollama_stream_error")
        yield f"\n[Ollama error: {exc}]"


def _schedule_lore_suggestions(
    story_id: str | None,
    user_input: str,
    assistant_text: str,
    model: str,
    logger: LoggerProtocol,
) -> None:
    if not story_id:
        return
    if not user_input.strip() and not assistant_text.strip():
        return

    def _run() -> None:
        db = SessionLocal()
        try:
            entries = db.query(LoreEntryModel).filter(LoreEntryModel.story_id == story_id).all()
            llm = get_chat_model()
            current_model = getattr(llm, "model", None)
            if current_model and current_model != model and hasattr(llm, "model_copy"):
                llm = llm.model_copy(update={"model": model})
            suggestions = extract_suggestions(llm, model, entries, user_input, assistant_text)
            created = save_suggestions(story_id, user_input, assistant_text, entries, suggestions, db)
            logger.debug("lore_suggestions_created story_id=%s count=%d", story_id, created)
        except Exception:
            logger.exception("lore_suggestions_failed story_id=%s", story_id)
        finally:
            db.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
