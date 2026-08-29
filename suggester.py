"""Daily build suggestions — two slots, appended to the AI Intelligence brief.

Slot 1 is always #prism-glamshelf, grounded in a real open GitHub issue when
one exists and in project context when none does. Slot 2 alternates strictly
between #portfolio and #new-build, flipped from what the database says went out
last rather than from the date, so a skipped run cannot desync the rotation.

Generation runs on Gemini's free tier. Every idea is checked against the last
~20 titles by string similarity before it ships — the prompt is asked not to
repeat itself, but the guard is what enforces it.
"""

import json
import logging
import re
from difflib import SequenceMatcher

import requests

import demand_signals
import github_issues
import supabase_client
from config import (
    GEMINI_API_KEY,
    GEMINI_ENDPOINT,
    GEMINI_MODELS,
    GEMINI_TIMEOUT,
    SUGGESTION_SYSTEM_PROMPT,
    SLOT_PROMPTS,
    BUCKET_PRISM,
    BUCKET_NEW_BUILD,
    PROJECT_CONTEXT,
    GITHUB_ISSUE_REPOS,
)

logger = logging.getLogger(__name__)

# A generated title this close to one already sent counts as a repeat.
TITLE_SIMILARITY_THRESHOLD = 0.75

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {"title": {"type": "STRING"}, "body": {"type": "STRING"}},
    "required": ["title", "body"],
}

# Remembered across both slots so the second call skips models already proven dead.
_working_model = None


# ── Gemini ────────────────────────────────────────────────────────────

def _extract_text(payload) -> str:
    """Concatenate every text part of the first candidate.

    Thinking-enabled models can emit a reasoning part ahead of the answer, so
    reading parts[0] blindly returns the wrong thing on those models.
    """
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini returned no candidates: {payload.get('promptFeedback')}")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p["text"] for p in parts if isinstance(p, dict) and p.get("text"))
    if not text.strip():
        raise ValueError(
            f"Gemini returned an empty part list (finish={candidates[0].get('finishReason')})"
        )
    return text


def _call_gemini(system_prompt: str, user_prompt: str) -> dict:
    """Ask Gemini for one {title, body} object, walking the model fallback list."""
    global _working_model

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json",
            "responseSchema": _RESPONSE_SCHEMA,
        },
    }

    if _working_model:
        order = [_working_model] + [m for m in GEMINI_MODELS if m != _working_model]
    else:
        order = list(GEMINI_MODELS)

    last_error = None
    for model in order:
        try:
            r = requests.post(
                GEMINI_ENDPOINT.format(model=model),
                params={"key": GEMINI_API_KEY},
                json=body,
                timeout=GEMINI_TIMEOUT,
            )
            r.raise_for_status()
            data = json.loads(_extract_text(r.json()))
            title = (data.get("title") or "").strip()
            text = (data.get("body") or "").strip()
            if not title or not text:
                raise ValueError("Gemini omitted title or body")
            _working_model = model
            logger.info("Gemini 200 — model %s responded.", model)
            return {"title": title, "body": text}
        except Exception as e:
            last_error = e
            logger.warning("Gemini model %s failed: %s", model, e)
            continue

    raise RuntimeError(f"All Gemini models failed; last error: {last_error}")


# ── Prompt assembly ───────────────────────────────────────────────────

def _format_exclusions(titles) -> str:
    if not titles:
        return "Nothing has been suggested yet."
    return "\n".join(f"- {t}" for t in titles)


def _format_reactions(reactions) -> str:
    """Turn recent thumbs up/down into a short calibration note for the prompt."""
    if not reactions:
        return "No feedback recorded yet — no calibration signal available."

    up = [r["title"] for r in reactions if r.get("reaction") == "up"]
    down = [r["title"] for r in reactions if r.get("reaction") == "down"]

    lines = []
    if up:
        lines.append("He UPVOTED these — make future ideas more like them:")
        lines += [f"- {t}" for t in up]
    if down:
        lines.append("He DOWNVOTED these — avoid this kind of idea:")
        lines += [f"- {t}" for t in down]
    if not lines:
        return "No feedback recorded yet — no calibration signal available."
    return "\n".join(lines)


def _project_due(history) -> str:
    """Pick the project that has waited longest for attention.

    Reads the most recent #prism-glamshelf source note and returns the *other*
    repo, so the fallback path alternates instead of parking on one project.
    """
    prism, glamshelf = GITHUB_ISSUE_REPOS
    for row in history:
        if row.get("bucket") != BUCKET_PRISM:
            continue
        note = row.get("source_note") or ""
        if prism.split("/")[-1].lower() in note.lower():
            return glamshelf
        if glamshelf.split("/")[-1].lower() in note.lower():
            return prism
    return prism


def _slot1_evidence(issue, history):
    """Evidence block plus source_note to persist, for the #prism-glamshelf slot."""
    if issue:
        labels = ", ".join(issue["labels"]) or "none"
        evidence = (
            "EVIDENCE — a real open GitHub issue on his own repo. Build the suggestion "
            "directly on top of it and reference it:\n"
            f"Repo: {issue['repo']}\n"
            f"Issue #{issue['number']}: {issue['title']}\n"
            f"Opened: {issue['created_at']} | Comments: {issue['comments']} | Labels: {labels}\n"
            f"Description: {issue['body'] or '(no description given)'}"
        )
        return evidence, issue["url"]

    due = _project_due(history)
    evidence = (
        "EVIDENCE — none. There are no open GitHub issues on either repo today, so you "
        "have no ticket to work from. Propose the highest-leverage next change to "
        f"{due} using the project context above and nothing else. Do not reference or "
        "invent an issue number. It is fine for 'Why now' to argue from the state of the "
        "project rather than from a reported problem."
    )
    return evidence, f"fallback: no open issues; project context for {due}"


