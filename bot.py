import logging
import sys
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import suggester
from config import (
    IST_TIMEZONE,
    GROQ_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    GEMINI_API_KEY,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    SUGGESTIONS_ENABLED,
    BUCKET_TAGS,
)
from fetcher import fetch_all_articles
from summarizer import summarize
from telegram_sender import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

IST = pytz.timezone(IST_TIMEZONE)

DIVIDER = "━" * 20


def _check_env():
    missing = [k for k, v in {
        "GROQ_API_KEY": GROQ_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }.items() if not v]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")


def _suggestions_ready():
    """True if the suggestions section has everything it needs to run.

    Missing suggestion config is a warning, not a failure — the news brief is
    the older, load-bearing half of this message and ships without it.
    """
    if not SUGGESTIONS_ENABLED:
        logger.info("SUGGESTIONS_ENABLED is off; skipping the BUILD NEXT section.")
        return False
    missing = [k for k, v in {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }.items() if not v]
    if missing:
        logger.warning("Suggestions disabled — missing %s.", ", ".join(missing))
        return False
    return True


def _render_suggestions(suggestions):
    """Format the BUILD NEXT section body."""
    blocks = ["🧭 **BUILD NEXT**"]
    for s in suggestions:
        tag = BUCKET_TAGS.get(s["bucket"], f"#{s['bucket']}")
        block = f"\n{tag}\n**{s['title']}**\n{s['body']}"
        # Link the ticket when this one came from a real issue.
        note = s.get("source_note") or ""
        if note.startswith("http"):
            block += f"\n{note}"
        blocks.append(block)
    return "\n".join(blocks)


def _build_keyboard(suggestions):
    """One 👍/👎 row per suggestion, callback_data carrying its uuid.

    Suggestions whose database write failed have no id to react against, so
    they ship as text with no buttons rather than with dead ones.
    """
    rows = []
    for s in suggestions:
        sid = s.get("suggestion_id")
        if not sid:
            continue
        tag = BUCKET_TAGS.get(s["bucket"], s["bucket"])
        rows.append([
            InlineKeyboardButton(f"👍 {tag}", callback_data=f"r|up|{sid}"),
            InlineKeyboardButton(f"👎 {tag}", callback_data=f"r|down|{sid}"),
        ])
    return InlineKeyboardMarkup(rows) if rows else None


def _get_brief():
    """Fetch and summarise the news half. Returns None if there is nothing to say."""
    try:
        grouped = fetch_all_articles()
    except Exception as e:
        logger.exception("Fetching failed: %s", e)
        return None

    if not grouped:
        logger.info("No articles found in the last 24h.")
        return None

    logger.info("Fetched %d articles across %d categories.",
                sum(len(v) for v in grouped.values()), len(grouped))
    try:
        return summarize(grouped)
    except Exception as e:
        logger.exception("Summarization failed: %s", e)
        return None


def _get_suggestions(date_iso):
    if not _suggestions_ready():
        return []
    try:
        return suggester.build_suggestions(date_iso)
    except Exception as e:
        # The news brief ships regardless of what the suggestion engine does.
        logger.exception("Suggestion generation failed: %s", e)
        return []


def build_and_send():
    now = datetime.now(IST)
    date_str = now.strftime("%a, %d %b %Y")
    logger.info("Running AI Intelligence Daily at %s IST", now.isoformat())

    body = _get_brief()
    suggestions = _get_suggestions(now.strftime("%Y-%m-%d"))

    if not body and not suggestions:
        logger.info("Nothing to send — no brief and no suggestions. Skipping.")
        return

    sections = [f"🤖 **AI INTELLIGENCE DAILY** — {date_str}", DIVIDER]
    if body:
        sections.append(body)
    if suggestions:
        # Appended to the same message — this bot never sends a second one.
        sections.append(DIVIDER)
        sections.append(_render_suggestions(suggestions))

    send_message("\n".join(sections), reply_markup=_build_keyboard(suggestions))
    logger.info("Telegram 200 — brief sent with %d suggestion(s).", len(suggestions))


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
