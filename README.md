# Stargazer: public site with accounts (free)

GitHub Pages serves the page. Supabase (free plan) provides sign-in and stores each person's list.
Nothing personal is in this folder: the list starts empty and fills from your account.

## Setup (about 15 minutes)

### 1. Supabase (accounts and storage)
1. Create a free account at supabase.com and make a **New project**. Pick a region near you and save the database password somewhere.
2. Open **SQL Editor -> New query**, paste all of `supabase/schema.sql`, press **Run**.
3. Open **Project Settings -> API**. Copy the **Project URL** and the **anon public** key. (Never use or share the `service_role` key.)
4. Open **Authentication -> URL Configuration**. Set **Site URL** to your Pages address (step 3 below, for example `https://YOURNAME.github.io/REPO/`) and add the same address under **Redirect URLs**.
5. Open **Authentication -> Sign In / Providers**. Email is on by default.
   - For personal use you can switch **Confirm email** off, so sign-up needs no email. Supabase's built-in email sender is only meant for light testing and is heavily rate limited.
   - Optional **GitHub** sign-in: create an OAuth app in GitHub (Settings -> Developer settings -> OAuth Apps), paste Supabase's callback URL into it, then paste the GitHub client ID and secret into Supabase. Then put `"github"` in `providers` in `config.js`.

### 2. Fill in `site/config.js`
Replace the two placeholders with the Project URL and the anon key from step 1.3.

### 3. GitHub Pages
1. Create a new **public** repository (Pages from a private repo needs a paid plan, and the site is public either way).
2. Upload everything in this folder: the whole project.
3. **Settings -> Pages -> Build and deployment**: Source "Deploy from a branch", branch `main`, folder `/ (root)`. Your address appears after a minute.
4. Go back to Supabase step 1.4 and enter that address.

### 4. Lock the door after you have signed up
Once your account exists, in Supabase go to **Authentication -> Sign In / Providers** and turn **Allow new users to sign up** off. The site is public, and otherwise anyone who finds it can create an account and store data in your free quota. Turn it back on only when you want to add someone.

### 5. Keep the free project awake
Supabase pauses free projects after about a week with no activity (you can resume it from the dashboard, but it is unreachable until then).
In the GitHub repo add two secrets under **Settings -> Secrets and variables -> Actions**: `SUPABASE_URL` and `SUPABASE_ANON_KEY`. The workflow in `.github/workflows/keepalive.yml` then pings the project twice a week.
(GitHub switches off scheduled workflows in a repo with no activity for 60 days; open the Actions tab and re-enable it if that happens, or just use the site regularly.)

## How it behaves
- Sign in on any device and your list appears. Saving, starring and deleting sync automatically, and the page also checks for changes when you return to it.
- **Merging is safe.** Each post keeps a last-changed time. The newer change wins, a delete beats an old copy, and a deleted post is never brought back by an old CSV. The same rule is enforced in the database.
- Offline edits are kept on the device and uploaded the next time it can reach your account.
- **Sign out** has a box to also wipe the list from that browser. Use it on shared computers.
- Open CSV / Merge CSV / Export CSV still work, for backups or moving data in.

## Limits and honest caveats
- Free plan (checked May 2026, confirm at supabase.com/pricing): 500 MB database, 50,000 monthly active users, 2 free projects. A list of thousands of posts is a few hundred KB.
- Your sign-in token is stored in the browser, as with most sites of this kind. The page loads no third-party scripts, and a Content-Security-Policy restricts script sources, which keeps that risk low.
- Subreddit mode works on Pages but Reddit does not let web pages read its hot feed, so it shows an archive-based approximation. For Reddit's real hot feed, run `hot_relay.py` on your own computer and open the page from `http://localhost:8765`.
- Reddit post thumbnails and media load straight from Reddit and the archives in each visitor's browser.

## Updating
Edit `site/index.html` and push to `main`.

## Your own list
Your saved posts are not in this repository. Sign in on the site and use **Open CSV** with your CSV once; it uploads to your account.
