"""Tests for provider-specific prompt strategies."""

from __future__ import annotations

import pytest

from langchain_core.messages import HumanMessage, SystemMessage

from src.backend.application.prompt_strategies.base import PromptContext
from src.backend.application.prompt_strategies.claude import ClaudePromptStrategy
from src.backend.application.prompt_strategies.factory import (
    detect_provider_from_model_name,
    get_prompt_strategy,
)
from src.backend.application.prompt_strategies.llama import LlamaPromptStrategy
from src.backend.application.prompt_strategies.qwen import QwenPromptStrategy
from src.backend.application.size_tier import get_size_profile


class TestDetectProviderFromModelName:
    """Tests for provider detection from model names."""

    def test_detect_claude(self):
        assert detect_provider_from_model_name("anthropic/claude-sonnet") == "anthropic"
        assert detect_provider_from_model_name("claude-3.5-sonnet") == "anthropic"

    def test_detect_qwen(self):
        assert detect_provider_from_model_name("qwen/qwen-2.5") == "qwen"
        assert detect_provider_from_model_name("qwen-3.5-122b") == "qwen"

    def test_detect_ollama(self):
        assert detect_provider_from_model_name("dolphin-llama3:8b") == "ollama"
        assert detect_provider_from_model_name("llama3.2:3b") == "ollama"

    def test_detect_mistral(self):
        assert detect_provider_from_model_name("mistral-7b") == "ollama"


class TestClaudePromptStrategy:
    """Tests for Claude XML-based strategy."""

    def test_provider_name(self):
        strategy = ClaudePromptStrategy()
        assert strategy.provider_name == "anthropic"

    def test_build_system_prompt_xml_structure(self):
        strategy = ClaudePromptStrategy()
        context = PromptContext(
            ai_instructions="Be concise.",
            plot_summary="The party entered the forest.",
            mode="story",
            model_name="anthropic/claude-sonnet",
        )

        prompt = strategy.build_system_prompt(context)

        assert "<ai_instructions>" in prompt
        assert "</ai_instructions>" in prompt
        assert "<plot_summary>" in prompt
        assert "</plot_summary>" in prompt

    def test_build_messages_includes_system(self):
        strategy = ClaudePromptStrategy()
        context = PromptContext(
            ai_instructions="Test instructions",
            user_text="I open the door",
            mode="story",
            model_name="anthropic/claude-sonnet",
        )

        messages = strategy.build_messages(context)

        assert len(messages) >= 1
        assert isinstance(messages[0], SystemMessage)

    def test_small_model_gets_cot_in_xml(self):
        strategy = ClaudePromptStrategy(size_profile=get_size_profile("llama3.2:3b"))
        context = PromptContext(
            mode="story",
            model_name="llama3.2:3b",
            user_text="Test",
        )

        prompt = strategy.build_system_prompt(context)

        assert "<thinking>" in prompt or "thinking" in prompt.lower()


class TestQwenPromptStrategy:
    """Tests for Qwen Markdown-based strategy."""

    def test_provider_name(self):
        strategy = QwenPromptStrategy()
        assert strategy.provider_name == "qwen"

    def test_build_system_prompt_markdown_structure(self):
        strategy = QwenPromptStrategy()
        context = PromptContext(
            ai_instructions="Be concise.",
            plot_summary="The party entered the forest.",
            mode="story",
            model_name="qwen/qwen-2.5",
        )

        prompt = strategy.build_system_prompt(context)

        assert "# Role" in prompt
        assert "## AI Instructions" in prompt
        assert "## Plot Summary" in prompt

    def test_build_messages_includes_system(self):
        strategy = QwenPromptStrategy()
        context = PromptContext(
            ai_instructions="Test instructions",
            user_text="I open the door",
            mode="story",
            model_name="qwen/qwen-2.5",
        )

        messages = strategy.build_messages(context)

        assert len(messages) >= 1
        assert isinstance(messages[0], SystemMessage)

    def test_small_model_gets_step_by_step(self):
        strategy = QwenPromptStrategy(size_profile=get_size_profile("qwen-7b"))
        context = PromptContext(
            mode="story",
            model_name="qwen-7b",
            user_text="Test",
        )

        prompt = strategy.build_system_prompt(context)

        assert "Step-by-Step" in prompt or "Thinking" in prompt


