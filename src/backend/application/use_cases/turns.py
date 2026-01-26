from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from src.backend.application.ports import LoggerProtocol, OllamaProtocol

from src.backend.application.input_formatting import normalize_mode
from src.backend.application.turn_service import stream_turn
from src.backend.application.use_cases.turn_models import TurnContext, TurnPayload
from src.backend.application.use_cases.lore import LoreRepository
from src.backend.application.use_cases.stories import StoryRepository

DEFAULT_CONTINUE_PROMPT = "Continue the story from the most recent assistant output. Do not repeat."


@dataclass(frozen=True)
class TurnSettings:
    model: str
    summary_model: str
    summary_max_chars: int


class TurnUseCase:
    def __init__(self, settings: TurnSettings, logger: LoggerProtocol) -> None:
        self._settings = settings
        self._logger = logger

    def _get_last_message_text(self, story, role: str = "assistant") -> str:
        if not story or not story.messages:
            return ""
        for msg in reversed(story.messages):
            if msg.role != role:
                continue
            text = (msg.text or "").strip()
            if text:
                return text
        return ""

    def _prepare_context(
        self,
        payload: TurnPayload,
        story_repo: StoryRepository,
        lore_repo: LoreRepository,
        ollama: OllamaProtocol,
    ) -> TurnContext:
        text = payload.text if payload.text is not None else (payload.trigger or "")
        mode = normalize_mode(payload.mode)
        story = None
        lore_entries = None
        if payload.story_id:
            story = story_repo.get_story(payload.story_id)
            if not story:
                raise ValueError("Story not found")
            if mode == "continue" and not text.strip():
                last_assistant = self._get_last_message_text(story, role="assistant")
                text = last_assistant or DEFAULT_CONTINUE_PROMPT
            if mode == "continue" and story.ollama_context:
                lore_entries = []
            else:
                retrieval_query = "" if mode == "continue" else text
                lore_entries = lore_repo.retrieve(story.id, retrieval_query, ollama)
        elif mode == "continue" and not text.strip():
            text = DEFAULT_CONTINUE_PROMPT
        return TurnContext(text=text, mode=mode, story=story, lore_entries=lore_entries)

    def run_stream(
        self,
        payload: TurnPayload,
        story_repo: StoryRepository,
        lore_repo: LoreRepository,
        ollama: OllamaProtocol,
    ) -> Iterator[str]:
        context = self._prepare_context(payload, story_repo, lore_repo, ollama)
        self._logger.debug("turn_stream_received trigger_len=%d mode=%s", len(context.text), context.mode)
        return stream_turn(
            context,
            ollama,
            self._settings.model,
            self._logger,
            commit=story_repo.commit,
            summary_model=self._settings.summary_model,
            summary_max_chars=self._settings.summary_max_chars,
        )
