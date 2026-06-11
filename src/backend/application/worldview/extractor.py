"""Worldview Extraction Engine.

Handles LLM-based extraction of worldview settings from text chunks.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List, Literal

logger = logging.getLogger(__name__)

# Valid nature types for worldview settings
NATURE_TYPES = Literal[
    "artifact", "norm", "rule", "fact", "custom", "location_rule", "social_custom"
]


@dataclass
class WorldviewSetting:
    """Represents a single worldview setting extracted from text."""
    term: str
    nature: str
    description: str
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "term": self.term,
            "nature": self.nature,
            "description": self.description,
            "source": self.source,
        }


class WorldviewExtractor:
    """Extracts worldview settings from text using LLM."""

    EXTRACTION_PROMPT = """Du bist ein Weltwissen-Analyst. Analysiere den folgenden Textabschnitt aus einer Geschichte und extrahiere alle atomaren Welt-Fakten.

Ein "Welt-Fakt" ist:
- Eine Regel, die in dieser Welt gilt (z.B. "Zauberer duerfen sich vor Nicht-Zauberern nicht zeigen")
- Eine soziale Norm oder ein Brauch (z.B. "Adelige gruessen sich mit Verbeugung")
- Ein spezifisches Objekt oder Artefakt mit besonderen Eigenschaften
- Ein fundamentales Faktum ueber die Welt (z.B. "Die Nordmauer ist 700 Fuss hoch")
- Eine Terminologie-Erklaerung (z.B. "Ein 'Phial of Light' enthält gefangenes Sternenlicht")

NICHT extrahieren:
- Charakter-Actions oder Dialoge
- Allgemeine Common-Sense-Fakten
- Plot-spezifische Ereignisse

Verfuegbare Kategorien (nature):
- artifact: Ein spezielles Objekt oder Artefakt
- norm: Eine allgemeine Regel oder Vorschrift
- rule: Eine spezifische Regel mit Konsequenzen
- fact: Ein fundamentales Faktum ueber die Welt
- custom: Ein Brauch oder Tradition
- location_rule: Eine Regel, die fuer einen bestimmten Ort gilt
- social_custom: Ein sozialer Brauch oder Etiquette

Format: Antworte NUR mit einem validen JSON Array, keine weiteren Texte.
Jedes Element muss folgende Felder haben:
{{
    "term": "Der Begriff (falls vorhanden, sonst leer string)",
    "nature": "eine der oben genannten Kategorien",
    "description": "Klare, neutrale Beschreibung des Fakts",
    "source": "Verweis auf Quelle (Kapitel, Seite, etc. oder leer)"
}}

Textabschnitt:
{text}

Antworte NUR mit dem JSON Array:"""

    def __init__(self, llm: any):
        """Initialize extractor with LLM instance.

        Args:
            llm: LLM instance with chat method
        """
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    def extract_from_chunk(self, text: str, source: str = "") -> List[WorldviewSetting]:
        """Extract worldview settings from a single text chunk.

        Args:
            text: The text chunk to analyze
            source: Source reference (chapter, page, etc.)

        Returns:
            List of extracted worldview settings
        """
        prompt = self.EXTRACTION_PROMPT.format(text=text)

        try:
            response = self.llm.chat(prompt)
            settings = self._parse_response(response, source)
            self.logger.debug("Extracted %d settings from chunk", len(settings))
            return settings
        except Exception as e:
            self.logger.error("Extraction failed: %s", e)
            return []

    def _parse_response(self, response: str, source: str) -> List[WorldviewSetting]:
        """Parse LLM response into WorldviewSetting objects.

        Args:
            response: Raw LLM response (should be JSON array)
            source: Default source if not in response

        Returns:
            List of parsed worldview settings
        """
        try:
            # Clean response in case of markdown code blocks
            response = response.strip()

            # Remove markdown code block wrappers
            if response.startswith("```"):
                # Find the JSON content between ``` markers
                start_idx = response.find("\n")
                if start_idx != -1:
                    # Find the closing ```
                    end_idx = response.rfind("```")
                    if end_idx != -1:
                        response = response[start_idx + 1:end_idx].strip()
                    else:
                        # No closing marker, skip the first line (language identifier)
                        response = response[start_idx + 1:].strip()
                else:
                    # Just ``` with nothing else
                    response = ""

            # Also handle json prefix on first line
            if response.startswith("json"):
                response = response[4:].strip()

            data = json.loads(response)

            if not isinstance(data, list):
                self.logger.warning("Expected array, got %s", type(data))
                return []

            settings = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                term = str(item.get("term", "")).strip()
                nature = str(item.get("nature", "")).strip().lower()
                description = str(item.get("description", "")).strip()
                item_source = str(item.get("source", "")).strip() or source

                # Validate
                if not nature or not description:
                    continue

                # Validate nature type
                valid_natures = ["artifact", "norm", "rule", "fact", "custom", "location_rule", "social_custom"]
                if nature not in valid_natures:
                    self.logger.warning("Invalid nature '%s', skipping", nature)
                    continue

                settings.append(WorldviewSetting(
                    term=term,
                    nature=nature,
                    description=description,
                    source=item_source,
                ))

            return settings

        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse JSON response: %s", e)
            self.logger.debug("Response was: %s", response[:500])
            return []
        except Exception as e:
            self.logger.error("Unexpected error parsing response: %s", e)
            return []

    def extract_from_text(self, text: str, chunk_size: int = 500, source: str = "") -> List[WorldviewSetting]:
        """Extract worldview settings from full text with chunking.

        Args:
            text: Full text to analyze
            chunk_size: Approximate chunk size in characters
            source: Base source reference

        Returns:
            List of all extracted worldview settings
        """
        if len(text) <= chunk_size:
            return self.extract_from_chunk(text, source)

        # Split into chunks
        chunks = self._chunk_text(text, chunk_size)
        all_settings = []

        for i, chunk in enumerate(chunks):
            chunk_source = f"{source} (Part {i+1}/{len(chunks)})" if source else f"Part {i+1}/{len(chunks)}"
            settings = self.extract_from_chunk(chunk, chunk_source)
            all_settings.extend(settings)

        return all_settings

    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Target chunk size

        Returns:
            List of text chunks
        """
        chunks = []
        overlap = 50  # Characters of overlap between chunks

        start = 0
        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence boundary
                for sep in [". ", ".\n", "!\n", "!\n", "?\n"]:
                    idx = text.rfind(sep, start, end)
                    if idx > start + chunk_size // 2:
                        end = idx + len(sep)
                        break

            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - overlap

            if start >= len(text):
                break

        return chunks
