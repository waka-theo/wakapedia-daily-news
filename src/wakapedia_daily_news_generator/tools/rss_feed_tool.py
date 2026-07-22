"""
RSS feed tool for sourcing fresh daily content.

Provides real, dated articles from curated RSS feeds so agents always have
concrete recent material to choose from — avoiding the "I cannot provide recent
news" failure mode and increasing daily variety for tools and fun facts.

The same tool class is instantiated once per category (news / tools / facts),
each exposing a distinct tool name so the LLM can pick unambiguously.
"""

import logging
from datetime import datetime, timedelta

import feedparser
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from wakapedia_daily_news_generator.tools.news_memory_tool import _normalize_url

logger = logging.getLogger(__name__)

# Network settings
REQUEST_TIMEOUT = 10  # seconds per feed
USER_AGENT = "WakapediaDailyNews/1.0 (+https://wakastellar.com)"

# Curated feeds per category. Edit these lists to tune sources.
FEEDS: dict[str, list[tuple[str, str]]] = {
    # Tech news — mix of international and French sources, broad topic coverage.
    "news": [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
        ("VentureBeat", "https://venturebeat.com/feed/"),
        ("Hacker News", "https://hnrss.org/frontpage?points=100"),
        ("ZDNet France", "https://www.zdnet.fr/feeds/rss/actualites/"),
        (
            "Le Monde Informatique",
            "https://www.lemondeinformatique.fr/flux-rss/thematique/toutes-les-actualites/rss.xml",
        ),
        ("InfoQ", "https://feed.infoq.com/"),
    ],
    # New / lesser-known tools — feeds that surface fresh launches every day
    # so the Daily Tool stops recycling the same well-known products.
    "tools": [
        ("Product Hunt", "https://www.producthunt.com/feed"),
        ("Show HN", "https://hnrss.org/show"),
        ("BetaList", "https://betalist.com/feed"),
        ("Hacker News", "https://hnrss.org/newest?points=50"),
    ],
    # Fun facts — "This Day in Tech History" gives a different real fact every
    # day across many themes (bugs, pioneers, inventions, records, origins...),
    # exactly what avoids the constant easter-egg bias. Kept as the single
    # dedicated source; the agent still has Serper + its own knowledge on top.
    "facts": [
        ("This Day in Tech History", "https://www.thisdayintechhistory.com/feed/"),
    ],
}

# Per-category tool metadata (name + description shown to the LLM).
_TOOL_META: dict[str, dict[str, str]] = {
    "news": {
        "name": "fetch_news_feed",
        "description": (
            "Récupère une liste d'ACTUALITÉS tech RÉELLES et DATÉES depuis des flux RSS "
            "fiables (TechCrunch, The Verge, Ars Technica, VentureBeat, LeMagIT, "
            "Le Monde Informatique, Hacker News, InfoQ). "
            "À UTILISER EN PREMIER pour choisir l'actu du jour. "
            "Paramètres: max_days (fenêtre en jours, défaut 7), limit (nb max, défaut 15)."
        ),
    },
    "tools": {
        "name": "fetch_tools_feed",
        "description": (
            "Récupère une liste de NOUVEAUX OUTILS/produits tech récemment lancés depuis "
            "des flux RSS (Product Hunt, Show HN, BetaList, Hacker News). "
            "À UTILISER EN PREMIER pour trouver un outil différent et récent chaque jour. "
            "Paramètres: max_days (défaut 7), limit (défaut 15)."
        ),
    },
    "facts": {
        "name": "fetch_facts_feed",
        "description": (
            "Récupère des articles d'HISTOIRE et de culture tech depuis des flux RSS "
            "(This Day in Tech History, Computer History Museum, Ars Technica, The Register) "
            "pour inspirer un fait insolite VARIÉ (pas seulement des easter eggs). "
            "Paramètres: max_days (défaut 30 pour les faits historiques), limit (défaut 15)."
        ),
    },
}


def _parse_entry_date(entry: feedparser.FeedParserDict) -> datetime | None:
    """Extract a datetime from a feed entry, or None if unavailable."""
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            try:
                return datetime(*value[:6])
            except (TypeError, ValueError):
                continue
    return None


def get_recent_entries(
    category: str, max_days: int = 7, limit: int = 15
) -> list[dict[str, str]]:
    """
    Fetch and merge recent entries from all feeds of a category.

    Returns a list of dicts: {title, url, source, date}. Dated entries within
    the window come first (most recent first); undated entries follow.
    For the 'facts' category the recency cutoff is NOT applied — historical facts
    are timeless, so we keep all entries (sorted newest first).
    Never raises — feeds that fail are skipped.
    """
    feeds = FEEDS.get(category, FEEDS["news"])
    apply_cutoff = category != "facts"
    cutoff = datetime.now() - timedelta(days=max_days)

    dated: list[tuple[datetime, dict[str, str]]] = []
    undated: list[dict[str, str]] = []
    seen: set[str] = set()

    for source, url in feeds:
        try:
            response = requests.get(
                url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except Exception as e:  # noqa: BLE001 - one bad feed must not break the rest
            logger.warning(f"RSS feed failed ({source} {url}): {e}")
            continue

        for entry in parsed.entries:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            if not link or not title:
                continue
            norm = _normalize_url(link)
            if norm in seen:
                continue
            seen.add(norm)

            entry_date = _parse_entry_date(entry)
            record = {
                "title": title,
                "url": link,
                "source": source,
                "date": entry_date.strftime("%Y-%m-%d") if entry_date else "",
            }
            if entry_date is None:
                undated.append(record)
            elif not apply_cutoff or entry_date >= cutoff:
                dated.append((entry_date, record))

    dated.sort(key=lambda item: item[0], reverse=True)
    ordered = [record for _, record in dated] + undated
    return ordered[:limit]


class RssFeedInput(BaseModel):
    """Input schema for the RSS feed tool."""

    max_days: int = Field(
        default=7, description="Fenêtre de fraîcheur en jours (défaut 7)"
    )
    limit: int = Field(default=15, description="Nombre maximum d'entrées (défaut 15)")


class RssFeedTool(BaseTool):
    """Tool that returns a list of recent articles from curated RSS feeds."""

    name: str = "fetch_rss_feed"
    description: str = "Récupère des articles récents depuis des flux RSS."
    args_schema: type[BaseModel] = RssFeedInput
    category: str = "news"

    def __init__(self, category: str = "news") -> None:
        meta = _TOOL_META.get(category, _TOOL_META["news"])
        super().__init__(  # type: ignore[call-arg]
            name=meta["name"],
            description=meta["description"],
            category=category,
        )

    def _run(self, max_days: int = 7, limit: int = 15) -> str:
        entries = get_recent_entries(self.category, max_days=max_days, limit=limit)

        if not entries:
            return (
                "Aucun flux RSS n'a répondu pour le moment. "
                "Utilisez l'outil de recherche web (Serper) pour trouver du contenu récent."
            )

        lines = [f"{len(entries)} entrées récentes trouvées via RSS :", ""]
        for record in entries:
            date = record["date"] or "date inconnue"
            lines.append(
                f"- [{record['source']} | {date}] {record['title']} — {record['url']}"
            )
        return "\n".join(lines)
