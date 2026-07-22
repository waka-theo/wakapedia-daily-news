"""Tests for refusal detection and markdown fence stripping in main.py."""

from wakapedia_daily_news_generator.main import (
    looks_like_refusal,
    strip_markdown_fences,
)


class TestLooksLikeRefusal:
    """Detection of LLM apology/refusal text instead of real content."""

    def test_detects_french_refusal(self) -> None:
        text = (
            "Malheureusement, je ne peux pas fournir d'actualités récentes sur la "
            "technologie pour le 21 juillet 2026. Je vous recommande de consulter "
            "des sources d'actualités fiables comme TechCrunch."
        )
        assert looks_like_refusal(text) is True

    def test_detects_no_access(self) -> None:
        assert looks_like_refusal("Je n'ai pas accès aux dernières informations.")

    def test_detects_english_refusal(self) -> None:
        assert looks_like_refusal("As an AI language model, I cannot browse the web.")
        assert looks_like_refusal("I don't have access to real-time data.")

    def test_real_content_is_not_refusal(self) -> None:
        text = (
            "OpenAI a annoncé le lancement de GPT-5, un modèle plus performant. "
            "Cette avancée est importante pour l'industrie SaaS."
        )
        assert looks_like_refusal(text) is False

    def test_empty_string_is_not_refusal(self) -> None:
        assert looks_like_refusal("") is False


class TestStripMarkdownFences:
    """Stripping of wrapping ```html ... ``` fences from LLM output."""

    def test_strips_html_fence(self) -> None:
        raw = "```html\n<html><body>Hi</body></html>\n```"
        assert strip_markdown_fences(raw) == "<html><body>Hi</body></html>"

    def test_strips_bare_fence(self) -> None:
        raw = "```\n<p>Content</p>\n```"
        assert strip_markdown_fences(raw) == "<p>Content</p>"

    def test_leaves_unfenced_content_untouched(self) -> None:
        raw = "<html><body>No fence</body></html>"
        assert strip_markdown_fences(raw) == raw

    def test_drops_trailing_commentary_after_html(self) -> None:
        """LLM commentary appended after the closing fence must be removed."""
        raw = (
            "```html\n"
            "<html lang='fr'><body><p>Contenu</p></body></html>\n"
            "```\n\n"
            "Cette newsletter est prête à être envoyée."
        )
        result = strip_markdown_fences(raw)
        assert result.endswith("</html>")
        assert "Cette newsletter" not in result
        assert "```" not in result
