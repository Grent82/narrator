from langchain_core.messages import HumanMessage, SystemMessage

from src.backend.infrastructure.openai_compatible_client import (
    OpenAICompatibleChatModel,
    _messages_payload,
    _openai_options,
)


def test_openai_compatible_message_payload_maps_langchain_roles() -> None:
    payload = _messages_payload(
        [
            SystemMessage(content="Rules"),
            HumanMessage(content="Act"),
        ]
    )

    assert payload == [
        {"role": "system", "content": "Rules"},
        {"role": "user", "content": "Act"},
    ]


def test_openai_compatible_options_translate_supported_generation_settings() -> None:
    payload = _openai_options(
        {
            "temperature": 0.8,
            "top_p": 0.9,
            "num_predict": 512,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "enable_thinking": False,
        }
    )

    assert payload["temperature"] == 0.8
    assert payload["top_p"] == 0.9
    assert payload["max_tokens"] == 512
    assert "top_k" not in payload
    assert "repeat_penalty" not in payload
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["stop"]


def test_openai_compatible_bind_and_model_copy_are_immutable() -> None:
    client = OpenAICompatibleChatModel(
        base_url="https://hub.example/v1",
        model="qwen/qwen3",
        api_key="secret",
    )

    bound = client.bind(temperature=0.7)
    copied = bound.model_copy({"model": "anthropic/claude-sonnet"})

    assert client.options == {}
    assert bound.options == {"temperature": 0.7}
    assert copied.model == "anthropic/claude-sonnet"
    assert copied.options == {"temperature": 0.7}
