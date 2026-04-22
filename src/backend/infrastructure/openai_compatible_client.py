from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, replace
from typing import Any

import httpx
from langchain_core.messages import AIMessage, BaseMessage

from src.backend.application.llm_settings import STOP_SEQUENCES


@dataclass(frozen=True)
class OpenAICompatibleChatModel:
    base_url: str
    model: str
    api_key: str | None = None
    timeout: float = 120.0
    options: dict[str, Any] = field(default_factory=dict)

    def bind(self, **kwargs: Any) -> OpenAICompatibleChatModel:
        merged = {**self.options, **kwargs}
        return replace(self, options=merged)

    def model_copy(self, update: dict[str, Any]) -> OpenAICompatibleChatModel:
        return replace(
            self,
            base_url=update.get("base_url", self.base_url),
            model=update.get("model", self.model),
            api_key=update.get("api_key", self.api_key),
            timeout=update.get("timeout", self.timeout),
            options=update.get("options", self.options),
        )

    def stream(self, input: Iterable[BaseMessage]) -> Iterator[AIMessage]:
        payload = self._payload(input, stream=True)
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                self._chat_completions_url(),
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    chunk = httpx.Response(200, content=data).json()
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content") or ""
                    if content:
                        yield AIMessage(content=content, response_metadata=chunk)

    def invoke(self, input: Iterable[BaseMessage] | str) -> AIMessage:
        payload = self._payload(input, stream=False)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self._chat_completions_url(),
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
        return AIMessage(content=content, response_metadata=data)

    def _chat_completions_url(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _payload(self, input: Iterable[BaseMessage] | str, stream: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _messages_payload(input),
            "stream": stream,
        }
        payload.update(_openai_options(self.options))
        return payload


def _messages_payload(input: Iterable[BaseMessage] | str) -> list[dict[str, str]]:
    if isinstance(input, str):
        return [{"role": "user", "content": input}]
    return [_message_payload(message) for message in input]


def _message_payload(message: BaseMessage) -> dict[str, str]:
    role = getattr(message, "type", "user")
    if role == "human":
        role = "user"
    elif role == "ai":
        role = "assistant"
    elif role not in {"system", "user", "assistant"}:
        role = "user"
    return {"role": role, "content": str(message.content)}


def _openai_options(options: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    option_map = {
        "temperature": "temperature",
        "top_p": "top_p",
        "num_predict": "max_tokens",
        "stop": "stop",
        "presence_penalty": "presence_penalty",
        "frequency_penalty": "frequency_penalty",
    }
    for source, target in option_map.items():
        value = options.get(source)
        if value is not None:
            payload[target] = value
    enable_thinking = options.get("enable_thinking")
    if enable_thinking is not None:
        payload["chat_template_kwargs"] = {"enable_thinking": bool(enable_thinking)}
    if "stop" not in payload:
        payload["stop"] = STOP_SEQUENCES
    return payload
