# 🤖 AI Intelligence Daily

A standalone Telegram bot that delivers a deep, founder-focused AI intelligence
brief every morning at **06:30 IST (01:00 UTC)**.

Every day it fetches the last 24 hours of AI news, research, and tool releases
from ~25 RSS sources, processes everything through **Groq LLaMA 3.3-70B**, and
sends a structured 5-section brief to Telegram.

> **Sister project to [Daily-Digest NewsBot](../Daily-Digest%20NewsBot).**
> This is a separate, standalone bot with its **own Telegram bot token**. It
> reuses the same fetching / dedup / Telegram patterns but is focused entirely
> on AI intelligence for a solo founder building D2C brands and AI tools in
> India. The two projects do not share code or runtime — only conventions.

## The 5 sections

1. 🚀 **NEW RELEASES** — model launches & product drops (WHAT / WHY / FOUNDER USE CASE / DIFFICULTY)
2. 🧠 **RESEARCH WORTH KNOWING** — practical research only (FINDING / WHY / WATCH FOR)
3. 🛠 **TOOLS YOU CAN USE TODAY** — immediately usable tools (TOOL / BEST FOR / TRY IT)
4. 💰 **AI BUSINESS** — funding, acquisitions, deals (WHAT / SIGNAL / INDIA ANGLE)
5. 💡 **FOUNDER INSIGHT** — one sharp, actionable takeaway

## File structure

```
AI-Intelligence-Daily/
├── bot.py              # Entrypoint, --run-now flag for testing
├── fetcher.py          # RSS fetching (requests + browser UA + feedparser), 24h filter, dedup
├── summarizer.py       # Groq API call with the deep founder prompt
├── telegram_sender.py  # Telegram send with 4000-char chunking
├── config.py           # RSS feeds, system prompt, env vars
├── dedup.py            # 24h headline dedup tracker
├── sent_stories.json   # Dedup state (committed by the workflow)
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile
└── .github/workflows/ai_daily.yml
```

## Local setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys
python bot.py --run-now     # build + send one brief immediately
```

### Environment variables

| Var | Notes |
| --- | --- |
| `GROQ_API_KEY` | Same key as the NewsBot is fine |
| `TELEGRAM_BOT_TOKEN` | **Must be a NEW bot** (e.g. `@AI_Intel_Daily_bot`) — do not reuse the NewsBot's token |
| `TELEGRAM_CHAT_ID` | Same chat ID as the NewsBot is fine |

## Deployment

Triggered via **`repository_dispatch`** from [cron-job.org](https://cron-job.org)
at 01:00 UTC daily — the same pattern as the NewsBot. There is no native
GitHub cron schedule. See the workflow at `.github/workflows/ai_daily.yml`.

The workflow restores `sent_stories.json` from `main`, runs the bot, and commits
the updated dedup state back so stories aren't repeated day to day.
