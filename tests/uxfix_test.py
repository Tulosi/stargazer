"""First-run sample list, one tab stop per card, phone Filters order, one stat on phones, no handle on every desktop tile. Run: python tests/uxfix_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') or r.request.url.startswith('data:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(900); ev = pg.evaluate
    check('first run offers sample posts next to Open CSV', ev("!!document.getElementById('introSample')") and 'Nothing loaded yet' in ev("document.querySelector('.nodata').textContent"))
    pg.click('#introSample'); pg.wait_for_timeout(2500)
    check('sample opens 12 invented posts', ev("POSTS.length")==12 and ev("document.querySelectorAll('.card').length")==12)
    check('sample pictures draw (data art)', ev("[...document.querySelectorAll('.card img')].filter(i=>i.naturalWidth>0).length")>=6)
    check('two sample posts are starred', ev("FAVS.size")==2)
    check('sample has no backup or pull warnings', ev("document.getElementById('expHint').hidden") and ev("document.getElementById('pullLine').hidden"))
    check('one h1 for screen readers', ev("document.querySelectorAll('h1').length")==1)
    check('no handle on every tile with a mouse in hover mode', ev("getComputedStyle(document.querySelector('.card .lhandle')).display")=='none')
    check('the card button reads Open post', ev("document.querySelector('.card .actions .btn.primary').textContent.trim()")=='Open post')
    check('thumb label says it shows controls', ev("document.querySelector('.card a.thumb').getAttribute('aria-label')").startswith('Show details and controls'))
    # one tab stop per card
    ev("document.querySelectorAll('.card')[0].querySelector('a.thumb').focus()")
    pg.keyboard.press('Tab')
    check('Tab goes from one card to the next', ev("document.activeElement===document.querySelectorAll('.card')[1].querySelector('a.thumb')"))
    ev("document.querySelectorAll('.card')[1].querySelector('a.thumb').focus()")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check('Enter moves into the card controls', ev("document.activeElement.closest('.actions,.lay-cap')!==null") and ev("document.activeElement.closest('.card')===document.querySelectorAll('.card')[1]"))
    pg.keyboard.press('Tab'); pg.keyboard.press('Tab'); pg.wait_for_timeout(100)
    check('Tab walks the controls inside the card', ev("document.activeElement.closest('.card')===document.querySelectorAll('.card')[1]"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('Esc returns to the picture and re-tucks the controls', ev("document.activeElement===document.querySelectorAll('.card')[1].querySelector('a.thumb')") and ev("document.querySelectorAll('.card')[1].querySelector('.actions .btn').getAttribute('tabindex')")=='-1')
    ev("document.querySelector('#layoutseg [data-l=list]').click()"); pg.wait_for_timeout(300)
    check('List keeps its controls tabbable', ev("document.querySelector('.card .actions .btn').getAttribute('tabindex')") is None and ev("document.querySelector('.card a.thumb').getAttribute('aria-label')").startswith('Open: '))
    ctx.close()
    # phone
    ctx = b.new_context(viewport={'width': 390, 'height': 780}, is_mobile=True, has_touch=True, device_scale_factor=2); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') or r.request.url.startswith('data:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(900); ev = pg.evaluate
    pg.click('#introSample'); pg.wait_for_timeout(2500)
    check('phone shows one stat when nothing is filtered', ev("[...document.querySelectorAll('#stats .st')].filter(e=>e.offsetParent!==null).length")==1 and ev("document.querySelector('#stats .st .lb').textContent")=='Posts')
    ev("document.getElementById('decktoggle').click()"); pg.wait_for_timeout(500)
    check('phone Filters opens on Filter and sort', ev("document.getElementById('sort').getBoundingClientRect().top < document.getElementById('layoutseg').getBoundingClientRect().top"))
    ev("document.getElementById('decktoggle').click()")
    ev("""()=>{ const s=document.getElementById('sort'); s.value='saved'; s.dispatchEvent(new Event('change')); }""")
    pg.wait_for_timeout(300)
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
