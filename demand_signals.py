"""Unmet-demand evidence for the #new-build slot.

Primary signal is people complaining that something does not exist — Reddit's
"somebody make this" / "I wish there was" corner. Secondary, deliberately
lighter, is Hacker News, which skews toward what is trendy rather than what is
missing.

Reddit rate-limits and sometimes blocks datacenter IPs outright, so every fetch
here degrades silently. Returning nothing is a supported outcome: the suggestion
prompt instructs the model to argue from project context and say so plainly
rather than invent a complaint it never saw.
"""

import logging
from urllib.parse import quote_plus

import feedparser
import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AIIntelligenceDaily/1.0)"}
TIMEOUT = 12

# Subreddits where the whole point of a post is an unmet need.
_DEMAND_FEEDS = [
    "https://www.reddit.com/r/SomebodyMakeThis/new.rss?limit=25",
    "https://www.reddit.com/r/AppIdeas/new.rss?limit=25",
    "https://www.reddit.com/r/indiehackers/search.rss?q={q}&restrict_sr=1&sort=new&t=month",
    "https://www.reddit.com/r/smallbusiness/search.rss?q={q}&restrict_sr=1&sort=new&t=month",
]
_DEMAND_QUERY = quote_plus('"i wish there was" OR "is there an app" OR "does this exist"')

# Secondary, lighter weight — what people are building, not what they lack.
_TREND_FEEDS = [
    "https://hnrss.org/newest?q=" + quote_plus("show hn"),
]

MAX_PER_FEED = 8
MAX_TOTAL = 18


def _parse(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        logger.info("Demand feed unavailable (%s): %s", url.split("/")[2], e)
        return None


def _harvest(urls, kind):
    out = []
    for url in urls:
        parsed = _parse(url.format(q=_DEMAND_QUERY))
        if not parsed or not parsed.entries:
            continue
        for entry in parsed.entries[:MAX_PER_FEED]:
            title = (entry.get("title") or "").strip()
            if len(title) < 15:
                continue
            out.append({"kind": kind, "title": title, "url": entry.get("link", "")})
    return out


def collect():
    """Return demand/trend signals, newest-ish first. May be empty."""
    signals = _harvest(_DEMAND_FEEDS, "complaint")
    # Only top up with trend noise if the complaint well came back dry-ish.
    if len(signals) < MAX_TOTAL:
        signals.extend(_harvest(_TREND_FEEDS, "trend"))

    seen = set()
    deduped = []
    for s in signals:
        key = s["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
        if len(deduped) >= MAX_TOTAL:
            break

    complaints = sum(1 for s in deduped if s["kind"] == "complaint")
    logger.info("Collected %d demand signals (%d complaints, %d trend).",
                len(deduped), complaints, len(deduped) - complaints)
    return deduped
