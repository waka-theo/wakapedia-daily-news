#!/usr/bin/env python
import os
import sys
import re
import requests
from datetime import datetime
from wakapedia_daily_news_generator.crew import WakapediaDailyNewsGeneratorCrew


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

    # Try to extract from HTML structure
    # Daily News section - handle various formats including "Titre :" prefix
    news_match = re.search(
        r'Daily New[s]?</h2>\s*<p>(?:<strong>(?:Titre\s*:?\s*)?</strong>\s*)?([^<]+?)(?:</p>|\s*<a)',
        result_str,
        re.IGNORECASE
    )
    if news_match:
        content['news_title'] = news_match.group(1).strip()

    # Try to extract news content from following paragraph(s)
    news_content_match = re.search(
        r'Daily New[s]?</h2>.*?</p>\s*<p>([^<]+)',
        result_str,
        re.IGNORECASE | re.DOTALL
    )
    if news_content_match:
        content['news_content'] = news_content_match.group(1).strip()
    elif news_match:
        # Use title as content if no separate content found
        content['news_content'] = content['news_title']

    # Extract news link
    news_link_match = re.search(r'Daily New[s]?</h2>.*?<a\s+href=["\']([^"\']+)["\']', result_str, re.IGNORECASE | re.DOTALL)
    if news_link_match:
        content['news_link'] = news_link_match.group(1).strip()

    # Daily Tool section - handle "SeaVerse" style content
    tool_match = re.search(
        r'Daily Tool</h2>\s*<p>([^<]+)',
        result_str,
        re.IGNORECASE
    )
    if tool_match:
        tool_text = tool_match.group(1).strip()
        # Try to split into title and content at first period or comma
        split_match = re.match(r'^([^.]+(?:\.[^.]{0,20})?)[.,]\s*(.+)$', tool_text)
        if split_match:
            content['tool_title'] = split_match.group(1).strip()
            content['tool_content'] = split_match.group(2).strip()
        else:
            content['tool_title'] = tool_text[:100] + '...' if len(tool_text) > 100 else tool_text
            content['tool_content'] = tool_text

    # Extract tool link
    tool_link_match = re.search(r'Daily Tool</h2>.*?<a\s+href=["\']([^"\']+)["\']', result_str, re.IGNORECASE | re.DOTALL)
    if tool_link_match:
        content['tool_link'] = tool_link_match.group(1).strip()

    # Daily Fun Fact section
    fun_match = re.search(r'Daily Fun Fact</h2>\s*(?:<div[^>]*>)?\s*<p>([^<]+)</p>', result_str, re.IGNORECASE)
    if not fun_match:
        fun_match = re.search(r'Daily Fun Fact</h2>\s*<div[^>]*>\s*([^<]+)', result_str, re.IGNORECASE)
    if fun_match:
        content['fun_content'] = fun_match.group(1).strip()

    return content


def format_text_message(content: dict) -> str:
    """Format content as a nice text message for Google Chat."""
    date_str = datetime.now().strftime("%d/%m/%Y")

    message = f"""*🗞️ WAKAPEDIA DAILY NEWS - {date_str}*
━━━━━━━━━━━━━━━━━━━━━━━

*📰 DAILY NEWS*
*{content.get('news_title', 'Actualité du jour')}*
{content.get('news_content', '')}

━━━━━━━━━━━━━━━━━━━━━━━

*🛠️ DAILY TOOL*
*{content.get('tool_title', 'Outil du jour')}*
{content.get('tool_content', '')}

━━━━━━━━━━━━━━━━━━━━━━━

*😄 DAILY FUN FACT*
{content.get('fun_content', '')}

━━━━━━━━━━━━━━━━━━━━━━━
_L'agitateur matinal de savoir Tech & Fun pour la team Wakastellar_"""

    return message


def send_to_google_chat_card(content: dict) -> bool:
    """
    Send the newsletter to Google Chat via webhook using Card format.
    """
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set. Skipping Google Chat notification.")
        return False

    try:
        from wakapedia_daily_news_generator.google_chat_card import create_simple_card

        card_payload = create_simple_card(
            news_title=content.get('news_title', 'Actualité du jour'),
            news_content=content.get('news_content', ''),
            tool_title=content.get('tool_title', 'Outil du jour'),
            tool_content=content.get('tool_content', ''),
            fun_content=content.get('fun_content', ''),
            news_link=content.get('news_link', ''),
            tool_link=content.get('tool_link', '')
        )

        response = requests.post(webhook_url, json=card_payload)
        response.raise_for_status()
        print("Newsletter Card sent to Google Chat successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Google Chat: {e}")
        return False


def send_to_google_chat(message: str, pdf_link: str = None) -> bool:
    """
    Send the newsletter to Google Chat via webhook (text format).
    """
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set. Skipping Google Chat notification.")
        return False

    # If we have a PDF link, add it to the message
    if pdf_link:
        message += f"\n\n📄 *Voir le PDF:* {pdf_link}"

    payload = {"text": message}

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Newsletter sent to Google Chat successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Google Chat: {e}")
        return False


def run():
    """
    Run the crew and send the result to Google Chat as Card.
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

    # If extraction failed, use default message
    if not content['news_content']:
        content['news_title'] = "Actualité tech du jour"
        content['news_content'] = "Consultez les dernières actualités tech sur votre fil d'actualité préféré."
    if not content['tool_content']:
        content['tool_title'] = "Outil du jour"
        content['tool_content'] = "Découvrez de nouveaux outils pour améliorer votre productivité."
    if not content['fun_content']:
        content['fun_content'] = "Pourquoi les développeurs préfèrent le mode sombre ? Parce que la lumière attire les bugs !"

    # Send Card to Google Chat
    if os.getenv("GOOGLE_CHAT_WEBHOOK_URL"):
        send_to_google_chat_card(content)
    else:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set. Newsletter content:")
        print(content)

    return result


def run_with_trigger():
    """
    Run the crew with Google Chat integration (for scheduled triggers).
    """
    return run()


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        WakapediaDailyNewsGeneratorCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        WakapediaDailyNewsGeneratorCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        WakapediaDailyNewsGeneratorCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

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
