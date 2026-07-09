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


# Despite the "no bullet points" rule the model sometimes prefixes story
# lines with a list marker ("- ", "1. ", or a bare ". "). Strip any marker
# that sits directly before an importance dot so lines start with the dot.
_LIST_MARKER_RE = re.compile(r"^\s*(?:[-*•.]|\d+[.)])\s*(?=[🔴🟡🔵])", re.MULTILINE)


# The model still repeats a section header before every story despite the
# "each section header appears exactly once" prompt rule.
_SECTION_EMOJIS = ("🚀", "🧠", "🛠", "💰", "💡", "🔍")


def _dedupe_section_headers(brief: str) -> str:
    """Keep the first occurrence of each section header line, drop repeats.

    Stories under a dropped repeat keep their blank-line separation, so the
    result reads as one section with multiple stories.
    """
    seen = set()
    out = []
    for line in brief.splitlines():
        emoji = next(
            (e for e in _SECTION_EMOJIS if line.strip().startswith(e)), None
        )
        if emoji:
            if emoji in seen:
                continue
            seen.add(emoji)
        out.append(line)
    return "\n".join(out)


# Deterministic filler scrub. Longer patterns first so e.g. "will likely be"
# is removed whole before "will likely" can match a fragment. (pattern, repl).
_FILLER_SUBS = [
    # Replace hedges with the firm form rather than deleting — bare deletion
    # left broken grammar ("as they be the first to ship").
    (r"will likely be ", "will be "),
    (r"will likely ", "will "),
    (r"is likely to ", "will "),
    (r"are likely to ", "will "),
    (r"in the coming months", ""),
    (r"in the coming weeks", ""),
    (r"in the coming days", ""),
    (r"is expected to ", ""),
    (r"are expected to ", ""),
    (r"aiming to ", ""),
    (r"with a focus on ", ""),
    (r"in order to ", "to "),
    (r"highlights the ", ""),
    (r"may impact ", ""),
    (r"potentially leading to ", ""),
    (r"could impact ", ""),
    # Specific before generic: rewrite "Indian companies like" to "Indian
    # companies" before the bare "companies like" deletion can strip it.
    (r"Indian companies like ", "Indian companies "),
    (r"companies like ", ""),
]


def _scrub_filler(digest: str) -> str:
    """Delete/replace the most common filler phrases, then tidy whitespace."""
    for pattern, repl in _FILLER_SUBS:
        digest = re.sub(pattern, repl, digest, flags=re.IGNORECASE)
    # Normalize tool citations: links are pasted bare ('Search: [name]' is the
    # other allowed form), so drop any 'URL:'/'Link:' prefix before a real link.
    digest = re.sub(r"\b(?:URL|Link):\s*(?=https?://)", "", digest)
    # Tidy artifacts left by deletions: collapse runs of spaces and remove
    # spaces left before sentence punctuation.
    digest = re.sub(r"[ \t]{2,}", " ", digest)
    digest = re.sub(r" +([.,;:])", r"\1", digest)
    return digest


# The model keeps hedging the AI-BUSINESS India angle ('may impact', 'could
# affect Indian companies like ...') instead of naming a specific company or
# saying nothing. These words/phrases mark a non-specific, speculative angle.
# The second alternative catches example-listing after ANY plural noun
# ("startups like Ninjacart", "sectors such as fintech"), not just
# "companies like" — that literal let "Indian startups like X and Y" through.
_INDIA_SEG_RE = re.compile(r"India:\s*(.*)$", re.IGNORECASE)
_INDIA_SPECULATION_RE = re.compile(
    r"\b(?:may|could|potentially|might|possibly)\b"
    r"|\b[a-z]+s\s+(?:like|such as)\s",
    re.IGNORECASE,
)


def _fix_india_angle(brief: str) -> str:
    """Force speculative India angles to the firm 'No direct India impact.'

    Scans each line's ``India:`` segment (it sits inline after the signal
    sentence in this brief's format) and, if it hedges with speculation words,
    replaces everything from ``India:`` onward with the fallback line.
    """
    out = []
    for line in brief.splitlines():
        m = _INDIA_SEG_RE.search(line)
        if m and _INDIA_SPECULATION_RE.search(m.group(1)):
            prefix = line[:m.start()].rstrip()
            line = (prefix + " " if prefix else "") + "India: No direct India impact."
        out.append(line)
    return "\n".join(out)


# FOUNDER INSIGHT keeps regressing to mentor-flavored filler ("explore how you
# can leverage AI tools like X and Y") despite the prompt rules. Detect the
# telltale phrases and, if any appear, ask the model once to rewrite just the
# insight grounded in today's stories.
_INSIGHT_SECTION_RE = re.compile(
    r"(💡\s*\**FOUNDER INSIGHT\**[^\n]*\n)(.*?)(?=\n🔍|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_GENERIC_INSIGHT_RE = re.compile(
    r"\b(?:leverage|leveraging|explore how|explore using|embrace|"
    r"consider (?:using|integrating|adopting|exploring)|"
    r"stay ahead|keep an eye|stay (?:updated|informed)|game.?changer|"
    r"rapidly evolving|landscape|tools? like|models? like|platforms? like|"
    r"freeing up|free up time|allowing you to focus|higher-level)\b",
    re.IGNORECASE,
)

