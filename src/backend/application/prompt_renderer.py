from __future__ import annotations

from src.backend.application.model_profiles import ModelClassProfile, get_model_profile


def render_profile_guidance(profile: ModelClassProfile | str | None, mode: str) -> str:
    profile_id = profile if isinstance(profile, str) else getattr(profile, "id", None)
    profile_value = get_model_profile(profile_id)
    mode_value = (mode or "story").strip().lower()
    lines: list[str] = []

    if mode_value == "continue":
        lines.extend(profile_value.continue_guidance)
    else:
        lines.extend(profile_value.story_turn_guidance)

    if profile_value.repetition_risk == "high":
        lines.append("Do not copy sentence structure from recent assistant messages.")
    if profile_value.prompt_verbosity == "compact":
        lines.append("Follow these rules literally and keep the response focused.")

    return "\n".join(f"- {line}" for line in lines if line.strip())


def render_summary_profile_guidance(profile: ModelClassProfile | str | None) -> str:
    profile_id = profile if isinstance(profile, str) else getattr(profile, "id", None)
    profile_value = get_model_profile(profile_id)
    lines = list(profile_value.summary_guidance)
    if profile_value.prompt_verbosity == "compact":
        lines.append("Prefer short, direct sentences.")
    return "\n".join(f"- {line}" for line in lines if line.strip())
