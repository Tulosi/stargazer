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
        pg.evaluate("""(()=>{ const p=list[1], m=META[p.id]; m.th='https://i.redd.it/deadpic1.png'; m.u='https://i.redd.it/deadpic1.png'; m.m='image'; delete m.gl;
          const c=cardEls.get(p.id); c.querySelectorAll('.thumb img').forEach(i=>i.remove()); openViewer(list[0]); })()"""); pg.wait_for_timeout(500)
        pg.evaluate("viewerPost(1)"); pg.wait_for_timeout(4000)
        check('%s: a post that will not load is skipped, full screen stays open (%s)' % (name, pg.evaluate("list.indexOf(VIEW.cur)")), pg.evaluate("!VIEW.root.hidden && list.indexOf(VIEW.cur)===2"))
        pg.evaluate("closeViewer()"); pg.wait_for_timeout(300)
        pg.evaluate("openViewer(list[1])"); pg.wait_for_timeout(4000)
        check('%s: opened directly, it stays in full screen and says so' % name, pg.evaluate("!VIEW.root.hidden && /Nothing to show/.test(VIEW.stage.textContent)"))
        pg.evaluate("closeViewer()"); pg.wait_for_timeout(300)
        check('%s: no page errors' % name, not errs)
        ctx.close()
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
