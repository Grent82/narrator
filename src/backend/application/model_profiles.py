from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Provider = Literal["ollama", "openai_compatible", "anthropic", "gemini"]
PromptVerbosity = Literal["compact", "balanced", "detailed"]
StructuredOutputStrength = Literal["weak", "medium", "strong"]
RepetitionRisk = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ModelClassProfile:
    id: str
    label: str
    prompt_verbosity: PromptVerbosity
    structured_output_strength: StructuredOutputStrength
    repetition_risk: RepetitionRisk
    max_effective_context: int
    story_turn_guidance: tuple[str, ...]
    continue_guidance: tuple[str, ...]
    summary_guidance: tuple[str, ...]


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: Provider
    model: str
    profile_id: str
    label: str
    max_context: int | None = None
    cost_tier: str = "local"
    supports_json_mode: bool = False
    supports_tools: bool = False


MODEL_CLASS_PROFILES: dict[str, ModelClassProfile] = {
    "local_small_instruct": ModelClassProfile(
        id="local_small_instruct",
        label="Local small instruct model",
        prompt_verbosity="compact",
        structured_output_strength="medium",
        repetition_risk="high",
        max_effective_context=4096,
        story_turn_guidance=(
            "Use the existing facts as constraints, not as text to repeat.",
            "Advance at least one concrete state, threat, decision, discovery, or consequence.",
            "Avoid teaser endings and repeated dramatic closing lines.",
        ),
        continue_guidance=(
            "Continue directly after the last assistant message.",
            "Do not repeat, paraphrase, restart, or summarize prior text.",
            "Write only new narrative progression.",
        ),
        summary_guidance=(
            "Use plain factual campaign-note prose.",
            "Remove narrator style, sensory flourish, and dramatic closing lines.",
            "Prefer chronology and stable facts over atmosphere.",
        ),
    ),
    "balanced_reasoning": ModelClassProfile(
        id="balanced_reasoning",
        label="Balanced hosted reasoning/chat model",
        prompt_verbosity="balanced",
        structured_output_strength="strong",
        repetition_risk="medium",
        max_effective_context=32000,
        story_turn_guidance=(
            "Preserve story state, character intent, and consequences.",
            "Advance the current scene without contradicting summary, lore, or recent turns.",
            "Keep tone consistent while avoiding repetitive phrasing.",
        ),
        continue_guidance=(
            "Continue from the precise endpoint of the latest assistant message.",
            "Do not restate existing paragraphs; add the next beat of action or consequence.",
        ),
        summary_guidance=(
            "Maintain concise third-person campaign notes.",
            "Separate durable facts from scene-level prose.",
        ),
    ),
    "reasoning_strong": ModelClassProfile(
        id="reasoning_strong",
        label="Large high-reasoning hosted model",
        prompt_verbosity="detailed",
        structured_output_strength="strong",
        repetition_risk="low",
        max_effective_context=128000,
        story_turn_guidance=(
            "Track explicit and implied consequences from the provided context.",
            "Respect all established state and character constraints.",
            "Move the scene forward with concrete causal progression.",
        ),
        continue_guidance=(
            "Continue seamlessly from the latest assistant message with no recap.",
            "Resolve the immediate next beat before introducing a new complication.",
        ),
        summary_guidance=(
            "Rewrite any overly literary chronicle into neutral campaign notes.",
            "Preserve durable state, conflicts, promises, consequences, and open threads.",
        ),
    ),
}


MODEL_SPECS: dict[str, ModelSpec] = {
    "ollama/huihui-qwen3-abliterated-8b": ModelSpec(
        id="ollama/huihui-qwen3-abliterated-8b",
        provider="ollama",
        model="huihui_ai/qwen3-abliterated:8b",
        profile_id="local_small_instruct",
        label="Huihui Qwen3 Abliterated 8B",
        max_context=4096,
    ),
    "ollama/llama3.2-3b": ModelSpec(
        id="ollama/llama3.2-3b",
        provider="ollama",
        model="llama3.2:3b",
        profile_id="local_small_instruct",
        label="Llama 3.2 3B",
        max_context=4096,
    ),
    "hub/claude-sonnet": ModelSpec(
        id="hub/claude-sonnet",
        provider="openai_compatible",
        model="anthropic/claude-sonnet",
        profile_id="balanced_reasoning",
        label="Claude Sonnet via AI Hub",
        max_context=200000,
        cost_tier="medium",
        supports_tools=True,
    ),
    "hub/claude-opus": ModelSpec(
        id="hub/claude-opus",
        provider="openai_compatible",
        model="anthropic/claude-opus",
        profile_id="reasoning_strong",
        label="Claude Opus via AI Hub",
        max_context=200000,
        cost_tier="high",
        supports_tools=True,
    ),
    "hub/qwen": ModelSpec(
        id="hub/qwen",
        provider="openai_compatible",
        model="qwen/qwen",
        profile_id="local_small_instruct",
        label="Qwen via AI Hub",
        max_context=32768,
        cost_tier="low",
    ),
}

DEFAULT_MODEL_PROFILE_ID = "local_small_instruct"


def get_model_profile(profile_id: str | None) -> ModelClassProfile:
    if profile_id and profile_id in MODEL_CLASS_PROFILES:
        return MODEL_CLASS_PROFILES[profile_id]
    return MODEL_CLASS_PROFILES[DEFAULT_MODEL_PROFILE_ID]


def get_model_spec(spec_id: str | None) -> ModelSpec | None:
    if not spec_id:
        return None
    return MODEL_SPECS.get(spec_id)


def infer_model_profile_id(model_name: str | None, explicit_profile_id: str | None = None) -> str:
    if explicit_profile_id in MODEL_CLASS_PROFILES:
        return str(explicit_profile_id)
    normalized = (model_name or "").strip().lower()
    for spec in MODEL_SPECS.values():
        if normalized and normalized == spec.model.lower():
            return spec.profile_id
    if any(token in normalized for token in ("opus", "gpt-5", "o3", "o4")):
        return "reasoning_strong"
    if any(token in normalized for token in ("sonnet", "gpt-4", "gemini")):
        return "balanced_reasoning"
    return DEFAULT_MODEL_PROFILE_ID
