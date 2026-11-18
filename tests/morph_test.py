"""Tile <-> full screen morph and velocity-matched swipes (Nov 2026 audit, items 10 and 11). A tap on a tile flies its picture to full
screen and closing flies it back; a flick between posts leaves at the finger's speed, a short drag springs back with a small overshoot.
Run: python tests/morph_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    for rm in ('no-preference', 'reduce'):
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, reduced_motion=rm); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
        pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
        ev("openSample()"); pg.wait_for_timeout(1000)
        pg.tap('#grid .card:nth-child(2) a.thumb'); pg.wait_for_timeout(100)
        g = ev("(()=>{ const g=document.querySelector('#viewer img.vmorph'); if(!g) return null; const r=g.getBoundingClientRect(), t=document.querySelector('#grid .card:nth-child(2) .thumb').getBoundingClientRect(); return {w:r.width, tw:t.width, fit:getComputedStyle(g).objectFit}; })()")
        if rm == 'reduce':
            check('reduced motion: no flight', g is None)
            ctx.close(); continue
        check('opening from a tile flies its picture (cover, mid-flight) %s' % g, g is not None and g['fit'] == 'cover')
        pg.wait_for_timeout(500)
        check('it lands and goes, and the real stage shows', ev("!document.querySelector('img.vmorph')") and ev("getComputedStyle(VIEW.stage).opacity") == '1')
        ev("closeViewer()"); pg.wait_for_timeout(120)
        check('closing on the same post flies it back to its tile', ev("!!document.querySelector('img.vmorph.back')") and ev("document.querySelector('#grid .card:nth-child(2) .thumb').style.visibility") == 'hidden')
        pg.wait_for_timeout(700)
        check('and the tile is shown again', ev("!document.querySelector('img.vmorph,.vmorphbg')") and ev("document.querySelector('#grid .card:nth-child(2) .thumb').style.visibility") == '')
        ev("openViewer(list[1])"); pg.wait_for_timeout(300)
        check('openViewer without a tile does not fly', ev("!document.querySelector('img.vmorph')"))
        # a fast flick leaves at the finger's speed
        dur = ev("""()=>new Promise(res=>{ dragFollow(0,-20); setTimeout(()=>{ dragFollow(0,-80); setTimeout(()=>{ dragEnd(0,-80,40); res(VIEW.stage.style.transition); }, 5); }, 16); })""")
        check('a fast flick leaves on a curve that starts at the finger speed, a little quicker (%s)' % dur, 'ms' in dur and int(dur.split('ms')[0].split()[-1]) < 320 and '0.72' not in dur)
        pg.wait_for_timeout(600)
        ev("dragFollow(0,-30)")
        ret = ev("(dragEnd(0,-30,600), VIEW.stage.style.transition)")
        check('a short slow drag springs back with an overshoot curve (%s)' % ret, '1.36' in ret)
        check('no page errors', not errs)
        ctx.close()
    b.close()
raise SystemExit(1 if bad else 0)
