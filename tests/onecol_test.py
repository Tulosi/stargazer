"""Tablets (iPad portrait and landscape): Tile size snaps to numbered column counts and always reaches 1 across (the last notch); that tile
is no taller than the window, the choice is remembered and survives rotating, and Full width can also go to 1 across. Run: python tests/onecol_test.py"""
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
    for (w, h) in ((744, 1133), (820, 1180), (834, 1194), (1024, 1366), (1366, 1024)):   # iPad mini, Air, Pro 11, Pro 13 portrait, Pro 13 landscape
        ctx, pg, errs = page(b, w, h)
        mx = int(pg.evaluate("$('size').max"))
        check('%dpx: first notch is 1' % w, pg.evaluate("document.querySelector('#sizerow .notches i').textContent") == '1')
        pg.evaluate("(%s)(%d)" % (SET, 0)); pg.wait_for_timeout(250)
        check('%dpx: the end stop gives one column' % w, pg.evaluate("cols") == 1 and pg.evaluate("getComputedStyle($('grid')).gridTemplateColumns.split(' ').length") == 1)
        check('%dpx: notch lit and title says 1 across' % w, pg.evaluate("document.querySelector('#sizerow .notches i:first-child').classList.contains('on') && $('size').title=='1 across'"))
        t = pg.evaluate(TALL)
        check('%dpx: no tile taller than the window (%s)' % (w, t), t['tallest'] <= t['room'])
        pg.evaluate("(%s)(%d)" % (SET, 1)); pg.wait_for_timeout(250)
        check('%dpx: one step back gives 2 across and no height cap' % w, pg.evaluate("cols") == 2 and pg.evaluate("MAXROWS") == 0)
        check('%dpx: no page errors' % w, not errs); ctx.close()
    ctx, pg, errs = page(b, 820, 1180)
    pg.evaluate("(%s)(0)" % SET); pg.wait_for_timeout(250)
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered on the next visit', pg.evaluate("cols") == 1)
    pg.set_viewport_size({'width': 1180, 'height': 820}); pg.wait_for_timeout(700)
    check('landscape: still one across', pg.evaluate("cols") == 1)
    pg.set_viewport_size({'width': 820, 'height': 1180}); pg.wait_for_timeout(700)
    check('portrait again: one across', pg.evaluate("cols") == 1)
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    pg.evaluate("(%s)(0)" % SET); pg.wait_for_timeout(300)
    check('Full width on a tablet also reaches 1 across', pg.evaluate("cols") == 1 and pg.evaluate("$('size').title") == '1 across')
    check('no page errors', not errs); ctx.close()
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
