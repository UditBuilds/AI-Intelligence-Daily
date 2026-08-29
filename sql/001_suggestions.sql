-- Daily build suggestions + their thumbs up/down feedback.
--
-- Written only by the AI Intelligence Daily job (GitHub Actions) and the
-- Telegram reaction webhook (Vercel), both of which authenticate with the
-- service key. RLS is enabled with no policies, so the project's public
-- anon key cannot read or write either table; the service role bypasses RLS.

create table if not exists suggestions (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  bucket text not null,  -- 'prism-glamshelf' | 'portfolio' | 'new-build'
  title text not null,
  body text not null,
  source_note text,      -- issue URL, or the research signal used
  sent_at timestamptz default now()
);

create table if not exists reactions (
  id uuid primary key default gen_random_uuid(),
  suggestion_id uuid references suggestions(id) on delete cascade,
  reaction text not null,  -- 'up' | 'down'
  reacted_at timestamptz default now()
);

-- next_slot2_bucket() orders by (date desc, sent_at desc) filtered on bucket;
-- recent_suggestions() and recent_reactions() both read newest-first.
create index if not exists suggestions_bucket_date_idx
  on suggestions (bucket, date desc, sent_at desc);
create index if not exists suggestions_sent_at_idx on suggestions (sent_at desc);
create index if not exists reactions_reacted_at_idx on reactions (reacted_at desc);
create index if not exists reactions_suggestion_id_idx on reactions (suggestion_id);

-- One reaction per suggestion: tapping again overwrites rather than stacking,
-- so the calibration window is not swamped by repeated taps on one idea.
create unique index if not exists reactions_one_per_suggestion_idx
  on reactions (suggestion_id);

alter table suggestions enable row level security;
alter table reactions enable row level security;
