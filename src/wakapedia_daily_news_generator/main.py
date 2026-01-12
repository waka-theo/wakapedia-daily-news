#!/usr/bin/env python
import os
import sys
import requests
from wakapedia_daily_news_generator.crew import WakapediaDailyNewsGeneratorCrew


def send_to_google_chat(content: str, webhook_url: str = None) -> bool:
    """
    Send the newsletter content to Google Chat via webhook.
    """
    webhook_url = webhook_url or os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: GOOGLE_CHAT_WEBHOOK_URL not set. Skipping Google Chat notification.")
        return False

    # Google Chat message format
    message = {
        "text": content
    }

    try:
        response = requests.post(webhook_url, json=message)
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

    result = WakapediaDailyNewsGeneratorCrew().crew().kickoff(inputs=inputs)

    # Send to Google Chat if webhook is configured
    if os.getenv("GOOGLE_CHAT_WEBHOOK_URL"):
        send_to_google_chat(str(result))

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
