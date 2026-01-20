"""
Unified memory tool for tech tools deduplication.
Supports checking by both name and URL to avoid presenting the same tools.
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
MEMORY_FILE = MEMORY_DIR / "used_tools.json"

# Maximum entries to keep
MAX_ENTRIES = 90


def _ensure_memory_file_exists() -> None:
    """Create memory file if it doesn't exist."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        _save_memory({"tools": []})


def _load_memory() -> dict:
    """Load memory from JSON file with error handling."""
    _ensure_memory_file_exists()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Validate structure
            if not isinstance(data, dict) or "tools" not in data:
                logger.warning("Invalid memory file structure, resetting")
                return {"tools": []}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse memory file: {e}. Creating backup and resetting.")
        # Create backup of corrupted file
        backup_path = MEMORY_FILE.with_suffix(".json.bak")
        try:
            MEMORY_FILE.rename(backup_path)
        except Exception:
            pass
        return {"tools": []}
    except Exception as e:
        logger.error(f"Failed to load memory file: {e}")
        return {"tools": []}


def _save_memory(data: dict) -> None:
    """Save memory to JSON file atomically."""
    _ensure_memory_file_exists()
    try:
        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=MEMORY_DIR,
            prefix="used_tools_",
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


def _normalize_name(name: str) -> str:
    """Normalize tool name for comparison."""
    return name.lower().strip()


class CheckToolUrlInput(BaseModel):
    """Input schema for checking if a tool URL has been used."""
    url: str = Field(..., description="The URL of the tool to check")


class CheckToolUrlTool(BaseTool):
    """Tool to check if a tool URL has already been presented."""

    name: str = "check_tool_url"
    description: str = (
        "Checks if a tool has already been presented in a previous newsletter by its URL. "
        "Returns 'OUI' if the tool already exists (to avoid), 'NON' if it's new (OK to use). "
        "ALWAYS use this tool BEFORE selecting a tool to avoid duplicates."
    )
    args_schema: Type[BaseModel] = CheckToolUrlInput

    def _run(self, url: str) -> str:
        memory = _load_memory()
        normalized_url = _normalize_url(url)

        for entry in memory.get("tools", []):
            entry_url = entry.get("url", "")
            if entry_url and _normalize_url(entry_url) == normalized_url:
                return "OUI - Cet outil a deja ete presente. Cherchez un autre outil."

        return "NON - Cet outil est nouveau, vous pouvez le presenter."


class CheckToolNameInput(BaseModel):
    """Input schema for checking if a tool name has been used."""
    tool_name: str = Field(..., description="The name of the tool to check")


class CheckToolNameTool(BaseTool):
    """Tool to check if a tool name has already been presented."""

    name: str = "check_tool"
    description: str = (
        "Checks if a tool has already been presented in a previous newsletter by its name. "
        "Returns 'OUI' if the tool already exists (to avoid), 'NON' if it's new (OK to use). "
        "ALWAYS use this tool BEFORE selecting a tool to avoid duplicates."
    )
    args_schema: Type[BaseModel] = CheckToolNameInput

    def _run(self, tool_name: str) -> str:
        memory = _load_memory()
        normalized_name = _normalize_name(tool_name)

        for entry in memory.get("tools", []):
            entry_name = entry.get("name", "")
            if entry_name and _normalize_name(entry_name) == normalized_name:
                return "OUI - Cet outil a deja ete presente. Cherchez un autre outil."

        return "NON - Cet outil est nouveau, vous pouvez le presenter."


class SaveToolInput(BaseModel):
    """Input schema for saving a presented tool."""
    tool_name: str = Field(..., description="The name of the tool")
    tool_url: str = Field(default="", description="The URL of the tool (optional but recommended)")


class SaveToolTool(BaseTool):
    """Tool to save a tech tool that was presented."""

    name: str = "save_tool_url"
    description: str = (
        "Saves a tool in memory after selecting it for the newsletter. "
        "ALWAYS use this tool AFTER finalizing the tool choice to avoid "
        "reusing it in future editions. Provide both name and URL for best deduplication."
    )
    args_schema: Type[BaseModel] = SaveToolInput

    def _run(self, tool_name: str, tool_url: str = "") -> str:
        memory = _load_memory()
        normalized_name = _normalize_name(tool_name)
        normalized_url = _normalize_url(tool_url) if tool_url else ""

        # Check if already exists (by name or URL)
        for entry in memory.get("tools", []):
            entry_name = entry.get("name", "")
            entry_url = entry.get("url", "")

            if entry_name and _normalize_name(entry_name) == normalized_name:
                return "Outil deja enregistre (meme nom), pas de doublon cree."
            if normalized_url and entry_url and _normalize_url(entry_url) == normalized_url:
                return "Outil deja enregistre (meme URL), pas de doublon cree."

        # Add new entry
        new_entry = {
            "name": tool_name,
            "url": tool_url,
            "date_used": datetime.now().isoformat()
        }
        memory["tools"].append(new_entry)

        # Keep only the last MAX_ENTRIES entries
        if len(memory["tools"]) > MAX_ENTRIES:
            memory["tools"] = memory["tools"][-MAX_ENTRIES:]

        _save_memory(memory)
        return "Outil sauvegarde avec succes. Il ne sera plus propose dans les prochaines editions."


class ListUsedToolsInput(BaseModel):
    """Input schema for listing presented tools."""
    limit: int = Field(default=10, description="Number of recent tools to display (default: 10)")


class ListUsedToolsTool(BaseTool):
    """Tool to list recently presented tech tools."""

    name: str = "list_used_tools_urls"
    description: str = (
        "Lists tools recently presented in previous newsletters. "
        "Useful to quickly see which tools have already been covered."
    )
    args_schema: Type[BaseModel] = ListUsedToolsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        tools = memory.get("tools", [])

        if not tools:
            return "Aucun outil en memoire. C'est la premiere newsletter !"

        recent = tools[-limit:]
        recent.reverse()  # Most recent first

        result = f"Les {len(recent)} derniers outils presentes:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            name = entry.get("name", "Sans nom")
            url = entry.get("url", "")
            if url:
                result += f"- [{date}] {name} ({url})\n"
            else:
                result += f"- [{date}] {name}\n"

        return result


# Aliases for backward compatibility
CheckToolTool = CheckToolNameTool
