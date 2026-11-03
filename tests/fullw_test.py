"""Full width button beside Tile size: lifts the 1760px page cap so Masonry / Grid tiles fill the whole browser window (more columns at the
same tile size; the slider keeps working), the top bar widens with it, it is remembered, layout stays cheap (no per-card layout reads),
and on phones (always full width) the button is hidden. Run: python tests/fullw_test.py"""
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
    check('on: still a multi-column tiling with more columns, tile size about the same', on['cols'] > off['cols'] > 1 and abs(on['tile'] - off['tile']) < 0.35 * off['tile'])
    check('on: slider still works', not on['dis'] and on['pressed'] == 'true')
    pg.evaluate("$('size').value=150; $('size').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(500)
    check('on: smaller tile size gives more columns (%s)' % pg.evaluate("cols"), pg.evaluate("cols") > on['cols'])
    src = pg.evaluate("layoutCard.toString()")
    check('layout reads no per-card layout values (no forced reflow per card)', 'offsetHeight' not in src and 'getBoundingClientRect' not in src and 'fullwRows' not in src)
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered on the next visit', pg.evaluate("FULLW && document.body.classList.contains('fullw')") and pg.evaluate(INFO)['grid'] >= 2520)
    pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
    check('off again: back under the cap', pg.evaluate(INFO)['grid'] <= 1760)
    check('desktop: no page errors', not errs); ctx.close()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = ctx.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500)
    check('phone: button hidden (the page is already full width)', not pg.is_visible('#fullw'))
    ctx.close()
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(500)
    check('1440px laptop: button hidden (the page already fills the window)', not pg.is_visible('#fullw'))
    ctx.close(); b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
