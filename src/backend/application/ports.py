from __future__ import annotations

from typing import Any, Iterable, Iterator, Protocol

from langchain_core.messages import BaseMessage


class LoggerProtocol(Protocol):
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...


class ChatModelProtocol(Protocol):
    def bind(self, **kwargs: Any) -> "ChatModelProtocol":
        ...

    def stream(self, input: Iterable[BaseMessage]) -> Iterator[BaseMessage]:
        ...

    def invoke(self, input: Iterable[BaseMessage]) -> BaseMessage:
        ...


class EmbeddingsProtocol(Protocol):
    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...
