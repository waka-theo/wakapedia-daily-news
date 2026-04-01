"""
Shared similarity utilities for content deduplication.
Used by news, tools, and facts memory modules.
"""

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
    "pas", "ne", "ni", "mais", "car", "donc", "si",
    "tout", "tous", "toute", "toutes", "autre", "autres",
    "même", "meme", "entre", "après", "apres", "avant",
    "sous", "vers", "chez", "selon", "lors", "dès", "des",
    # English
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "by",
    "with", "from", "is", "are", "was", "were", "been", "be",
    "has", "have", "had", "this", "that", "these", "those",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
    "first", "one", "two", "three", "its", "it", "not", "but",
    "and", "or", "can", "will", "just", "more", "also", "than",
    "into", "about", "over", "such", "after", "before",
])

# Canonical synonyms - different words that refer to the same concept
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
    "ia": "ai",
    "intelligence": "ai",
    "artificielle": "ai",
    "artificial": "ai",
    "learning": "ai",
    "neural": "ai",
    "neurone": "ai",
    "deep": "ai",
    "llm": "ai",
    "llms": "ai",
    "chatgpt": "ai",
    "gpt": "ai",
    "claude": "ai",
    "gemini": "ai",
    "modèle": "ai",
    "modele": "ai",
    "modèles": "ai",
    "modeles": "ai",
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
    "mariner": "space",
    # Cryptography / Security
    "cryptographie": "crypto",
    "cryptography": "crypto",
    "chiffrement": "crypto",
    "encryption": "crypto",
    "sécurité": "crypto",
    "security": "crypto",
    "hacker": "crypto",
    "pirate": "crypto",
    # SaaS / Software industry (for news dedup)
    "saas": "saas_software",
    "saaspocalypse": "saas_software",
    "logiciel": "saas_software",
    "logiciels": "saas_software",
    "software": "saas_software",
    "éditeur": "saas_software",
    "editeur": "saas_software",
    "éditeurs": "saas_software",
    "editeurs": "saas_software",
    # AI agents (for news dedup)
    "agentique": "ai_agents",
    "agent": "ai_agents",
    "agents": "ai_agents",
    # Disruption / transformation (for news dedup)
    "disruption": "disruption",
    "disrupter": "disruption",
    "disrupte": "disruption",
    "bouleverser": "disruption",
    "bouleverse": "disruption",
    "bouscule": "disruption",
    "bousculer": "disruption",
    "révolution": "disruption",
    "revolution": "disruption",
    "révolutionne": "disruption",
    "revolutionne": "disruption",
    "transformer": "disruption",
    "transforme": "disruption",
    "réinventer": "disruption",
    "reinventer": "disruption",
    "réinvente": "disruption",
    "reinvente": "disruption",
    "menace": "disruption",
    "menacer": "disruption",
    "apocalypse": "disruption",
    "panique": "disruption",
    "crise": "disruption",
    "mort": "disruption",
    "fin": "disruption",
    # Coincidences (for facts dedup)
    "coïncidence": "coincidence",
    "coincidence": "coincidence",
    "coïncidences": "coincidence",
    "coincidences": "coincidence",
    # Historical non-tech (for facts dedup)
    "titanic": "titanic_story",
    "titan": "titanic_story",
    "lincoln": "lincoln_kennedy",
    "kennedy": "lincoln_kennedy",
}


def normalize_keyword(word: str) -> str:
    """Normalize a keyword by applying synonym mapping."""
    word = word.lower().strip()
    word = word.strip(".,;:!?\"'()-")
    return SYNONYMS.get(word, word)


# Short words that are meaningful and should not be filtered by length
MEANINGFUL_SHORT_WORDS = frozenset(["ia", "ai", "ux", "ui", "ci", "cd", "qa"])


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text, removing stop words and normalizing."""
    words = text.lower().strip().split()
    keywords = set()
    for word in words:
        clean_word = word.strip(".,;:!?\"'()-")
        if not clean_word:
            continue
        if clean_word in STOP_WORDS:
            continue
        # Skip very short words unless they are meaningful acronyms
        if len(clean_word) < 3 and clean_word not in MEANINGFUL_SHORT_WORDS:
            continue
        normalized = normalize_keyword(clean_word)
        keywords.add(normalized)
    return keywords


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate keyword-based similarity between two texts.

    Uses intelligent keyword extraction:
    - Removes stop words (French and English)
    - Normalizes synonyms to canonical forms
    - Uses Jaccard-like similarity with min denominator for better detection
    """
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)

    if not keywords1 or not keywords2:
        return 0.0

    common = keywords1.intersection(keywords2)

    # Use min instead of max for more aggressive duplicate detection
    # If a short summary shares most keywords with a longer one, it's likely the same topic
    return len(common) / min(len(keywords1), len(keywords2))
