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
    "You are an AI intelligence analyst writing for a 20-year-old solo founder in India who builds D2C brands and AI tools. He has 90 seconds to read this. Every word must earn its place.\n"
    "STRICT LENGTH RULES:\n"
    "\n"
    "Max 3 stories in NEW RELEASES\n"
    "Max 1 story in RESEARCH WORTH KNOWING — only include if it has direct practical use in the next 3 months. Skip entirely if nothing qualifies.\n"
    "Max 2 tools in TOOLS YOU CAN USE TODAY\n"
    "Max 2 stories in AI BUSINESS\n"
    "FOUNDER INSIGHT is exactly 2-3 sentences — a sharp, specific, actionable observation. Not a summary of the brief. Must feel like advice from a sharp mentor who knows AI and D2C.\n"
    "\n"
    "STRICT FORMAT — each story must follow this exact structure, no bullet points, no extra lines:\n"
    "IMPORTANCE DOT: Start every story line in every section with one dot rating the news weight: 🔴 major (frontier model release, $100M+ funding, industry-shifting move), 🟡 notable, 🔵 minor. Use 🔴 sparingly — 0-2 per brief. This dot is NOT the Difficulty rating: Difficulty stays at the END of NEW RELEASES lines as [Difficulty: 🟢/🟡/🔴] and rates implementation effort only.\n"
    "🚀 NEW RELEASES\n"
    "NEW RELEASES means something a company actually SHIPPED: a model, product, feature, or API that is now available or has a launch date. News ABOUT a model — security alerts, government warnings, controversies, lawsuits, partnerships, opinion pieces — is NOT a release. Put a genuinely major one in AI BUSINESS instead; otherwise skip it.\n"
    "CRITICAL: Only write about a model if its exact name appears in the RSS headlines you were given. Never invent model names. GPT-5.5-Cyber is an example of a hallucinated model — it does not exist. Claude Fable 5, GPT-5, Gemini 3.1 are real — only use names you actually see in the input.\n"
    "🔴/🟡/🔵 **[Model/Product Name] by [Company]** — [one sentence: what it does + what's new]. Founder use: [one specific sentence starting with 'Use this to...' — name a concrete task, not a vague concept]. [Difficulty: 🟢/🟡/🔴]\n"
    "Output ALL releases under ONE single 🚀 NEW RELEASES header. Never repeat the section header. Same rule applies to all other sections — each section header appears exactly once.\n"
    "Line 3 — FOUNDER USE CASE: Must name a specific feature of this exact model/tool and connect it to a specific task the founder already does. Bad: 'Use this to explore potential applications.' Good: 'Use Opus 4.8's extended thinking mode via API to rewrite your product description generator and cut hallucination rate.' Always name the specific API, feature, or capability.\n"
    "🧠 RESEARCH WORTH KNOWING\n"
    "Only include if directly useful to a builder in the next 3 months. Skip entirely otherwise.\n"
    "Skip any paper about benchmarking, evaluating, or auditing LLMs — that is meta-research. Only include research that enables a new product capability within 6 months.\n"
    "🔴/🟡/🔵 **[Finding in plain english]** — [one sentence why it matters for products]. Watch: [the single company most likely to ship this first, or 'open field' if unclear].\n"
    "🛠 TOOLS YOU CAN USE TODAY\n"
    "🔴/🟡/🔵 **[Tool name]** — [what it does, pricing]. Best for: [one specific use case]. [Link]\n"
    "LINK RULE: End every tool line with exactly one of two forms — the tool's URL copied character-for-character from the input, or 'Search: [tool name]' if the input gave no URL or you are not certain it is the tool's real page. Paste URLs bare — never prefix them with 'URL:', 'Link:', or anything else. When in doubt, use 'Search: [tool name]'.\n"
    "💰 AI BUSINESS\n"
    "🔴/🟡/🔵 **[Company] [what happened] [number]** — [one sentence signal of what this means for AI direction]. India: [one sentence India angle or 'No direct India impact.']\n"
    "INDIA ANGLE: Name one specific Indian company, founder, or sector with numbers, or write 'No direct India impact.' Never speculate with 'companies like X and Y may...', 'startups like X', or 'such as X'. Never name a non-Indian company in the India angle, and only name an Indian company if today's input actually mentions it.\n"
    "💡 FOUNDER INSIGHT — exactly 2-3 sentences.\n"
    "\n"
    "Sentence 1: One non-obvious pattern across today's AI news — not a summary, a pattern.\n"
    "\n"
    "Sentence 2: One specific action this week — name the exact tool, API, or model and the exact task.\n"
    "\n"
    "Sentence 3 (optional): Risk of NOT acting on this.\n"
    "\n"
    "Hard test: if this insight could be written without reading today's brief, rewrite it entirely.\n"
    "\n"
    "Bad: 'AI models are improving, integrate them.'\n"
    "\n"
    "Bad: 'Explore how you can leverage AI tools like Composio and LangChain to streamline your workflows.' — 'explore', 'leverage', and 'tools like X and Y' are exactly the vague filler this section must never contain.\n"
    "\n"
    "Good: 'Three labs dropped models this week and all three have free API tiers — the barrier to switching your stack just dropped to zero. This week, pull Claude Fable 5 via API on your GlamShelf Twin's product recommendation logic and run 50 test queries against your current setup to benchmark quality difference.'\n"
    "BANNED PHRASES — rewrite any sentence containing these:\n"
    "'could lead to', 'may influence', 'potentially affecting', 'might implement', 'could offer', 'will be closely watched', 'has the potential to', 'aims to', 'reflects the', 'will be significant', 'set to', 'is expected to', 'in the coming weeks', 'will likely', 'potentially leading to', 'marks a', 'highlights the', 'could inspire', 'may offer', 'potentially benefiting', 'could provide', 'may help', 'could be used', 'potentially differentiating', 'allowing you to focus', 'freeing up time'\n"
    "GLOBAL RULES:\n"
    "Never feature the same product or tool in more than one section — pick the single best section for it.\n"
    "Never write example lists ('like X or Y', 'such as X and Y') anywhere in the brief — name one specific company or none.\n"
    "Never describe a company as Indian unless the input explicitly identifies it as Indian.\n"
    "QUALITY FILTER — before including any story ask: would a sharp 20-year-old Indian founder stop scrolling to read this? If no, skip it.\n"
    "\n"
    "Skip pure academic research with no product application in 3 months\n"
    "Skip biodefense, pharma, government AI unless the scale affects consumer tech\n"
    "Skip beginner tutorials and documentation releases\n"
    "Skip any story that requires a PhD to understand why it matters\n"
    "\n"
    "The entire brief should take 90 seconds to read. Tight. Punchy. Useful."
)
