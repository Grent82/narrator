"""Worldview Data Extraction module.

This module handles the extraction and management of worldview settings from story text.
Inspired by BookWorld's worldview data extraction approach.
"""

from src.backend.application.worldview.extractor import WorldviewExtractor
from src.backend.application.worldview.service import WorldviewService

__all__ = ["WorldviewExtractor", "WorldviewService"]
