"""Full width button beside Tile size: lifts the 1760px page cap and makes the tiles bigger (Tile size then runs from 150px up to one tile
across the window, default 3 across, its value kept apart from the normal one), the top bar widens with it, it is remembered, layout
stays cheap (no per-card layout reads), the normal tile size comes back when it is turned off, and on phones the button is hidden. Run: python tests/fullw_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
INFO = """(()=>{ const g=$('grid').getBoundingClientRect(), c=document.querySelector('#grid .card').getBoundingClientRect();
  return {grid: Math.round(g.width), deck: Math.round(document.querySelector('.deck-in').getBoundingClientRect().width), cols, tile: Math.round(c.width),
          pressed: $('fullw').getAttribute('aria-pressed'), dis: $('size').disabled}; })()"""
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 2560, 'height': 1200}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1200)
    off = pg.evaluate(INFO)
    check('off: page capped at 1760px (%s)' % off, off['grid'] <= 1760 and off['pressed'] == 'false')
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(600)
    on = pg.evaluate(INFO)
    check('on: tiles span the browser width (%s)' % on, on['grid'] >= 2560 - 40 and on['deck'] >= 2560 - 2)
    check('on: tiles get bigger, 3 across by default', on['cols'] == 3 and on['tile'] > 2 * off['tile'])
    mx = pg.evaluate("+$('size').max")
    check('on: slider still works and now runs up to one tile across (max %s)' % mx, not on['dis'] and on['pressed'] == 'true' and mx >= on['grid'] - 10)
    pg.evaluate("$('size').value=$('size').max; $('size').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(500)
    check('on: slider at the top gives one tile across', pg.evaluate("cols") == 1)
    pg.evaluate("$('size').value=300; $('size').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(500)
    check('on: scrubbing down gives smaller tiles (%s cols)' % pg.evaluate("cols"), pg.evaluate("cols") > 6)
    src = pg.evaluate("layoutCard.toString()")
    check('layout reads no per-card layout values (no forced reflow per card)', 'offsetHeight' not in src and 'getBoundingClientRect' not in src and 'fullwRows' not in src)
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered on the next visit, with its own tile size', pg.evaluate("FULLW && document.body.classList.contains('fullw')") and pg.evaluate(INFO)['grid'] >= 2520 and pg.evaluate("$('size').value") == '300')
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    back = pg.evaluate(INFO)
    check('off again: back under the cap with the earlier tile size (%s)' % back, back['grid'] <= 1760 and back['cols'] == off['cols'] and pg.evaluate("$('size').max") == '360')
    check('desktop: no page errors', not errs); ctx.close()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = ctx.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500)
    check('phone: button hidden (the page is already full width)', pg.evaluate("getComputedStyle($('fullw')).display") == 'none')
    ctx.close()
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1000)
    c0 = pg.evaluate("cols"); pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    check('1440px laptop: button shown and tiles get bigger (%s -> %s cols)' % (c0, pg.evaluate("cols")), pg.evaluate("getComputedStyle($('fullw')).display") != 'none' and pg.evaluate("cols") == 3 < c0)
    ctx.close(); b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
