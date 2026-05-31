import logging
import re

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, CATEGORY_LABELS, CATEGORY_ORDER
from dedup import add_headlines

logger = logging.getLogger(__name__)

# Story headlines in the brief are wrapped in **bold**.
_HEADLINE_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_TRENDING_RE = re.compile(r"(🔍\s*Trending Topics:)\s*(.*)", re.IGNORECASE | re.DOTALL)

# Generic words that must never appear in Trending Topics.
_GENERIC_TRENDING = {
    "analysis", "reports", "report", "data", "research", "trends", "updates",
    "update", "insights", "perspectives", "recommendations", "statistics",
    "graphs", "charts", "tables", "studies", "findings", "results",
    "conclusions", "suggestions", "ideas", "opinions", "views", "editorials",
    "articles", "columns", "blogs", "news", "story", "stories",
}
_MAX_TRENDING = 7


def _sanitize_trending(digest: str) -> str:
    """Replace a possibly-runaway Trending Topics line with a clean, deduped,
    capped one. Guards against the model's repetition-loop hallucination."""
    m = _TRENDING_RE.search(digest)
    if not m:
        return digest

    raw = m.group(2)
    seen = set()
    clean = []
    for token in raw.split("·"):
        t = token.strip().strip("*").strip()
        if not t or len(t) > 40:
            continue
        key = t.lower()
        if key in _GENERIC_TRENDING or key in seen:
            continue
        seen.add(key)
        clean.append(t)
        if len(clean) >= _MAX_TRENDING:
            break

    new_line = f"{m.group(1)} " + " · ".join(clean)
    # Trending Topics is the last line; drop anything the model ran on after it.
    return digest[:m.start()] + new_line


# Deterministic filler scrub. Longer patterns first so e.g. "will likely be"
# is removed whole before "will likely" can match a fragment. (pattern, repl).
_FILLER_SUBS = [
    (r"will likely be ", ""),
    (r"will likely ", ""),
    (r"is likely to ", ""),
    (r"are likely to ", ""),
    (r"in the coming months", ""),
    (r"in the coming weeks", ""),
    (r"in the coming days", ""),
    (r"is expected to ", ""),
    (r"are expected to ", ""),
    (r"aiming to ", ""),
    (r"with a focus on ", ""),
    (r"in order to ", "to "),
]


def _scrub_filler(digest: str) -> str:
    """Delete/replace the most common filler phrases, then tidy whitespace."""
    for pattern, repl in _FILLER_SUBS:
        digest = re.sub(pattern, repl, digest, flags=re.IGNORECASE)
    # Tidy artifacts left by deletions: collapse runs of spaces and remove
    # spaces left before sentence punctuation.
    digest = re.sub(r"[ \t]{2,}", " ", digest)
    digest = re.sub(r" +([.,;:])", r"\1", digest)
    return digest


def _clean_headline(text: str) -> str:
    return text.strip().lstrip("🚀🧠🛠💰💡🟢🟡🔴 ").strip()


def _extract_headlines(brief: str):
    """Pull every **bolded** story headline out of the brief body."""
    headlines = []
    for match in _HEADLINE_RE.findall(brief):
        text = _clean_headline(match)
        if text:
            headlines.append(text)
    return headlines


def _format_articles(grouped):
    """Turn the {category: [articles]} dict into a compact prompt for Groq."""
    lines = []
    for cat in CATEGORY_ORDER:
        items = grouped.get(cat)
        if not items:
            continue
        label = CATEGORY_LABELS.get(cat, cat.upper())
        lines.append(f"### Category: {label}")
        # Cap per category to stay under Groq's tokens/min limit.
        for a in items[:10]:
            lines.append(f"- Source: {a['source']}")
            lines.append(f"  Title: {a['title']}")
            if a.get("summary"):
                lines.append(f"  Summary: {a['summary'][:200]}")
            if a.get("url"):
                lines.append(f"  URL: {a['url']}")
        lines.append("")
    return "\n".join(lines)


def summarize(grouped):
    """Run the fetched, grouped articles through Groq and return the brief body."""
    if not grouped:
        return None

    client = Groq(api_key=GROQ_API_KEY)
    user_content = _format_articles(grouped)

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
        max_tokens=2000,
    )
    logger.info("Groq 200 — model %s responded.", GROQ_MODEL)
    brief = resp.choices[0].message.content.strip()

    # Deterministic guard against the Trending Topics repetition hallucination.
    brief = _sanitize_trending(brief)

    # Strip the most common filler phrases the model still emits.
    brief = _scrub_filler(brief)

    # Record headlines so tomorrow's brief can skip these stories.
    add_headlines(_extract_headlines(brief))

    return brief
