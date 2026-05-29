"""Story deduplication across daily briefs.

Headlines that have already been sent in the last 24 hours are stored in
``sent_stories.json``. ``fetcher`` uses this to drop near-duplicate articles
before summarising; ``summarizer`` records the headlines it just sent.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

logger = logging.getLogger(__name__)

STORIES_FILE = Path("sent_stories.json")
DEDUP_WINDOW = timedelta(hours=24)
SIMILARITY_THRESHOLD = 0.8


def _now():
    return datetime.now(timezone.utc)


def _parse_ts(value: str):
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _load_recent():
    """Read the store, dropping entries older than 24 hours."""
    if not STORIES_FILE.exists():
        return []
    try:
        data = json.loads(STORIES_FILE.read_text(encoding="utf-8"))
        entries = data.get("sent", [])
    except Exception as e:
        logger.warning("Could not read %s, treating as empty: %s", STORIES_FILE, e)
        return []

    cutoff = _now() - DEDUP_WINDOW
    fresh = []
    for entry in entries:
        ts = _parse_ts(entry.get("sent_at", ""))
        if ts and ts >= cutoff:
            fresh.append(entry)
    return fresh


def recent_headlines():
    """Return the list of headline strings sent within the last 24 hours."""
    return [e["headline"] for e in _load_recent() if e.get("headline")]


def is_duplicate(title: str, headlines, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """True if ``title`` is >= threshold similar to any already-sent headline."""
    norm = (title or "").strip().lower()
    if not norm:
        return False
    for h in headlines:
        ratio = SequenceMatcher(None, norm, h.strip().lower()).ratio()
        if ratio >= threshold:
            return True
    return False


def add_headlines(headlines):
    """Append newly-sent headlines with a timestamp and persist (24h pruned)."""
    if not headlines:
        return
    fresh = _load_recent()
    now_iso = _now().isoformat()
    for h in headlines:
        h = (h or "").strip()
        if h:
            fresh.append({"headline": h, "sent_at": now_iso})
    try:
        STORIES_FILE.write_text(
            json.dumps({"sent": fresh}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Recorded %d sent headlines (store now holds %d).", len(headlines), len(fresh))
    except Exception as e:
        logger.warning("Could not write %s: %s", STORIES_FILE, e)
