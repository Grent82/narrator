import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    content_width: str
    row_gap: str
    flex_1: str
    title: str
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
    lore_grid: str
    lore_add_card: str
    lore_add_icon: str
    lore_add_text: str
    lore_card: str
    lore_card_title: str
    lore_card_body: str
    lore_tag: str
    lore_menu_button: str
    dialog_card: str
    dialog_title: str
    dialog_body: str
    dialog_actions: str
    dialog_input: str
    dialog_input_props: str


THEMES = {
    "default": Theme(
        content_width="w-full max-w-3xl",
        row_gap="items-center gap-2",
        flex_1="flex-1",
        
        title="text-2xl font-semibold",
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
        lore_grid="grid grid-cols-2 gap-4",
        lore_add_card="rounded-xl border border-amber-500/40 bg-amber-900/40 p-4 flex flex-col items-center justify-center text-center min-h-32",
        lore_add_icon="text-amber-300 text-4xl",
        lore_add_text="text-amber-200 text-sm",
        lore_card="rounded-xl border border-slate-700/60 bg-slate-800/60 p-4 flex flex-col h-full min-h-32",
        lore_card_title="text-slate-100 font-semibold text-lg",
        lore_card_body="text-slate-400 text-sm w-full max-h-24 overflow-hidden whitespace-normal break-all",
        lore_tag="text-[10px] uppercase bg-slate-700/70 text-slate-200 px-2 py-0.5 rounded-full tracking-wide",
        lore_menu_button="text-slate-300",
        dialog_card="w-96 mx-auto bg-slate-900/90 text-slate-100 border border-slate-700/60 rounded-xl",
        dialog_title="text-lg font-semibold text-center w-full",
        dialog_body="w-full items-center gap-4",
        dialog_actions="w-full justify-center gap-3",
        dialog_input="w-full justify-center",
        dialog_input_props="dark filled rounded color=blue-4 label-color=grey-4 input-class=text-slate-100",
    ),
}


def get_theme() -> Theme:
    name = os.getenv("FRONTEND_THEME", "default").strip().lower()
    return THEMES.get(name, THEMES["default"])


THEME = get_theme()
