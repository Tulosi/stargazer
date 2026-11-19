"""Imgur album and gallery links never borrow i.imgur.com/<id>.jpg (Nov 2026): album / gallery ids are numbered apart from image ids, so that address
is usually an unrelated picture (an old watch-strap album showed a stranger's infographic). Single-image links still use it. Also: the tab icon follows
the skin. Run: python tests/imgur_album_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1200, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(600); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(900)
    def cands(u, th='https://b.thumbs.redditmedia.com/abc.jpg'):
        return ev("""([u,th])=>{ const p = POSTS[0], m = metaOf(p); m.u = u; m.th = th; m.m = /\\/(a|gallery)\\//.test(u) ? 'gallery' : 'image';
            return { tile: imgCandidates(p), full: fullResCandidates(p, ''), chain: buildChain(p, m).map(e=>e.href) }; }""", [u, th])
    for u in ['http://imgur.com/a/TG4Fr', 'https://imgur.com/a/diy-nato-watch-strap-TG4Fr', 'https://imgur.com/gallery/TG4Fr', 'https://www.imgur.com/a/TG4Fr']:
        c = cands(u)
        allu = c['tile'] + c['full'] + c['chain']
        check('%s: no i.imgur.com/<album id>.jpg anywhere (tile, full screen, link check)' % u, not any('i.imgur.com/TG4Fr' in x for x in allu))
        check('%s: Reddit\'s own preview still comes first on the tile' % u, c['tile'][:1] == ['https://b.thumbs.redditmedia.com/abc.jpg'])
    for u in ['http://imgur.com/AbCdEfG', 'https://www.imgur.com/AbCdEfG', 'https://i.imgur.com/AbCdEfG.png']:
        c = cands(u)
        check('%s: a single-image link still offers i.imgur.com/AbCdEfG.jpg' % u, 'https://i.imgur.com/AbCdEfG.jpg' in c['tile'] and 'https://i.imgur.com/AbCdEfG.jpg' in c['full'])
    ico = lambda: ev("document.getElementById('favicon').getAttribute('href')")
    check('the tab icon is the Lemondrop mark by default', '%23f7e01b' in ico())
    ev("document.querySelector('#theme [data-skin=legacy]').click()"); pg.wait_for_timeout(100)
    check('Legacy brings its own tab icon back', '%23f7e01b' not in ico() and ico().startswith('data:image/svg+xml'))
    pg.reload(); pg.wait_for_timeout(500)
    check('and keeps it after a reload', '%23f7e01b' not in ico())
    ev("document.querySelector('#theme [data-skin=lemondrop]').click()"); pg.wait_for_timeout(100)
    check('switching back shows the Lemondrop mark again', '%23f7e01b' in ico())
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
