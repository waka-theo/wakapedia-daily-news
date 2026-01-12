#!/usr/bin/env python
import os
import sys
import re
import requests
from datetime import datetime
from pathlib import Path
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
    # Daily News section
    news_match = re.search(r'Daily New[s]?</h2>\s*<p><strong>([^<]+)</strong>\s*[-–]?\s*([^<]+)', result_str, re.IGNORECASE)
    if news_match:
        content['news_title'] = news_match.group(1).strip()
        content['news_content'] = news_match.group(2).strip()

    # Extract news link
    news_link_match = re.search(r'Daily New[s]?</h2>.*?<a\s+href=["\']([^"\']+)["\']', result_str, re.IGNORECASE | re.DOTALL)
    if news_link_match:
        content['news_link'] = news_link_match.group(1).strip()

    # Daily Tool section
    tool_match = re.search(r'Daily Tool</h2>\s*<p><strong>([^<]+)</strong>\s*([^<]+)', result_str, re.IGNORECASE)
    if tool_match:
        content['tool_title'] = tool_match.group(1).strip()
        content['tool_content'] = tool_match.group(2).strip()

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


def generate_newsletter_pdf(content: dict) -> str:
    """Generate PDF from the newsletter content."""
    try:
        from wakapedia_daily_news_generator.pdf_generator import generate_pdf

        pdf_path = generate_pdf(
            news_title=content.get('news_title', 'Actualité du jour'),
            news_content=content.get('news_content', ''),
            tool_title=content.get('tool_title', 'Outil du jour'),
            tool_content=content.get('tool_content', ''),
            fun_content=content.get('fun_content', '')
        )
        print(f"PDF generated: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
        return None


def upload_to_google_drive(pdf_path: str) -> str:
    """Upload PDF to Google Drive and return the link."""
    try:
        from wakapedia_daily_news_generator.google_drive import upload_and_get_link
        return upload_and_get_link(pdf_path)
    except Exception as e:
        print(f"Failed to upload to Google Drive: {e}")
        return None


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
    Run the crew and send the result to Google Chat as PDF.
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

    # If extraction failed, use raw content
    if not content['news_content']:
        content['news_content'] = result_str[:500] + "..." if len(result_str) > 500 else result_str

    # Generate PDF
    pdf_path = generate_newsletter_pdf(content)

    # Upload to Google Drive if configured
    pdf_link = None
    if pdf_path and os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
        pdf_link = upload_to_google_drive(pdf_path)

    # Send Card to Google Chat
    if os.getenv("GOOGLE_CHAT_WEBHOOK_URL"):
        send_to_google_chat_card(content)

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
