"""Tests for model size tier detection and configuration."""

from __future__ import annotations

import pytest

from src.backend.application.size_tier import (
    SIZE_PROFILES,
    extract_size_from_name,
    get_cot_instructions,
    get_repetition_prevention_guidance,
    get_size_profile,
    infer_size_tier,
)


class TestExtractSizeFromName:
    """Tests for size extraction from model names."""

    def test_extract_8b(self):
        assert extract_size_from_name("dolphin-llama3:8b") == 8

    def test_extract_7b(self):
        assert extract_size_from_name("llama3.1-7b") == 7

    def test_extract_70b(self):
        assert extract_size_from_name("llama3:70b") == 70

    def test_extract_122b(self):
        assert extract_size_from_name("qwen-3.5-122b") == 122

    def test_extract_14b(self):
        assert extract_size_from_name("mistral-14b-v0.1") == 14

    def test_extract_unknown(self):
        assert extract_size_from_name("some-unknown-model") is None

    def test_extract_with_decimal(self):
        assert extract_size_from_name("model-3.5b") == 3


class TestInferSizeTier:
    """Tests for size tier inference."""

    def test_tiny_3b(self):
        # 3b is detected via numeric extraction (3 < 4)
        assert infer_size_tier("llama3.2:3b") == "tiny"

    def test_tiny_1b(self):
        assert infer_size_tier("model-1b") == "tiny"

    def test_small_7b(self):
        assert infer_size_tier("dolphin-llama3:8b") == "small"

    def test_small_14b(self):
        assert infer_size_tier("llama3:14b") == "small"

    def test_medium_27b(self):
        assert infer_size_tier("mistral-27b") == "medium"

    def test_medium_32b(self):
        assert infer_size_tier("qwen-32b") == "medium"

    def test_large_70b(self):
        assert infer_size_tier("llama3:70b") == "large"

    def test_large_72b(self):
        assert infer_size_tier("qwen-72b") == "large"

    def test_massive_120b(self):
        # qwen-3.5-122b should extract 122 (largest number), not 3.5
        assert infer_size_tier("qwen-3.5-122b") == "massive"

    def test_massive_405b(self):
        assert infer_size_tier("llama405b") == "massive"

    def test_unknown_defaults_to_medium(self):
        assert infer_size_tier("unknown-model") == "medium"


class TestGetSizeProfile:
    """Tests for size profile retrieval."""

    def test_small_model_profile(self):
        profile = get_size_profile("dolphin-llama3:8b")
        assert profile.tier == "small"
        assert profile.require_cot is True
        assert profile.repetition_risk == "high"

    def test_massive_model_profile(self):
        profile = get_size_profile("qwen-3.5-122b")
        assert profile.tier == "massive"
        assert profile.require_cot is False
        assert profile.repetition_risk == "low"

    def test_none_defaults_to_medium(self):
        profile = get_size_profile(None)
        assert profile.tier == "medium"


class TestGetCotInstructions:
    """Tests for Chain-of-Thought instruction generation."""

    def test_small_model_gets_cot(self):
        instructions = get_cot_instructions("dolphin-llama3:8b", "story")
        assert instructions is not None
        assert len(instructions) > 0
        assert "step-by-step" in instructions.lower() or "thinking" in instructions.lower()

    def test_massive_model_no_cot(self):
        instructions = get_cot_instructions("qwen-3.5-122b", "story")
        assert instructions == ""

    def test_none_model_no_cot(self):
        instructions = get_cot_instructions(None, "story")
        assert instructions == ""

    def test_continue_mode_cot(self):
        instructions = get_cot_instructions("llama3.2:3b", "continue")
        assert instructions is not None
        assert len(instructions) > 0


class TestGetRepetitionPreventionGuidance:
    """Tests for repetition prevention guidance."""

    def test_tiny_model_gets_strong_prevention(self):
        guidance = get_repetition_prevention_guidance("llama3.2:3b")
        assert guidance is not None
        assert len(guidance) > 0
        assert "CRITICAL" in guidance or "WARNING" in guidance

    def test_small_model_gets_prevention(self):
        guidance = get_repetition_prevention_guidance("dolphin-llama3:8b")
        assert guidance is not None
        assert len(guidance) > 0

    def test_large_model_no_prevention(self):
        guidance = get_repetition_prevention_guidance("llama3:70b")
        assert guidance == ""

    def test_none_model_no_prevention(self):
        guidance = get_repetition_prevention_guidance(None)
        assert guidance == ""


class TestSizeProfileProperties:
    """Tests for size profile property values."""

    def test_tiny_profile(self):
        profile = SIZE_PROFILES["tiny"]
        assert profile.verbosity == "compact"
        assert profile.require_cot is True
        assert profile.cot_style == "explicit_tags"
        assert profile.include_few_shot is True

    def test_small_profile(self):
        profile = SIZE_PROFILES["small"]
        assert profile.verbosity == "balanced"
        assert profile.require_cot is True
        assert profile.cot_style == "implicit"
        assert profile.include_few_shot is True

    def test_medium_profile(self):
        profile = SIZE_PROFILES["medium"]
        assert profile.verbosity == "balanced"
        assert profile.require_cot is False
        assert profile.cot_style == "implicit"
        assert profile.include_few_shot is False

    def test_large_profile(self):
        profile = SIZE_PROFILES["large"]
        assert profile.verbosity == "detailed"
        assert profile.require_cot is False
        assert profile.cot_style == "none"
        assert profile.include_few_shot is False

    def test_massive_profile(self):
        profile = SIZE_PROFILES["massive"]
        assert profile.verbosity == "elaborate"
        assert profile.require_cot is False
        assert profile.use_tot is True
        assert profile.structured_output_strength == "native"
