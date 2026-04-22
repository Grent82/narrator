from src.backend.application.model_profiles import get_model_profile, infer_model_profile_id


def test_infer_model_profile_uses_explicit_profile_first() -> None:
    assert infer_model_profile_id("unknown-model", "reasoning_strong") == "reasoning_strong"


def test_infer_model_profile_maps_known_local_model_to_local_profile() -> None:
    assert infer_model_profile_id("huihui_ai/qwen3-abliterated:8b") == "local_small_instruct"


def test_infer_model_profile_maps_hub_style_model_names() -> None:
    assert infer_model_profile_id("anthropic/claude-opus") == "reasoning_strong"
    assert infer_model_profile_id("anthropic/claude-sonnet") == "balanced_reasoning"


def test_get_model_profile_falls_back_to_local_profile() -> None:
    assert get_model_profile("does-not-exist").id == "local_small_instruct"
