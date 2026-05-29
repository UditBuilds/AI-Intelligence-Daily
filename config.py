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
    "🚀 NEW RELEASES\n"
    "[Model/Product Name] by [Company] — [one sentence: what it does + what's new]. Founder use: [one specific sentence starting with 'Use this to...' — name a concrete task, not a vague concept]. [Difficulty: 🟢/🟡/🔴]\n"
    "🧠 RESEARCH WORTH KNOWING\n"
    "Only include if directly useful to a builder in the next 3 months. Skip entirely otherwise.\n"
    "[Finding in plain english] — [one sentence why it matters for products]. Watch: [who will ship this first].\n"
    "🛠 TOOLS YOU CAN USE TODAY\n"
    "[Tool name] — [what it does, pricing]. Best for: [one specific use case]. [URL]\n"
    "💰 AI BUSINESS\n"
    "[Company] [what happened] [number] — [one sentence signal of what this means for AI direction]. India: [one sentence India angle or 'No direct India impact.']\n"
    "INDIA ANGLE: One sentence. Must be specific — name an Indian company, sector, or founder behavior that is directly affected. If you cannot name something specific, write 'No direct India impact.' Never write vague statements about the 'Indian market' or 'Indian startups' in general.\n"
    "💡 FOUNDER INSIGHT\n"
    "This is the most important section. Write exactly 2-3 sentences.\n"
    "RULES:\n"
    "\n"
    "Must contain one specific, contrarian, or non-obvious observation about today's AI landscape\n"
    "Must tell him exactly ONE thing to do THIS WEEK — name the specific tool, model, or API\n"
    "Must NOT summarize or recap the brief — if it reads like a summary, rewrite it entirely\n"
    "Must feel like advice from a senior AI-aware founder mentor, not a news anchor\n"
    "Good example: 'Anthropic hitting $965B pre-IPO means the AI infrastructure layer is locking in fast — pick your Claude vs GPT vs Gemini stack now before API costs spike post-IPO. This week, run one real workflow through Opus 4.8 and compare output quality against whatever you currently use.'\n"
    "Bad example: 'To stay competitive, integrate AI tools like X and Y into your D2C brand' — this is a recap, not an insight\n"
    "BANNED PHRASES — rewrite any sentence containing these:\n"
    "'could lead to', 'may influence', 'potentially affecting', 'might implement', 'could offer', 'will be closely watched', 'has the potential to', 'aims to', 'reflects the', 'will be significant', 'set to', 'is expected to', 'in the coming weeks', 'will likely', 'potentially leading to', 'marks a', 'highlights the', 'could inspire', 'may offer', 'potentially benefiting', 'could provide', 'may help', 'could be used', 'potentially differentiating', 'allowing you to focus', 'freeing up time'\n"
    "QUALITY FILTER — before including any story ask: would a sharp 20-year-old Indian founder stop scrolling to read this? If no, skip it.\n"
    "\n"
    "Skip pure academic research with no product application in 3 months\n"
    "Skip biodefense, pharma, government AI unless the scale affects consumer tech\n"
    "Skip beginner tutorials and documentation releases\n"
    "Skip any story that requires a PhD to understand why it matters\n"
    "\n"
    "The entire brief should take 90 seconds to read. Tight. Punchy. Useful."
)
