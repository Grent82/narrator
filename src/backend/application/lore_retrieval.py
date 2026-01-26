import os
from typing import Any, List
from sqlalchemy.orm import Session

from src.backend.infrastructure.models import LoreEntryModel


def retrieve_relevant_lore(
    db: Session,
    story_id: str,
    user_input: str,
    ollama: Any,
) -> List[LoreEntryModel]:
    top_k = int(os.getenv("LORE_TOP_K", "8"))
    base_query = db.query(LoreEntryModel).filter(LoreEntryModel.story_id == story_id)
    return base_query.order_by(LoreEntryModel.created_at.desc()).limit(top_k).all()
