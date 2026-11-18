"""Tile size snaps to numbered steps, each a count of tiles across (Masonry and Grid), most tiles on the left and 1 across on the right everywhere: phones get 3 / 2 / 1, tablets and desktops get
from as many 150px tiles as fit down to 1 across, with more steps on wider windows (at most 5, 10 in Full width). The slider
cannot rest between steps, every step gives the column count on its label, one across is no taller than the window, the choice is
remembered, an old pixel setting carries over, and a different window width snaps to the nearest step. Run: python tests/tilesize_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
SET = "v=>{ $('size').value=v; $('size').dispatchEvent(new Event('input',{bubbles:true})); }"
LABELS = "[...document.querySelectorAll('#sizerow .notches i')].map(t=>+t.textContent)"
COLS = "getComputedStyle($('grid')).gridTemplateColumns.split(' ').length"
TALL = """(()=>{ const room = innerHeight - document.querySelector('.deck').offsetHeight;
  return {room, tallest: Math.max(...[...document.querySelectorAll('#grid .card')].map(c=>c.getBoundingClientRect().height))}; })()"""
def page(b, w, h, touch=False, init=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch and w <= 720); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    if init: pg.add_init_script(init)
    pg.goto(PAGE); pg.wait_for_timeout(500); pg.evaluate("openSample()"); pg.wait_for_timeout(1000)
    return ctx, pg, errs
with sync_playwright() as p:
    b = p.chromium.launch()
    counts = {}
    for (w, h, touch) in ((820, 1180, True), (1024, 768, False), (1440, 900, False), (1920, 1080, False)):
        ctx, pg, errs = page(b, w, h, touch)
        for lay in ('masonry', 'grid'):
            pg.evaluate("l=>document.querySelector('#layoutseg [data-l=\"'+l+'\"], [data-layout=\"'+l+'\"]')?.click()", lay); pg.wait_for_timeout(200)
            labels = pg.evaluate(LABELS); counts[w] = len(labels)
            sl = pg.evaluate("({min:$('size').min, max:$('size').max, step:$('size').step})")
            check('%dpx %s: one numbered notch per slider position, whole steps only (%s)' % (w, lay, labels), sl['min'] == '0' and sl['step'] == '1' and int(sl['max']) == len(labels) - 1)
            fit = pg.evaluate("Math.floor(($('grid').clientWidth + 6)/156)")
            check('%dpx %s: every count from min(fit, 5) down to 1 (%s)' % (w, lay, labels), labels == list(range(min(fit, 5), 0, -1)))
            seen = []
            for i in range(len(labels)):
                pg.evaluate("(%s)(%d)" % (SET, i)); pg.wait_for_timeout(120); seen.append(pg.evaluate(COLS))
            check('%dpx %s: each step gives the column count on its label (%s)' % (w, lay, seen), seen == labels)
            check('%dpx %s: the chosen notch is lit and the slider says it' % (w, lay), pg.evaluate("document.querySelector('#sizerow .notches i.on').textContent") == '1' and pg.evaluate("$('size').getAttribute('aria-valuetext')") == '1 across')
            t = pg.evaluate(TALL)
            check('%dpx %s: at 1 across no tile is taller than the window (%s)' % (w, lay, t), t['tallest'] <= t['room'])
        pg.evaluate("(%s)(1)" % SET); pg.wait_for_timeout(150)
        check('%dpx: a value between steps cannot be set' % w, pg.evaluate("($('size').value='1.5', $('size').value)") in ('1', '2'))
        check('%dpx: no page errors' % w, not errs); ctx.close()
    check('wider windows never get fewer steps, and never more than 5 (%s)' % counts, counts[820] <= counts[1024] <= counts[1440] <= counts[1920] == 5)
    # remembered, and snaps to the nearest step on another width
    ctx, pg, errs = page(b, 1440, 900)
    labels = pg.evaluate(LABELS); i = labels.index(3)
    pg.evaluate("(%s)(%d)" % (SET, i)); pg.wait_for_timeout(150)
    check('stored as a column count', pg.evaluate("localStorage.getItem('saved-posts-tile-cols')") == '3')
    pg.reload(); pg.wait_for_timeout(1200)
    check('remembered on the next visit', pg.evaluate(COLS) == 3 and pg.evaluate("document.querySelector('#sizerow .notches i.on').textContent") == '3')
    pg.set_viewport_size({'width': 1000, 'height': 900}); pg.wait_for_timeout(700)
    check('a narrower window keeps 3 across', pg.evaluate(COLS) == 3)
    check('no page errors', not errs); ctx.close()
    ctx, pg, errs = page(b, 1440, 900, init="try{ if(!sessionStorage.getItem('x')){ localStorage.setItem('saved-posts-tile','370'); sessionStorage.setItem('x','1'); } }catch(e){}")
    check('an old one-across setting (370) carries over', pg.evaluate(COLS) == 1)
    ctx.close()
    ctx, pg, errs = page(b, 390, 844, True, init="try{ if(!sessionStorage.getItem('x')){ localStorage.setItem('saved-posts-tile-phone','2'); sessionStorage.setItem('x','1'); } }catch(e){}")
    check('phone: an old step setting (index 2 = 3 across) carries over', pg.evaluate(COLS) == 3)
    ctx.close()
    # phones: 3 / 2 / 1 across
    ctx, pg, errs = page(b, 390, 844, True)
    check('phone: three notches 3, 2, 1, in the same order as desktop', pg.evaluate(LABELS) == [3, 2, 1])
    check('phone: starts with one column, at the right end', pg.evaluate(COLS) == 1 and pg.evaluate("$('size').value") == '2')
    for i, want in ((1, 2), (0, 3), (2, 1)):
        pg.evaluate("(%s)(%d)" % (SET, i)); pg.wait_for_timeout(150)
        check('phone: step %d gives %d column(s)' % (i, want), pg.evaluate(COLS) == want)
    pg.evaluate("(%s)(1)" % SET); pg.wait_for_timeout(150); pg.reload(); pg.wait_for_timeout(1000)
    check('phone: remembered (2 across)', pg.evaluate(COLS) == 2)
    check('phone: one across is not height-capped', pg.evaluate("((%s)(2), MAXROWS)" % SET) == 0)
    check('phone: tile size row is visible', pg.evaluate("(()=>{ $('decktoggle').click(); return !!$('sizerow').offsetParent; })()"))
    check('phone: no page errors', not errs); ctx.close()
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
