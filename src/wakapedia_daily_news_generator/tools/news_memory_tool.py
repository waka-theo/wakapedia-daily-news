"""
Memory tool for news URLs deduplication.
Prevents republishing the same news articles.
Includes robust error handling, atomic write operations,
and title-based similarity detection to avoid covering the same theme.
"""

import json
import logging
import os
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from wakapedia_daily_news_generator.tools.similarity_utils import (
    calculate_similarity,
    extract_keywords,
)

logger = logging.getLogger(__name__)

# Similarity threshold for news titles (higher than facts because titles are shorter)
NEWS_TITLE_SIMILARITY_THRESHOLD = 0.5

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
        with open(MEMORY_FILE, encoding="utf-8") as f:
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
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
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
    args_schema: type[BaseModel] = CheckNewsUrlInput

    def _run(self, url: str) -> str:
        memory = _load_memory()
        normalized_url = _normalize_url(url)

        for entry in memory.get("urls", []):
            entry_url = entry.get("url", "")
            if _normalize_url(entry_url) == normalized_url:
                return "OUI - Cette URL a deja ete utilisee. Cherchez un autre article."

        return "NON - Cette URL est nouvelle, vous pouvez l'utiliser."


class CheckNewsTitleInput(BaseModel):
    """Input schema for checking if a news title/topic has been covered."""
    title: str = Field(..., description="The article title to check for topic similarity")


class CheckNewsTitleTool(BaseTool):
    """Tool to check if a news topic has already been covered."""

    name: str = "check_news_title"
    description: str = (
        "Checks if an article TOPIC has already been covered in a previous newsletter. "
        "Provide the article title. Returns 'OUI' if a similar topic was already covered "
        "(even from a different source). Use this BEFORE check_news_url to avoid "
        "covering the same theme from different sources."
    )
    args_schema: type[BaseModel] = CheckNewsTitleInput

    def _run(self, title: str) -> str:
        memory = _load_memory()
        used_urls = memory.get("urls", [])

        for entry in used_urls:
            existing_title = entry.get("title", "")
            if not existing_title:
                continue
            similarity = calculate_similarity(title, existing_title)
            if similarity > NEWS_TITLE_SIMILARITY_THRESHOLD:
                date = entry.get("date_used", "")[:10]
                return (
                    f"OUI - Ce theme a deja ete couvert: "
                    f"'{existing_title}' ({date}). "
                    f"Cherchez un article sur un THEME DIFFERENT."
                )

        return "NON - Ce theme est nouveau, vous pouvez continuer avec check_news_url."


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
    args_schema: type[BaseModel] = SaveNewsUrlInput

    def _run(self, url: str, title: str) -> str:
        memory = _load_memory()
        normalized_url = _normalize_url(url)

        # Check if URL already exists
        for entry in memory.get("urls", []):
            if _normalize_url(entry.get("url", "")) == normalized_url:
                return "URL deja enregistree, pas de doublon cree."

        # Gate: check title similarity before allowing save
        for entry in memory.get("urls", []):
            existing_title = entry.get("title", "")
            if not existing_title:
                continue
            similarity = calculate_similarity(title, existing_title)
            if similarity > NEWS_TITLE_SIMILARITY_THRESHOLD:
                date = entry.get("date_used", "")[:10]
                return (
                    f"REFUSE - Ce theme a deja ete couvert: "
                    f"'{existing_title}' ({date}). "
                    f"Cherchez un article sur un THEME COMPLETEMENT DIFFERENT."
                )

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
    limit: int = Field(default=20, description="Number of recent URLs to display (default: 20)")


class ListUsedNewsUrlsTool(BaseTool):
    """Tool to list recently used news URLs."""

    name: str = "list_used_news_urls"
    description: str = (
        "Lists article URLs recently used in previous newsletters. "
        "Useful to quickly see which topics have already been covered "
        "and identify recurring themes to AVOID."
    )
    args_schema: type[BaseModel] = ListUsedNewsUrlsInput

    def _run(self, limit: int = 20) -> str:
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

        # Add theme frequency summary
        all_keywords: list[str] = []
        for entry in urls:
            title = entry.get("title", "")
            if title:
                all_keywords.extend(extract_keywords(title))

        if all_keywords:
            theme_counts = Counter(all_keywords)
            top_themes = theme_counts.most_common(5)
            result += "\n--- THEMES LES PLUS FREQUENTS (a eviter) ---\n"
            for theme, count in top_themes:
                if count >= 2:
                    result += f"- '{theme}' : {count} fois\n"

        return result
