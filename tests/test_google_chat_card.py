"""Tests for Google Chat card generation."""

from datetime import datetime
from unittest.mock import patch

import pytest

from wakapedia_daily_news_generator.google_chat_card import create_simple_card


class TestCreateSimpleCard:
    """Tests for Google Chat card creation."""

    def test_creates_valid_card_structure(self):
        """Test that card has valid structure."""
        card = create_simple_card(
            news_title="Test News",
            news_content="News content here",
            tool_title="Test Tool",
            tool_content="Tool content here",
            fun_content="Fun fact here"
        )

        assert "cards" in card
        assert len(card["cards"]) == 1
        assert "header" in card["cards"][0]
        assert "sections" in card["cards"][0]

    def test_includes_header_with_title(self):
        """Test that header includes title."""
        card = create_simple_card(
            news_title="Test News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact"
        )

        header = card["cards"][0]["header"]
        assert header["title"] == "Wakapedia Daily News"

    def test_includes_date_in_subtitle(self):
        """Test that subtitle includes formatted date."""
        with patch("wakapedia_daily_news_generator.google_chat_card.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15)  # Wednesday

            card = create_simple_card(
                news_title="News",
                news_content="Content",
                tool_title="Tool",
                tool_content="Content",
                fun_content="Fact"
            )

            subtitle = card["cards"][0]["header"]["subtitle"]
            assert "Mercredi" in subtitle
            assert "15" in subtitle
            assert "Janvier" in subtitle
            assert "2026" in subtitle

    def test_has_four_sections(self):
        """Test that card has four sections (news, tool, fact, footer)."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact"
        )

        sections = card["cards"][0]["sections"]
        assert len(sections) == 4

    def test_includes_news_link_button(self):
        """Test that news section includes link button when provided."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact",
            news_link="https://example.com/news"
        )

        news_section = card["cards"][0]["sections"][0]
        widgets = news_section["widgets"]

        # Find button widget
        button_widget = None
        for widget in widgets:
            if "buttons" in widget:
                button_widget = widget
                break

        assert button_widget is not None
        assert widgets[-1]["buttons"][0]["textButton"]["onClick"]["openLink"]["url"] == "https://example.com/news"

    def test_excludes_news_link_button_when_empty(self):
        """Test that news section excludes button when no link."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact",
            news_link=""
        )

        news_section = card["cards"][0]["sections"][0]
        widgets = news_section["widgets"]

        # Should not have button widget
        for widget in widgets:
            assert "buttons" not in widget

    def test_includes_tool_link_button(self):
        """Test that tool section includes link button when provided."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact",
            tool_link="https://example.com/tool"
        )

        tool_section = card["cards"][0]["sections"][1]
        widgets = tool_section["widgets"]

        # Find button widget
        has_button = any("buttons" in widget for widget in widgets)
        assert has_button

    def test_includes_logo_when_provided(self):
        """Test that logo is included in header when provided."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact",
            logo_url="https://example.com/logo.png"
        )

        header = card["cards"][0]["header"]
        assert header["imageUrl"] == "https://example.com/logo.png"
        assert header["imageStyle"] == "AVATAR"

    def test_excludes_logo_when_not_provided(self):
        """Test that logo is not included when not provided."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact"
        )

        header = card["cards"][0]["header"]
        assert "imageUrl" not in header

    def test_formats_content_with_html(self):
        """Test that content is formatted with HTML."""
        card = create_simple_card(
            news_title="Test Title",
            news_content="Test Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact"
        )

        news_section = card["cards"][0]["sections"][0]

        # Find title widget
        title_found = False
        for widget in news_section["widgets"]:
            if "textParagraph" in widget:
                text = widget["textParagraph"]["text"]
                if "<b>Test Title</b>" in text:
                    title_found = True
                    break

        assert title_found

    def test_includes_section_headers_with_colors(self):
        """Test that section headers have colored formatting."""
        card = create_simple_card(
            news_title="News",
            news_content="Content",
            tool_title="Tool",
            tool_content="Content",
            fun_content="Fact"
        )

        news_section = card["cards"][0]["sections"][0]
        first_widget = news_section["widgets"][0]

        text = first_widget["textParagraph"]["text"]
        assert "<font color=" in text
        assert "DAILY NEWS" in text.upper()
