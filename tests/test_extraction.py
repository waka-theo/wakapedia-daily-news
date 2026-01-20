"""Tests for content extraction from crew output."""

import pytest

from wakapedia_daily_news_generator.main import (
    extract_content_from_result,
    strip_html_tags,
    validate_webhook_url,
)


class TestStripHtmlTags:
    """Tests for HTML tag stripping."""

    def test_removes_simple_tags(self):
        """Test removal of simple HTML tags."""
        assert strip_html_tags("<p>Hello</p>") == "Hello"
        assert strip_html_tags("<strong>Bold</strong>") == "Bold"

    def test_removes_nested_tags(self):
        """Test removal of nested HTML tags."""
        assert strip_html_tags("<p><strong>Text</strong></p>") == "Text"

    def test_removes_tags_with_attributes(self):
        """Test removal of tags with attributes."""
        assert strip_html_tags('<a href="url">Link</a>') == "Link"
        assert strip_html_tags('<p class="test">Content</p>') == "Content"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        assert strip_html_tags("") == ""

    def test_handles_no_tags(self):
        """Test handling of text without tags."""
        assert strip_html_tags("Plain text") == "Plain text"

    def test_strips_whitespace(self):
        """Test that result is stripped."""
        assert strip_html_tags("  <p>Text</p>  ") == "Text"


class TestExtractContentFromResult:
    """Tests for content extraction."""

    def test_extracts_news_title(self, sample_crew_output: str):
        """Test extraction of news title."""
        content = extract_content_from_result(sample_crew_output)
        assert content["news_title"] == "OpenAI lance GPT-5"

    def test_extracts_news_content(self, sample_crew_output: str):
        """Test extraction of news content."""
        content = extract_content_from_result(sample_crew_output)
        assert "OpenAI a annonce" in content["news_content"]

    def test_extracts_news_link(self, sample_crew_output: str):
        """Test extraction of news link."""
        content = extract_content_from_result(sample_crew_output)
        assert content["news_link"] == "https://techcrunch.com/openai-gpt5"

    def test_extracts_tool_title(self, sample_crew_output: str):
        """Test extraction of tool title."""
        content = extract_content_from_result(sample_crew_output)
        assert content["tool_title"] == "Cursor AI"

    def test_extracts_tool_content(self, sample_crew_output: str):
        """Test extraction of tool content."""
        content = extract_content_from_result(sample_crew_output)
        assert "editeur de code" in content["tool_content"]

    def test_extracts_tool_link(self, sample_crew_output: str):
        """Test extraction of tool link."""
        content = extract_content_from_result(sample_crew_output)
        assert content["tool_link"] == "https://cursor.sh"

    def test_extracts_fun_content(self, sample_crew_output: str):
        """Test extraction of fun fact."""
        content = extract_content_from_result(sample_crew_output)
        assert "papillon de nuit" in content["fun_content"]
        assert "Harvard Mark II" in content["fun_content"]

    def test_handles_empty_output(self, empty_crew_output: str):
        """Test handling of empty/malformed output."""
        content = extract_content_from_result(empty_crew_output)
        assert content["news_title"] == ""
        assert content["news_content"] == ""
        assert content["tool_title"] == ""
        assert content["tool_content"] == ""
        assert content["fun_content"] == ""

    def test_truncates_long_title(self):
        """Test that long titles are truncated."""
        long_title = "A" * 100
        html = f"""
        <h2>Daily News</h2>
        <p><strong>{long_title}</strong> - Content here.</p>
        """
        content = extract_content_from_result(html)
        assert len(content["news_title"]) <= 60
        assert content["news_title"].endswith("...")


class TestValidateWebhookUrl:
    """Tests for webhook URL validation."""

    def test_valid_google_chat_url(self):
        """Test that valid Google Chat URLs pass."""
        url = "https://chat.googleapis.com/v1/spaces/xxx/messages?key=yyy"
        assert validate_webhook_url(url) is True

    def test_rejects_empty_url(self):
        """Test that empty URLs are rejected."""
        assert validate_webhook_url("") is False
        assert validate_webhook_url(None) is False

    def test_rejects_http_url(self):
        """Test that HTTP URLs are rejected."""
        url = "http://chat.googleapis.com/v1/spaces/xxx/messages"
        assert validate_webhook_url(url) is False

    def test_rejects_non_google_url(self):
        """Test that non-Google URLs are rejected."""
        url = "https://webhook.example.com/hook"
        assert validate_webhook_url(url) is False

    def test_rejects_malicious_url(self):
        """Test that URLs trying to mimic Google are rejected."""
        url = "https://chat.googleapis.com.evil.com/hook"
        assert validate_webhook_url(url) is False
