from types import SimpleNamespace

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.backend.application.prompt_builder import build_chat_messages, build_system_prompt
from src.backend.infrastructure.models import StoryMessageModel, StoryModel


class StubLogger:
    def debug(self, msg: str, *args, **kwargs) -> None:
        return None

    def exception(self, msg: str, *args, **kwargs) -> None:
        return None


def test_build_system_prompt_skips_player_lore_and_includes_relevant_sections() -> None:
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="neutral_storyteller",
        ai_instructions="Stay grounded.",
        plot_essentials="The relic matters.",
        author_note="Keep tension high.",
    )
    story.plot_summary = "The party entered the crypt."

    lore_entries = [
        Document(
            page_content="The player is a wanderer.",
            metadata={"title": "Hero", "tag": "Player", "description": "The player is a wanderer."},
        ),
        Document(
            page_content="A cursed relic hidden below the abbey.",
            metadata={
                "title": "Abbey Relic",
                "tag": "Artifact",
                "description": "A cursed relic hidden below the abbey.",
            },
        ),
    ]

    prompt = build_system_prompt(story, lore_entries=lore_entries, logger=StubLogger())

    assert "[AI INSTRUCTIONS]\nStay grounded." in prompt
    assert "[PLOT SUMMARY]\nThe party entered the crypt." in prompt
    assert "[PLOT ESSENTIALS]\nThe relic matters." in prompt
    assert "[AUTHOR NOTE]\nKeep tension high." in prompt
    assert "* Artifact - A cursed relic hidden below the abbey." in prompt
    assert "The player is a wanderer." not in prompt


def test_build_system_prompt_includes_model_profile_guidance() -> None:
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="neutral_storyteller",
        ai_instructions="Stay grounded.",
    )

    prompt = build_system_prompt(story, mode="continue", model_profile_id="local_small_instruct")

    assert "[MODEL-SPECIFIC GUIDANCE]" in prompt
    assert "Do not repeat, paraphrase, restart, or summarize prior text." in prompt
    assert "Do not copy sentence structure from recent assistant messages." in prompt


def test_build_chat_messages_keeps_recent_pairs_and_formats_user_turns() -> None:
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="neutral_storyteller",
        ai_instructions="Stay grounded.",
    )
    story.messages = [
        StoryMessageModel(role="user", text="older say", mode="say", position=0),
        StoryMessageModel(role="assistant", text="older answer", position=1),
        StoryMessageModel(role="user", text="latest do", mode="do", position=2),
        StoryMessageModel(role="assistant", text="latest answer", position=3),
    ]

    messages = build_chat_messages(story, user_text="current action", mode="story", recent_pairs=1)

    assert isinstance(messages[0], SystemMessage)
    assert len(messages) == 4
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "MODE: DO\nTEXT: latest do"
    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "latest answer"
    assert isinstance(messages[3], HumanMessage)
    assert messages[3].content == "MODE: STORY\nTEXT: current action"


def test_build_system_prompt_skips_lore_covered_by_plot_essentials_title_or_trigger() -> None:
    story = StoryModel(
        title="Test Story",
        ai_instruction_key="neutral_storyteller",
        ai_instructions="Stay grounded.",
        plot_essentials="The Relic of Ashes and the black bell must not be repeated.",
    )
    lore_entries = [
        Document(
            page_content="Relic details.",
            metadata={
                "title": "Relic of Ashes",
                "tag": "Artifact",
                "description": "Relic details.",
            },
        ),
        Document(
            page_content="Bell details.",
            metadata={
                "title": "Bell Keepers",
                "tag": "Faction",
                "description": "Bell details.",
                "triggers": "black bell,abbey toll",
            },
        ),
        Document(
            page_content="A narrow bridge over a chasm.",
            metadata={
                "title": "Bridge",
                "tag": "Place",
                "description": "A narrow bridge over a chasm.",
            },
        ),
    ]

    prompt = build_system_prompt(story, lore_entries=lore_entries, logger=StubLogger())

    assert "* Place - A narrow bridge over a chasm." in prompt
    assert "Relic details." not in prompt
    assert "Bell details." not in prompt


def test_build_chat_messages_supports_dict_history_and_overlap_window() -> None:
    story = SimpleNamespace(
        ai_instructions="Stay grounded.",
        plot_summary="",
        plot_essentials="",
        author_note="",
        lore_entries=[],
        messages=[
            {"role": "user", "text": "u1", "mode": "say"},
            {"role": "assistant", "text": "a1"},
            {"role": "system", "text": "ignore me"},
            {"role": "assistant", "text": "   "},
            {"role": "user", "text": "u2", "mode": "do"},
            {"role": "assistant", "text": "a2"},
            {"role": "user", "text": "u3", "mode": "story"},
            {"role": "assistant", "text": "a3"},
        ],
    )

    messages = build_chat_messages(
        story,
        user_text="now",
        mode="story",
        recent_pairs=1,
        overlap_pairs=1,
    )

    assert isinstance(messages[0], SystemMessage)
    assert [m.content for m in messages[1:]] == [
        "MODE: DO\nTEXT: u2",
        "a2",
        "MODE: STORY\nTEXT: u3",
        "a3",
        "MODE: STORY\nTEXT: now",
    ]


def test_build_chat_messages_without_story_adds_only_current_user_message() -> None:
    messages = build_chat_messages(None, user_text="open gate", mode="do")

    assert len(messages) == 1
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "MODE: DO\nTEXT: open gate"
