#!/usr/bin/env python
import os
import sys
import re
import requests
from datetime import datetime
from wakapedia_daily_news_generator.crew import WakapediaDailyNewsGeneratorCrew


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def extract_content_from_result(result_str: str) -> dict:
    """
    Extract structured content from the crew result.
    Parses the HTML output to get individual sections including links.
    """
    content = {
        'news_title': '',
        'news_content': '',
        'news_link': '',
        'tool_title': '',
        'tool_content': '',
        'tool_link': '',
        'fun_content': ''
    }

    # Daily News section - try to extract title from <strong> first
    news_title_match = re.search(
        r'Daily New[s]?</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>\s*<strong>([^<]+)</strong>',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if news_title_match:
        content['news_title'] = news_title_match.group(1).strip()

    # Extract full news paragraph content
    news_content_match = re.search(
        r'Daily New[s]?</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if news_content_match:
        raw_content = news_content_match.group(1)
        cleaned = re.sub(r'<strong>[^<]+</strong>\s*[-–]?\s*', '', raw_content)
        full_content = strip_html_tags(cleaned)
        content['news_content'] = full_content
        if not content['news_title'] and full_content:
            first_sentence = re.split(r'[.!?]', full_content)[0]
            content['news_title'] = first_sentence[:80] + ('...' if len(first_sentence) > 80 else '')

    # Extract news link
    news_link_match = re.search(
        r'Daily New[s]?</h2>.*?<a\s+href=["\']([^"\']+)["\']',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if news_link_match:
        content['news_link'] = news_link_match.group(1).strip()

    # Daily Tool section - extract tool name from <strong>
    tool_title_match = re.search(
        r'Daily Tool</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>.*?<strong>([^<]+)</strong>',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if tool_title_match:
        content['tool_title'] = tool_title_match.group(1).strip()

    # Extract full tool paragraph content
    tool_content_match = re.search(
        r'Daily Tool</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if tool_content_match:
        full_content = strip_html_tags(tool_content_match.group(1))
        content['tool_content'] = full_content
        if not content['tool_title'] and full_content:
            content['tool_title'] = "Outil du jour"

    # Extract tool link
    tool_link_match = re.search(
        r'Daily Tool</h2>.*?<a\s+href=["\']([^"\']+)["\']',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if tool_link_match:
        content['tool_link'] = tool_link_match.group(1).strip()

    # Daily Fun Fact section - extract full content
    fun_match = re.search(
        r'Daily Fun Fact</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if fun_match:
        content['fun_content'] = strip_html_tags(fun_match.group(1))

    return content


def send_to_google_chat_card(content: dict) -> bool:
    """
    Send the newsletter to Google Chat via webhook using Card format.
    """
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set.")
        return False

    try:
        from wakapedia_daily_news_generator.google_chat_card import create_simple_card

        # Logo URL from environment variable (must be publicly accessible)
        logo_url = os.getenv("NEWSLETTER_LOGO_URL")
        
        card_payload = create_simple_card(
            news_title=content.get('news_title', 'Actualité du jour'),
            news_content=content.get('news_content', ''),
            tool_title=content.get('tool_title', 'Outil du jour'),
            tool_content=content.get('tool_content', ''),
            fun_content=content.get('fun_content', ''),
            news_link=content.get('news_link', ''),
            tool_link=content.get('tool_link', ''),
            logo_url=logo_url
        )

        response = requests.post(webhook_url, json=card_payload)
        response.raise_for_status()
        print("Newsletter sent to Google Chat successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Google Chat: {e}")
        return False


def run():
    """
    Run the crew and send the result to Google Chat.
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }

    # Run the crew
    result = WakapediaDailyNewsGeneratorCrew().crew().kickoff(inputs=inputs)
    result_str = str(result)

    # Extract content from the result
    content = extract_content_from_result(result_str)

    # Debug output
    print("\n" + "=" * 50)
    print("Extracted content:")
    print(f"  news_title: {content['news_title'][:50]}..." if content['news_title'] else "  news_title: EMPTY")
    print(f"  tool_title: {content['tool_title']}" if content['tool_title'] else "  tool_title: EMPTY")
    print(f"  fun_content: {content['fun_content'][:50]}..." if content['fun_content'] else "  fun_content: EMPTY")
    print("=" * 50 + "\n")

    # Apply fallbacks if extraction failed
    if not content['news_content']:
        content['news_title'] = "Actualité tech du jour"
        content['news_content'] = "Consultez les dernières actualités tech."
    if not content['tool_content']:
        content['tool_title'] = "Outil du jour"
        content['tool_content'] = "Découvrez de nouveaux outils."
    if not content['fun_content']:
        content['fun_content'] = "Pourquoi les développeurs préfèrent le mode sombre ? Parce que la lumière attire les bugs !"

    # Send to Google Chat
    if os.getenv("GOOGLE_CHAT_WEBHOOK_URL"):
        send_to_google_chat_card(content)
    else:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set.")
        print(result_str)

    return result


def train():
    """Train the crew."""
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        WakapediaDailyNewsGeneratorCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        WakapediaDailyNewsGeneratorCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution."""
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        WakapediaDailyNewsGeneratorCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            openai_model_name=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
