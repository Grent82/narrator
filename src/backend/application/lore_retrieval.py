import os
from typing import List

from ollama import Client as OllamaClient
from sqlalchemy.orm import Session

from src.backend.infrastructure.embeddings import embed_text
from src.backend.infrastructure.models import LoreEntryModel


def retrieve_relevant_lore(
    db: Session,
    story_id: str,
    user_input: str,
    ollama: OllamaClient,
) -> List[LoreEntryModel]:
    top_k = int(os.getenv("LORE_TOP_K", "8"))
    embedding = embed_text(ollama, user_input)
    base_query = db.query(LoreEntryModel).filter(LoreEntryModel.story_id == story_id)
    if embedding:
        results = (
            base_query.filter(LoreEntryModel.embedding.isnot(None))
            .order_by(LoreEntryModel.embedding.cosine_distance(embedding))
            .limit(top_k)
            .all()
        )
        if results:
            return results
    return base_query.order_by(LoreEntryModel.created_at.desc()).limit(top_k).all()
