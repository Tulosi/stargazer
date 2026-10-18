"""Filters and Source are separate panels. Run: python tests/panels_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 800}, has_touch=True); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1000); ev = pg.evaluate
    vis = lambda sel: pg.is_visible(sel)
    check('both closed at start', not vis('#panel') and not vis('#srcpanel'))
    check('source controls live in the Source panel only', ev("!!$('srcpanel').querySelector('#srcCsv') && !!$('srcpanel').querySelector('#csvTools') && !$('panel').querySelector('#srcCsv') && !$('panel').querySelector('#csvTools')"))
    check('filters stay in the Filters panel', ev("!!$('panel').querySelector('#catChips') && !!$('panel').querySelector('#sort') && !$('srcpanel').querySelector('#catChips')"))
    pg.tap('#srctoggle'); check('Source opens', vis('#srcpanel') and not vis('#panel') and ev("$('srctoggle').getAttribute('aria-expanded')") == 'true')
    pg.tap('#decktoggle'); check('Filters replaces Source', vis('#panel') and not vis('#srcpanel'))
    pg.tap('#decktoggle'); check('Filters closes', not vis('#panel'))
    pg.tap('#srctoggle'); pg.tap('#srcSub'); pg.tap('#srcCsv'); check('swap back to Saved CSV works', ev("!$('csvTools').hidden") and vis('#csvOpen'))
    pg.keyboard.press('Escape'); check('Escape closes Source', not vis('#srcpanel'))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
