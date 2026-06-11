"""Model size tier detection and configuration.

This module provides automatic detection of model size tiers based on
model names and defines size-dependent prompt behaviors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

SizeTier = Literal["tiny", "small", "medium", "large", "massive"]

# Size thresholds in billions of parameters
# Note: Ranges are [min, max), so small includes 4B up to but not including 14B
SIZE_THRESHOLDS: dict[SizeTier, tuple[int, int]] = {
    "tiny": (0, 4),      # < 4B
    "small": (4, 16),    # 4B - 16B (includes 7B, 8B, 14B)
    "medium": (16, 40),  # 16B - 40B
    "large": (40, 100),  # 40B - 100B
    "massive": (100, 999999),  # > 100B
}

# Token patterns for size detection in model names
# Note: These are checked in order, so more specific patterns should come first
SIZE_TOKENS: dict[SizeTier, list[str]] = {
    "tiny": ["1.5b", "1b", "0.5b", ":3b", "3b"],  # 3b can be ambiguous (llama3.2:3b)
    "small": ["7b", "8b", "9b", "10b", "12b", "14b"],
    "medium": ["20b", "22b", "27b", "30b", "32b", "35b", "40b"],
    "large": ["50b", "55b", "60b", "65b", "70b", "72b", "80b", "90b", "100b"],
    "massive": ["405b", "200b", "180b", "150b", "140b", "130b", "123b", "122b", "120b", "110b"],
}


@dataclass(frozen=True)
class SizeProfile:
    """Profile for a size tier defining prompt behavior."""
    tier: SizeTier
    # Verbosity level for prompts
    verbosity: Literal["compact", "balanced", "detailed", "elaborate"]
    # Whether to require explicit chain-of-thought
    require_cot: bool
    # CoT style: none, implicit (step-by-step text), explicit (thinking tags)
    cot_style: Literal["none", "implicit", "explicit_tags"]
    # Whether to use tree-of-thought for complex tasks
    use_tot: bool
    # Structured output capability
    structured_output_strength: Literal["weak", "medium", "strong", "native"]
    # Repetition risk level
    repetition_risk: Literal["very_high", "high", "medium", "low"]
    # Guidance density (instructions per prompt section)
    guidance_density: Literal["minimal", "moderate", "dense", "comprehensive"]
    # Whether to include few-shot examples
    include_few_shot: bool
    # Token budget for system prompt (percentage of context)
    system_prompt_budget_pct: float


SIZE_PROFILES: dict[SizeTier, SizeProfile] = {
    "tiny": SizeProfile(
        tier="tiny",
        verbosity="compact",
        require_cot=True,
        cot_style="explicit_tags",
        use_tot=False,
        structured_output_strength="weak",
        repetition_risk="very_high",
        guidance_density="dense",
        include_few_shot=True,
        system_prompt_budget_pct=0.15,
    ),
    "small": SizeProfile(
        tier="small",
        verbosity="balanced",
        require_cot=True,
        cot_style="implicit",
        use_tot=False,
        structured_output_strength="medium",
        repetition_risk="high",
        guidance_density="dense",
        include_few_shot=True,
        system_prompt_budget_pct=0.20,
    ),
    "medium": SizeProfile(
        tier="medium",
        verbosity="balanced",
        require_cot=False,
        cot_style="implicit",
        use_tot=False,
        structured_output_strength="strong",
        repetition_risk="medium",
        guidance_density="moderate",
        include_few_shot=False,
        system_prompt_budget_pct=0.25,
    ),
    "large": SizeProfile(
        tier="large",
        verbosity="detailed",
        require_cot=False,
        cot_style="none",
        use_tot=False,
        structured_output_strength="strong",
        repetition_risk="low",
        guidance_density="moderate",
        include_few_shot=False,
        system_prompt_budget_pct=0.30,
    ),
    "massive": SizeProfile(
        tier="massive",
        verbosity="elaborate",
        require_cot=False,
        cot_style="none",
        use_tot=True,
        structured_output_strength="native",
        repetition_risk="low",
        guidance_density="minimal",
        include_few_shot=False,
        system_prompt_budget_pct=0.35,
    ),
}


def extract_size_from_name(model_name: str) -> int | None:
    """Extract parameter count from model name.

    Examples:
        "dolphin-llama3:8b" -> 8
        "qwen-3.5-122b" -> 122
        "mistral-7b-v0.3" -> 7

    Note: Returns the largest number followed by 'b', as version numbers
    (like 3.5) are typically smaller than parameter counts.
    """
    # Pattern to match numbers followed by 'b' (e.g., 7b, 14b, 70b, 122b)
    pattern = r"(\d+(?:\.\d+)?)\s*b\b"
    matches = re.findall(pattern, model_name.lower())
    if not matches:
        return None
    # Return the largest match, as version numbers are typically smaller
    # than parameter counts (e.g., qwen-3.5-122b -> 122, not 3.5)
    return int(float(max(matches, key=lambda x: float(x))))


def infer_size_tier(model_name: str) -> SizeTier:
    """Infer size tier from model name.

    Args:
        model_name: The model identifier (e.g., "dolphin-llama3:8b")

    Returns:
        The inferred size tier
    """
    # First, try numeric extraction (most reliable for models like qwen-3.5-122b)
    size = extract_size_from_name(model_name)
    if size is not None:
        for tier, (min_size, max_size) in SIZE_THRESHOLDS.items():
            if min_size <= size < max_size:
                return tier

    # Fall back to explicit token matching for edge cases
    normalized = model_name.lower()
    for tier, tokens in SIZE_TOKENS.items():
        for token in tokens:
            if token in normalized:
                return tier

    # Default to medium if undetectable
    return "medium"


def get_size_profile(model_name: str | None) -> SizeProfile:
    """Get size profile for a model.

    Args:
        model_name: The model identifier

    Returns:
        The SizeProfile for the model's size tier
    """
    if not model_name:
        return SIZE_PROFILES["medium"]

    tier = infer_size_tier(model_name)
    return SIZE_PROFILES[tier]


def get_cot_instructions(model_name: str | None, mode: str = "story") -> str:
    """Get Chain-of-Thought instructions for a model.

    Args:
        model_name: The model identifier
        mode: The operation mode (story, continue, say, do)

    Returns:
        CoT guidance text to append to prompts
    """
    if not model_name:
        return ""

    profile = get_size_profile(model_name)

    if profile.cot_style == "none":
        return ""

    if profile.cot_style == "explicit_tags":
        if mode == "continue":
            return (
                "\n\n<guidance>\n"
                "Before writing your response, think through the continuation carefully:\n"
                "1. Analyze the exact endpoint of the last assistant message\n"
                "2. Consider what naturally follows without repeating\n"
                "3. Plan your opening sentence to match seamlessly\n"
                "</guidance>\n"
                "\n"
                "Use <thinking> tags to work through your reasoning before answering.\n"
            )
        return (
            "\n\n<guidance>\n"
            "Before responding, think through the story progression:\n"
            "1. Review the current situation and character state\n"
            "2. Consider the consequences of the player's action\n"
            "3. Plan the next story beat with concrete details\n"
            "</guidance>\n"
            "\n"
            "Use <thinking> tags to work through your reasoning before answering.\n"
        )

    # implicit style
    if mode == "continue":
        return (
            "\n\n<guidance>\n"
            "Think step-by-step before writing:\n"
            "- What is the exact endpoint of the last response?\n"
            "- What is the immediate next beat that follows?\n"
            "- How do you continue without repeating or restating?\n"
            "Write your reasoning, then provide the continuation.\n"
            "</guidance>\n"
        )
    return (
        "\n\n<guidance>\n"
        "Think step-by-step before responding:\n"
        "- What is the current situation?\n"
        "- What does the player's action trigger?\n"
        "- What is the most interesting but logical next beat?\n"
        "Write your reasoning, then provide the story response.\n"
        "</guidance>\n"
    )


def get_structured_output_guidance(model_name: str | None, output_format: str) -> str:
    """Get structured output guidance for a model.

    Args:
        model_name: The model identifier
        output_format: Description of expected output format

    Returns:
        Guidance text for producing structured output
    """
    if not model_name:
        return ""

    profile = get_size_profile(model_name)

    if profile.structured_output_strength == "native":
        return f"Output must be valid {output_format}. The API enforces structure."

    if profile.structured_output_strength == "strong":
        return (
            f"You MUST output only valid {output_format}. "
            "No explanations, no markdown fences, no extra text. "
            "Validate your output before sending."
        )

    if profile.structured_output_strength == "medium":
        return (
            f"Output format: {output_format}\n"
            "Be strict about the format. Avoid extra text or explanations."
        )

    # weak
    return f"Try to follow this format: {output_format}"


def get_repetition_prevention_guidance(model_name: str | None) -> str:
    """Get repetition prevention guidance for a model.

    Args:
        model_name: The model identifier

    Returns:
        Guidance text for preventing repetition
    """
    if not model_name:
        return ""

    profile = get_size_profile(model_name)

    if profile.repetition_risk == "very_high":
        return (
            "\n\n<repetition-prevention>\n"
            "CRITICAL: You tend to repeat yourself. Follow these rules strictly:\n"
            "- Do NOT copy any sentences from previous assistant messages\n"
            "- Do NOT rephrase or paraphrase prior text\n"
            "- Do NOT restart scenes or reset character states\n"
            "- Do NOT use similar closing lines repeatedly\n"
            "- Each response must add NEW content, not restate old content\n"
            "- If you catch yourself repeating, STOP and rewrite\n"
            "</repetition-prevention>\n"
        )

    if profile.repetition_risk == "high":
        return (
            "\n\n<guidance>\n"
            "Avoid repetition:\n"
            "- Do not copy sentence structure from recent messages\n"
            "- Do not restate prior text; only add new content\n"
            "- Vary your vocabulary and phrasing\n"
            "</guidance>\n"
        )

    if profile.repetition_risk == "medium":
        return (
            "\n\n<guidance>\n"
            "Be mindful of repetition:\n"
            "- Add new content rather than restating\n"
            "- Vary your phrasing\n"
            "</guidance>\n"
        )

    return ""  # low risk - no special guidance needed
