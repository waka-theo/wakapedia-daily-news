"""
Memory tool for news URLs deduplication.
Prevents republishing the same news articles.
Includes robust error handling and atomic write operations.
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Path to memory file (at project root)
MEMORY_DIR = Path(__file__).parent.parent.parent.parent / "memory"
MEMORY_FILE = MEMORY_DIR / "used_news_urls.json"

# Maximum entries to keep
MAX_ENTRIES = 90


def _ensure_memory_file_exists() -> None:
    """Create memory file if it doesn't exist."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        _save_memory({"urls": []})


def _load_memory() -> dict:
    """Load memory from JSON file with error handling."""
    _ensure_memory_file_exists()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Validate structure
            if not isinstance(data, dict) or "urls" not in data:
                logger.warning("Invalid memory file structure, resetting")
                return {"urls": []}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse memory file: {e}. Creating backup and resetting.")
        # Create backup of corrupted file
        backup_path = MEMORY_FILE.with_suffix(".json.bak")
        try:
            MEMORY_FILE.rename(backup_path)
        except Exception:
            pass
        return {"urls": []}
    except Exception as e:
        logger.error(f"Failed to load memory file: {e}")
        return {"urls": []}


def _save_memory(data: dict) -> None:
    """Save memory to JSON file atomically."""
    _ensure_memory_file_exists()
    try:
        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=MEMORY_DIR,
            prefix="used_news_urls_",
            suffix=".tmp"
        )
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Atomic replace
            os.replace(temp_path, MEMORY_FILE)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise
    except Exception as e:
        logger.error(f"Failed to save memory file: {e}")
        raise


def _normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    return url.rstrip("/").lower().strip()


class CheckNewsUrlInput(BaseModel):
    """Input schema for checking if a URL has been used."""
    url: str = Field(..., description="The article URL to check")


class CheckNewsUrlTool(BaseTool):
    """Tool to check if a news URL has been used."""

    name: str = "check_news_url"
    description: str = (
        "Checks if an article URL has already been used in a previous newsletter. "
        "Returns 'OUI' if the URL already exists (to avoid), 'NON' if it's new (OK to use). "
        "ALWAYS use this tool BEFORE selecting an article to avoid duplicates."
    )
    args_schema: Type[BaseModel] = CheckNewsUrlInput

    def _run(self, url: str) -> str:
        memory = _load_memory()
        normalized_url = _normalize_url(url)

        for entry in memory.get("urls", []):
            entry_url = entry.get("url", "")
            if _normalize_url(entry_url) == normalized_url:
                return "OUI - Cette URL a deja ete utilisee. Cherchez un autre article."

        return "NON - Cette URL est nouvelle, vous pouvez l'utiliser."


class SaveNewsUrlInput(BaseModel):
    """Input schema for saving a used URL."""
    url: str = Field(..., description="The article URL to save")
    title: str = Field(..., description="The article title")


class SaveNewsUrlTool(BaseTool):
    """Tool to save a used news URL."""

    name: str = "save_news_url"
    description: str = (
        "Saves an article URL in memory after selecting it for the newsletter. "
        "ALWAYS use this tool AFTER finalizing the article choice to avoid "
        "reusing it in future editions."
    )
    args_schema: Type[BaseModel] = SaveNewsUrlInput

    def _run(self, url: str, title: str) -> str:
        memory = _load_memory()
        normalized_url = _normalize_url(url)

        # Check if URL already exists
        for entry in memory.get("urls", []):
            if _normalize_url(entry.get("url", "")) == normalized_url:
                return "URL deja enregistree, pas de doublon cree."

        # Add new entry
        new_entry = {
            "url": url,
            "title": title,
            "date_used": datetime.now().isoformat()
        }
        memory["urls"].append(new_entry)

        # Keep only the last MAX_ENTRIES entries
        if len(memory["urls"]) > MAX_ENTRIES:
            memory["urls"] = memory["urls"][-MAX_ENTRIES:]

        _save_memory(memory)
        return "URL sauvegardee avec succes. Elle ne sera plus proposee dans les prochaines editions."


class ListUsedNewsUrlsInput(BaseModel):
    """Input schema for listing used URLs."""
    limit: int = Field(default=10, description="Number of recent URLs to display (default: 10)")


class ListUsedNewsUrlsTool(BaseTool):
    """Tool to list recently used news URLs."""

    name: str = "list_used_news_urls"
    description: str = (
        "Lists article URLs recently used in previous newsletters. "
        "Useful to quickly see which topics have already been covered."
    )
    args_schema: Type[BaseModel] = ListUsedNewsUrlsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        urls = memory.get("urls", [])

        if not urls:
            return "Aucune URL en memoire. C'est la premiere newsletter !"

        recent = urls[-limit:]
        recent.reverse()  # Most recent first

        result = f"Les {len(recent)} dernieres URLs utilisees:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            title = entry.get("title", "Sans titre")
            result += f"- [{date}] {title}\n"

        return result
