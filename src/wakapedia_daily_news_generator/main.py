#!/usr/bin/env python
"""
Wakapedia Daily News Generator - Main entry point.
Runs the crew and sends the newsletter to Google Chat.
"""

import argparse
import logging
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from wakapedia_daily_news_generator.crew import WakapediaDailyNewsGeneratorCrew

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("wakapedia")

# Pre-compiled regex patterns for better performance
NEWS_TITLE_PATTERN = re.compile(
    r'Daily New[s]?</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>\s*<strong>([^<]+)</strong>',
    re.IGNORECASE | re.DOTALL
)
NEWS_CONTENT_PATTERN = re.compile(
    r'Daily New[s]?</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL
)
NEWS_LINK_PATTERN = re.compile(
    r'Daily New[s]?</h2>.*?<a\s+href=["\']([^"\']+)["\']',
    re.IGNORECASE | re.DOTALL
)
TOOL_TITLE_PATTERN = re.compile(
    r'Daily Tool</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>.*?<strong>([^<]+)</strong>',
    re.IGNORECASE | re.DOTALL
)
TOOL_CONTENT_PATTERN = re.compile(
    r'Daily Tool</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL
)
TOOL_LINK_PATTERN = re.compile(
    r'Daily Tool</h2>.*?<a\s+href=["\']([^"\']+)["\']',
    re.IGNORECASE | re.DOTALL
)
FUN_FACT_PATTERN = re.compile(
    r'Daily Fun Fact</h2>\s*(?:<[^>]*>\s*)*<p[^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL
)

