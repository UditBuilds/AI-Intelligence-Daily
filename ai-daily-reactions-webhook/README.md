# ⚡ AI Daily Reactions Webhook

A lightweight, standalone Vercel Serverless Function that receives Telegram inline-keyboard button taps (👍 / 👎) from **AI Intelligence Daily**, records founder feedback in **Supabase**, and answers Telegram callback queries.

---

## 🎯 How It Works

1. **AI Intelligence Daily** sends the daily brief with inline buttons for each build suggestion (`callback_data="r|up|<suggestion_id>"` or `"r|down|<suggestion_id>"`).
2. When you tap a button, Telegram sends a `callback_query` POST request to this webhook endpoint (`/api/webhook`).
3. This function:
   - Parses the reaction (`up` or `down`) and the suggestion UUID.
   - Upserts the record into the `reactions` table in Supabase.
   - Responds to Telegram with an immediate toast notification (`Recorded 👍` / `Recorded 👎`).
4. Tomorrow's generation run in **AI Intelligence Daily** reads recent reactions from Supabase and calibrates Gemini's prompt suggestions.

---

## 🛠 Prerequisites

1. **Supabase Database Schema**:
   Ensure `sql/001_suggestions.sql` from the `AI_UpdateBot` repository has been executed against your Supabase project:
   ```sql
   create table if not exists suggestions (
     id uuid primary key default gen_random_uuid(),
     date date not null,
     bucket text not null,
     title text not null,
     body text not null,
     source_note text,
     sent_at timestamptz default now()
   );

   create table if not exists reactions (
     id uuid primary key default gen_random_uuid(),
     suggestion_id uuid references suggestions(id) on delete cascade,
     reaction text not null,
     reacted_at timestamptz default now()
   );

   create unique index if not exists reactions_one_per_suggestion_idx
     on reactions (suggestion_id);
   ```

2. **Telegram Bot Token**:
   The token for your Telegram Bot (e.g. `@AI_Intel_Daily_bot`).

---

## 🚀 Deploy to Vercel

### Option 1: Via Vercel CLI
```bash
cd ai-daily-reactions-webhook
npm install
vercel
```

### Option 2: Via GitHub + Vercel Dashboard
1. Push this directory as its own GitHub repository (e.g., `github.com/Uditbuilds/ai-daily-reactions-webhook`).
2. Import the repo into [Vercel](https://vercel.com).
3. Set the following **Environment Variables** in Vercel Project Settings:

| Variable | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Token for the Telegram bot |
| `SUPABASE_URL` | Your Supabase Project URL (`https://<project-ref>.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Supabase **Service Role** key (bypasses RLS) |
| `TELEGRAM_SECRET_TOKEN` | *(Optional)* Secret string to verify requests |

---

## 🔗 Register Telegram Webhook

Once deployed to Vercel (e.g., `https://ai-daily-reactions-webhook.vercel.app`), register the webhook with Telegram by making this API call:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://<YOUR_VERCEL_DOMAIN>/api/webhook",
       "allowed_updates": ["callback_query"]
     }'
```

*If using `TELEGRAM_SECRET_TOKEN`, include `"secret_token": "<YOUR_SECRET_TOKEN>"` in the JSON payload.*

To verify the webhook status at any time:
```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```