def _slot2_evidence(bucket):
    """Evidence block plus source_note for whichever slot-2 bucket is up."""
    if bucket != BUCKET_NEW_BUILD:
        return (
            "EVIDENCE — none supplied. Reason from what AI-engineering hiring actually "
            "tests for. Do not cite job postings, salary figures, or company names you "
            "cannot verify.",
            "portfolio: no external signal",
        )

    signals = demand_signals.collect()
    if not signals:
        return (
            "EVIDENCE — none. The demand feeds returned nothing today, so you have no "
            "complaint to point at. Propose an idea anyway, and in 'Why now' say plainly "
            "that this is reasoned from the founder's own domain rather than from a "
            "specific complaint. Do not invent a Reddit thread or a review.",
            "new-build: demand feeds empty",
        )

    complaints = [s for s in signals if s["kind"] == "complaint"]
    lines = [
        "EVIDENCE — real posts pulled today. Ground the idea in one of these and name "
        "the frustration it comes from. Prefer a complaint over a trend:"
    ]
    for s in signals:
        lines.append(f"- [{s['kind']}] {s['title']}")
    return "\n".join(lines), f"demand signals: {len(complaints)} complaints, {len(signals)} total"


def _build_user_prompt(bucket, evidence, exclusions, calibration, retry_note=""):
    return (
        f"PROJECT CONTEXT — his two live projects:\n{PROJECT_CONTEXT}\n\n"
        f"THIS SLOT:\n{SLOT_PROMPTS[bucket]}\n\n"
        f"{evidence}\n\n"
        "ALREADY SUGGESTED — do not repeat any of these ideas, and do not propose a "
        f"reworded version of one:\n{exclusions}\n\n"
        f"FEEDBACK CALIBRATION:\n{calibration}\n"
        f"{retry_note}"
    )


# ── Dedup guard ───────────────────────────────────────────────────────

def _normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", (title or "").lower()).strip()


def _too_similar(title: str, recent_titles):
    """Return the colliding title if ``title`` repeats something recent."""
    norm = _normalize(title)
    if not norm:
        return None
    for prev in recent_titles:
        if SequenceMatcher(None, norm, _normalize(prev)).ratio() >= TITLE_SIMILARITY_THRESHOLD:
            return prev
    return None


def _generate(bucket, evidence, recent_titles, calibration):
    """Generate one suggestion, retrying once if it repeats a recent title."""
    exclusions = _format_exclusions(recent_titles)
    system = f"{SUGGESTION_SYSTEM_PROMPT}\n\n{SLOT_PROMPTS[bucket]}"

    result = _call_gemini(system, _build_user_prompt(bucket, evidence, exclusions, calibration))

    clash = _too_similar(result["title"], recent_titles)
    if clash:
        logger.warning("Suggestion %r repeats %r — regenerating once.", result["title"], clash)
        retry = (
            f"\nYOUR PREVIOUS ATTEMPT WAS REJECTED. You proposed {result['title']!r}, which is "
            f"the same idea as {clash!r} from the exclusion list. Propose a genuinely different "
            "idea — a different subsystem or a different user problem, not a rewording of the "
            "same one."
        )
        result = _call_gemini(
            system, _build_user_prompt(bucket, evidence, exclusions, calibration, retry)
        )
        clash = _too_similar(result["title"], recent_titles)
        if clash:
            # Shipping a near-repeat beats dropping the slot; the log flags it so
            # a pattern of collisions is visible in the Actions run.
            logger.error("Retry still repeats %r; sending anyway.", clash)

    return result


# ── Entry point ───────────────────────────────────────────────────────

def build_suggestions(date_str: str):
    """Generate, persist, and return today's two suggestions.

    Each returned dict carries ``suggestion_id`` (None if the Supabase write
    failed, which means that idea ships without feedback buttons).
    """
    history = supabase_client.recent_suggestions()
    recent_titles = [h["title"] for h in history if h.get("title")]
    recent_sources = [h.get("source_note") for h in history]
    calibration = _format_reactions(supabase_client.recent_reactions())
    logger.info(
        "History: %d recent titles, calibration signal: %s",
        len(recent_titles), "none" if calibration.startswith("No feedback") else "yes",
    )

    slot2_bucket = supabase_client.next_slot2_bucket()
    issue = github_issues.pick_issue(exclude_urls=recent_sources)

    plan = [
        (BUCKET_PRISM,) + _slot1_evidence(issue, history),
        (slot2_bucket,) + _slot2_evidence(slot2_bucket),
    ]

    out = []
    for bucket, evidence, source_note in plan:
        try:
            result = _generate(bucket, evidence, recent_titles, calibration)
        except Exception as e:
            # One dead slot must not take the other down with it.
            logger.error("Could not generate the %s suggestion: %s", bucket, e)
            continue

        sid = supabase_client.insert_suggestion(
            date_str=date_str,
            bucket=bucket,
            title=result["title"],
            body=result["body"],
            source_note=source_note,
        )
        out.append({
            "bucket": bucket,
            "title": result["title"],
            "body": result["body"],
            "source_note": source_note,
            "suggestion_id": sid,
        })
        # Keep the second slot from echoing the first within the same run.
        recent_titles.append(result["title"])

    logger.info("Generated %d/2 suggestions.", len(out))
    return out
