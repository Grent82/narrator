"""Worldview Service - Use Case for worldview setting management."""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.backend.application.worldview.extractor import WorldviewExtractor, WorldviewSetting
from src.backend.infrastructure.models import WorldviewSettingModel

logger = logging.getLogger(__name__)


class WorldviewService:
    """Service for worldview setting management and extraction."""

    def __init__(self, db: Session, extractor: Optional[WorldviewExtractor] = None):
        """Initialize worldview service.

        Args:
            db: Database session
            extractor: Optional extractor instance (created if not provided)
        """
        self.db = db
        self.extractor = extractor
        self.logger = logging.getLogger(__name__)

    def set_extractor(self, extractor: WorldviewExtractor) -> None:
        """Set the extractor instance.

        Args:
            extractor: WorldviewExtractor instance
        """
        self.extractor = extractor

    def extract_and_save(
        self,
        story_id: str,
        text: str,
        chunk_size: int = 500,
        source: str = "",
        auto_merge: bool = True,
    ) -> dict:
        """Extract worldview settings from text and save to database.

        Args:
            story_id: Story ID
            text: Text to extract from
            chunk_size: Chunk size for extraction
            source: Source reference
            auto_merge: Whether to merge duplicate settings

        Returns:
            Dict with extraction stats and saved settings
        """
        if not self.extractor:
            raise ValueError("Extractor not set. Call set_extractor() first.")

        # Extract settings
        extracted = self.extractor.extract_from_text(text, chunk_size, source)
        extracted_count = len(extracted)

        if auto_merge:
            extracted = self._merge_duplicates(extracted)

        # Save to database
        saved = []
        for setting in extracted:
            # Check for existing
            existing = self.db.query(WorldviewSettingModel).filter(
                WorldviewSettingModel.story_id == story_id,
                WorldviewSettingModel.term == setting.term,
                WorldviewSettingModel.nature == setting.nature,
            ).first()

            if existing:
                # Update existing
                existing.description = setting.description
                existing.source = setting.source or existing.source
                saved.append({
                    "action": "updated",
                    "id": existing.id,
                    "term": setting.term,
                })
            else:
                # Create new
                model = WorldviewSettingModel(
                    story_id=story_id,
                    term=setting.term,
                    nature=setting.nature,
                    description=setting.description,
                    source=setting.source,
                )
                self.db.add(model)
                self.db.flush()
                saved.append({
                    "action": "created",
                    "id": model.id,
                    "term": setting.term,
                })

        self.db.commit()

        return {
            "extracted_count": extracted_count,
            "merged_count": extracted_count - len(saved),
            "saved_count": len(saved),
            "settings": saved,
        }

    def _merge_duplicates(self, settings: List[WorldviewSetting]) -> List[WorldviewSetting]:
        """Merge duplicate settings (same term + nature).

        Args:
            settings: List of settings to merge

        Returns:
            List with duplicates merged
        """
        merged = {}

        for setting in settings:
            key = (setting.term.lower(), setting.nature.lower())

            if key in merged:
                # Merge descriptions
                existing = merged[key]
                if setting.description not in existing.description:
                    existing.description += " " + setting.description
                if setting.source and not existing.source:
                    existing.source = setting.source
            else:
                merged[key] = WorldviewSetting(
                    term=setting.term,
                    nature=setting.nature,
                    description=setting.description,
                    source=setting.source,
                )

        return list(merged.values())

    def get_settings(self, story_id: str, nature: Optional[str] = None) -> List[WorldviewSettingModel]:
        """Get worldview settings for a story.

        Args:
            story_id: Story ID
            nature: Optional filter by nature type

        Returns:
            List of worldview settings
        """
        query = self.db.query(WorldviewSettingModel).filter(
            WorldviewSettingModel.story_id == story_id
        )

        if nature:
            query = query.filter(WorldviewSettingModel.nature == nature)

        return query.order_by(WorldviewSettingModel.nature, WorldviewSettingModel.term).all()

    def get_relevant_settings(
        self,
        story_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> List[WorldviewSettingModel]:
        """Get worldview settings relevant to a query.

        Currently returns all settings - future implementation will use embeddings.

        Args:
            story_id: Story ID
            query_text: Query text for relevance matching
            top_k: Number of results to return

        Returns:
            List of relevant worldview settings
        """
        # TODO: Implement embedding-based retrieval when Qdrant integration is ready
        # For now, return all settings limited by top_k
        all_settings = self.get_settings(story_id)
        return all_settings[:top_k]
