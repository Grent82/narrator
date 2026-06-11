"""Tests for WorldviewSettingModel."""

from src.backend.infrastructure.models import WorldviewSettingModel, _generate_id


class TestWorldviewSettingModel:
    """Tests for the WorldviewSettingModel class."""

    def test_setting_creation_with_term(self):
        """Test creating a worldview setting with a term."""
        setting = WorldviewSettingModel(
            id=_generate_id(),
            story_id="test-story-id",
            term="Invisibility Cloak",
            nature="artifact",
            description="A cloak that renders the wearer invisible to the naked eye",
            source="Chapter 9: The Midnight Duel",
        )
        assert setting.id is not None
        assert setting.story_id == "test-story-id"
        assert setting.term == "Invisibility Cloak"
        assert setting.nature == "artifact"
        assert setting.description == "A cloak that renders the wearer invisible to the naked eye"
        assert setting.source == "Chapter 9: The Midnight Duel"

    def test_setting_creation_without_term(self):
        """Test creating a worldview setting without a term (general rule)."""
        setting = WorldviewSettingModel(
            id=_generate_id(),
            story_id="test-story-id",
            term="",
            nature="norm",
            description="Wizards must not reveal their magic to non-magical people",
            source="International Wizarding Accord",
        )
        assert setting.term == ""
        assert setting.nature == "norm"

    def test_setting_nature_types(self):
        """Test different nature types."""
        nature_types = ["artifact", "norm", "rule", "fact", "custom", "location_rule", "social_custom"]
        for nature in nature_types:
            setting = WorldviewSettingModel(
                id=_generate_id(),
                story_id="test-story-id",
                term=f"Test {nature}",
                nature=nature,
                description=f"A {nature} type setting",
            )
            assert setting.nature == nature

    def test_setting_table_name(self):
        """Test that worldview setting has correct table name."""
        assert WorldviewSettingModel.__tablename__ == "worldview_settings"

    def test_setting_column_names(self):
        """Test that worldview setting has correct column names."""
        columns = [c.name for c in WorldviewSettingModel.__table__.columns]
        assert "id" in columns
        assert "story_id" in columns
        assert "term" in columns
        assert "nature" in columns
        assert "description" in columns
        assert "source" in columns
