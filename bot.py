import logging
import sys
from datetime import datetime

import pytz

from config import IST_TIMEZONE, GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from fetcher import fetch_all_articles
from summarizer import summarize
from telegram_sender import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

IST = pytz.timezone(IST_TIMEZONE)


def _check_env():
    missing = [k for k, v in {
        "GROQ_API_KEY": GROQ_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }.items() if not v]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")


def build_and_send():
    now = datetime.now(IST)
    date_str = now.strftime("%a, %d %b %Y")
    logger.info("Running AI Intelligence Daily at %s IST", now.isoformat())

    try:
        grouped = fetch_all_articles()
    except Exception as e:
        logger.exception("Fetching failed: %s", e)
        return

    fetched = sum(len(v) for v in grouped.values())
    logger.info("Fetched %d articles across %d categories.", fetched, len(grouped))

    if not grouped:
        logger.info("No articles found in the last 24h. Skipping.")
        return

    try:
        body = summarize(grouped)
    except Exception as e:
        logger.exception("Summarization failed: %s", e)
        return

    if not body:
        logger.info("Empty brief from Groq. Skipping.")
        return

    divider = "━" * 20
    message = (
        f"🤖 **AI INTELLIGENCE DAILY** — {date_str}\n"
        f"{divider}\n"
        f"{body}"
    )

    send_message(message)
    logger.info("Telegram 200 — brief sent.")


def main():
    _check_env()
    build_and_send()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        main()
    else:
        # No native scheduler: this bot is triggered via repository_dispatch
        # (cron-job.org) which always passes --run-now. Running bare does the
        # same single-shot build for convenience.
        main()
