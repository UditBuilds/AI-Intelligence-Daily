import logging
import re

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, CATEGORY_LABELS, CATEGORY_ORDER
from dedup import add_headlines

logger = logging.getLogger(__name__)

# Story headlines in the brief are wrapped in **bold**.
_HEADLINE_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


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

    # Record headlines so tomorrow's brief can skip these stories.
    add_headlines(_extract_headlines(brief))

    return brief
