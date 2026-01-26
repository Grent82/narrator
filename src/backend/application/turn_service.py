from __future__ import annotations

import time
from typing import Callable, Iterator

from src.backend.application.ports import LoggerProtocol, OllamaProtocol

from src.backend.application.input_formatting import format_user_for_summary
from src.backend.application.prompt_builder import build_prompt
from src.backend.application.use_cases.turn_models import TurnContext


def _build_prompt_and_context(context: TurnContext) -> tuple[str, list[int] | None]:
    if context.story:
        prompt = build_prompt(context.story, context.text, mode=context.mode, lore_entries=context.lore_entries)
        ollama_context = context.story.ollama_context if context.story.ollama_context else None
    else:
        prompt = context.text
        ollama_context = None
    return prompt, ollama_context


def stream_turn(
    context: TurnContext,
    ollama: OllamaProtocol,
    model: str,
    logger: LoggerProtocol,
    commit: Callable[[], None] | None = None,
    summary_model: str | None = None,
    summary_max_chars: int | None = None,
) -> Iterator[str]:
    start = time.monotonic()
    buffer = ""
    last_meta = {}
    try:
        prompt, ollama_context = _build_prompt_and_context(context)
        logger.debug("ollama_stream_request prompt=%s", prompt)
        logger.debug("ollama_stream_request model=%s prompt_len=%d", model, len(prompt))
        for part in ollama.generate(model=model, prompt=prompt, stream=True, context=ollama_context):
            token = part.get("response", "")
            last_meta = part or last_meta
            if token:
                buffer += token
                yield token
        logger.debug("ollama_stream_completed duration_ms=%d", int((time.monotonic() - start) * 1000))
        if context.story and last_meta.get("context"):
            context.story.ollama_context = last_meta.get("context")
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
