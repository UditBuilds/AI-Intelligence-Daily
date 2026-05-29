import logging
import re
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests

from config import RSS_FEEDS, LOOKBACK_HOURS, CATEGORY_ORDER
from dedup import recent_headlines, is_duplicate

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")

# A browser User-Agent + explicit fetch avoids SSL/handshake issues that
# feedparser's raw urllib fetch trips on (e.g. OpenAI's blog feed).
FETCH_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AIIntelligenceDaily/1.0)"}
FETCH_TIMEOUT = 15


def _parse_feed(feed):
    """Fetch a feed with requests + browser UA, then hand bytes to feedparser.

    Falls back to feedparser's own fetch if the HTTP request fails outright,
    so a transient requests error never silently drops an otherwise-good feed.
    """
    try:
        r = requests.get(feed["url"], headers=FETCH_HEADERS, timeout=FETCH_TIMEOUT)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        logger.warning("HTTP fetch failed for %s (%s); trying feedparser direct.", feed["name"], e)
        return feedparser.parse(feed["url"])


def _clean(text: str) -> str:
    if not text:
        return ""
    return TAG_RE.sub("", text).strip()


def _entry_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime.fromtimestamp(mktime(t), tz=timezone.utc)
            except Exception:
                continue
    return None


def fetch_all_articles():
    """Fetch every feed, keep last-24h non-duplicate items, group by category.

    Returns a dict: {category_tag: [article, ...]} ordered per CATEGORY_ORDER.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    already_sent = recent_headlines()
    skipped_dupes = 0
    total = 0
    grouped = {cat: [] for cat in CATEGORY_ORDER}

    for feed in RSS_FEEDS:
        try:
            parsed = _parse_feed(feed)
            if parsed.bozo and not parsed.entries:
                logger.warning("Feed failed: %s (%s)", feed["name"], parsed.bozo_exception)
                continue

            for entry in parsed.entries[:25]:
                published = _entry_time(entry)
                if published and published < cutoff:
                    continue

                title = _clean(entry.get("title", ""))
                summary = _clean(entry.get("summary", "") or entry.get("description", ""))
                if not title:
                    continue

                if is_duplicate(title, already_sent):
                    skipped_dupes += 1
                    continue

                url = entry.get("link", "") or entry.get("id", "")
                article = {
                    "source": feed["name"],
                    "category": feed["category"],
                    "title": title,
                    "summary": summary[:500],
                    "url": url,
                    "published": published.isoformat() if published else "",
                }
                grouped.setdefault(feed["category"], []).append(article)
                total += 1
        except Exception as e:
            logger.warning("Error fetching %s: %s", feed["name"], e)
            continue

    logger.info(
        "Fetched %d articles in last %dh (%d dropped as already-sent duplicates)",
        total, LOOKBACK_HOURS, skipped_dupes,
    )

    # Drop empty categories so the summarizer only sees sections with content.
    return {cat: items for cat, items in grouped.items() if items}
