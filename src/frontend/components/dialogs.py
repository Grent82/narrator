import asyncio
from typing import Callable, Dict, List
from uuid import uuid4

from nicegui import ui
from nicegui.context import context

from src.frontend.components.lore_grid import render_lore_grid
from src.frontend.components.plot_fields import PLOT_FIELD_DEFS, plot_field
from src.frontend.components.story_details_fields import parse_tags, story_details_fields
from src.frontend.story_defaults import AI_INSTRUCTION_PRESETS, DEFAULT_AI_INSTRUCTION_KEY, get_ai_instructions
from src.frontend.story_generator_options import (
    ROLE_OPTIONS_BY_PRESET,
    START_TEMPLATES,
)
from src.frontend.ui_constants import (
    DIALOG_ACTIONS,
    DIALOG_BODY,
    DIALOG_CARD,
    DIALOG_INPUT,
    DIALOG_INPUT_PROPS,
    DIALOG_TITLE,
    TEXT_MUTED,
)
from src.frontend.state import generate_story_draft, get_story_generate_job
from src.shared.lore_tags import LORE_TAG_OPTIONS


StorySubmit = Callable[[str, str, str, str, str, str, List[str], List[Dict[str, str]]], None]


def _story_dialog(
    dialog_title: str,
    submit_label: str,
    on_submit: StorySubmit,
    initial_title: str,
    initial_preset_key: str,
    initial_ai_instructions: str,
    initial_plot_summary: str,
    initial_plot_essentials: str,
    initial_author_note: str,
    initial_description: str,
    initial_tags: List[str],
    initial_lore_entries: List[Dict[str, str]],
    show_generator: bool = False,
) -> ui.dialog:
    dialog = ui.dialog()
    lore_entries: List[Dict[str, str]] = [dict(entry) for entry in initial_lore_entries]
    draft_state: Dict[str, object] = {}

    def next_lore_id() -> str:
        return str(uuid4())

    def apply_preset(key: str | None) -> None:
        preset_key = key or DEFAULT_AI_INSTRUCTION_KEY
        ai_instructions_input.value = get_ai_instructions(preset_key)
        ai_instructions_input.update()

    with dialog:
        with ui.card().classes(DIALOG_CARD).style("width: 100%; max-width: 72rem; height: 85vh;"):
            with ui.column().classes(f"{DIALOG_BODY} h-full"):
                ui.label(dialog_title).classes(DIALOG_TITLE)

                with ui.tabs().classes("w-full justify-center") as tabs:
                    tab_generator = ui.tab("Generator") if show_generator else None
                    tab_plot = ui.tab("Plot")
                    tab_lore = ui.tab("Lore")
                    tab_details = ui.tab("Details")

                start_tab = tab_generator or tab_plot
                with ui.tab_panels(tabs, value=start_tab).classes(
                    "w-full flex-1 min-h-0 overflow-y-auto bg-slate-900/80 text-slate-100 backdrop-blur"
                ):
                    with ui.tab_panel(tab_plot).classes("w-full q-pa-none"):
                        with ui.column().classes("w-full items-center gap-4"):
                            preset_options = {key: value["label"] for key, value in AI_INSTRUCTION_PRESETS.items()}
                            preset_select = ui.select(
                                preset_options,
                                value=initial_preset_key or DEFAULT_AI_INSTRUCTION_KEY,
                                label="AI Instruction Preset",
                            ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)

                            ai_def = PLOT_FIELD_DEFS["ai_instructions"]
                            summary_def = PLOT_FIELD_DEFS["plot_summary"]
                            plot_def = PLOT_FIELD_DEFS["plot_essentials"]
                            author_def = PLOT_FIELD_DEFS["author_note"]

                            ai_instructions_input = plot_field(
                                title=ai_def.title,
                                help_text=ai_def.help_text(editable=True),
                                value=initial_ai_instructions,
                                readonly=False,
                            )

                            plot_field(
                                title=summary_def.title,
                                help_text=summary_def.help_text(editable=False),
                                value=initial_plot_summary,
                                readonly=False,
                            )

                            plot_essentials_input = plot_field(
                                title=plot_def.title,
                                help_text=plot_def.help_text(editable=True),
                                value=initial_plot_essentials,
                                readonly=False,
                            )

                            author_note_input = plot_field(
                                title=author_def.title,
                                help_text=author_def.help_text(editable=True),
                                value=initial_author_note,
                                readonly=False,
                            )

                    if show_generator and tab_generator is not None:
                        with ui.tab_panel(tab_generator).classes("w-full q-pa-none"):
                            with ui.column().classes("w-full items-center gap-4"):
                                role_select = ui.select(ROLE_OPTIONS_BY_PRESET,label="Role", ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                                name_input = ui.input("Name").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                                gender_input = ui.input("Gender").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                                age_input = ui.input("Age").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                                traits_input = (
                                    ui.textarea("Traits (start with 'You have ...')")
                                    .props(f"autogrow {DIALOG_INPUT_PROPS}")
                                    .classes(DIALOG_INPUT)
                                )
                                world_input = (
                                    ui.textarea("World input")
                                    .props(f"autogrow {DIALOG_INPUT_PROPS}")
                                    .classes(DIALOG_INPUT)
                                )
                                start_template_select = ui.select(
                                    START_TEMPLATES,
                                    label="Start situation template",
                                ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                                start_custom_input = (
                                    ui.textarea("Start situation (custom)")
                                    .props(f"autogrow {DIALOG_INPUT_PROPS}")
                                    .classes(DIALOG_INPUT)
                                )

                                def update_role_options() -> None:
                                    options = ROLE_OPTIONS_BY_PRESET
                                    role_select.set_options(options)
                                    if role_select.value not in options:
                                        role_select.value = options[0] if options else None
                                    role_select.update()

                                async def handle_generate() -> None:
                                    client = context.client

                                    def safe_notify(message: str, *, type: str | None = None) -> None:
                                        if not client.has_socket_connection:
                                            return
                                        options = {"message": message}
                                        if type:
                                            options["type"] = type
                                        client.outbox.enqueue_message("notify", options, client.id)

                                    if not (world_input.value or "").strip():
                                        safe_notify("World input is required.", type="negative")
                                        return
                                    if not (name_input.value or "").strip():
                                        safe_notify("Name is required.", type="negative")
                                        return
                                    if not (role_select.value or "").strip():
                                        safe_notify("Role is required.", type="negative")
                                        return
                                    if not (traits_input.value or "").strip():
                                        safe_notify("Traits are required (start with 'You have ...').", type="negative")
                                        return
                                    job = await asyncio.to_thread(
                                        generate_story_draft,
                                        ai_instruction_key=preset_select.value or DEFAULT_AI_INSTRUCTION_KEY,
                                        role=str(role_select.value or ""),
                                        name=str(name_input.value or ""),
                                        gender=str(gender_input.value or ""),
                                        age=str(age_input.value or ""),
                                        traits=str(traits_input.value or ""),
                                        world_input=str(world_input.value or ""),
                                        start_template=str(start_template_select.value or ""),
                                        start_custom=str(start_custom_input.value or ""),
                                    )
                                    if not job or not job.get("job_id"):
                                        safe_notify("Story generation failed. Try again.", type="negative")
                                        return
                                    job_id = str(job.get("job_id", ""))
                                    safe_notify("Generation started. Waiting for result...")
                                    for _ in range(900):
                                        if not client.has_socket_connection:
                                            return
                                        status = await asyncio.to_thread(get_story_generate_job, job_id)
                                        if not status:
                                            await asyncio.sleep(2)
                                            continue
                                        if status.get("status") == "error":
                                            safe_notify(f"Generation failed: {status.get('error')}", type="negative")
                                            return
                                        if status.get("status") == "done" and status.get("result"):
                                            draft = status.get("result") or {}
                                            draft_state.clear()
                                            draft_state.update(draft)
                                            if not client.has_socket_connection:
                                                return
                                            title_input.value = draft.get("title", "") or ""
                                            description_input.value = draft.get("description", "") or ""
                                            plot_essentials_input.value = draft.get("plot_essentials", "") or ""
                                            author_note_input.value = draft.get("author_note", "") or ""
                                            tags_input.value = ", ".join(draft.get("tags", []) or [])
                                            lore_entries[:] = list(draft.get("lore", []) or [])
                                            title_input.update()
                                            description_input.update()
                                            plot_essentials_input.update()
                                            author_note_input.update()
                                            tags_input.update()
                                            refresh_lore_grid()
                                            safe_notify("Story generated.", type="positive")
                                            return
                                        await asyncio.sleep(2)
                                    safe_notify("Generation still running. Please try again.", type="warning")

                                ui.button("Generate", on_click=handle_generate).props("outline")

                    with ui.tab_panel(tab_lore).classes("w-full q-pa-none"):
                        with ui.column().classes("w-full items-center gap-4"):
                            lore_grid_container = ui.element("div").classes("w-full")

                    with ui.tab_panel(tab_details).classes("w-full q-pa-none"):
                        with ui.column().classes("w-full items-center gap-4"):
                            title_input, description_input, tags_input = story_details_fields(
                                initial_title,
                                initial_description,
                                initial_tags,
                            )

                def handle_submit() -> None:
                    if show_generator and not draft_state:
                        ui.notify("Generate a story first.", type="negative")
                        return
                    draft = draft_state if show_generator else {}
                    title_value = title_input.value or draft.get("title", "")
                    description_value = description_input.value or draft.get("description", "")
                    plot_essentials_value = plot_essentials_input.value or draft.get("plot_essentials", "")
                    author_note_value = author_note_input.value or draft.get("author_note", "")
                    tags_value = tags_input.value or ", ".join(draft.get("tags", []) or [])
                    lore_value = list(lore_entries) or list(draft.get("lore", []) or [])
                    on_submit(
                        title_value or "",
                        preset_select.value or DEFAULT_AI_INSTRUCTION_KEY,
                        ai_instructions_input.value or "",
                        plot_essentials_value or "",
                        author_note_value or "",
                        description_value or "",
                        parse_tags(tags_value or ""),
                        lore_value,
                    )
                    dialog.close()

                with ui.row().classes(DIALOG_ACTIONS):
                    ui.button(submit_label, on_click=handle_submit)

    def refresh_lore_grid() -> None:
        render_lore_grid(
            lore_grid_container,
            lore_entries,
            open_add_dialog,
            open_edit_dialog,
            handle_delete,
            handle_duplicate,
        )

    edit_state = {"entry_id": ""}

    def set_lore_form_values(title: str, description: str, tag: str | None, triggers: str) -> None:
        lore_title_input.value = title
        lore_description_input.value = description
        lore_triggers_input.value = triggers
        tag_value = None
        if tag:
            for option in LORE_TAG_OPTIONS:
                if option.lower() == tag.lower():
                    tag_value = option
                    break
        if tag and not tag_value:
            tag_value = "Custom"
            lore_custom_tag_input.value = tag
        else:
            lore_custom_tag_input.value = ""
        lore_tag_input.value = tag_value
        toggle_custom_tag(tag_value)
        lore_title_input.update()
        lore_description_input.update()
        lore_triggers_input.update()
        lore_custom_tag_input.update()
        lore_tag_input.update()

    def open_add_dialog() -> None:
        edit_state["entry_id"] = ""
        set_lore_form_values("", "", None, "")
        lore_dialog_title.text = "New Lore Entry"
        lore_dialog_title.update()
        lore_dialog.open()

    def open_edit_dialog(entry: Dict[str, str]) -> None:
        edit_state["entry_id"] = entry.get("id", "")
        set_lore_form_values(
            entry.get("title", ""),
            entry.get("description", ""),
            entry.get("tag", ""),
            entry.get("triggers", ""),
        )
        lore_dialog_title.text = entry.get("title", "") or "Lore Entry"
        lore_dialog_title.update()
        lore_dialog.open()

    def save_lore_entry() -> None:
        tag_value = lore_custom_tag_input.value if lore_tag_input.value == "Custom" else (lore_tag_input.value or "")
        entry_data = {
            "id": edit_state.get("entry_id", "") or next_lore_id(),
            "title": lore_title_input.value or "",
            "description": lore_description_input.value or "",
            "tag": tag_value,
            "triggers": lore_triggers_input.value or "",
        }
        if edit_state.get("entry_id"):
            for idx, entry in enumerate(lore_entries):
                if entry.get("id") == entry_data["id"]:
                    lore_entries[idx] = entry_data
                    break
        else:
            lore_entries.insert(0, entry_data)
        edit_state["entry_id"] = ""
        lore_dialog.close()
        refresh_lore_grid()

    def handle_delete(entry: Dict[str, str]) -> None:
        entry_id = entry.get("id", "")
        if not entry_id:
            return
        lore_entries[:] = [item for item in lore_entries if item.get("id") != entry_id]
        refresh_lore_grid()

    def handle_duplicate(entry: Dict[str, str]) -> None:
        lore_entries.insert(
            0,
            {
                "id": next_lore_id(),
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "tag": entry.get("tag", ""),
                "triggers": entry.get("triggers", ""),
            },
        )
        refresh_lore_grid()

    lore_dialog = ui.dialog()
    with lore_dialog:
        with ui.card().classes(DIALOG_CARD):
            with ui.column().classes(DIALOG_BODY):
                lore_dialog_title = ui.label("Lore Entry").classes(DIALOG_TITLE)
                lore_title_input = ui.input("Title").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                lore_description_input = (
                    ui.textarea("Description")
                    .props(f"autogrow {DIALOG_INPUT_PROPS}")
                    .classes(DIALOG_INPUT)
                )
                lore_triggers_input = ui.input("Triggers").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                lore_tag_input = ui.select(LORE_TAG_OPTIONS, label="Tag").props(DIALOG_INPUT_PROPS).classes(
                    DIALOG_INPUT
                )
                lore_custom_tag_input = (
                    ui.input("Custom tag")
                    .props(f"{DIALOG_INPUT_PROPS} placeholder=Enter a custom type...")
                    .classes(DIALOG_INPUT)
                )
                if hasattr(lore_custom_tag_input, "set_visibility"):
                    lore_custom_tag_input.set_visibility(False)
                else:
                    lore_custom_tag_input.visible = False
                with ui.row().classes(DIALOG_ACTIONS):
                    ui.button("Cancel", on_click=lore_dialog.close)
                    ui.button("Save", on_click=save_lore_entry)

    def sync_lore_title(value: str) -> None:
        if edit_state.get("entry_id"):
            lore_dialog_title.text = value or "Lore Entry"
        else:
            lore_dialog_title.text = value or "New Lore Entry"
        lore_dialog_title.update()

    lore_title_input.on("input", lambda e: sync_lore_title(e.value))

    def toggle_custom_tag(value: str | None) -> None:
        is_custom = value == "Custom"
        if hasattr(lore_custom_tag_input, "set_visibility"):
            lore_custom_tag_input.set_visibility(is_custom)
        else:
            lore_custom_tag_input.visible = is_custom
        if not is_custom:
            lore_custom_tag_input.value = ""
            lore_custom_tag_input.update()

    lore_tag_input.on("update:model-value", lambda e: toggle_custom_tag(lore_tag_input.value))
    lore_tag_input.on("change", lambda e: toggle_custom_tag(lore_tag_input.value))

    preset_select.on("update:model-value", lambda e: apply_preset(preset_select.value))
    preset_select.on("change", lambda e: apply_preset(preset_select.value))
    if show_generator:
        preset_select.on("update:model-value", lambda e: update_role_options())
        preset_select.on("change", lambda e: update_role_options())

    refresh_lore_grid()
    return dialog


def create_story_dialog(on_create: StorySubmit) -> ui.dialog:
    return _story_dialog(
        dialog_title="Create a new story",
        submit_label="Create",
        on_submit=on_create,
        initial_title="",
        initial_preset_key=DEFAULT_AI_INSTRUCTION_KEY,
        initial_ai_instructions=get_ai_instructions(DEFAULT_AI_INSTRUCTION_KEY),
        initial_plot_summary="",
        initial_plot_essentials="",
        initial_author_note="",
        initial_description="",
        initial_tags=[],
        initial_lore_entries=[],
        show_generator=True,
    )


def edit_story_dialog(story: Dict[str, object], on_save: StorySubmit) -> ui.dialog:
    return _story_dialog(
        dialog_title="Edit story",
        submit_label="Save",
        on_submit=on_save,
        initial_title=str(story.get("title", "")),
        initial_preset_key=str(story.get("ai_instruction_key", DEFAULT_AI_INSTRUCTION_KEY)),
        initial_ai_instructions=str(story.get("ai_instructions", "")),
        initial_plot_summary=str(story.get("plot_summary", "")),
        initial_plot_essentials=str(story.get("plot_essentials", "")),
        initial_author_note=str(story.get("author_note", "")),
        initial_description=str(story.get("description", "")),
        initial_tags=list(story.get("tags", [])),
        initial_lore_entries=list(story.get("lore", [])),
        show_generator=False,
    )


def create_story_generate_dialog(on_submit: StorySubmit) -> ui.dialog:
    dialog = ui.dialog()
    draft_state: Dict[str, object] = {}

    with dialog:
        with ui.card().classes(DIALOG_CARD).style("width: 100%; max-width: 72rem; height: 85vh;"):
            with ui.column().classes(f"{DIALOG_BODY} h-full"):
                ui.label("Generate a new story").classes(DIALOG_TITLE)

                with ui.row().classes("w-full flex-1 min-h-0 gap-4"):
                    with ui.column().classes("w-1/2 min-h-0 gap-4"):
                        preset_options = {key: value["label"] for key, value in AI_INSTRUCTION_PRESETS.items()}
                        preset_select = ui.select(
                            preset_options,
                            value=DEFAULT_AI_INSTRUCTION_KEY,
                            label="AI Instruction Preset",
                        ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)

                        role_select = ui.select( ROLE_OPTIONS_BY_PRESET, label="Role", ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                        name_input = ui.input("Name").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                        gender_input = ui.input("Gender").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                        age_input = ui.input("Age").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                        traits_input = (
                            ui.textarea("Traits (start with 'You have ...')")
                            .props(f"autogrow {DIALOG_INPUT_PROPS}")
                            .classes(DIALOG_INPUT)
                        )
                        world_input = (
                            ui.textarea("World input")
                            .props(f"autogrow {DIALOG_INPUT_PROPS}")
                            .classes(DIALOG_INPUT)
                        )
                        start_template_select = ui.select( START_TEMPLATES, label="Start situation template",
                        ).props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                        start_custom_input = (
                            ui.textarea("Start situation (custom)")
                            .props(f"autogrow {DIALOG_INPUT_PROPS}")
                            .classes(DIALOG_INPUT)
                        )

                def update_role_options() -> None:
                    options = ROLE_OPTIONS_BY_PRESET
                    role_select.set_options(options)
                    if role_select.value not in options:
                        role_select.value = options[0] if options else None
                    role_select.update()

                async def handle_generate() -> None:
                    client = context.client

                    def safe_notify(message: str, *, type: str | None = None) -> None:
                        if not client.has_socket_connection:
                            return
                        options = {"message": message}
                        if type:
                            options["type"] = type
                        client.outbox.enqueue_message("notify", options, client.id)

                    if not (world_input.value or "").strip():
                        safe_notify("World input is required.", type="negative")
                        return
                    if not (name_input.value or "").strip():
                        safe_notify("Name is required.", type="negative")
                        return
                    if not (role_select.value or "").strip():
                        safe_notify("Role is required.", type="negative")
                        return
                    if not (traits_input.value or "").strip():
                        safe_notify("Traits are required (start with 'You have ...').", type="negative")
                        return
                    job = await asyncio.to_thread(
                        generate_story_draft,
                        ai_instruction_key=preset_select.value or DEFAULT_AI_INSTRUCTION_KEY,
                        role=str(role_select.value or ""),
                        name=str(name_input.value or ""),
                        gender=str(gender_input.value or ""),
                        age=str(age_input.value or ""),
                        traits=str(traits_input.value or ""),
                        world_input=str(world_input.value or ""),
                        start_template=str(start_template_select.value or ""),
                        start_custom=str(start_custom_input.value or ""),
                    )
                    if not job or not job.get("job_id"):
                        safe_notify("Story generation failed. Try again.", type="negative")
                        return
                    job_id = str(job.get("job_id", ""))
                    safe_notify("Generation started. Waiting for result...")
                    for _ in range(120):
                        if not client.has_socket_connection:
                            return
                        status = await asyncio.to_thread(get_story_generate_job, job_id)
                        if not status:
                            await asyncio.sleep(2)
                            continue
                        if status.get("status") == "error":
                            safe_notify(f"Generation failed: {status.get('error')}", type="negative")
                            return
                        if status.get("status") == "done" and status.get("result"):
                            draft = status.get("result") or {}
                            draft_state.clear()
                            draft_state.update(draft)
                            safe_notify("Story generated.", type="positive")
                            return
                        await asyncio.sleep(2)
                    safe_notify("Generation still running. Please try again.", type="warning")

                with ui.row().classes(DIALOG_ACTIONS):
                    ui.button(
                        "Generate",
                        on_click=handle_generate,
                    ).props("outline")
                    

    preset_select.on("update:model-value", lambda e: update_role_options())
    preset_select.on("change", lambda e: update_role_options())
    return dialog


def confirm_delete_dialog(
    title: str,
    message: str,
    on_confirm: Callable[[], None],
) -> ui.dialog:
    dialog = ui.dialog()
    with dialog:
        with ui.card().classes(DIALOG_CARD):
            ui.label(title).classes(DIALOG_TITLE)
            ui.label(message).classes(TEXT_MUTED)
            with ui.row().classes(DIALOG_ACTIONS):
                ui.button(
                    "Delete",
                    color="negative",
                    on_click=lambda: (on_confirm(), dialog.close()),
                )
    return dialog
