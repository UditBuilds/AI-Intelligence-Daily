import asyncio
import html
import logging
import re

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

MAX_LEN = 4000

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def _to_html(text: str) -> str:
    """Escape HTML-unsafe chars, then turn **bold** markers into <b> tags.

    URLs are left as plain text so Telegram auto-detects them and generates
    a link preview card for the first one in the message.
    """
    escaped = html.escape(text, quote=False)
    return _BOLD_RE.sub(r"<b>\1</b>", escaped)


def _chunks(text: str):
    while text:
        if len(text) <= MAX_LEN:
            yield text
            return
        cut = text.rfind("\n", 0, MAX_LEN)
        if cut == -1:
            cut = MAX_LEN
        yield text[:cut]
        text = text[cut:].lstrip()


async def _send(message: str):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    html_message = _to_html(message)
    chunks = list(_chunks(html_message))
    for i, chunk in enumerate(chunks):
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=chunk,
                parse_mode=ParseMode.HTML,
                # Allow preview on the first chunk only.
                disable_web_page_preview=(i != 0),
            )
        except TelegramError as e:
            logger.error("Telegram send failed: %s", e)


def send_message(message: str):
    asyncio.run(_send(message))
