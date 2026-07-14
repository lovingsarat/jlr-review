create extension if not exists vector;

create table if not exists public.feedback_items (
  id text primary key,
  source_hash text not null unique,
  platform text not null,
  author text not null,
  date date not null,
  event text not null,
  text text not null,
  sentiment text not null check (sentiment in ('Positive', 'Neutral', 'Negative')),
  city text not null,
  is_upcoming boolean not null default false,
  embedding vector(768),
  created_at timestamptz not null default now()
);

create index if not exists feedback_items_date_idx on public.feedback_items (date desc);
create index if not exists feedback_items_embedding_idx on public.feedback_items using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function public.match_feedback(query_embedding vector(768), match_count integer default 8)
returns table (
  id text,
  platform text,
  author text,
  date date,
  event text,
  text text,
  sentiment text,
  city text,
  is_upcoming boolean,
  similarity real
)
language sql
stable
as $$
  select
    feedback_items.id,
    feedback_items.platform,
    feedback_items.author,
    feedback_items.date,
    feedback_items.event,
    feedback_items.text,
    feedback_items.sentiment,
    feedback_items.city,
    feedback_items.is_upcoming,
    1 - (feedback_items.embedding <=> query_embedding) as similarity
  from public.feedback_items
  where feedback_items.embedding is not null
  order by feedback_items.embedding <=> query_embedding
  limit match_count;
$$;
