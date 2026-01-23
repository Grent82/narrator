import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    content_width: str
    row_gap: str
    row_between: str
    row_end: str
    card_width: str
    flex_1: str
    title: str
    section_title: str
    text_lg: str
    text_muted: str
    text_pre: str


THEMES = {
    "default": Theme(
        content_width="w-full max-w-3xl",
        row_gap="items-center gap-2",
        row_between="items-center justify-between",
        row_end="justify-end gap-2",
        card_width="w-96",
        flex_1="flex-1",
        title="text-2xl font-semibold",
        section_title="text-lg font-semibold",
        text_lg="text-lg",
        text_muted="text-gray-500",
        text_pre="whitespace-pre-wrap",
    ),
    "noir": Theme(
        content_width="w-full max-w-4xl",
        row_gap="items-center gap-3",
        row_between="items-center justify-between",
        row_end="justify-end gap-2",
        card_width="w-[28rem]",
        flex_1="flex-1",
        title="text-3xl font-semibold",
        section_title="text-lg font-semibold",
        text_lg="text-lg",
        text_muted="text-slate-400",
        text_pre="whitespace-pre-wrap",
    ),
}


def get_theme() -> Theme:
    name = os.getenv("FRONTEND_THEME", "default").strip().lower()
    return THEMES.get(name, THEMES["default"])


THEME = get_theme()
