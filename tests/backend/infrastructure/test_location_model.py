"""Tests for Location and Travel models."""

import pytest
from src.backend.infrastructure.models import LocationModel, TravelTaskModel, _generate_id


class TestLocationModel:
    """Tests for the LocationModel class."""

    def test_location_creation(self):
        """Test creating a location with required fields."""
        location = LocationModel(
            id=_generate_id(),
            story_id="test-story-id",
            name="Dark Forest",
            description="A mysterious forest with ancient trees",
            tag="Wilderness",
            location_metadata={},
        )
        assert location.id is not None
        assert location.story_id == "test-story-id"
        assert location.name == "Dark Forest"
        assert location.description == "A mysterious forest with ancient trees"
        assert location.tag == "Wilderness"

    def test_location_with_metadata(self):
        """Test creating a location with metadata."""
        location = LocationModel(
            id=_generate_id(),
            story_id="test-story-id",
            name="Ancient Ruins",
            description="Ruins of a forgotten civilization",
            tag="Landmark",
            location_metadata={"danger_level": "high", "accessible_by": ["warriors", "explorers"]},
        )
        assert location.location_metadata["danger_level"] == "high"
        assert "warriors" in location.location_metadata["accessible_by"]

    def test_location_table_name(self):
        """Test that location has correct table name."""
        assert LocationModel.__tablename__ == "locations"

    def test_location_column_names(self):
        """Test that location has correct column names including mapped metadata."""
        columns = [c.name for c in LocationModel.__table__.columns]
        assert "id" in columns
        assert "story_id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "tag" in columns
        assert "metadata" in columns  # DB column name
        assert "location_metadata" in columns or "metadata" in columns


class TestTravelTaskModel:
    """Tests for the TravelTaskModel class."""

    def test_travel_creation(self):
        """Test creating a travel task."""
        task = TravelTaskModel(
            id=_generate_id(),
            story_id="test-story-id",
            character_name="Hero",
            from_location_id="location-1",
            to_location_id="location-2",
            distance=3,
            remaining_turns=3,
        )
        assert task.id is not None
        assert task.character_name == "Hero"
        assert task.distance == 3
        assert task.remaining_turns == 3

    def test_travel_custom_distance(self):
        """Test creating a travel task with custom distance."""
        task = TravelTaskModel(
            id=_generate_id(),
            story_id="test-story-id",
            character_name="Hero",
            to_location_id="location-2",
            distance=5,
            remaining_turns=5,
        )
        assert task.distance == 5
        assert task.remaining_turns == 5

    def test_travel_completed_status(self):
        """Test updating a travel task to completed."""
        from datetime import datetime

        task = TravelTaskModel(
            id=_generate_id(),
            story_id="test-story-id",
            character_name="Hero",
            to_location_id="location-2",
            distance=3,
            remaining_turns=3,
        )
        task.status = "completed"
        task.completed_at = datetime.now()
        assert task.status == "completed"
        assert task.completed_at is not None

    def test_travel_table_name(self):
        """Test that travel task has correct table name."""
        assert TravelTaskModel.__tablename__ == "travel_tasks"
