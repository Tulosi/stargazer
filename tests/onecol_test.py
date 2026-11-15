"""Tablets (iPad portrait): Tile size reaches one tile across. At iPad widths 360px tiles still fit two across, so the slider gets one
more stop at its right end (labelled 1) that makes the masonry one column; that tile is no taller than the window, the choice is
remembered, a wider window (landscape) shows 360 without forgetting it, and Full width can also go to 1 across there. Wide desktops keep
the old 150-360 range. Run: python tests/onecol_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
SET = "v=>{ $('size').value=v; $('size').dispatchEvent(new Event('input',{bubbles:true})); }"
TALL = """(()=>{ const room = innerHeight - document.querySelector('.deck').offsetHeight;
  return {room, tallest: Math.max(...[...document.querySelectorAll('#grid .card')].map(c=>c.getBoundingClientRect().height))}; })()"""
def page(b, w, h, touch=True):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1200)
    return ctx, pg, errs
with sync_playwright() as p:
    b = p.chromium.launch()
    for (w, h) in ((744, 1133), (820, 1180), (834, 1194), (1024, 1366)):   # iPad mini, iPad Air, iPad Pro 11, iPad Pro 13 (portrait)
        ctx, pg, errs = page(b, w, h)
        check('%dpx: slider goes past 360 to a one-across stop, labelled 1' % w, pg.evaluate("$('size').max") == '370' and pg.evaluate("document.querySelector('#sizerow .notches i').textContent") == '1')
        pg.evaluate("(%s)(360)" % SET); pg.wait_for_timeout(250)
        c360 = pg.evaluate("cols")
        check('%dpx: 360 still gives 2 or more columns (%s)' % (w, c360), c360 >= 2 or w < 800)
        pg.evaluate("(%s)(370)" % SET); pg.wait_for_timeout(250)
        check('%dpx: the end stop gives one column' % w, pg.evaluate("cols") == 1 and pg.evaluate("getComputedStyle($('grid')).gridTemplateColumns.split(' ').length") == 1)
        check('%dpx: notch lit and title says 1 across' % w, pg.evaluate("document.querySelector('#sizerow .notches i').classList.contains('on') && $('size').title=='1 across'"))
        t = pg.evaluate(TALL)
        check('%dpx: no tile taller than the window (%s)' % (w, t), t['tallest'] <= t['room'])
        check('%dpx: no page errors' % w, not errs)
        ctx.close()
    ctx, pg, errs = page(b, 820, 1180)
    pg.evaluate("(%s)(370)" % SET); pg.wait_for_timeout(250)
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered on the next visit', pg.evaluate("cols") == 1 and pg.evaluate("$('size').value") == '370')
    pg.set_viewport_size({'width': 1180, 'height': 820}); pg.wait_for_timeout(700)
    check('landscape: back to the normal range, shown at 360, several columns', pg.evaluate("$('size').max") == '360' and pg.evaluate("$('size').value") == '360' and pg.evaluate("cols") >= 3)
    check('landscape: the one-across choice is not forgotten', pg.evaluate("localStorage.getItem('saved-posts-tile')") == '370')
    pg.set_viewport_size({'width': 820, 'height': 1180}); pg.wait_for_timeout(700)
    check('portrait again: one across again', pg.evaluate("cols") == 1)
    pg.evaluate("(%s)(250)" % SET); pg.wait_for_timeout(250)
    check('moving off the stop: several columns, notch unlit, no height cap', pg.evaluate("cols") >= 2 and not pg.evaluate("document.querySelector('#sizerow .notches i').classList.contains('on')") and pg.evaluate("MAXROWS") == 0)
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    mx = int(pg.evaluate("$('size').max"))
    pg.evaluate("(%s)(%d)" % (SET, mx)); pg.wait_for_timeout(300)
    check('Full width on a tablet also reaches 1 across', pg.evaluate("cols") == 1 and pg.evaluate("$('size').title") == '1 across')
    check('no page errors', not errs); ctx.close()
    ctx, pg, errs = page(b, 1440, 900, touch=False)
    check('1440px desktop: unchanged 150-360 range, no end stop', pg.evaluate("$('size').max") == '360' and pg.evaluate("document.querySelectorAll('#sizerow .notches i').length") == 0)
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    mx = int(pg.evaluate("$('size').max")); pg.evaluate("(%s)(%d)" % (SET, mx)); pg.wait_for_timeout(300)
    check('1440px Full width: still stops at 2 across', pg.evaluate("cols") == 2)
    ctx.close(); b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
