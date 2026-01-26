from __future__ import annotations

MODE_OPTIONS = {
    "say": {"temperature": 0.8, "top_p": 0.9, "top_k": 50, "repeat_penalty": 1.08},
    "do": {"temperature": 0.72, "top_p": 0.87, "top_k": 40, "repeat_penalty": 1.1},
    "story": {"temperature": 0.95, "top_p": 0.94, "top_k": 60, "repeat_penalty": 1.05},
    "continue": {"temperature": 0.9, "top_p": 0.93, "top_k": 60, "repeat_penalty": 1.06},
}

DEFAULT_OPTIONS = {"temperature": 0.9, "top_p": 0.93, "top_k": 60, "repeat_penalty": 1.06}
