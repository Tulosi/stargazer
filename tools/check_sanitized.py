"""Fails if the public page (and so the standalone download built from it) carries saved posts.

Run by pages.yml before the site and stargazer.zip are published, and runnable by hand:
    python tools/check_sanitized.py
"""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parents[1]
page = (root / 'site' / 'index.html').read_text(encoding='utf-8')
bad = []

m = re.search(r'const SEED_CSV = `(.*?)`;', page, re.S)
if not m:
    bad.append('SEED_CSV not found in site/index.html')
elif m.group(1).strip() != 'id,permalink,starred,updated,deleted':
    rows = len(m.group(1).strip().splitlines()) - 1
    bad.append(f'SEED_CSV holds {rows} post row(s); the public page must start empty')

for p in (root / 'site').rglob('*.csv'):
    bad.append(f'CSV file in site/: {p.relative_to(root)}')

# Reddit post links built into the page (sample posts use invented ids under data: artwork, never a real permalink)
links = sorted(set(re.findall(r'/r/[A-Za-z0-9_]+/comments/[a-z0-9]{5,8}\b', page)))
if links:
    bad.append(f'{len(links)} Reddit post link(s) in site/index.html, e.g. {links[0]}')

if bad:
    print('Not sanitized:\n  ' + '\n  '.join(bad))
    sys.exit(1)
print('site/index.html is sanitized: SEED_CSV is empty, no CSV files, no built-in Reddit post links.')
