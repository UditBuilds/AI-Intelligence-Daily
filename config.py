import os

from dotenv import load_dotenv

load_dotenv()

# --- Secrets / environment ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Model / timing ---
GROQ_MODEL = "openai/gpt-oss-120b"
IST_TIMEZONE = "Asia/Kolkata"
# This brief runs once a day, so look back a full 24 hours.
LOOKBACK_HOURS = 24

# --- RSS sources, tagged by category ---
RSS_FEEDS = [
    # ── NEW RELEASES (model launches, product drops, lab announcements) ──
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "category": "ai_releases"},
    {"name": "Mistral AI", "url": "https://mistral.ai/news/rss", "category": "ai_releases"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss", "category": "ai_releases"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "category": "ai_releases"},
    {"name": "Google News OpenAI", "url": "https://news.google.com/rss/search?q=openai+release&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},
    {"name": "Google News Anthropic", "url": "https://news.google.com/rss/search?q=anthropic+claude+release&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},
    {"name": "Google News Meta AI", "url": "https://news.google.com/rss/search?q=meta+AI+llama+release&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},
    {"name": "Google News Gemini", "url": "https://news.google.com/rss/search?q=google+gemini+release&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},
    {"name": "Google News Mistral", "url": "https://news.google.com/rss/search?q=mistral+AI+model&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},
    {"name": "Google News xAI", "url": "https://news.google.com/rss/search?q=xai+grok+release&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_releases"},

    # ── RESEARCH WORTH KNOWING ──
    {"name": "ArXiv AI", "url": "https://rss.arxiv.org/rss/cs.AI", "category": "ai_research"},
    {"name": "ArXiv ML", "url": "https://rss.arxiv.org/rss/cs.LG", "category": "ai_research"},
    {"name": "Google News AI Research", "url": "https://news.google.com/rss/search?q=AI+research+breakthrough+paper&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_research"},

    # ── TOOLS YOU CAN USE TODAY ──
    {"name": "Product Hunt AI", "url": "https://www.producthunt.com/feed?category=artificial-intelligence", "category": "ai_tools"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "category": "ai_tools"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": "ai_tools"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "ai_tools"},
    {"name": "Google News AI Tools", "url": "https://news.google.com/rss/search?q=AI+tool+launch+startup&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_tools"},

    # ── AI BUSINESS ──
    {"name": "Google News AI Funding", "url": "https://news.google.com/rss/search?q=AI+startup+funding+raised&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_business"},
    {"name": "Google News AI Acquisition", "url": "https://news.google.com/rss/search?q=AI+company+acquisition+deal&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_business"},
    {"name": "Google News AI India", "url": "https://news.google.com/rss/search?q=AI+India+startup+investment&hl=en-IN&gl=IN&ceid=IN:en", "category": "ai_business"},
]

# Human-readable labels for each category, used when formatting the LLM input.
CATEGORY_LABELS = {
    "ai_releases": "NEW RELEASES",
    "ai_research": "RESEARCH",
    "ai_tools": "TOOLS",
    "ai_business": "AI BUSINESS",
}

# Order categories are fed to the model — mirrors the brief's section order.
CATEGORY_ORDER = ["ai_releases", "ai_research", "ai_tools", "ai_business"]

SYSTEM_PROMPT = (
    "You are a top-tier AI intelligence analyst writing for a 20-year-old solo founder in India who builds D2C brands and AI tools. He reads this brief at 6:30 AM in 60 seconds. Every word must carry maximum density, zero fluff, and actionable signal.\n"
    "\n"
    "STRICT SECTION & LENGTH LIMITS:\n"
    "• Max 3 stories under 🚀 NEW RELEASES\n"
    "• Max 1 story under 🧠 RESEARCH WORTH KNOWING — only include if directly useful to a builder within 3 months. Skip section if nothing qualifies.\n"
    "• Max 2 tools under 🛠 TOOLS YOU CAN USE TODAY\n"
    "• Max 2 stories under 💰 AI BUSINESS\n"
    "• FOUNDER INSIGHT is exactly 2 sentences: Sentence 1 is a non-obvious pattern across today's news. Sentence 2 is one high-ROI tactical action for this week.\n"
    "\n"
    "STRICT COMPACT & BULLETED FORMAT:\n"
    "Every section header appears EXACTLY ONCE in order. Each story must start with a bullet point ('•') and be ultra-compact with crisp bold labels:\n"
    "\n"
    "🚀 NEW RELEASES\n"
    "• **[Model/Product Name]** ([Company]) — [What it is & key spec/metric]. ⚡ *Founder use:* [One specific task/API integration]. [🟢/🟡/🔴]\n"
    "CRITICAL: Only write about a model if its exact name appears in the RSS input. Never invent model names.\n"
    "\n"
    "🧠 RESEARCH WORTH KNOWING\n"
    "• **[Paper/Finding Topic]** — [Plain-English breakthrough with metrics/numbers]. 🎯 *Product impact:* [New capability enabled in 3-6 months].\n"
    "\n"
    "🛠 TOOLS YOU CAN USE TODAY\n"
    "• **[Tool Name]** ([Pricing/Tier]) — [Core capability]. 💡 *Best for:* [Specific use case]. [URL or Search: Tool Name]\n"
    "NEVER invent URLs. If not 100% sure of the exact URL, write 'Search: [tool name]'.\n"
    "\n"
    "💰 AI BUSINESS\n"
    "• **[Company/Deal]** ([Funding/Valuation/Metrics]) — [Strategic signal]. 🇮🇳 *India:* [Specific Indian startup/sector impact or 'No direct India impact.']\n"
    "\n"
    "💡 FOUNDER INSIGHT\n"
    "[Sentence 1: Pattern across today's news.] [Sentence 2: Specific high-ROI action for this week naming exact API/tool.]\n"
    "\n"
    "QUALITY & HIGH-SIGNAL RULES:\n"
    "1. QUANTITATIVE SIGNAL: Always include hard numbers, pricing, context window sizes, benchmark gains, or deal sizes when present in input.\n"
    "2. NO SPECULATION: Never use vague hedges like 'companies like X and Y may benefit'. Name specific companies or state facts directly.\n"
    "3. BANNED PHRASES: 'could lead to', 'may influence', 'potentially affecting', 'might implement', 'could offer', 'will be closely watched', 'has the potential to', 'aims to', 'reflects the', 'set to', 'in the coming weeks', 'will likely', 'potentially leading to', 'marks a', 'highlights the', 'allowing you to focus', 'freeing up time'.\n"
    "4. NO FLUFF: Skip beginner documentation, academic meta-evaluations, pharma/biodefense, and generic PR announcements.\n"
    "\n"
    "Make the entire output neat, tight, compact, and packed with high-value intelligence."
)


# ═══════════════════════════════════════════════════════════════════
#  IDEA SUGGESTIONS — "what to build next", appended to the daily brief
# ═══════════════════════════════════════════════════════════════════

# --- Secrets ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Set SUGGESTIONS_ENABLED=0 to ship the news brief without the section
# (useful for a quick rollback without touching the workflow).
SUGGESTIONS_ENABLED = os.getenv("SUGGESTIONS_ENABLED", "1") not in ("0", "false", "False")

# --- Gemini ---
# Free-tier model ids drift; suggester tries these in order and uses the first
# that answers, so a retired id degrades to the next instead of killing the run.
GEMINI_MODELS = [
    m.strip() for m in os.getenv(
        "GEMINI_MODELS", "gemini-2.5-flash,gemini-2.0-flash,gemini-flash-latest"
    ).split(",") if m.strip()
]
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_TIMEOUT = 45

# --- Supabase tables ---
SUGGESTIONS_TABLE = "suggestions"
REACTIONS_TABLE = "reactions"

# How much history feeds the next generation.
DEDUP_LOOKBACK = 20   # recent titles passed as an exclusion list
REACTION_LOOKBACK = 10  # recent 👍/👎 passed as calibration context

# --- Slot 1: repos scanned for open issues ---
GITHUB_ISSUE_REPOS = ["UditBuilds/Prism-Productivity-Tool", "UditBuilds/glamshelf-twin"]
GITHUB_API = "https://api.github.com"
GITHUB_TIMEOUT = 20

# An issue title shorter than this is too thin to turn into a real suggestion.
MIN_ISSUE_TITLE_LEN = 12

# --- Buckets ---
BUCKET_PRISM = "prism-glamshelf"
BUCKET_PORTFOLIO = "portfolio"
BUCKET_NEW_BUILD = "new-build"
# Slot 2 flips between these two, in this order, day over day.
SLOT2_BUCKETS = [BUCKET_PORTFOLIO, BUCKET_NEW_BUILD]

BUCKET_TAGS = {
    BUCKET_PRISM: "#prism-glamshelf",
    BUCKET_PORTFOLIO: "#portfolio",
    BUCKET_NEW_BUILD: "#new-build",
}

# Short project context so Gemini writes suggestions that fit what exists.
PROJECT_CONTEXT = (
    "Prism-Productivity-Tool: an AI-native productivity + spaced-repetition PWA. "
    "Next.js 14, TypeScript, Supabase. Has tasks, notes, reminders, SM-2 flashcards, "
    "PDF-to-cards, a focus timer, push notifications, offline sync, and gym logging.\n"
    "glamshelf-twin: an AI customer-support twin running for a live D2C beauty brand. "
    "Flask, Claude API, WATI/WhatsApp, Instagram webhooks, Shopify, Telegram. "
    "Handles roughly 80% of inbound customer DMs autonomously."
)

# The shared voice for every suggestion, whichever slot it fills.
SUGGESTION_SYSTEM_PROMPT = (
    "You write one build suggestion per request for a 20-year-old solo founder in India "
    "who ships AI tools and D2C products. He reads this at 6:30 AM and wants to know what "
    "to open his editor and build today. Every word must earn its place.\n"
    "\n"
    "OUTPUT: a JSON object with exactly two keys, 'title' and 'body'.\n"
    "\n"
    "TITLE: 4-9 words. Names the thing being built, not the benefit. "
    "Good: 'Offline queue for Prism reminder writes'. "
    "Bad: 'Improve reliability and user experience'.\n"
    "\n"
    "BODY: exactly 3 lines separated by newlines, in this order and no other:\n"
    "Line 1 — What: one sentence naming the concrete thing to build. Name the actual file, "
    "table, endpoint, or screen where it lands when you know it.\n"
    "Line 2 — Why now: one sentence with a specific reason grounded in the evidence you were "
    "given. Cite the signal (the issue, the complaint, the skill gap). Never a generic benefit.\n"
    "Line 3 — First step: one sentence naming the single first action, doable in under 2 hours. "
    "Start with a verb.\n"
    "\n"
    "HARD RULES:\n"
    "- Never invent a GitHub issue, a Reddit thread, a statistic, or a product that you were "
    "not given. If you have no specific evidence, argue from the project context instead and "
    "say so plainly. A vague honest reason beats a precise invented one.\n"
    "- No preamble, no sign-off, no markdown headers, no bullet points, no emoji in title or body.\n"
    "- Scope it to a weekend at most. If it needs a month, cut it down to the first shippable slice.\n"
    "\n"
    "BANNED PHRASES — rewrite any sentence containing these: 'could lead to', 'may influence', "
    "'has the potential to', 'aims to', 'is expected to', 'will likely', 'in the coming weeks', "
    "'leverage', 'seamlessly', 'robust solution', 'game-changer', 'unlock new possibilities', "
    "'streamline your workflow', 'take it to the next level', 'best practices', 'enhance the "
    "user experience', 'improve engagement'.\n"
    "\n"
    "Hard test: if this suggestion could have been written without reading the evidence given, "
    "rewrite it entirely."
)

# Per-slot briefs. Each is appended to the shared prompt above.
SLOT_PROMPTS = {
    BUCKET_PRISM: (
        "This suggestion must be work on Prism-Productivity-Tool or glamshelf-twin — "
        "the founder's two live projects. Pick the single highest-leverage next change. "
        "Prefer something a user would notice."
    ),
    BUCKET_PORTFOLIO: (
        "This suggestion must be a project that strengthens the founder's portfolio for "
        "AI-engineering roles. Anything genuinely relevant to AI engineering counts — "
        "agents, evals, RAG, inference optimisation, data pipelines, tool-use systems, "
        "observability. Favour projects that demonstrate engineering judgement a recruiter "
        "can verify from a README and a demo, not toy wrappers around a chat API. "
        "The project must be startable this week and demo-able within two weekends."
    ),
    BUCKET_NEW_BUILD: (
        "This suggestion must be a standalone app or tool the founder could ship and "
        "potentially charge for. Ground it in evidence of unmet demand — someone complaining "
        "that a thing does not exist, a bad review, a recurring 'I wish there was X'. "
        "Demand evidence beats trend-following: a hot topic with no frustrated users behind it "
        "is a worse idea than a boring one with real complaints. Name the specific frustration "
        "and who has it."
    ),
}
