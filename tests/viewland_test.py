"""Leaving full screen after moving on through posts brings the feed to the card of the last post shown (phone and desktop). Run: python tests/viewland_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp, touch in [('phone', {'width': 390, 'height': 844}, True), ('desktop', {'width': 1200, 'height': 800}, False)]:
        ctx = b.new_context(viewport=vp, has_touch=touch, is_mobile=touch); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
        pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1200)
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
        pg.evaluate("openViewer(list[0])"); pg.wait_for_timeout(400)
        for _ in range(8): pg.evaluate("viewerPost(1)"); pg.wait_for_timeout(150)
        target = pg.evaluate("VIEW.cur.id")
        pg.evaluate("closeViewer()"); pg.wait_for_timeout(700)
        r = pg.evaluate("(id=>{ const c=cardEls.get(id).getBoundingClientRect(); return {top:c.top, bottom:c.bottom, h:innerHeight, active: document.activeElement && document.activeElement.closest('.card') && document.activeElement.closest('.card').dataset.id}; })", target)
        check('%s: the last post shown is on screen after leaving full screen (%s)' % (name, r), r['bottom'] > 0 and r['top'] < r['h'])
        check('%s: its card takes focus' % name, r['active'] == target)
        if touch: check('phone: it is the card in focus for autoplay', pg.evaluate("(id=>pinned && pinned.dataset.id===id)", target))
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
        pg.evaluate("openViewer(list[0])"); pg.wait_for_timeout(300); pg.evaluate("closeViewer()"); pg.wait_for_timeout(600)
        check('%s: closing without moving on leaves the page where it was' % name, pg.evaluate("scrollY") < 5)
        check('%s: no page errors' % name, not errs)
        ctx.close()
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
