"""Account panel is first; Local and Account lists are told apart. Run: python tests/lists_test.py (Supabase mocked)"""
import os, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    H = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*'}
    def route(r):
        u = r.request.url
        if u.startswith('file:'): return r.continue_()
        if r.request.method == 'OPTIONS': return r.fulfill(status=204, headers=H)
        if '/auth/v1/user' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps({'id': 'u1', 'email': 'a@b.c'}), headers=H)
        if '/rest/v1/' in u: return r.fulfill(status=200, content_type='application/json', body='[]', headers=H)
        return r.abort()
    pg.route('**/*', route); ev = pg.evaluate
    pg.goto(PAGE); pg.wait_for_timeout(1200); pg.click('#srctoggle')
    top = lambda sel: ev("document.querySelector('%s').getBoundingClientRect().top" % sel)
    check('Source switch and list tools come first; the optional Account block follows', top('#srcCsv') < top('#csvTools') < top('#acct'))
    check('Account heading present', ev("document.querySelector('#acct h2').textContent") == 'Account')
    check('signed out: list is Local, no sync button', ev("$('csvKind').dataset.k") == 'local' and 'Local list' in ev("$('csvKind').textContent") and not pg.is_visible('#csvCloud'))
    check('selector labels the list as Local', ev("$('csvSel').options[0].textContent") in ('No source loaded',) or ev("$('csvSel').options[0].textContent").startswith('Local'))
    # sign in with a reset-style session so no password is needed
    pg.goto('about:blank'); pg.goto(PAGE + '#access_token=AAA.BBB.CCC&refresh_token=R&expires_in=3600&type=recovery'); pg.wait_for_timeout(1500)
    pg.click('#acSkipPw'); pg.wait_for_timeout(1200)
    check('after sign-in the current list is an Account list', ev("$('csvKind').dataset.k") == 'account' and 'Account list' in ev("$('csvKind').textContent") and ev("$('csvSel').options[0].textContent").startswith('Account'))
    check('button offers Stop syncing', pg.is_visible('#csvCloud') and pg.inner_text('#csvCloud') == 'Stop syncing')
    pg.click('#csvCloud'); pg.click('#cOk'); pg.wait_for_timeout(600)
    check('Stop syncing makes it Local again', ev("$('csvKind').dataset.k") == 'local' and pg.inner_text('#csvCloud') == 'Sync with account' and ev("$('csvSel').options[0].textContent") in ('No source loaded',) or ev("$('csvSel').options[0].textContent").startswith('Local'))
    pg.click('#csvCloud'); pg.click('#cOk'); pg.wait_for_timeout(1200)
    check('Sync with account makes it an Account list', ev("$('csvKind').dataset.k") == 'account' and pg.inner_text('#csvCloud') == 'Stop syncing')
    pg.click('#csvCloud'); pg.click('#cCancel') if False else pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('cancelling the dialog changes nothing', ev("$('csvKind').dataset.k") == 'account')
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
