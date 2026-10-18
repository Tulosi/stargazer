# Stargazer

A single-file web page (`site/index.html`, no build step, no dependencies) that shows saved Reddit posts as a bento gallery.
Hosted on GitHub Pages. Accounts and storage come from Supabase (free plan). The page is public; the data is not.

## Layout
- `site/index.html`  the whole app (HTML, CSS, JS). `site/config.js` holds the Supabase URL and anon key (safe to publish; Row Level Security protects data).
- `supabase/schema.sql`  table, row-level security and the `merge_posts` function. Run once in the Supabase SQL editor.
- `supabase/functions/redgifs/index.ts`  optional Edge Function (deployed by hand, Verify JWT off): looks RedGifs clips up for the page when the browser cannot reach the RedGifs API ("Failed to fetch"). The page tries RedGifs directly first, then this helper.
- `tools/hot_relay.py`  optional local relay that lets the page read Reddit's real hot feed (browsers cannot call Reddit directly).
- `.github/workflows/`  `pages.yml` deploys `site/`; `keepalive.yml` pings Supabase so the free project is not paused.
- `tests/`  Playwright checks (`merge_test.py`, `nsfw_test.py`, `panels_test.py`, `lists_test.py`, `reset_test.py`, `viewer_yt_test.py`, `wayback_test.py`, `gone_pic_test.py`, `audio_test.py`, `unload_test.py`, `cloud_reload_test.py`, `first_load_test.py`, `stats_test.py`, `intro_test.py`, `nav_test.py`, `view_test.py`).

## Rules that must not be broken
1. **No personal data in the repo.** No saved-post lists, no CSV files, no subreddit lists from a real account, no keys other than the Supabase anon key. `.gitignore` blocks `*.csv` and `local/`.
2. **Never add the Supabase `service_role` key anywhere.**
3. **Data scheme** (CSV and database): `id, permalink, starred, updated, deleted`. `updated` is the ms time of the last change to that post; `deleted=1` is a tombstone that is kept forever.
   Merge rule, in `pickRec` / `mergeSets` in the page and in `merge_posts` in SQL (keep them identical): newer `updated` wins; on a tie a tombstone beats a live row; two live ties keep the star if either has it.
   A post with a tombstone must never be revived by an older copy.
   A manual NSFW override is stored in the permalink as `?nsfw=1` / `?nsfw=0` (see `nsfwMark`, `toggleNsfw`); no mark means the automatic guess. Keep it in the permalink so the columns and the database schema do not change.
4. Every edit must stamp the record (`nowT`) and call `markDirty`; deletions go through `deleteRows`.
5. The page must keep working with no `config.js` values (accounts hidden) and from `file://`.

## Working notes
- The top bar has two floating panels: **Filters** (`#panel`, what is shown) and **Source** (`#srcpanel`, which list, sign-in, sync, Subreddit mode). Opening one closes the other. Keep source/account controls out of Filters. The Source switch and list tools come first in the Source panel; the Account block (sign-in, marked Optional) follows as a folded section, then Advanced (RedGifs helper status). A list is either **Local** (this browser or a linked file) or **Account** (`rec.cloud`, synced); `csvInfo` shows which, and `#csvCloud` switches it.
- Navigation: `#navbtns` holds Source, Filters, Shuffle and Search. On wide screens it is `display:contents` inside the top bar (labelled buttons, search box always visible); on phones it is a fixed bottom bar and the panels open as bottom sheets. The top bar loses its `backdrop-filter` on phones because a blurred parent would trap fixed children.
- The Active / Retrieved / Total strip lives in the top bar; on phones it folds to one line on scroll down (FLIP animation, header flow height held constant). A refresh keeps filters and scroll for the tab (sessionStorage only; NSFW never persists to a later visit).
- The page is one file on purpose. Search by function name (`syncCloud`, `mergeSets`, `fillCard`, `openViewer`, ...).
- Archive APIs (Arctic Shift, PullPush, Wayback) are rate limited; requests go through `timed()` / `apiRetry()` with per-host spacing and back-off. Do not add direct `fetch` calls to them.
- Images load through the `IMGQ` queue (limits concurrency, pauses on bursts of failures, shows a countdown).
- Touch screens use touch events for pinch/zoom in the viewer; mouse and pen use pointer events.
- Test by loading the page in Playwright with network routes mocked (see `tests/`). There is no live access to Reddit or the archives from the dev sandbox.

## Deploying
Push to `main`; `pages.yml` publishes `site/`. Settings needed once: Pages source = GitHub Actions; Actions secrets `SUPABASE_URL`, `SUPABASE_ANON_KEY` for the keepalive.
