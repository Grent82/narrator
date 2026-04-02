from src.backend.application.input_formatting import (
    format_input_block,
    format_user_for_summary,
    normalize_mode,
)


def test_normalize_mode_defaults_to_story_for_unknown_value() -> None:
    assert normalize_mode("weird") == "story"
    assert normalize_mode(None) == "story"


def test_format_input_block_normalizes_mode_and_trims_text() -> None:
    assert format_input_block(" SAY ", "  hello there  ") == "MODE: SAY\nTEXT: hello there"


def test_format_user_for_summary_handles_supported_modes() -> None:
    assert format_user_for_summary("say", "Hello") == 'You say: "Hello"'
    assert format_user_for_summary("do", "open the gate") == "You do: open the gate"
    assert format_user_for_summary("continue", "ignored") == ""
    assert format_user_for_summary("story", "A storm rolls in") == "A storm rolls in"

