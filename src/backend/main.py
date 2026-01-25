import os
import time

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from ollama import Client as OllamaClient
from pydantic import BaseModel, Field

from src.backend.api.story_routes import router as story_router
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
    trigger: str = Field(..., min_length=1)
    story_id: str | None = None


class TurnResponse(BaseModel):
    result: str


def process_trigger(trigger: str, ollama: OllamaClient, story: StoryModel | None = None) -> str:
    start = time.monotonic()
    try:
        prompt = build_prompt(story, trigger) if story else trigger
        logger.debug("ollama_request prompt=%s", prompt)
        logger.debug("ollama_request model=%s prompt_len=%d", OLLAMA_MODEL, len(prompt))
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        _log_ollama_metadata("ollama_response_meta", response)
        result = response.get("response", "").strip()
        logger.debug("ollama_response chars=%d duration_ms=%d", len(result), int((time.monotonic() - start) * 1000))
        return result
    except Exception as exc:
        logger.exception("ollama_error")
        return f"Ollama error: {exc}"


def stream_trigger(trigger: str, ollama: OllamaClient, story: StoryModel | None = None, db=None):
    start = time.monotonic()
    buffer = ""
    last_meta = {}
    try:
        prompt = build_prompt(story, trigger) if story else trigger
        logger.debug("ollama_stream_request model=%s prompt_len=%d", OLLAMA_MODEL, len(prompt))
        for part in ollama.generate(model=OLLAMA_MODEL, prompt=prompt, stream=True):
            token = part.get("response", "")
            last_meta = part or last_meta
            if token:
                buffer += token
                yield token
        logger.debug( "ollama_stream_completed duration_ms=%d", int((time.monotonic() - start) * 1000), )
        if last_meta:
            _log_ollama_metadata("ollama_stream_response_meta", last_meta)
        if story and db:
            update_story_summary(
                client=ollama,
                model=SUMMARY_MODEL,
                story=story,
                user_input=trigger,
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


def _log_ollama_metadata(prefix: str, response: dict) -> None:
    keys = [
        "model",
        "created_at",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    ]
    meta = {key: response.get(key) for key in keys if key in response}
    if meta:
        logger.debug("%s %s", prefix, meta)


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
    story = None
    if payload.story_id:
        story = db.query(StoryModel).filter(StoryModel.id == payload.story_id).first()
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    logger.debug("turn_received trigger_len=%d", len(payload.trigger))
    result = process_trigger(payload.trigger, ollama, story)
    if story:
        update_story_summary(
            client=ollama,
            model=SUMMARY_MODEL,
            story=story,
            user_input=payload.trigger,
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
    story = None
    if payload.story_id:
        story = db.query(StoryModel).filter(StoryModel.id == payload.story_id).first()
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    logger.debug("turn_stream_received trigger_len=%d", len(payload.trigger))
    return StreamingResponse(stream_trigger(payload.trigger, ollama, story, db), media_type="text/plain")


app.include_router(story_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
