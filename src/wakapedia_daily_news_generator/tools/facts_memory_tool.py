"""
Memory tool for fun facts deduplication.
Prevents presenting the same facts.
Includes robust error handling, atomic writes, and similarity detection.
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Path to memory file (at project root)
MEMORY_DIR = Path(__file__).parent.parent.parent.parent / "memory"
MEMORY_FILE = MEMORY_DIR / "used_facts.json"

# Maximum entries to keep
MAX_ENTRIES = 90

# Similarity threshold (60%)
SIMILARITY_THRESHOLD = 0.6


def _ensure_memory_file_exists() -> None:
    """Create memory file if it doesn't exist."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        _save_memory({"facts": []})


def _load_memory() -> dict:
    """Load memory from JSON file with error handling."""
    _ensure_memory_file_exists()
    try:
        with open(MEMORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
            # Validate structure
            if not isinstance(data, dict) or "facts" not in data:
                logger.warning("Invalid memory file structure, resetting")
                return {"facts": []}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse memory file: {e}. Creating backup and resetting.")
        # Create backup of corrupted file
        backup_path = MEMORY_FILE.with_suffix(".json.bak")
        try:
            MEMORY_FILE.rename(backup_path)
        except Exception:
            pass
        return {"facts": []}
    except Exception as e:
        logger.error(f"Failed to load memory file: {e}")
        return {"facts": []}


def _save_memory(data: dict) -> None:
    """Save memory to JSON file atomically."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=MEMORY_DIR,
            prefix="used_facts_",
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


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate keyword-based similarity between two texts."""
    keywords1 = set(text1.lower().strip().split())
    keywords2 = set(text2.lower().strip().split())

    if not keywords1 or not keywords2:
        return 0.0

    common = keywords1.intersection(keywords2)
    return len(common) / max(len(keywords1), len(keywords2))


class CheckFactInput(BaseModel):
    """Input schema for checking if a fun fact has been presented."""
    fact_summary: str = Field(
        ...,
        description="A short summary of the fact (a few keywords) to identify it"
    )


class CheckFactTool(BaseTool):
    """Tool to check if a fun fact has been presented."""

    name: str = "check_fact"
    description: str = (
        "Checks if a fun fact has already been presented in a previous newsletter. "
        "Provide a short summary with main keywords (e.g., 'first computer bug moth 1947'). "
        "Returns 'OUI' if the fact already exists (to avoid), 'NON' if it's new (OK to use). "
        "ALWAYS use this tool BEFORE selecting a fact to avoid duplicates."
    )
    args_schema: type[BaseModel] = CheckFactInput

    def _run(self, fact_summary: str) -> str:
        memory = _load_memory()
        normalized_summary = fact_summary.lower().strip()
        used_facts = memory.get("facts", [])

        # Check for exact match
        for entry in used_facts:
            existing = entry.get("summary", "").lower().strip()
            if normalized_summary == existing:
                return "OUI - Ce fait a deja ete presente. Cherchez un autre fun fact."

        # Check for similar facts (approximate duplicate detection)
        for entry in used_facts:
            existing = entry.get("summary", "")
            similarity = _calculate_similarity(normalized_summary, existing)
            if similarity > SIMILARITY_THRESHOLD:
                return (
                    f"ATTENTION - Ce fait semble similaire a un fait deja presente "
                    f"({existing}). Verifiez bien ou cherchez un autre fun fact."
                )

        return "NON - Ce fait est nouveau, vous pouvez le presenter."


class SaveFactInput(BaseModel):
    """Input schema for saving a presented fun fact."""
    fact_summary: str = Field(..., description="A short summary of the fact to identify it")
    fact_full: str = Field(default="", description="The complete fact (optional)")


class SaveFactTool(BaseTool):
    """Tool to save a presented fun fact."""

    name: str = "save_fact"
    description: str = (
        "Saves a fun fact in memory after selecting it for the newsletter. "
        "ALWAYS use this tool AFTER finalizing the fact choice to avoid "
        "reusing it in future editions."
    )
    args_schema: type[BaseModel] = SaveFactInput

    def _run(self, fact_summary: str, fact_full: str = "") -> str:
        memory = _load_memory()
        normalized_summary = fact_summary.lower().strip()

        # Check if fact already exists
        for entry in memory.get("facts", []):
            if entry.get("summary", "").lower().strip() == normalized_summary:
                return "Fait deja enregistre, pas de doublon cree."

        # Add new entry
        new_entry = {
            "summary": fact_summary,
            "full": fact_full,
            "date_used": datetime.now().isoformat()
        }
        memory["facts"].append(new_entry)

        # Keep only the last MAX_ENTRIES entries
        if len(memory["facts"]) > MAX_ENTRIES:
            memory["facts"] = memory["facts"][-MAX_ENTRIES:]

        _save_memory(memory)
        return "Fun fact sauvegarde avec succes. Il ne sera plus propose dans les prochaines editions."


class ListUsedFactsInput(BaseModel):
    """Input schema for listing presented fun facts."""
    limit: int = Field(default=10, description="Number of recent facts to display (default: 10)")


class ListUsedFactsTool(BaseTool):
    """Tool to list recently presented fun facts."""

    name: str = "list_used_facts"
    description: str = (
        "Lists fun facts recently presented in previous newsletters. "
        "Useful to quickly see which facts have already been covered."
    )
    args_schema: type[BaseModel] = ListUsedFactsInput

    def _run(self, limit: int = 10) -> str:
        memory = _load_memory()
        facts = memory.get("facts", [])

        if not facts:
            return "Aucun fait en memoire. C'est la premiere newsletter !"

        recent = facts[-limit:]
        recent.reverse()  # Most recent first

        result = f"Les {len(recent)} derniers fun facts presentes:\n\n"
        for entry in recent:
            date = entry.get("date_used", "date inconnue")[:10]
            summary = entry.get("summary", "Sans resume")
            result += f"- [{date}] {summary}\n"

        return result
