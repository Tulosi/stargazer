"""Full width button beside Tile size: one post at a time across the feed, no tile taller than the window, slider set aside and its value kept,
remembered across visits, works on phones too. Run: python tests/fullw_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp, touch in [('desktop', {'width': 1280, 'height': 800}, False), ('phone', {'width': 390, 'height': 844}, True)]:
        ctx = b.new_context(viewport=vp, has_touch=touch, is_mobile=touch); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
        pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1200)
        cols0 = pg.evaluate("cols"); size0 = pg.evaluate("$('size').value")
        pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
        info = pg.evaluate("""(()=>{ const g=$('grid').getBoundingClientRect().width, cs=[...document.querySelectorAll('#grid .card')].map(c=>c.getBoundingClientRect());
          const deck=document.querySelector('.deck').offsetHeight; return {cols, wide: cs.every(r=>Math.abs(r.width-g)<2), tallest: Math.max(...cs.map(r=>r.height)), room: innerHeight-deck, dis: $('size').disabled, pressed: $('fullw').getAttribute('aria-pressed')}; })()""")
        check('%s: one post across the whole feed (%s)' % (name, info), info['cols'] == 1 and info['wide'])
        check('%s: no tile is taller than the window below the top bar' % name, info['tallest'] <= info['room'])
        check('%s: the slider is set aside, the button shows it is on' % name, info['dis'] and info['pressed'] == 'true')
        pg.reload(); pg.wait_for_timeout(1500)
        check('%s: remembered on the next visit' % name, pg.evaluate("FULLW && cols===1 && document.body.classList.contains('fullw')"))
        pg.evaluate("$('fullw').click()"); pg.wait_for_timeout(500)
        check('%s: off again gives the earlier tile size back (%s cols, slider %s)' % (name, pg.evaluate("cols"), pg.evaluate("$('size').value")), pg.evaluate("cols") == cols0 and pg.evaluate("$('size').value") == size0 and not pg.evaluate("$('size').disabled"))
        check('%s: no page errors' % name, not errs)
        ctx.close()
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
