"""Supabase (PostgREST) access for the daily build suggestions.

Two tables back this feature: ``suggestions`` (one row per idea sent) and
``reactions`` (one row per 👍/👎 tap, written by the Vercel webhook). Only the
service key touches them, so both tables run RLS-enabled with no policies.

Reads degrade to empty on failure — a dead history query should cost us
calibration quality, not the whole brief. Writes report failure to the caller,
which decides whether the suggestion still ships without feedback buttons.
"""

import logging

import requests

from config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    SUGGESTIONS_TABLE,
    REACTIONS_TABLE,
    DEDUP_LOOKBACK,
    REACTION_LOOKBACK,
    SLOT2_BUCKETS,
)

logger = logging.getLogger(__name__)

TIMEOUT = 20


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


def _headers(extra=None):
    h = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _rest(table: str) -> str:
    return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"


def _get(table: str, params: dict):
    """GET a table, returning [] on any failure."""
    if not is_configured():
        logger.warning("Supabase not configured; treating %s as empty.", table)
        return []
    try:
        r = requests.get(_rest(table), headers=_headers(), params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Supabase read from %s failed: %s", table, e)
        return []


def recent_suggestions(limit: int = DEDUP_LOOKBACK):
    """The last ``limit`` suggestions, newest first — the dedup exclusion list."""
    return _get(SUGGESTIONS_TABLE, {
        "select": "title,bucket,source_note,date",
        "order": "sent_at.desc",
        "limit": limit,
    })


def recent_reactions(limit: int = REACTION_LOOKBACK):
    """The last ``limit`` reactions with their suggestion's title and bucket.

    Uses PostgREST's embedded-resource syntax over the reactions →
    suggestions foreign key, so this is one round trip, not a join in Python.
    """
    rows = _get(REACTIONS_TABLE, {
        "select": f"reaction,reacted_at,{SUGGESTIONS_TABLE}(title,bucket)",
        "order": "reacted_at.desc",
        "limit": limit,
    })
    out = []
    for row in rows:
        parent = row.get(SUGGESTIONS_TABLE) or {}
        title = parent.get("title")
        if not title:
            # Suggestion row was deleted out from under the reaction.
            continue
        out.append({
            "reaction": row.get("reaction"),
            "title": title,
            "bucket": parent.get("bucket", ""),
        })
    return out


def next_slot2_bucket() -> str:
    """Flip slot 2 between portfolio and new-build, based on what was last sent.

    State-tracked rather than derived from the date so a skipped or failed run
    never silently flips the rotation twice.
    """
    first, second = SLOT2_BUCKETS
    rows = _get(SUGGESTIONS_TABLE, {
        "select": "bucket,date,sent_at",
        "bucket": f"in.({','.join(SLOT2_BUCKETS)})",
        "order": "date.desc,sent_at.desc",
        "limit": 1,
    })
    if not rows:
        logger.info("No slot-2 history; starting rotation at %s.", first)
        return first
    last = rows[0].get("bucket")
    nxt = second if last == first else first
    logger.info("Slot 2: last sent %s, sending %s.", last, nxt)
    return nxt


def insert_suggestion(date_str: str, bucket: str, title: str, body: str, source_note: str = None):
    """Insert one suggestion and return its uuid, or None if the write failed."""
    if not is_configured():
        logger.warning("Supabase not configured; suggestion not persisted.")
        return None
    payload = {
        "date": date_str,
        "bucket": bucket,
        "title": title,
        "body": body,
        "source_note": source_note,
    }
    try:
        r = requests.post(
            _rest(SUGGESTIONS_TABLE),
            headers=_headers({"Prefer": "return=representation"}),
            json=payload,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json()
        sid = rows[0]["id"] if rows else None
        logger.info("Stored %s suggestion %s", bucket, sid)
        return sid
    except Exception as e:
        logger.error("Supabase insert failed for bucket %s: %s", bucket, e)
        return None
