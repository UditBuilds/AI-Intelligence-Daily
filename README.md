# 🤖 AI Intelligence Daily

A standalone Telegram bot that delivers a deep, founder-focused AI intelligence
brief every morning at **06:30 IST (01:00 UTC)**.

Every day it fetches the last 24 hours of AI news, research, and tool releases
from ~25 RSS sources, processes everything through **Groq LLaMA 3.3-70B**, and
sends a structured 5-section brief to Telegram — followed by **2 researched
build suggestions** with 👍/👎 buttons, in the same message.

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

## 🧭 BUILD NEXT — the suggestions section

Appended to the same daily message (never a second one). Exactly two
suggestions, in two fixed slots, each written as *What / Why now / First step*.

**Slot 1 — `#prism-glamshelf`, every day.** Pulls open issues from
`Prism-Productivity-Tool` and `glamshelf-twin`, ranks them most-commented first
with the oldest breaking ties, and builds the suggestion on the winner. Issues
already used as a source recently are skipped so the slot does not stall on one
ticket. When neither repo has a usable open issue, it falls back to a
context-grounded idea for whichever project is more due — alternating between
the two — so this slot is **never empty**.

**Slot 2 — alternates `#portfolio` ⇄ `#new-build`.** The flip is read from the
database (the most recent slot-2 row), not from the date, so a skipped or failed
run cannot desync the rotation.

- `#portfolio` — projects that strengthen an AI-engineering portfolio.
- `#new-build` — standalone tools, biased toward **evidence of unmet demand**
  (Reddit "somebody make this" / "I wish there was" posts) over trend-following.
  Hacker News is pulled in only as a lighter secondary signal.

**Dedup.** The last ~20 titles go into the prompt as an exclusion list, *and* a
`SequenceMatcher` guard rejects any generated title ≥0.75 similar to a recent
one and regenerates once. The prompt asks; the guard enforces.

**Feedback loop.** Each suggestion ships with 👍/👎 inline buttons whose
`callback_data` carries its row uuid. Taps are recorded by a **separate Vercel
function** ([`ai-daily-reactions-webhook`](../ai-daily-reactions-webhook)) —
deliberately its own repo and deploy. The next morning's run reads the last ~10
reactions and feeds them into the generation prompt as calibration.

If Gemini, Supabase, or GitHub is down, the suggestions section is skipped and
**the news brief still ships**. Setting `SUGGESTIONS_ENABLED=0` does the same
thing deliberately.

## File structure

```
AI-Intelligence-Daily/
├── bot.py              # Entrypoint, --run-now flag; assembles the single message
├── fetcher.py          # RSS fetching (requests + browser UA + feedparser), 24h filter, dedup
├── summarizer.py       # Groq API call with the deep founder prompt
├── telegram_sender.py  # Telegram send with 4000-char chunking + inline keyboard
├── config.py           # RSS feeds, system prompts, env vars
├── dedup.py            # 24h headline dedup tracker
├── suggester.py        # BUILD NEXT: slot logic, Gemini call, title dedup guard
├── github_issues.py    # Slot 1 evidence — open issues from the two repos
├── demand_signals.py   # Slot 2 evidence — unmet-demand posts for #new-build
├── supabase_client.py  # PostgREST reads/writes for suggestions + reactions
├── sql/001_suggestions.sql  # Schema for the two tables (run once)
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

Then apply `sql/001_suggestions.sql` once against your Supabase project.

### Environment variables

| Var | Notes |
| --- | --- |
| `GROQ_API_KEY` | Same key as the NewsBot is fine |
| `TELEGRAM_BOT_TOKEN` | **Must be a NEW bot** (e.g. `@AI_Intel_Daily_bot`) — do not reuse the NewsBot's token |
| `TELEGRAM_CHAT_ID` | Same chat ID as the NewsBot is fine |
| `GEMINI_API_KEY` | Free tier. Generates the two daily suggestions |
| `SUPABASE_URL` | Project that holds `suggestions` + `reactions` |
| `SUPABASE_SERVICE_KEY` | Service role — both tables are RLS-locked with no policies |
| `GITHUB_TOKEN` | Reads open issues. Optional for public repos, but avoids the 60 req/hr anonymous limit |
| `SUGGESTIONS_ENABLED` | Optional. `0` ships the news brief without the BUILD NEXT section |
| `GEMINI_MODELS` | Optional. Comma-separated fallback order; first model that answers wins |

## Deployment

Triggered via **`repository_dispatch`** from [cron-job.org](https://cron-job.org)
at 01:00 UTC daily — the same pattern as the NewsBot. There is no native
GitHub cron schedule. See the workflow at `.github/workflows/ai_daily.yml`.

The workflow restores `sent_stories.json` from `main`, runs the bot, and commits
the updated dedup state back so stories aren't repeated day to day. Suggestion
history lives in Supabase, not in the repo.
