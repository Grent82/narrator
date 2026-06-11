"""Tests for WorldviewExtractor."""

import json
from unittest.mock import MagicMock

import pytest

from src.backend.application.worldview.extractor import WorldviewExtractor, WorldviewSetting


class TestWorldviewExtractor:
    """Tests for the WorldviewExtractor class."""

    def test_parse_valid_response(self):
        """Test parsing a valid JSON response."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = json.dumps([
            {
                "term": "Invisibility Cloak",
                "nature": "artifact",
                "description": "A cloak that renders the wearer invisible",
                "source": "Chapter 9"
            },
            {
                "term": "",
                "nature": "norm",
                "description": "Wizards must not reveal magic to non-magical people",
                "source": ""
            }
        ])

        settings = extractor._parse_response(response, "default_source")

        assert len(settings) == 2
        assert settings[0].term == "Invisibility Cloak"
        assert settings[0].nature == "artifact"
        assert settings[0].description == "A cloak that renders the wearer invisible"
        assert settings[0].source == "Chapter 9"
        assert settings[1].term == ""
        assert settings[1].nature == "norm"

    def test_parse_response_with_markdown(self):
        """Test parsing response with markdown code blocks."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = "```json\n[\n  {\n    \"term\": \"Test\",\n    \"nature\": \"fact\",\n    \"description\": \"A test fact\",\n    \"source\": \"\"\n  }\n]\n```"

        settings = extractor._parse_response(response, "")

        assert len(settings) == 1
        assert settings[0].term == "Test"
        assert settings[0].nature == "fact"

    def test_parse_invalid_nature(self):
        """Test that invalid nature types are skipped."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = json.dumps([
            {
                "term": "Test",
                "nature": "invalid_nature",
                "description": "Should be skipped",
                "source": ""
            },
            {
                "term": "Valid",
                "nature": "fact",
                "description": "Should be included",
                "source": ""
            }
        ])

        settings = extractor._parse_response(response, "")

        assert len(settings) == 1
        assert settings[0].term == "Valid"

    def test_parse_missing_fields(self):
        """Test that settings with missing required fields are skipped."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = json.dumps([
            {
                "term": "No Nature",
                "description": "Missing nature",
                "source": ""
            },
            {
                "term": "No Description",
                "nature": "fact",
                "source": ""
            },
            {
                "term": "Valid",
                "nature": "fact",
                "description": "Complete",
                "source": ""
            }
        ])

        settings = extractor._parse_response(response, "")

        assert len(settings) == 1
        assert settings[0].term == "Valid"

    def test_parse_invalid_json(self):
        """Test handling of invalid JSON response."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = "This is not JSON"

        settings = extractor._parse_response(response, "")

        assert settings == []

    def test_parse_non_array_response(self):
        """Test handling of non-array JSON response."""
        extractor = WorldviewExtractor(llm=MagicMock())

        response = json.dumps({"not": "an array"})

        settings = extractor._parse_response(response, "")

        assert settings == []

    def test_chunk_text(self):
        """Test text chunking with overlap."""
        extractor = WorldviewExtractor(llm=MagicMock())

        text = "This is a test. " * 100  # 1600 characters
        chunks = extractor._chunk_text(text, chunk_size=200)

        assert len(chunks) > 1
        assert all(len(chunk) <= 250 for chunk in chunks)  # Allow some overlap

    def test_extract_from_short_text(self):
        """Test extraction from text shorter than chunk size."""
        mock_llm = MagicMock()
        mock_llm.chat.return_value = json.dumps([
            {
                "term": "Test Term",
                "nature": "fact",
                "description": "A test fact",
                "source": "test"
            }
        ])

        extractor = WorldviewExtractor(llm=mock_llm)
        settings = extractor.extract_from_chunk("Short text", "source")

        assert len(settings) == 1
        assert settings[0].term == "Test Term"
        mock_llm.chat.assert_called_once()

    def test_worldview_setting_to_dict(self):
        """Test WorldviewSetting to_dict method."""
        setting = WorldviewSetting(
            term="Test",
            nature="fact",
            description="A test",
            source="source"
        )

        result = setting.to_dict()

        assert result == {
            "term": "Test",
            "nature": "fact",
            "description": "A test",
            "source": "source"
        }
