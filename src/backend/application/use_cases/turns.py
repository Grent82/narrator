from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from src.backend.application.ports import ChatModelProtocol, LoggerProtocol

from src.backend.application.input_formatting import normalize_mode
from src.backend.application.turn_service import stream_turn
from src.backend.application.use_cases.turn_models import TurnContext, TurnPayload
from src.backend.application.use_cases.lore import LoreRepository
from src.backend.application.use_cases.stories import StoryRepository


@dataclass(frozen=True)
class TurnSettings:
    model: str
    summary_model: str
    summary_max_chars: int
    recent_pairs: int = 3
    overlap_pairs: int = 0


class TurnUseCase:
    def __init__(self, settings: TurnSettings, logger: LoggerProtocol) -> None:
        self._settings = settings
        self._logger = logger

    def _prepare_context(
        self,
        payload: TurnPayload,
        story_repo: StoryRepository,
        lore_repo: LoreRepository,
    ) -> TurnContext:
        text = payload.text if payload.text is not None else (payload.trigger or "")
        mode = normalize_mode(payload.mode)
        story = None
        lore_entries = None
        if payload.story_id:
            story = story_repo.get_story(payload.story_id)
            if not story:
                raise ValueError("Story not found")
            retrieval_query = "" if mode == "continue" else text
            lore_entries = lore_repo.retrieve(story.id, retrieval_query)
        return TurnContext(text=text, mode=mode, story=story, lore_entries=lore_entries)

    def run_stream(
        self,
        payload: TurnPayload,
        story_repo: StoryRepository,
        lore_repo: LoreRepository,
        chat_model: ChatModelProtocol,
    ) -> Iterator[str]:
        context = self._prepare_context(payload, story_repo, lore_repo)
        return stream_turn(
            context,
            chat_model,
            self._settings.model,
            self._logger,
            commit=story_repo.commit,
            summary_model=self._settings.summary_model,
            summary_max_chars=self._settings.summary_max_chars,
            recent_pairs=self._settings.recent_pairs,
            overlap_pairs=self._settings.overlap_pairs,
        )
