import os

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

DB_URL = os.getenv("DB_URL", "sqlite:///./data.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "17000"))

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

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
    return f"Received: {trigger}"


@app.get("/health")
def healthcheck():
    return {"status": "ok", "db_url": DB_URL, "redis_url": REDIS_URL}


@app.post("/turn", response_model=TurnResponse)
def handle_turn(payload: TurnRequest, db=Depends(get_db)):
    _ = db
    result = process_trigger(payload.trigger)
    return TurnResponse(result=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
