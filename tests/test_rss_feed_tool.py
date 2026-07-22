"""Tests for the RSS feed tool."""

import email.utils
from datetime import datetime, timedelta

import pytest

from wakapedia_daily_news_generator.tools import rss_feed_tool
from wakapedia_daily_news_generator.tools.rss_feed_tool import (
    RssFeedTool,
    get_recent_entries,
)


def _build_rss(items: list[tuple[str, str, datetime | None]]) -> bytes:
    """Build a minimal RSS document from (title, link, date) tuples."""
    body = ""
    for title, link, dt in items:
        pub = (
            f"<pubDate>{email.utils.format_datetime(dt)}</pubDate>" if dt else ""
        )
        body += f"<item><title>{title}</title><link>{link}</link>{pub}</item>"
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        f"<rss version='2.0'><channel>{body}</channel></rss>"
    ).encode()


class _FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        pass


@pytest.fixture
def single_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restrict FEEDS to one 'news' source for deterministic tests."""
    monkeypatch.setattr(
        rss_feed_tool,
        "FEEDS",
        {"news": [("TestSource", "https://example.com/feed")]},
    )


def _patch_get(monkeypatch: pytest.MonkeyPatch, content: bytes) -> None:
    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(content)

    monkeypatch.setattr(rss_feed_tool.requests, "get", fake_get)


class TestGetRecentEntries:
    def test_returns_recent_entry(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An article within the window is returned."""
        recent = datetime.now() - timedelta(days=2)
        _patch_get(
            monkeypatch,
            _build_rss([("Recent news", "https://example.com/a", recent)]),
        )
        entries = get_recent_entries("news", max_days=7)
        assert len(entries) == 1
        assert entries[0]["title"] == "Recent news"
        assert entries[0]["url"] == "https://example.com/a"
        assert entries[0]["source"] == "TestSource"

    def test_filters_out_old_entry(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An article older than max_days is excluded."""
        old = datetime.now() - timedelta(days=30)
        recent = datetime.now() - timedelta(days=1)
        _patch_get(
            monkeypatch,
            _build_rss(
                [
                    ("Old news", "https://example.com/old", old),
                    ("Fresh news", "https://example.com/fresh", recent),
                ]
            ),
        )
        entries = get_recent_entries("news", max_days=7)
        titles = [e["title"] for e in entries]
        assert "Fresh news" in titles
        assert "Old news" not in titles

    def test_deduplicates_by_url(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Same URL twice yields a single entry."""
        recent = datetime.now() - timedelta(days=1)
        _patch_get(
            monkeypatch,
            _build_rss(
                [
                    ("News A", "https://example.com/dup", recent),
                    ("News A bis", "https://example.com/dup/", recent),
                ]
            ),
        )
        entries = get_recent_entries("news", max_days=7)
        assert len(entries) == 1

    def test_sorted_most_recent_first(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Entries are returned newest first."""
        _patch_get(
            monkeypatch,
            _build_rss(
                [
                    ("Older", "https://example.com/1", datetime.now() - timedelta(days=5)),
                    ("Newer", "https://example.com/2", datetime.now() - timedelta(days=1)),
                ]
            ),
        )
        entries = get_recent_entries("news", max_days=7)
        assert [e["title"] for e in entries] == ["Newer", "Older"]

    def test_failing_feed_is_skipped(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A network error on a feed must not raise; returns empty list."""

        def boom(url: str, **kwargs: object) -> _FakeResponse:
            raise ConnectionError("network down")

        monkeypatch.setattr(rss_feed_tool.requests, "get", boom)
        entries = get_recent_entries("news", max_days=7)
        assert entries == []


class TestRssFeedTool:
    def test_tool_names_per_category(self) -> None:
        """Each category exposes a distinct tool name."""
        assert RssFeedTool(category="news").name == "fetch_news_feed"
        assert RssFeedTool(category="tools").name == "fetch_tools_feed"
        assert RssFeedTool(category="facts").name == "fetch_facts_feed"

    def test_run_formats_entries(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        recent = datetime.now() - timedelta(days=1)
        _patch_get(
            monkeypatch,
            _build_rss([("Formatted news", "https://example.com/f", recent)]),
        )
        output = RssFeedTool(category="news")._run(max_days=7, limit=5)
        assert "Formatted news" in output
        assert "https://example.com/f" in output
        assert "TestSource" in output

    def test_run_graceful_when_no_feed(
        self, single_source: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(url: str, **kwargs: object) -> _FakeResponse:
            raise ConnectionError("network down")

        monkeypatch.setattr(rss_feed_tool.requests, "get", boom)
        output = RssFeedTool(category="news")._run()
        assert "Serper" in output  # falls back to suggesting web search
