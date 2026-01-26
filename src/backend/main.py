import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from ollama import Client as OllamaClient
from pydantic import BaseModel

from src.backend.api.story_routes import router as story_router
from src.backend.application.use_cases.turn_models import TurnPayload
from src.backend.application.use_cases.lore import DbLoreRepository
from src.backend.application.use_cases.stories import DbStoryRepository
from src.backend.application.use_cases.turns import TurnSettings, TurnUseCase
from src.backend.infrastructure.db import get_db
from src.backend.infrastructure.ollama_client import get_ollama_client
from src.shared.logging_config import configure_logging

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "17000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", OLLAMA_MODEL)
SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "2400"))
RECENT_TURN_PAIRS = int(os.getenv("RECENT_TURN_PAIRS", "3"))
BACKEND_LOG_FILE = os.getenv("BACKEND_LOG_FILE", "logs/backend.log")

logger = configure_logging(BACKEND_LOG_FILE, "backend")

TURN_USE_CASE = TurnUseCase(
    TurnSettings(
        model=OLLAMA_MODEL,
        summary_model=SUMMARY_MODEL,
        summary_max_chars=SUMMARY_MAX_CHARS,
        recent_pairs=RECENT_TURN_PAIRS,
    ),
    logger,
)

class TurnRequest(BaseModel):
    text: str | None = None
    mode: str | None = None
    story_id: str | None = None
    trigger: str | None = None


class TurnResponse(BaseModel):
    result: str


def _to_turn_payload(payload: TurnRequest) -> TurnPayload:
    return TurnPayload(
        text=payload.text,
        mode=payload.mode,
        story_id=payload.story_id,
        trigger=payload.trigger,
    )


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "redis_url": REDIS_URL,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
    }


@app.post("/turn/stream")
def handle_turn_stream(
    payload: TurnRequest,
    db=Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
):
    try:
        repo = DbStoryRepository(db=db)
        lore_repo = DbLoreRepository(db=db)
        stream = TURN_USE_CASE.run_stream(_to_turn_payload(payload), repo, lore_repo, ollama)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return StreamingResponse(
        stream,
        media_type="text/plain",
    )


app.include_router(story_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
