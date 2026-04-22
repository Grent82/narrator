from src.backend.infrastructure.llm_config import (
    active_chat_model_name,
    active_provider_name,
    active_summary_model_name,
    get_chat_model_config,
)


def test_llm_config_defaults_to_ollama(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "local-model")
    monkeypatch.setenv("OLLAMA_URL", "http://ollama:11434")

    config = get_chat_model_config()

    assert active_provider_name() == "ollama"
    assert active_chat_model_name() == "local-model"
    assert active_summary_model_name() == "local-model"
    assert config.provider == "ollama"
    assert config.model == "local-model"
    assert config.base_url == "http://ollama:11434"


def test_llm_config_supports_openai_compatible_hub(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ai_hub")
    monkeypatch.setenv("LLM_MODEL", "anthropic/claude-sonnet")
    monkeypatch.setenv("SUMMARY_MODEL", "qwen/qwen3")
    monkeypatch.setenv("LLM_BASE_URL", "https://hub.example/v1")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("LLM_ENABLE_THINKING", "false")

    config = get_chat_model_config()

    assert active_provider_name() == "openai_compatible"
    assert active_chat_model_name() == "anthropic/claude-sonnet"
    assert active_summary_model_name() == "qwen/qwen3"
    assert config.provider == "openai_compatible"
    assert config.base_url == "https://hub.example/v1"
    assert config.model == "anthropic/claude-sonnet"
    assert config.api_key == "secret"
    assert config.timeout == 15
    assert config.enable_thinking is False
