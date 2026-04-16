from src.backend.api.story_routes import _normalize_persisted_messages


def test_transient_assistant_errors_are_not_persisted() -> None:
    messages = [
        {"role": "user", "text": "continue"},
        {"role": "assistant", "text": "Normal reply"},
        {"role": "assistant", "text": "\n[Ollama error: model requires more memory]"},
        {"role": "assistant", "text": "Backend error: request failed"},
        {"role": "assistant", "text": "Unexpected error: timeout"},
        {"role": "assistant", "text": "[Ollama warning: degraded mode]"},
    ]

    normalized = _normalize_persisted_messages(messages)

    assert normalized == [
        {"role": "user", "text": "continue"},
        {"role": "assistant", "text": "Normal reply"},
    ]
