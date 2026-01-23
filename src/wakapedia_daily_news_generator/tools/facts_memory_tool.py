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

# Similarity threshold (40% - more strict to catch reformulations)
SIMILARITY_THRESHOLD = 0.4

# French and English stop words to ignore in similarity calculation
STOP_WORDS = frozenset([
    # French
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    "et", "ou", "a", "au", "aux", "en", "dans", "sur", "pour", "par",
    "avec", "sans", "est", "sont", "été", "était", "ce", "cette", "ces",
    "qui", "que", "dont", "où", "quand", "comment", "pourquoi",
    "son", "sa", "ses", "leur", "leurs", "mon", "ma", "mes",
    "il", "elle", "ils", "elles", "on", "nous", "vous",
    "plus", "moins", "très", "bien", "aussi", "comme", "ainsi",
    "premier", "première", "premiers", "premières",
    "avoir", "être", "fait", "faire", "été",
    # English
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "by",
    "with", "from", "is", "are", "was", "were", "been", "be",
    "has", "have", "had", "this", "that", "these", "those",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
    "first", "one", "two", "three",
])

# Canonical synonyms - different words that refer to the same concept
# Maps variants to a canonical form
SYNONYMS = {
    # Bug/insect story
    "mite": "bug_insect",
    "moth": "bug_insect",
    "papillon": "bug_insect",
    "insecte": "bug_insect",
    # Bug term
    "bug": "bug_term",
    "bogue": "bug_term",
    "erreur": "bug_term",
    # Grace Hopper
    "hopper": "grace_hopper",
    "grace": "grace_hopper",
    # Harvard Mark II
    "harvard": "harvard_mark",
    "mark": "harvard_mark",
    # Computer terms
    "ordinateur": "computer",
    "computer": "computer",
    "informatique": "computer",
    "machine": "computer",
    # Origin/history
    "origine": "origin",
    "origin": "origin",
    "histoire": "origin",
    "history": "origin",
    "naissance": "origin",
    # Year references - grouped by decade
    "1947": "year_1940s",
    "1940": "year_1940s",
    "1940s": "year_1940s",
    "1990": "year_1990s",
    "1990s": "year_1990s",
    "1995": "year_1990s",
    "1996": "year_1990s",
    "1997": "year_1990s",
    "1998": "year_1990s",
    "1999": "year_1990s",
    # Easter eggs / hidden features
    "easter": "easter_egg",
    "egg": "easter_egg",
    "caché": "easter_egg",
    "cache": "easter_egg",
    "hidden": "easter_egg",
    "secret": "easter_egg",
    # Simulators/games
    "simulateur": "simulator_game",
    "simulator": "simulator_game",
    "jeu": "simulator_game",
    "game": "simulator_game",
    "vol": "flight_sim",
    "flight": "flight_sim",
    # Spreadsheet software
    "excel": "spreadsheet",
    "tableur": "spreadsheet",
    "spreadsheet": "spreadsheet",
    "calc": "spreadsheet",
    # Microsoft / Office
    "microsoft": "microsoft",
    "office": "microsoft",
    # Developers
    "développeur": "developer",
    "developpeur": "developer",
    "developer": "developer",
    "programmeur": "developer",
    "programmer": "developer",
    "ingénieur": "developer",
    "ingenieur": "developer",
    "engineer": "developer",
    # Email
    "email": "email",
    "mail": "email",
    "courriel": "email",
    "courrier": "email",
    # Network / Internet
    "internet": "network",
    "arpanet": "network",
    "réseau": "network",
    "reseau": "network",
    "network": "network",
    "web": "network",
    # AI / Machine Learning
    "intelligence": "ai",
    "artificielle": "ai",
    "artificial": "ai",
    "learning": "ai",
    "neural": "ai",
    "neurone": "ai",
    "deep": "ai",
    # Programming languages
    "langage": "programming",
    "language": "programming",
    "programmation": "programming",
    "programming": "programming",
    "code": "programming",
    "coder": "programming",
    # Space / NASA
    "nasa": "space",
    "spatial": "space",
    "space": "space",
    "apollo": "space",
    "lune": "space",
    "moon": "space",
    "fusée": "space",
    "rocket": "space",
    # Cryptography / Security
    "cryptographie": "crypto",
    "cryptography": "crypto",
    "chiffrement": "crypto",
    "encryption": "crypto",
    "sécurité": "crypto",
    "security": "crypto",
    "hacker": "crypto",
    "pirate": "crypto",
}


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


def _normalize_keyword(word: str) -> str:
    """Normalize a keyword by applying synonym mapping."""
    word = word.lower().strip()
    # Remove common punctuation
    word = word.strip(".,;:!?\"'()-")
    # Apply synonym mapping
    return SYNONYMS.get(word, word)


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text, removing stop words and normalizing."""
    words = text.lower().strip().split()
    keywords = set()
    for word in words:
        # Clean punctuation
        clean_word = word.strip(".,;:!?\"'()-")
        if not clean_word:
            continue
        # Skip stop words
        if clean_word in STOP_WORDS:
            continue
        # Skip very short words (likely not meaningful)
        if len(clean_word) < 3:
            continue
        # Normalize via synonyms
        normalized = _normalize_keyword(clean_word)
        keywords.add(normalized)
    return keywords


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate keyword-based similarity between two texts.

    Uses intelligent keyword extraction:
    - Removes stop words (French and English)
    - Normalizes synonyms to canonical forms
    - Uses Jaccard-like similarity with min denominator for better detection
    """
    keywords1 = _extract_keywords(text1)
    keywords2 = _extract_keywords(text2)

    if not keywords1 or not keywords2:
        return 0.0

    common = keywords1.intersection(keywords2)

    # Use min instead of max for more aggressive duplicate detection
    # If a short summary shares most keywords with a longer one, it's likely the same topic
    return len(common) / min(len(keywords1), len(keywords2))


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
