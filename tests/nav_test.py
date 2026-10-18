"""Navigation: labelled buttons + inline search on wide screens; bottom bar + bottom sheets on phones; outside tap closes a panel. Run: python tests/nav_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    d = b.new_page(viewport={'width': 1100, 'height': 600}); d.on('pageerror', lambda e: errs.append(str(e)))
    d.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    d.goto(PAGE); d.wait_for_timeout(800)
    check('desktop: search box is always visible', d.is_visible('#q'))
    check('desktop: search button is not needed', not d.is_visible('#searchbtn'))
    check('desktop: Source, Filters and Shuffle show text labels', all(d.is_visible('#%s .nl' % i) for i in ('srctoggle', 'decktoggle', 'shufflebtn')))
    m = b.new_context(viewport={'width': 400, 'height': 700}, has_touch=True, is_mobile=True).new_page(); m.on('pageerror', lambda e: errs.append(str(e)))
    m.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    m.goto(PAGE); m.wait_for_timeout(800); ev = m.evaluate
    r = ev("(()=>{ const n=document.getElementById('navbtns').getBoundingClientRect(); return [n.bottom, innerHeight, getComputedStyle(document.getElementById('navbtns')).position]; })()")
    check('phone: nav is a bar fixed to the bottom of the screen', r[2] == 'fixed' and abs(r[0] - r[1]) < 2)
    check('phone: nav buttons are 40px circles', all(ev("(()=>{ const r=document.getElementById('%s').getBoundingClientRect(); return Math.round(r.width)===40 && Math.round(r.height)===40; })()" % i) for i in ('srctoggle', 'decktoggle', 'shufflebtn', 'searchbtn')))
    m.click('#decktoggle'); m.wait_for_timeout(300)
    r = ev("(()=>{ const a=document.getElementById('panel').getBoundingClientRect(), n=document.getElementById('navbtns').getBoundingClientRect(); return [a.bottom, n.top, getComputedStyle(document.getElementById('panel')).position]; })()")
    check('phone: Filters opens as a sheet just above the bar', r[2] == 'fixed' and r[0] <= r[1] + 1)
    m.mouse.click(200, 70); m.wait_for_timeout(300)
    check('tapping outside closes the sheet', ev("document.body.classList.contains('deck-collapsed')"))
    m.click('#searchbtn'); m.wait_for_timeout(300)
    r = ev("(()=>{ const s=document.getElementById('searchbox').getBoundingClientRect(), n=document.getElementById('navbtns').getBoundingClientRect(); return [s.bottom, n.top]; })()")
    check('phone: search field docks above the bar', r[0] <= r[1])
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
