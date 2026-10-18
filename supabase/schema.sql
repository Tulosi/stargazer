-- Run this once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
-- One row per saved post per user. Each user can only ever see and change their own rows.

create table if not exists public.saved_posts (
  user_id   uuid        not null default auth.uid() references auth.users(id) on delete cascade,
  id        text        not null check (id ~ '^[a-z0-9]{4,10}$'),
  permalink text        not null default '' check (length(permalink) < 600),
  starred   boolean     not null default false,
  updated   bigint      not null default 0,        -- client time (ms) of the last change to this post
  deleted   boolean     not null default false,    -- true = deletion record (kept so other devices learn about it)
  synced_at timestamptz not null default now(),    -- server time of the last write, used for incremental downloads
  primary key (user_id, id)
);

create index if not exists saved_posts_sync on public.saved_posts (user_id, synced_at);

alter table public.saved_posts enable row level security;

drop policy if exists "own rows: read"   on public.saved_posts;
drop policy if exists "own rows: write"  on public.saved_posts;
create policy "own rows: read"  on public.saved_posts for select to authenticated using (user_id = auth.uid());
create policy "own rows: write" on public.saved_posts for all    to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Merge a batch of posts into the caller's list. The newer `updated` wins; on an exact tie a deletion wins,
-- and two live copies keep the star if either has it. This is the same rule the page uses, enforced here too
-- so two devices writing at the same moment can never undo each other's deletes.
create or replace function public.merge_posts(rows jsonb)
returns integer
language plpgsql
security invoker
set search_path = public
as $$
declare n integer;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  if jsonb_typeof(rows) <> 'array' or jsonb_array_length(rows) > 1000 then raise exception 'send an array of at most 1000 rows'; end if;

  insert into public.saved_posts as t (user_id, id, permalink, starred, updated, deleted)
  select auth.uid(), lower(r.id), coalesce(r.permalink, ''), coalesce(r.starred, false) and not coalesce(r.deleted, false),
         coalesce(r.updated, 0), coalesce(r.deleted, false)
  from jsonb_to_recordset(rows) as r(id text, permalink text, starred boolean, updated bigint, deleted boolean)
  on conflict (user_id, id) do update
    set permalink = coalesce(nullif(excluded.permalink, ''), t.permalink),
        starred   = case when excluded.updated = t.updated and not excluded.deleted and not t.deleted
                         then excluded.starred or t.starred else excluded.starred end,
        updated   = excluded.updated,
        deleted   = excluded.deleted,
        synced_at = now()
    where excluded.updated > t.updated
       or (excluded.updated = t.updated and excluded.deleted and not t.deleted)
       or (excluded.updated = t.updated and not excluded.deleted and not t.deleted and excluded.starred and not t.starred);

  get diagnostics n = row_count;
  return n;
end $$;

revoke all on function public.merge_posts(jsonb) from public, anon;
grant execute on function public.merge_posts(jsonb) to authenticated;
