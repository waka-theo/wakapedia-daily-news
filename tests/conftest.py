"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_memory_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for memory files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_news_memory() -> dict:
    """Sample news memory data."""
    return {
        "urls": [
            {
                "url": "https://techcrunch.com/article-1",
                "title": "Test Article 1",
                "date_used": "2026-01-15T08:00:00"
            },
            {
                "url": "https://theverge.com/article-2",
                "title": "Test Article 2",
                "date_used": "2026-01-16T08:00:00"
            }
        ]
    }


@pytest.fixture
def sample_tools_memory() -> dict:
    """Sample tools memory data."""
    return {
        "tools": [
            {
                "name": "TestTool",
                "url": "https://testtool.com",
                "date_used": "2026-01-15T08:00:00"
            },
            {
                "name": "AnotherTool",
                "url": "https://anothertool.io",
                "date_used": "2026-01-16T08:00:00"
            }
        ]
    }


@pytest.fixture
def sample_facts_memory() -> dict:
    """Sample facts memory data."""
    return {
        "facts": [
            {
                "summary": "first bug moth harvard 1947",
                "full": "The first computer bug was a moth found in Harvard Mark II in 1947.",
                "date_used": "2026-01-15T08:00:00"
            },
            {
                "summary": "python name monty python",
                "full": "Python is named after Monty Python, not the snake.",
                "date_used": "2026-01-16T08:00:00"
            }
        ]
    }


@pytest.fixture
def sample_crew_output() -> str:
    """Sample HTML output from the crew."""
    return """
    <html>
    <body>
    <h2>Daily News</h2>
    <p><strong>OpenAI lance GPT-5</strong> - OpenAI a annonce aujourd'hui le lancement de GPT-5,
    son nouveau modele de langage. Cette nouvelle version promet des ameliorations significatives
    en termes de comprehension et de generation de texte.
    <a href="https://techcrunch.com/openai-gpt5">Lire plus</a></p>

    <h2>Daily Tool</h2>
    <p><strong>Cursor AI</strong> - Un editeur de code base sur l'IA qui revolutionne
    le developpement logiciel avec des suggestions intelligentes.
    <a href="https://cursor.sh">Decouvrir</a></p>

    <h2>Daily Fun Fact</h2>
    <p>Le premier bug informatique documente etait un vrai papillon de nuit trouve dans
    le Harvard Mark II en 1947 par Grace Hopper.</p>
    </body>
    </html>
    """


@pytest.fixture
def empty_crew_output() -> str:
    """Sample empty/malformed output from the crew."""
    return "<html><body>Error occurred</body></html>"
