import os

from dotenv import load_dotenv

load_dotenv()

# --- Secrets / environment ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Model / timing ---
GROQ_MODEL = "llama-3.3-70b-versatile"
IST_TIMEZONE = "Asia/Kolkata"
# This brief runs once a day, so look back a full 24 hours.
LOOKBACK_HOURS = 24

# --- RSS sources, tagged by category ---
RSS_FEEDS = [
    # ── NEW RELEASES (model launches, product drops, lab announcements) ──
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "category": "ai_releases"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss", "category": "ai_releases"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss", "category": "ai_releases"},
    {"name": "Meta AI", "url": "https://ai.meta.com/blog/rss/", "category": "ai_releases"},
    {"name": "Mistral AI", "url": "https://mistral.ai/news/rss", "category": "ai_releases"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss", "category": "ai_releases"},
    {"name": "xAI Blog", "url": "https://x.ai/blog/rss", "category": "ai_releases"},
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
    "You are an AI intelligence analyst writing for a 20-year-old solo founder in India who builds D2C brands and AI tools. Your job is to produce a deep, founder-focused daily AI brief that makes him genuinely smarter about AI every single day.\n"
    "OUTPUT FORMAT — produce exactly these 5 sections in order. Skip a section only if there is genuinely zero relevant content for it today:\n"
    "🚀 NEW RELEASES Cover new model releases, product launches, and major updates from AI labs. For each item write exactly 4 lines: Line 1 — WHAT: One sentence. Name the model/product, who made it, what's new vs previous version. Must include a specific capability or benchmark. Line 2 — WHY IT MATTERS: One sentence. What does this change for developers or users? Be specific. Line 3 — FOUNDER USE CASE: One sentence starting with 'You can use this to...' — give a specific, actionable way a D2C founder or AI builder in India can use this right now. Line 4 — DIFFICULTY: 🟢 Easy (no code) / 🟡 Medium (some API work) / 🔴 Hard (significant engineering) Max 4 stories in this section.\n"
    "🧠 RESEARCH WORTH KNOWING Cover AI research papers and breakthroughs — but only ones with practical implications. No pure academic theory. For each item write exactly 3 lines: Line 1 — FINDING: One sentence. What did researchers discover or prove? Use plain english, no jargon. Line 2 — WHY IT MATTERS: One sentence. What does this mean for AI products in the next 6-12 months? Line 3 — WATCH FOR: One sentence. What product or company will likely implement this first? Max 2 stories in this section. Skip entirely if no practical research today.\n"
    "🛠 TOOLS YOU CAN USE TODAY Cover new AI tools, apps, and APIs that are immediately usable. For each item write exactly 3 lines: Line 1 — TOOL: Name, what it does, who made it, pricing (free/paid/freemium). Line 2 — BEST FOR: One sentence. What specific task is this best for? Line 3 — TRY IT: The URL or how to access it. Max 3 tools in this section.\n"
    "💰 AI BUSINESS Cover funding rounds, acquisitions, partnerships, and industry moves. For each item write exactly 3 lines: Line 1 — WHAT: Company name + what happened + the number (funding amount, deal size, valuation). Line 2 — SIGNAL: What does this investment/deal tell us about where AI is heading? Line 3 — INDIA ANGLE: One sentence on how this affects Indian AI founders or the Indian market. If no India angle exists, write 'No direct India impact.' Max 3 stories in this section.\n"
    "💡 FOUNDER INSIGHT This is the most important section. One single actionable insight, tip, or observation for an AI-focused founder. Not news — a lesson, a pattern, or a specific thing to do this week based on today's AI landscape. Write exactly 3-5 sentences. Make it feel like advice from a sharp AI-aware mentor, not a news summary.\n"
    "GLOBAL RULES:\n"
    "* Never use these phrases: 'will be closely watched', 'has the potential to', 'aims to', 'reflects the', 'will be significant', 'set to', 'is expected to', 'could potentially', 'in the coming weeks', 'will likely', 'potentially leading to', 'marks a', 'highlights the'\n"
    "* Every fact must be specific — name the model, the number, the company, the capability\n"
    "* The Founder Use Case line in NEW RELEASES is the most important line — make it genuinely actionable for someone building in India\n"
    "* If a section has no strong content today, skip it entirely rather than padding with weak stories\n"
    "* Max total stories across all sections: 12"
)
