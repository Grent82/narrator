import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.backend.api.story_routes import router as story_router
from src.backend.application.model_profiles import infer_model_profile_id
from src.backend.application.use_cases.lore import DbLoreRepository
from src.backend.application.use_cases.stories import DbStoryRepository
from src.backend.application.use_cases.turn_models import TurnPayload
from src.backend.application.use_cases.turns import TurnSettings, TurnUseCase
from src.backend.infrastructure.db import get_db
from src.backend.infrastructure.langchain_clients import get_chat_model, get_embedding_model
from src.backend.infrastructure.llm_config import (
    active_chat_model_name,
    active_provider_name,
    active_summary_model_name,
)
from src.shared.logging_config import configure_logging

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "17000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = active_chat_model_name()
SUMMARY_MODEL = active_summary_model_name()
MODEL_PROFILE_ID = infer_model_profile_id(OLLAMA_MODEL, os.getenv("MODEL_PROFILE"))
SUMMARY_MODEL_PROFILE_ID = infer_model_profile_id(SUMMARY_MODEL, os.getenv("SUMMARY_MODEL_PROFILE"))
SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "1200"))
RECENT_TURN_PAIRS = int(os.getenv("RECENT_TURN_PAIRS", "3"))
RECENT_TURN_OVERLAP = int(os.getenv("RECENT_TURN_OVERLAP", "2"))
BACKEND_LOG_FILE = os.getenv("BACKEND_LOG_FILE", "logs/backend.log")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:17080,http://127.0.0.1:17080").split(",")
    if origin.strip()
]

logger = configure_logging(BACKEND_LOG_FILE, "backend")
DB_DEPENDENCY = Depends(get_db)
CHAT_MODEL_DEPENDENCY = Depends(get_chat_model)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TURN_USE_CASE = TurnUseCase(
    TurnSettings(
        model=OLLAMA_MODEL,
        summary_model=SUMMARY_MODEL,
        summary_max_chars=SUMMARY_MAX_CHARS,
        model_profile_id=MODEL_PROFILE_ID,
        summary_model_profile_id=SUMMARY_MODEL_PROFILE_ID,
        recent_pairs=RECENT_TURN_PAIRS,
        overlap_pairs=RECENT_TURN_OVERLAP,
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
        "llm_provider": active_provider_name(),
        "llm_model": OLLAMA_MODEL,
        "model_profile": MODEL_PROFILE_ID,
        "summary_model": SUMMARY_MODEL,
        "summary_model_profile": SUMMARY_MODEL_PROFILE_ID,
    }


@app.post("/turn/stream")
def handle_turn_stream(
    payload: TurnRequest,
    db=DB_DEPENDENCY,
    chat_model=CHAT_MODEL_DEPENDENCY,
):
    try:
        repo = DbStoryRepository(db=db)
        lore_repo = DbLoreRepository(embeddings=get_embedding_model())
        stream = TURN_USE_CASE.run_stream(_to_turn_payload(payload), repo, lore_repo, chat_model)
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