# Real tech facts for fallback (NO JOKES - verified historical facts)
FALLBACK_FACTS = [
    "Le premier bug informatique documente etait un vrai insecte : un papillon de nuit trouve dans le Harvard Mark II en 1947 par Grace Hopper.",
    "Le nom 'Python' vient de la troupe comique Monty Python, pas du serpent. Guido van Rossum regardait leurs sketches pendant le developpement.",
    "Le premier SMS de l'histoire a ete envoye le 3 decembre 1992. Il disait simplement 'Merry Christmas'.",
    "Le terme 'spam' pour les emails indesirables vient d'un sketch des Monty Python ou le mot 'spam' est repete sans cesse.",
    "La touche Caps Lock existe car les premiers claviers de machine a ecrire ne permettaient pas de taper en minuscules facilement.",
    "Le premier ordinateur portable pesait 24 kg. C'etait l'Osborne 1, lance en 1981.",
    "Le code source de MS-DOS ne contenait a l'origine que 4000 lignes de code assembleur.",
    "Le bug de l'an 2000 (Y2K) a coute environ 300 milliards de dollars en corrections preventives dans le monde.",
    "La fusee Ariane 5 a explose 37 secondes apres son lancement en 1996 a cause d'un bug de conversion 64 bits vers 16 bits.",
    "Le premier domaine .com enregistre etait symbolics.com, le 15 mars 1985.",
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 4  # seconds


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def extract_content_from_result(result_str: str) -> dict[str, str]:
    """
    Extract structured content from the crew result.
    Parses the HTML output to get individual sections including links.
    """
    content: dict[str, str] = {
        'news_title': '',
        'news_content': '',
        'news_link': '',
        'tool_title': '',
        'tool_content': '',
        'tool_link': '',
        'fun_content': ''
    }

    # Daily News section - try to extract title from <strong> first
    news_title_match = NEWS_TITLE_PATTERN.search(result_str)
    if news_title_match:
        news_title = news_title_match.group(1).strip()
        # Truncate title if too long (max 60 characters)
        if len(news_title) > 60:
            news_title = news_title[:57] + '...'
        content['news_title'] = news_title

    # Extract full news paragraph content
    news_content_match = NEWS_CONTENT_PATTERN.search(result_str)
    if news_content_match:
        raw_content = news_content_match.group(1)
        cleaned = re.sub(r'<strong>[^<]+</strong>\s*[-–]?\s*', '', raw_content)
        full_content = strip_html_tags(cleaned)
        content['news_content'] = full_content
        if not content['news_title'] and full_content:
            first_sentence = re.split(r'[.!?]', full_content)[0]
            content['news_title'] = first_sentence[:57] + '...' if len(first_sentence) > 60 else first_sentence

    # Extract news link
    news_link_match = NEWS_LINK_PATTERN.search(result_str)
    if news_link_match:
        content['news_link'] = news_link_match.group(1).strip()

    # Daily Tool section - extract tool name from <strong>
    tool_title_match = TOOL_TITLE_PATTERN.search(result_str)
    if tool_title_match:
        tool_title = tool_title_match.group(1).strip()
        # Remove "Nom de l'outil :" prefix if present
        tool_title = re.sub(r"^Nom de l'outil\s*:\s*", '', tool_title, flags=re.IGNORECASE)
        content['tool_title'] = tool_title

    # Extract full tool paragraph content
    tool_content_match = TOOL_CONTENT_PATTERN.search(result_str)
    if tool_content_match:
        full_content = strip_html_tags(tool_content_match.group(1))
        content['tool_content'] = full_content
        if not content['tool_title'] and full_content:
            content['tool_title'] = "Outil du jour"

    # Extract tool link
    tool_link_match = TOOL_LINK_PATTERN.search(result_str)
    if tool_link_match:
        content['tool_link'] = tool_link_match.group(1).strip()

    # Daily Fun Fact section - extract full content
    fun_match = FUN_FACT_PATTERN.search(result_str)
    if fun_match:
        content['fun_content'] = strip_html_tags(fun_match.group(1))

    return content


def validate_webhook_url(url: str) -> bool:
    """Validate that the webhook URL is a valid Google Chat webhook."""
    if not url:
        return False
    # Basic validation - must be HTTPS and from Google
    if not url.startswith("https://"):
        return False
    # Extract hostname and validate it's exactly chat.googleapis.com
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname == "chat.googleapis.com"
    except Exception:
        return False


def send_to_google_chat_card(content: dict[str, str]) -> bool:
    """
    Send the newsletter to Google Chat via webhook using Card format.
    """
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("GOOGLE_CHAT_WEBHOOK_URL not set")
        return False

    if not validate_webhook_url(webhook_url):
        logger.error("Invalid GOOGLE_CHAT_WEBHOOK_URL format")
        return False

    try:
        from wakapedia_daily_news_generator.google_chat_card import create_simple_card

        # Logo URL from environment variable (must be publicly accessible)
        logo_url = os.getenv("NEWSLETTER_LOGO_URL")

        card_payload = create_simple_card(
            news_title=content.get('news_title', 'Actualite du jour'),
            news_content=content.get('news_content', ''),
            tool_title=content.get('tool_title', 'Outil du jour'),
            tool_content=content.get('tool_content', ''),
            fun_content=content.get('fun_content', ''),
            news_link=content.get('news_link', ''),
            tool_link=content.get('tool_link', ''),
            logo_url=logo_url
        )

        response = requests.post(
            webhook_url,
            json=card_payload,
            timeout=30
        )
        response.raise_for_status()
        logger.info("Newsletter sent to Google Chat successfully!")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send to Google Chat: {e}")
        return False


def run_crew_with_retry(inputs: dict[str, Any], max_retries: int = MAX_RETRIES) -> Any:
    """
    Run the crew with retry logic and exponential backoff.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Starting crew execution (attempt {attempt + 1}/{max_retries})")
            start_time = time.time()

            result = WakapediaDailyNewsGeneratorCrew().crew().kickoff(inputs=inputs)

            elapsed = time.time() - start_time
            logger.info(f"Crew execution completed in {elapsed:.1f}s")
            return result

        except Exception as e:
            last_exception = e
            logger.error(f"Crew execution failed (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)

    # All retries failed
    raise RuntimeError(f"Crew execution failed after {max_retries} attempts") from last_exception


def save_to_archive(content: dict[str, str], result_str: str) -> None:
    """Save the newsletter to the archives directory."""
    try:
        archive_dir = Path(__file__).parent.parent.parent / "archives"
        archive_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        archive_file = archive_dir / f"{today}.html"

        archive_file.write_text(result_str, encoding="utf-8")
        logger.info(f"Newsletter archived to {archive_file}")
    except Exception as e:
        logger.warning(f"Failed to archive newsletter: {e}")


def run(dry_run: bool = False) -> Any:
    """
    Run the crew and send the result to Google Chat.

    Args:
        dry_run: If True, generate newsletter but don't send to Google Chat.
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }

    logger.info("=" * 50)
    logger.info("Starting Wakapedia Daily News Generator")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 50)

    # Run the crew with retry logic
    try:
        result = run_crew_with_retry(inputs)
    except RuntimeError as e:
        logger.critical(f"Newsletter generation failed: {e}")
        # Could add notification here (email, Slack, etc.)
        raise

    result_str = str(result)

    # Extract content from the result
    content = extract_content_from_result(result_str)

    # Log extracted content
    logger.info("Extracted content:")
    logger.info(f"  news_title: {content['news_title'][:50]}..." if content['news_title'] else "  news_title: EMPTY")
    logger.info(f"  tool_title: {content['tool_title']}" if content['tool_title'] else "  tool_title: EMPTY")
    logger.info(f"  fun_content: {content['fun_content'][:50]}..." if content['fun_content'] else "  fun_content: EMPTY")

    # Apply fallbacks if extraction failed
    if not content['news_content']:
        logger.warning("News content extraction failed, using fallback")
        content['news_title'] = "Actualite tech du jour"
        content['news_content'] = "Consultez les dernieres actualites tech."

    if not content['tool_content']:
        logger.warning("Tool content extraction failed, using fallback")
        content['tool_title'] = "Outil du jour"
        content['tool_content'] = "Decouvrez de nouveaux outils."

    if not content['fun_content']:
        logger.warning("Fun fact content extraction failed, using fallback")
        # Use a real tech fact, NOT a joke
        content['fun_content'] = random.choice(FALLBACK_FACTS)

    # Archive the newsletter
    save_to_archive(content, result_str)

    # Send to Google Chat (unless dry run)
    if dry_run:
        logger.info("Dry run mode - skipping Google Chat send")
        # Save preview to file
        preview_dir = Path(__file__).parent.parent.parent / "output"
        preview_dir.mkdir(exist_ok=True)
        preview_file = preview_dir / "preview.html"
        preview_file.write_text(result_str, encoding="utf-8")
        logger.info(f"Preview saved to {preview_file}")
    elif os.getenv("GOOGLE_CHAT_WEBHOOK_URL"):
        send_to_google_chat_card(content)
    else:
        logger.warning("GOOGLE_CHAT_WEBHOOK_URL not set - newsletter generated but not sent")
        # Don't print full content to avoid exposing sensitive data in logs

    logger.info("Newsletter generation completed")
    return result


