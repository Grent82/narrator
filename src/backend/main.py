import os
import time

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from ollama import Client as OllamaClient
from pydantic import BaseModel

from src.backend.api.story_routes import router as story_router
from src.backend.application.lore_retrieval import retrieve_relevant_lore
from src.backend.application.input_formatting import format_user_for_summary, normalize_mode
from src.backend.application.prompt_builder import build_prompt
from src.backend.application.summarizer import update_story_summary
from src.backend.infrastructure.db import get_db
from src.backend.infrastructure.ollama_client import get_ollama_client
from src.backend.infrastructure.models import StoryModel
from src.shared.logging_config import configure_logging

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "17000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", OLLAMA_MODEL)
SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "2400"))
BACKEND_LOG_FILE = os.getenv("BACKEND_LOG_FILE", "logs/backend.log")

logger = configure_logging(BACKEND_LOG_FILE, "backend")

class TurnRequest(BaseModel):
    text: str | None = None
    mode: str | None = None
    story_id: str | None = None
    trigger: str | None = None


class TurnResponse(BaseModel):
    result: str


def _get_last_message_text(story: StoryModel, role: str = "assistant") -> str:
    if not story or not story.messages:
        return ""
    for msg in reversed(story.messages):
        if msg.role != role:
            continue
        text = (msg.text or "").strip()
        if text:
            return text
    return ""


def process_trigger(
    text: str,
    ollama: OllamaClient,
    mode: str,
    story: StoryModel | None = None,
    lore_entries=None,
) -> str:
    start = time.monotonic()
    try:
        prompt = build_prompt(story, text, mode=mode, lore_entries=lore_entries) if story else text
        logger.debug("ollama_request prompt=%s", prompt)
        logger.debug("ollama_request model=%s prompt_len=%d", OLLAMA_MODEL, len(prompt))
        context = story.ollama_context if story and story.ollama_context else None
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt, context=context)
        if story and response.get("context"):
            story.ollama_context = response.get("context")
        result = response.get("response", "").strip()
        logger.debug("ollama_response chars=%d duration_ms=%d", len(result), int((time.monotonic() - start) * 1000))
        return result
    except Exception as exc:
        logger.exception("ollama_error")
        return f"Ollama error: {exc}"


def stream_trigger(
    text: str,
    ollama: OllamaClient,
    mode: str,
    story: StoryModel | None = None,
    lore_entries=None,
    db=None,
):
    start = time.monotonic()
    buffer = ""
    last_meta = {}
    try:
        prompt = build_prompt(story, text, mode=mode, lore_entries=lore_entries) if story else text
        logger.debug("ollama_stream_request prompt=%s", prompt)
        logger.debug("ollama_stream_request model=%s prompt_len=%d", OLLAMA_MODEL, len(prompt))
        context = story.ollama_context if story and story.ollama_context else None
        for part in ollama.generate(model=OLLAMA_MODEL, prompt=prompt, stream=True, context=context):
            token = part.get("response", "")
            last_meta = part or last_meta
            if token:
                buffer += token
                yield token
        logger.debug( "ollama_stream_completed duration_ms=%d", int((time.monotonic() - start) * 1000), )
        if story and last_meta.get("context"):
            story.ollama_context = last_meta.get("context")
        if story and db:
            update_story_summary(
                client=ollama,
                model=SUMMARY_MODEL,
                story=story,
                user_input=format_user_for_summary(mode, text),
                assistant_text=buffer,
                max_chars=SUMMARY_MAX_CHARS,
                logger=logger,
            )
            db.commit()
        else:
            logger.debug("story_summary_skipped no_story_or_db")
    except Exception as exc:
        logger.exception("ollama_stream_error")
        yield f"\n[Ollama error: {exc}]"


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "redis_url": REDIS_URL,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
    }


@app.post("/turn", response_model=TurnResponse)
def handle_turn(
    payload: TurnRequest,
    db=Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
):
    text = payload.text if payload.text is not None else (payload.trigger or "")
    mode = normalize_mode(payload.mode)
    story = None
    lore_entries = None
    if payload.story_id:
        story = db.query(StoryModel).filter(StoryModel.id == payload.story_id).first()
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        if mode == "continue" and not text.strip():
            last_assistant = _get_last_message_text(story, role="assistant")
            text = last_assistant or "Continue the story from the most recent assistant output. Do not repeat."
        if mode == "continue" and story.ollama_context:
            lore_entries = []
        else:
            retrieval_query = "" if mode == "continue" else text
            lore_entries = retrieve_relevant_lore(db, story.id, retrieval_query, ollama)
    elif mode == "continue" and not text.strip():
        text = "Continue the story from the most recent assistant output. Do not repeat."
    logger.debug("turn_received trigger_len=%d mode=%s", len(text), mode)
    result = process_trigger(text, ollama, mode, story, lore_entries=lore_entries)
    if story:
        update_story_summary(
            client=ollama,
            model=SUMMARY_MODEL,
            story=story,
            user_input=format_user_for_summary(mode, text),
            assistant_text=result,
            max_chars=SUMMARY_MAX_CHARS,
            logger=logger,
        )
        db.commit()
    logger.debug("turn_completed result_len=%d", len(result))
    return TurnResponse(result=result)


@app.post("/turn/stream")
def handle_turn_stream(
    payload: TurnRequest,
    db=Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
):
    text = payload.text if payload.text is not None else (payload.trigger or "")
    mode = normalize_mode(payload.mode)
    story = None
    lore_entries = None
    if payload.story_id:
        story = db.query(StoryModel).filter(StoryModel.id == payload.story_id).first()
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        if mode == "continue" and not text.strip():
            last_assistant = _get_last_message_text(story, role="assistant")
            text = last_assistant or "Continue the story from the most recent assistant output. Do not repeat."
        if mode == "continue" and story.ollama_context:
            lore_entries = []
        else:
            retrieval_query = "" if mode == "continue" else text
            lore_entries = retrieve_relevant_lore(db, story.id, retrieval_query, ollama)
    elif mode == "continue" and not text.strip():
        text = "Continue the story from the most recent assistant output. Do not repeat."
    logger.debug("turn_stream_received trigger_len=%d mode=%s", len(text), mode)
    return StreamingResponse(
        stream_trigger(text, ollama, mode, story, lore_entries=lore_entries, db=db),
        media_type="text/plain",
    )


app.include_router(story_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
