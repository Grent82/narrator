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
    side_panel: str
    side_panel_props: str
    side_panel_nav: str
    side_panel_tabs: str
    side_panel_panel: str
    side_panel_section: str
    component_title: str
    component_help: str
    component_container: str
    component_input: str
    component_input_class: str
    component_input_style: str


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

        side_panel="bg-slate-900/100 text-slate-100 backdrop-blur",
        side_panel_props="width=400 bordered",
        side_panel_nav="items-center justify-betweens",
        side_panel_tabs="w-full",
        side_panel_panel="w-full bg-slate-900/80 text-slate-100 backdrop-blur",
        side_panel_section="w-full text-sm text-slate-300",

        component_container="w-full rounded-md border border-slate-600/50 bg-slate-800/50 p-3",
        component_title="text-sm font-semibold text-slate-200",
        component_help="text-xs text-slate-400",
        component_input="w-full text-xs",
        component_input_class="text-slate-200",
        component_input_style="color:#e2e8f0;",
    ),
}


def get_theme() -> Theme:
    name = os.getenv("FRONTEND_THEME", "default").strip().lower()
    return THEMES.get(name, THEMES["default"])


THEME = get_theme()
