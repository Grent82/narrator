import os
import time

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from ollama import Client as OllamaClient
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.shared.logging_config import configure_logging

app = FastAPI()

DB_URL = os.getenv("DB_URL", "sqlite:///./data.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "17000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b")
BACKEND_LOG_FILE = os.getenv("BACKEND_LOG_FILE", "logs/backend.log")
logger = configure_logging(BACKEND_LOG_FILE, "backend")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
ollama_client = OllamaClient(host=OLLAMA_URL)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TurnRequest(BaseModel):
    trigger: str = Field(..., min_length=1)


class TurnResponse(BaseModel):
    result: str


def process_trigger(trigger: str) -> str:
    start = time.monotonic()
    try:
        logger.debug("ollama_request model=%s prompt_len=%d", OLLAMA_MODEL, len(trigger))
        response = ollama_client.generate(model=OLLAMA_MODEL, prompt=trigger)
        result = response.get("response", "").strip()
        logger.debug("ollama_response chars=%d duration_ms=%d", len(result), int((time.monotonic() - start) * 1000))
        return result
    except Exception as exc:
        logger.exception("ollama_error")
        return f"Ollama error: {exc}"


def stream_trigger(trigger: str):
    start = time.monotonic()
    try:
        logger.debug("ollama_stream_request model=%s prompt_len=%d", OLLAMA_MODEL, len(trigger))
        for part in ollama_client.generate(model=OLLAMA_MODEL, prompt=trigger, stream=True):
            token = part.get("response", "")
            if token:
                yield token
        logger.debug(
            "ollama_stream_completed duration_ms=%d",
            int((time.monotonic() - start) * 1000),
        )
    except Exception as exc:
        logger.exception("ollama_stream_error")
        yield f"\n[Ollama error: {exc}]"


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "db_url": DB_URL,
        "redis_url": REDIS_URL,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
    }


@app.post("/turn", response_model=TurnResponse)
def handle_turn(payload: TurnRequest, db=Depends(get_db)):
    _ = db
    logger.debug("turn_received trigger_len=%d", len(payload.trigger))
    result = process_trigger(payload.trigger)
    logger.debug("turn_completed result_len=%d", len(result))
    return TurnResponse(result=result)


@app.post("/turn/stream")
def handle_turn_stream(payload: TurnRequest, db=Depends(get_db)):
    _ = db
    logger.debug("turn_stream_received trigger_len=%d", len(payload.trigger))
    return StreamingResponse(stream_trigger(payload.trigger), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
