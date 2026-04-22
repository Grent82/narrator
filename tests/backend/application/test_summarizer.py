from src.backend.application.summarizer import (
    resolve_summary_prompt_key,
    summarize_turn,
    update_story_summary,
)
from src.backend.infrastructure.models import StoryModel


class StubLogger:
    def debug(self, msg: str, *args, **kwargs) -> None:
        return None

    def exception(self, msg: str, *args, **kwargs) -> None:
        return None


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChatModel:
    def __init__(
        self, response_text: str, model: str = "base-model", raise_on_invoke: bool = False
    ) -> None:
        self.response_text = response_text
        self.model = model
        self.raise_on_invoke = raise_on_invoke
        self.invocations: list[str] = []
        self.copies: list[FakeChatModel] = []

    def bind(self, **kwargs):
        return self

    def stream(self, input):
        return iter(())

    def invoke(self, input):
        if self.raise_on_invoke:
            raise RuntimeError("invoke failed")
        self.invocations.append(str(input))
        return FakeResponse(self.response_text)

    def model_copy(self, update: dict):
        copied = FakeChatModel(
            self.response_text,
            model=update.get("model", self.model),
            raise_on_invoke=self.raise_on_invoke,
        )
        self.copies.append(copied)
        return copied


def test_resolve_summary_prompt_key_maps_known_storytellers() -> None:
    assert resolve_summary_prompt_key("neutral_storyteller") == "neutral_summarizer"
    assert resolve_summary_prompt_key("dark_storyteller") == "dark_summarizer"
    assert resolve_summary_prompt_key("unknown") == "neutral"


def test_summarize_turn_returns_previous_summary_when_model_returns_empty_text() -> None:
    model = FakeChatModel("")

    result = summarize_turn(
        client=model,
        model="base-model",
        previous_summary="Existing summary",
        user_input="Open the crypt",
        assistant_text="The crypt opens",
        max_chars=240,
        logger=StubLogger(),
    )

    assert result == "Existing summary"


def test_summarize_turn_rejects_unreasonably_short_regression() -> None:
    model = FakeChatModel("Too short")
    previous = "A long existing summary with enough detail to trigger the minimum-length safeguard."

    result = summarize_turn(
        client=model,
        model="base-model",
        previous_summary=previous,
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
    )

    assert result == previous


def test_summarize_turn_uses_model_copy_when_summary_model_differs() -> None:
    model = FakeChatModel("Updated summary text", model="story-model")

    result = summarize_turn(
        client=model,
        model="summary-model",
        previous_summary="",
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
    )

    assert result == "Updated summary text"
    assert model.invocations == []
    assert len(model.copies) == 1
    assert model.copies[0].model == "summary-model"
    assert len(model.copies[0].invocations) == 1


def test_summarize_turn_uses_neutral_prompt_for_unknown_summary_prompt_key() -> None:
    model = FakeChatModel("Updated summary text")

    summarize_turn(
        client=model,
        model="base-model",
        previous_summary="Existing summary",
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
        summary_prompt_key="unsupported-key",
    )

    prompt = model.invocations[0]
    assert "factual story chronicle" in prompt
    assert "campaign notes" not in prompt


def test_summarize_turn_returns_previous_summary_on_invoke_error() -> None:
    model = FakeChatModel("unused", raise_on_invoke=True)
    previous = "Existing summary"

    result = summarize_turn(
        client=model,
        model="base-model",
        previous_summary=previous,
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
    )

    assert result == previous


def test_update_story_summary_persists_trimmed_summary_on_story() -> None:
    model = FakeChatModel("Updated summary text that is longer than allowed.")
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="neutral_storyteller",
        ai_instructions="Stay grounded.",
        summary_prompt_key="neutral_summarizer",
    )
    story.plot_summary = ""

    updated = update_story_summary(
        client=model,
        model="other-model",
        story=story,
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=20,
        logger=StubLogger(),
    )

    assert updated == "Updated summary text"
    assert story.plot_summary == "Updated summary text"


def test_update_story_summary_uses_storyteller_to_summarizer_mapping_when_key_missing() -> None:
    model = FakeChatModel("Updated summary text")
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="dark_storyteller",
        ai_instructions="Stay grounded.",
        summary_prompt_key="",
    )
    story.plot_summary = "Previous summary"

    update_story_summary(
        client=model,
        model="base-model",
        story=story,
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
    )

    prompt = model.invocations[0]
    assert "campaign notes" in prompt


def test_dark_summary_prompt_requests_plain_factual_chronicle() -> None:
    model = FakeChatModel("Updated summary text")

    summarize_turn(
        client=model,
        model="base-model",
        previous_summary="An overly dramatic prior summary.",
        user_input="Advance",
        assistant_text="New events occur",
        max_chars=240,
        logger=StubLogger(),
        summary_prompt_key="dark_summarizer",
    )

    prompt = model.invocations[0]
    assert "campaign notes" in prompt
    assert "Do not mimic the narrator's voice" in prompt
    assert "Do not end with dramatic closing lines." in prompt
