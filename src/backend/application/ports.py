from __future__ import annotations

from typing import Any, Iterator, Protocol


class LoggerProtocol(Protocol):
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...


class OllamaProtocol(Protocol):
    def generate(self, *, model: str, prompt: str, stream: bool = False, context: list[int] | None = None) -> Any:
        ...

    def chat(self, *, model: str, messages: list[dict], stream: bool = False) -> Any:
        ...