def train(n_iterations: int, filename: str) -> None:
    """
    Train the crew.

    Args:
        n_iterations: Number of training iterations.
        filename: Output filename for trained model.
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        logger.info(f"Starting crew training: {n_iterations} iterations, output: {filename}")
        WakapediaDailyNewsGeneratorCrew().crew().train(
            n_iterations=n_iterations,
            filename=filename,
            inputs=inputs
        )
        logger.info("Training completed successfully")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


def replay(task_id: str) -> None:
    """
    Replay the crew execution from a specific task.

    Args:
        task_id: The task ID to replay from.
    """
    try:
        logger.info(f"Replaying from task: {task_id}")
        WakapediaDailyNewsGeneratorCrew().crew().replay(task_id=task_id)
        logger.info("Replay completed successfully")
    except Exception as e:
        logger.error(f"Replay failed: {e}")
        raise


def test(n_iterations: int, eval_llm: str) -> None:
    """
    Test the crew execution.

    Args:
        n_iterations: Number of test iterations.
        eval_llm: LLM model string for evaluation (e.g., "openai/gpt-4o-mini").
    """
    inputs = {
        'company_name': 'WAKASTELLAR',
        'email_address': 'wakapedia@wakastellar.com'
    }
    try:
        logger.info(f"Starting crew test: {n_iterations} iterations, eval_llm: {eval_llm}")
        WakapediaDailyNewsGeneratorCrew().crew().test(
            n_iterations=n_iterations,
            eval_llm=eval_llm,
            inputs=inputs
        )
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


def status() -> None:
    """Display the current status of the newsletter system."""
    import json
    from pathlib import Path

    memory_dir = Path(__file__).parent.parent.parent / "memory"

    print("\n" + "=" * 50)
    print("Wakapedia Daily News - System Status")
    print("=" * 50)

    # Check memory files
    memory_files = {
        "News URLs": "used_news_urls.json",
        "Tools": "used_tools.json",
        "Facts": "used_facts.json",
    }

    print("\nMemory Status:")
    for name, filename in memory_files.items():
        filepath = memory_dir / filename
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text())
                key = "urls" if "urls" in data else "tools" if "tools" in data else "facts"
                count = len(data.get(key, []))
                print(f"  {name}: {count}/90 entries")
            except Exception:
                print(f"  {name}: ERROR reading file")
        else:
            print(f"  {name}: Not initialized")

    # Check environment variables
    print("\nEnvironment Variables:")
    env_vars = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
        "GOOGLE_CHAT_WEBHOOK_URL": bool(os.getenv("GOOGLE_CHAT_WEBHOOK_URL")),
        "NEWSLETTER_LOGO_URL": bool(os.getenv("NEWSLETTER_LOGO_URL")),
    }
    for var, is_set in env_vars.items():
        status_icon = "[OK]" if is_set else "[NOT SET]"
        print(f"  {var}: {status_icon}")

    # Check archives
    archive_dir = Path(__file__).parent.parent.parent / "archives"
    if archive_dir.exists():
        archives = list(archive_dir.glob("*.html"))
        print(f"\nArchives: {len(archives)} newsletters saved")
        if archives:
            latest = sorted(archives)[-1]
            print(f"  Latest: {latest.name}")
    else:
        print("\nArchives: Not initialized")

    print("=" * 50 + "\n")


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Wakapedia Daily News Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                              Run the newsletter generator
  %(prog)s run --dry-run                    Generate without sending
  %(prog)s status                           Show system status
  %(prog)s train 5 model.pkl                Train the crew
  %(prog)s replay task_123                  Replay from a specific task
  %(prog)s test 3 openai/gpt-4o-mini        Test with evaluation LLM
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the newsletter generator")
    run_parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Generate newsletter without sending to Google Chat"
    )

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train the crew")
    train_parser.add_argument("n_iterations", type=int, help="Number of training iterations")
    train_parser.add_argument("filename", help="Output filename for trained model")

    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay from a specific task")
    replay_parser.add_argument("task_id", help="Task ID to replay from")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test the crew execution")
    test_parser.add_argument("n_iterations", type=int, help="Number of test iterations")
    test_parser.add_argument("eval_llm", help="LLM model for evaluation (e.g., openai/gpt-4o-mini)")

    args = parser.parse_args()

    if args.command == "run":
        run(dry_run=args.dry_run)
    elif args.command == "status":
        status()
    elif args.command == "train":
        train(args.n_iterations, args.filename)
    elif args.command == "replay":
        replay(args.task_id)
    elif args.command == "test":
        test(args.n_iterations, args.eval_llm)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
