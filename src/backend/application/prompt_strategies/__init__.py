"""Provider-specific prompt strategies.

This package contains strategy implementations for different LLM providers.
Each strategy handles:
- Provider-specific prompt formatting (XML vs Markdown)
- Template selection and rendering
- Model-size adapted guidance injection
"""

from src.backend.application.prompt_strategies.base import PromptStrategy
from src.backend.application.prompt_strategies.claude import ClaudePromptStrategy
from src.backend.application.prompt_strategies.llama import LlamaPromptStrategy
from src.backend.application.prompt_strategies.qwen import QwenPromptStrategy
from src.backend.application.prompt_strategies.factory import get_prompt_strategy

__all__ = [
    "PromptStrategy",
    "ClaudePromptStrategy",
    "LlamaPromptStrategy",
    "QwenPromptStrategy",
    "get_prompt_strategy",
]
