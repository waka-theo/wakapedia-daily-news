"""Tests for memory tools."""

import json
from pathlib import Path
from unittest.mock import patch


class TestNewsMemoryTool:
    """Tests for news memory tools."""

    def test_load_memory_creates_file_if_missing(self, temp_memory_dir: Path):
        """Test that memory file is created if it doesn't exist."""
        memory_file = temp_memory_dir / "used_news_urls.json"

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import _load_memory

            result = _load_memory()

            assert memory_file.exists()
            assert result == {"urls": []}

    def test_load_memory_handles_corrupted_json(self, temp_memory_dir: Path):
        """Test that corrupted JSON is handled gracefully."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text("invalid json {{{")

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import _load_memory

            result = _load_memory()

            assert result == {"urls": []}
            # Backup should be created
            assert (temp_memory_dir / "used_news_urls.json.bak").exists()

    def test_check_news_url_returns_no_for_new_url(
        self, temp_memory_dir: Path, sample_news_memory: dict
    ):
        """Test that new URLs return NON."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps(sample_news_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import CheckNewsUrlTool

            tool = CheckNewsUrlTool()
            result = tool._run("https://new-article.com/test")

            assert "NON" in result

    def test_check_news_url_returns_yes_for_existing_url(
        self, temp_memory_dir: Path, sample_news_memory: dict
    ):
        """Test that existing URLs return OUI."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps(sample_news_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import CheckNewsUrlTool

            tool = CheckNewsUrlTool()
            result = tool._run("https://techcrunch.com/article-1")

            assert "OUI" in result

    def test_check_news_url_normalizes_url(
        self, temp_memory_dir: Path, sample_news_memory: dict
    ):
        """Test that URLs are normalized for comparison."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps(sample_news_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import CheckNewsUrlTool

            tool = CheckNewsUrlTool()
            # Test with trailing slash and different case
            result = tool._run("HTTPS://TECHCRUNCH.COM/ARTICLE-1/")

            assert "OUI" in result

    def test_save_news_url_adds_entry(self, temp_memory_dir: Path):
        """Test that save adds a new entry."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps({"urls": []}))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import SaveNewsUrlTool

            tool = SaveNewsUrlTool()
            result = tool._run("https://new-article.com", "New Article Title")

            assert "sauvegardee" in result.lower()

            # Verify file was updated
            data = json.loads(memory_file.read_text())
            assert len(data["urls"]) == 1
            assert data["urls"][0]["url"] == "https://new-article.com"
            assert data["urls"][0]["title"] == "New Article Title"

    def test_save_news_url_prevents_duplicate(
        self, temp_memory_dir: Path, sample_news_memory: dict
    ):
        """Test that duplicate URLs are not added."""
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps(sample_news_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import SaveNewsUrlTool

            tool = SaveNewsUrlTool()
            result = tool._run("https://techcrunch.com/article-1", "Duplicate")

            assert "deja" in result.lower()

            # Verify count unchanged
            data = json.loads(memory_file.read_text())
            assert len(data["urls"]) == 2

    def test_save_news_url_limits_entries(self, temp_memory_dir: Path):
        """Test that memory is limited to MAX_ENTRIES."""
        # Create memory with 90 entries
        urls = [
            {"url": f"https://example.com/{i}", "title": f"Article {i}", "date_used": "2026-01-01T00:00:00"}
            for i in range(90)
        ]
        memory_file = temp_memory_dir / "used_news_urls.json"
        memory_file.write_text(json.dumps({"urls": urls}))

        with patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.news_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.news_memory_tool import SaveNewsUrlTool

            tool = SaveNewsUrlTool()
            tool._run("https://new-article.com", "New Article")

            data = json.loads(memory_file.read_text())
            assert len(data["urls"]) == 90
            # Oldest should be removed, newest should be last
            assert data["urls"][-1]["url"] == "https://new-article.com"


class TestToolMemory:
    """Tests for tool memory."""

    def test_check_tool_url_returns_no_for_new_tool(
        self, temp_memory_dir: Path, sample_tools_memory: dict
    ):
        """Test that new tools return NON."""
        memory_file = temp_memory_dir / "used_tools.json"
        memory_file.write_text(json.dumps(sample_tools_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.tool_memory.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.tool_memory.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.tool_memory import CheckToolUrlTool

            tool = CheckToolUrlTool()
            result = tool._run("https://newtool.com")

            assert "NON" in result

    def test_check_tool_url_returns_yes_for_existing_tool(
        self, temp_memory_dir: Path, sample_tools_memory: dict
    ):
        """Test that existing tool URLs return OUI."""
        memory_file = temp_memory_dir / "used_tools.json"
        memory_file.write_text(json.dumps(sample_tools_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.tool_memory.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.tool_memory.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.tool_memory import CheckToolUrlTool

            tool = CheckToolUrlTool()
            result = tool._run("https://testtool.com")

            assert "OUI" in result


class TestFactsMemory:
    """Tests for facts memory."""

    def test_check_fact_returns_no_for_new_fact(
        self, temp_memory_dir: Path, sample_facts_memory: dict
    ):
        """Test that new facts return NON."""
        memory_file = temp_memory_dir / "used_facts.json"
        memory_file.write_text(json.dumps(sample_facts_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.facts_memory_tool import CheckFactTool

            tool = CheckFactTool()
            result = tool._run("ariane 5 explosion 1996 integer overflow")

            assert "NON" in result

    def test_check_fact_detects_similar_fact(
        self, temp_memory_dir: Path, sample_facts_memory: dict
    ):
        """Test that similar facts are detected."""
        memory_file = temp_memory_dir / "used_facts.json"
        memory_file.write_text(json.dumps(sample_facts_memory))

        with patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.facts_memory_tool import CheckFactTool

            tool = CheckFactTool()
            # Similar to "first bug moth harvard 1947"
            result = tool._run("bug moth harvard mark computer 1947")

            assert "ATTENTION" in result or "OUI" in result

    def test_save_fact_adds_entry(self, temp_memory_dir: Path):
        """Test that save adds a new fact."""
        memory_file = temp_memory_dir / "used_facts.json"
        memory_file.write_text(json.dumps({"facts": []}))

        with patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_DIR",
            temp_memory_dir
        ), patch(
            "wakapedia_daily_news_generator.tools.facts_memory_tool.MEMORY_FILE",
            memory_file
        ):
            from wakapedia_daily_news_generator.tools.facts_memory_tool import SaveFactTool

            tool = SaveFactTool()
            result = tool._run("y2k bug 2000", "The Y2K bug affected many systems.")

            assert "sauvegarde" in result.lower()

            data = json.loads(memory_file.read_text())
            assert len(data["facts"]) == 1