_INSIGHT_REWRITE_PROMPT = (
    "You wrote this FOUNDER INSIGHT for a daily AI brief read by a 20-year-old "
    "solo founder in India building D2C brands and AI tools:\n\n{insight}\n\n"
    "It is too generic. Rewrite it in 2-3 sentences using ONLY the stories "
    "below. Sentence 1: one non-obvious pattern connecting at least two of "
    "today's stories — a pattern, not a summary. Sentence 2: one concrete "
    "action this week, naming an exact tool, model, or API from the stories "
    "and the exact task to point it at. Optional sentence 3: the cost of not "
    "acting. Banned words: leverage, explore, consider, embrace, landscape, "
    "stay ahead, 'tools like', 'freeing up time', 'allowing you to focus', "
    "'higher-level'. Reply with ONLY the rewritten insight text — no header, "
    "no preamble.\n\nToday's stories:\n{body}"
)


def _sharpen_insight(client, brief: str) -> str:
    """If the FOUNDER INSIGHT contains generic-filler phrases, rewrite it once."""
    m = _INSIGHT_SECTION_RE.search(brief)
    if not m:
        return brief
    insight = m.group(2).strip()
    if not insight or not _GENERIC_INSIGHT_RE.search(insight):
        return brief

    logger.info("Founder Insight looked generic; requesting a rewrite.")
    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": _INSIGHT_REWRITE_PROMPT.format(
                    insight=insight, body=brief[:m.start()]
                ),
            }],
            temperature=0.4,
            max_tokens=300,
        )
        rewritten = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Insight rewrite failed (%s); keeping the original.", e)
        return brief

    if not rewritten:
        return brief
    if _GENERIC_INSIGHT_RE.search(rewritten):
        logger.warning("Insight rewrite is still generic; using it anyway.")
    return brief[:m.start(2)] + rewritten + brief[m.end(2):]


# RESEARCH's "Watch:" segment hedges the same way the India angle does
# ("Indian startups like X or Y may ship this") — same markers, same fix:
# fall back to the firm "open field" the prompt allows.
_WATCH_SEG_RE = re.compile(r"Watch:\s*(.*)$", re.IGNORECASE)


def _fix_watch_segment(brief: str) -> str:
    out = []
    for line in brief.splitlines():
        m = _WATCH_SEG_RE.search(line)
        if m and _INDIA_SPECULATION_RE.search(m.group(1)):
            line = line[:m.start()].rstrip() + " Watch: open field."
        out.append(line)
    return "\n".join(out)


def _clean_headline(text: str) -> str:
    return text.strip().lstrip("🚀🧠🛠💰💡🟢🟡🔴🔵 ").strip()


# Fallback headline shape when the model drops the **bold** markers: a story
# line starts with an importance dot and the headline runs up to the em-dash.
_STORY_LINE_RE = re.compile(r"^[🔴🟡🔵]\s*(.+?)\s+—", re.MULTILINE)


def _extract_headlines(brief: str):
    """Pull every story headline out of the brief body.

    Prefers **bolded** headlines; if the model emitted none (it often drops
    the markers), falls back to dot-prefixed story lines so the dedup store
    still gets populated.
    """
    headlines = [_clean_headline(m) for m in _HEADLINE_RE.findall(brief)]
    headlines = [h for h in headlines if h]
    if not headlines:
        headlines = [_clean_headline(m) for m in _STORY_LINE_RE.findall(brief)]
        headlines = [h for h in headlines if h]
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

    # Strip stray list markers so story lines start with their importance dot.
    brief = _LIST_MARKER_RE.sub("", brief)

    # Collapse the per-story repeated section headers to one per section.
    brief = _dedupe_section_headers(brief)

    # Force any speculative India angle to the firm fallback line FIRST — the
    # filler scrub below deletes "may impact"/"could impact", which would
    # otherwise strip the speculation markers this guard keys on and let a
    # mangled India line slip through.
    brief = _fix_india_angle(brief)

    # Same treatment for RESEARCH's speculative "Watch:" segment.
    brief = _fix_watch_segment(brief)

    # Rewrite a generic FOUNDER INSIGHT before the filler scrub so the
    # replacement text gets scrubbed too.
    brief = _sharpen_insight(client, brief)

    # Strip the most common filler phrases the model still emits.
    brief = _scrub_filler(brief)

    # Record headlines so tomorrow's brief can skip these stories.
    add_headlines(_extract_headlines(brief))

    return brief