class TestLlamaPromptStrategy:
    """Tests for Llama/Dolphin Markdown-based strategy."""

    def test_provider_name(self):
        strategy = LlamaPromptStrategy()
        assert strategy.provider_name == "ollama"

    def test_build_system_prompt_markdown_structure(self):
        strategy = LlamaPromptStrategy()
        context = PromptContext(
            ai_instructions="Be concise.",
            plot_summary="The party entered the forest.",
            mode="story",
            model_name="dolphin-llama3:8b",
        )

        prompt = strategy.build_system_prompt(context)

        assert "# Role" in prompt
        assert "## AI Instructions" in prompt
        assert "## Current StoryState" in prompt or "## Plot Summary" in prompt

    def test_build_messages_includes_system(self):
        strategy = LlamaPromptStrategy()
        context = PromptContext(
            ai_instructions="Test instructions",
            user_text="I open the door",
            mode="story",
            model_name="dolphin-llama3:8b",
        )

        messages = strategy.build_messages(context)

        assert len(messages) >= 1
        assert isinstance(messages[0], SystemMessage)

    def test_small_model_gets_thinking_steps(self):
        strategy = LlamaPromptStrategy(size_profile=get_size_profile("llama3.2:3b"))
        context = PromptContext(
            mode="story",
            model_name="llama3.2:3b",
            user_text="Test",
        )

        prompt = strategy.build_system_prompt(context)

        assert "Thinking" in prompt or "thinking" in prompt
        assert "CRITICAL" in prompt or "WARNING" in prompt  # Repetition prevention

    def test_repetition_prevention_for_small_models(self):
        strategy = LlamaPromptStrategy()
        context = PromptContext(
            mode="story",
            model_name="dolphin-llama3:8b",
            user_text="Test",
        )

        prompt = strategy.build_system_prompt(context)

        # Small models should get repetition prevention guidance
        assert "Repetition" in prompt or "repeat" in prompt.lower()


class TestGetPromptStrategy:
    """Tests for the strategy factory."""

    def test_get_claude_strategy(self):
        strategy = get_prompt_strategy("anthropic/claude-sonnet")
        assert isinstance(strategy, ClaudePromptStrategy)

    def test_get_qwen_strategy(self):
        strategy = get_prompt_strategy("qwen/qwen-2.5")
        assert isinstance(strategy, QwenPromptStrategy)

    def test_get_ollama_strategy(self):
        strategy = get_prompt_strategy("dolphin-llama3:8b")
        assert isinstance(strategy, LlamaPromptStrategy)

    def test_get_llama_strategy(self):
        strategy = get_prompt_strategy("llama3.2:3b")
        assert isinstance(strategy, LlamaPromptStrategy)

    def test_default_to_llama(self):
        strategy = get_prompt_strategy("unknown-model")
        assert isinstance(strategy, LlamaPromptStrategy)

    def test_explicit_provider_override(self):
        strategy = get_prompt_strategy("some-model", provider="qwen")
        assert isinstance(strategy, QwenPromptStrategy)


class TestPromptContext:
    """Tests for PromptContext dataclass."""

    def test_context_creation(self):
        context = PromptContext(
            ai_instructions="Test",
            plot_summary="Summary",
            plot_essentials="Essentials",
            author_note="Note",
            mode="story",
            model_name="test-model",
            user_text="Hello",
        )

        assert context.ai_instructions == "Test"
        assert context.plot_summary == "Summary"
        assert context.mode == "story"
        assert context.user_text == "Hello"

    def test_context_defaults(self):
        context = PromptContext()

        assert context.ai_instructions is None
        assert context.plot_summary is None
        assert context.mode == "story"
        assert context.user_text == ""
