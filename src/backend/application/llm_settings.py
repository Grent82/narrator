from __future__ import annotations

import os

STOP_SEQUENCES = ["\nUser:", "\n\n[", "</response>", "[END]"]

COMMON_OPTIONS = {
    "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "16384")),
    "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "20m"),
    "min_p": float(os.getenv("OLLAMA_MIN_P", "0.08")),
    "stop": STOP_SEQUENCES,
}

MODE_OPTIONS = {
    "say": {"temperature": 0.8, "top_p": 0.9, "top_k": 50, "repeat_penalty": 1.1, **COMMON_OPTIONS},
    "do": {"temperature": 0.72, "top_p": 0.87, "top_k": 40, "repeat_penalty": 1.12, **COMMON_OPTIONS},
    "story": {"temperature": 0.95, "top_p": 0.94, "top_k": 60, "repeat_penalty": 1.07, **COMMON_OPTIONS},
    "continue": {"temperature": 0.9, "top_p": 0.93, "top_k": 60, "repeat_penalty": 1.08, **COMMON_OPTIONS},
}

DEFAULT_OPTIONS = {"temperature": 0.9, "top_p": 0.93, "top_k": 60, "repeat_penalty": 1.08, **COMMON_OPTIONS}
