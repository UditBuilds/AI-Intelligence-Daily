import { createClient } from '@supabase/supabase-js';

// Types for Vercel Serverless Function
interface VercelRequest {
  method?: string;
  headers: Record<string, string | string[] | undefined>;
  body: any;
}

interface VercelResponse {
  status: (statusCode: number) => VercelResponse;
  json: (data: any) => void;
  send: (body: string) => void;
}

interface TelegramCallbackQuery {
  id: string;
  from: {
    id: number;
    first_name: string;
    username?: string;
  };
  data?: string;
  message?: {
    message_id: number;
    chat: {
      id: number;
    };
  };
}

interface TelegramUpdate {
  update_id: number;
  callback_query?: TelegramCallbackQuery;
  message?: {
    message_id: number;
    chat: {
      id: number;
    };
    text?: string;
  };
}

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const SUPABASE_URL = process.env.SUPABASE_URL || '';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || '';
const TELEGRAM_SECRET_TOKEN = process.env.TELEGRAM_SECRET_TOKEN || '';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
});

/**
 * Answer a Telegram callback query with a pop-up toast message.
 */
async function answerCallbackQuery(callbackQueryId: string, text: string) {
  if (!TELEGRAM_BOT_TOKEN) {
    console.error('TELEGRAM_BOT_TOKEN is not configured.');
    return;
  }

  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/answerCallbackQuery`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        callback_query_id: callbackQueryId,
        text: text,
        show_alert: false,
      }),
    });
    if (!response.ok) {
      const err = await response.text();
      console.error('Failed to answer callback query:', err);
    }
  } catch (error) {
    console.error('Error answering callback query:', error);
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // Verify Telegram secret token if configured
  if (TELEGRAM_SECRET_TOKEN) {
    const headerSecret = req.headers['x-telegram-bot-api-secret-token'];
    if (headerSecret !== TELEGRAM_SECRET_TOKEN) {
      console.warn('Unauthorized webhook request: secret token mismatch.');
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  const update: TelegramUpdate = req.body;

  if (!update) {
    return res.status(400).json({ error: 'Missing update payload' });
  }

  // Handle button reaction taps
  if (update.callback_query) {
    const cq = update.callback_query;
    const data = cq.data || '';

    // Protocol: "r|up|<suggestion_uuid>" or "r|down|<suggestion_uuid>"
    if (data.startsWith('r|')) {
      const parts = data.split('|');
      const reaction = parts[1]; // 'up' or 'down'
      const suggestionId = parts[2];

      if ((reaction === 'up' || reaction === 'down') && suggestionId) {
        console.log(`Processing reaction: ${reaction} for suggestion: ${suggestionId}`);

        try {
          // Upsert into reactions table (replaces reaction if tapped again)
          const { error } = await supabase.from('reactions').upsert(
            {
              suggestion_id: suggestionId,
              reaction: reaction,
              reacted_at: new Date().toISOString(),
            },
            { onConflict: 'suggestion_id' }
          );

          if (error) {
            console.error('Supabase reaction upsert failed:', error);
            await answerCallbackQuery(cq.id, '⚠️ Failed to save feedback.');
          } else {
            const replyText =
              reaction === 'up'
                ? 'Recorded 👍 — calibrated for tomorrow!'
                : "Recorded 👎 — won't suggest similar ideas.";
            await answerCallbackQuery(cq.id, replyText);
          }
        } catch (err) {
          console.error('Unexpected error recording reaction:', err);
          await answerCallbackQuery(cq.id, '⚠️ An error occurred.');
        }
      } else {
        console.warn('Malformed reaction callback_data:', data);
        await answerCallbackQuery(cq.id, '⚠️ Invalid reaction data.');
      }
    } else {
      await answerCallbackQuery(cq.id, 'Acknowledged.');
    }

    return res.status(200).json({ ok: true });
  }

  // Acknowledge any other updates gracefully
  return res.status(200).json({ ok: true, ignored: true });
}
