from __future__ import annotations

import time
from typing import Callable, Iterator

from src.backend.application.ports import LoggerProtocol, OllamaProtocol

from src.backend.application.input_formatting import format_user_for_summary
from src.backend.application.llm_settings import DEFAULT_OPTIONS, MODE_OPTIONS
from src.backend.application.prompt_builder import build_chat_messages
from src.backend.application.use_cases.turn_models import TurnContext


def stream_turn(
    context: TurnContext,
    ollama: OllamaProtocol,
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
    try:
        messages = build_chat_messages(
            context.story,
            context.text,
            mode=context.mode,
            lore_entries=context.lore_entries,
            recent_pairs=recent_pairs,
            overlap_pairs=overlap_pairs,
        )
        logger.debug("ollama_stream_request model=%s messages=%d", model, len(messages))
        options = MODE_OPTIONS.get(context.mode, DEFAULT_OPTIONS)
        for part in ollama.chat(model=model, messages=messages, stream=True, options=options):
            token = (part.get("message") or {}).get("content", "")
            if token:
                buffer += token
                yield token
        logger.debug("ollama_stream_completed duration_ms=%d", int((time.monotonic() - start) * 1000))
        if context.story and commit and summary_model and summary_max_chars is not None:
            from src.backend.application.summarizer import update_story_summary

            update_story_summary(
                client=ollama,
                model=summary_model,
                story=context.story,
                user_input=format_user_for_summary(context.mode, context.text),
                assistant_text=buffer,
                max_chars=summary_max_chars,
                logger=logger,
            )
            commit()
        else:
            logger.debug("story_summary_skipped no_story_or_commit")
    except Exception as exc:
        logger.exception("ollama_stream_error")
        yield f"\n[Ollama error: {exc}]"
