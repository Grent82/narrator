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
