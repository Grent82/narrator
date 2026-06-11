from __future__ import annotations

from src.backend.application.model_profiles import (
    ModelClassProfile,
    get_effective_size_profile,
    get_model_profile,
)
from src.backend.application.size_tier import get_size_profile


def render_profile_guidance(
    profile: ModelClassProfile | str | None,
    mode: str,
    model_name: str | None = None,
) -> str:
    profile_id = profile if isinstance(profile, str) else getattr(profile, "id", None)
    profile_value = get_model_profile(profile_id)
    mode_value = (mode or "story").strip().lower()
    lines: list[str] = []

    if mode_value == "continue":
        lines.extend(profile_value.continue_guidance)
    else:
        lines.extend(profile_value.story_turn_guidance)

    # Add size-tier specific guidance
    size_profile = get_effective_size_profile(model_name, profile_id)

    if size_profile.repetition_risk in ("very_high", "high"):
        lines.append("Do not copy sentence structure from recent assistant messages.")
    if profile_value.prompt_verbosity == "compact":
        lines.append("Follow these rules literally and keep the response focused.")
    if size_profile.include_few_shot:
        lines.append("Review the provided examples before responding.")

    return "\n".join(f"- {line}" for line in lines if line.strip())


def render_summary_profile_guidance(
    profile: ModelClassProfile | str | None,
    model_name: str | None = None,
) -> str:
    profile_id = profile if isinstance(profile, str) else getattr(profile, "id", None)
    profile_value = get_model_profile(profile_id)
    lines = list(profile_value.summary_guidance)

    size_profile = get_effective_size_profile(model_name, profile_id)
    if profile_value.prompt_verbosity == "compact":
        lines.append("Prefer short, direct sentences.")
    if size_profile.require_cot:
        lines.append("Think through the summary update step-by-step before writing.")

    return "\n".join(f"- {line}" for line in lines if line.strip())


def render_size_guidance(model_name: str | None, mode: str = "story") -> str:
    """Render size-tier specific guidance for a model.

    This is a convenience function that returns the full size-adapted guidance
    including CoT, repetition prevention, and few-shot indicators.

    Args:
        model_name: The model identifier
        mode: The operation mode

    Returns:
        Formatted guidance text
    """
    from src.backend.application.size_tier import (
        get_cot_instructions,
        get_repetition_prevention_guidance,
    )

    lines = []

    cot = get_cot_instructions(model_name, mode)
    if cot:
        lines.append(cot)

    rep = get_repetition_prevention_guidance(model_name)
    if rep:
        lines.append(rep)

    return "\n\n".join(lines) if lines else ""
