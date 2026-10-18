"""Dead pictures alone should not trigger the 'Image servers are pushing back' pause; a wall of failures with nothing loading should. Run: python tests/imgpause_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("for(let i=0;i<8;i++) noteImgOK(); for(let i=0;i<12;i++) noteImgFail('https://i.redd.it/x'+i)")
    check('12 failures among 8 successes: no pause', ev("IMGQ.until") <= ev("Date.now()"))
    ev("IMGQ.okT = []; IMGQ.fails = []; for(let i=0;i<12;i++) noteImgFail('https://i.redd.it/y'+i)")
    check('12 failures with nothing loading: pause', ev("IMGQ.until") > ev("Date.now()"))
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
