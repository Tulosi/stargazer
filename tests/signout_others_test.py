"""'Sign out other devices' calls logout with scope=others and keeps this device signed in. Run: python tests/signout_others_test.py (network mocked)"""
import os, json, time
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
now = int(time.time())
SESSION = {'access_token': 't', 'refresh_token': 'r', 'expires_at': now + 7200, 'uid': 'u1', 'email': 'a@b.c'}
calls = []; fail = [False]
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    if '/auth/v1/logout' in u:
        calls.append(u)
        return r.fulfill(status=500 if fail[0] else 204, content_type='application/json', body='{"msg":"boom"}' if fail[0] else '')
    if '/rest/v1/' in u: return r.fulfill(status=200, content_type='application/json', body='[]')
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 800}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
    pg.add_init_script("try{ localStorage.setItem('saved-posts-session', %s); }catch(e){}" % json.dumps(json.dumps(SESSION)))
    pg.goto(PAGE); pg.wait_for_timeout(1200); ev = pg.evaluate
    pg.click('#srctoggle'); pg.wait_for_timeout(200)
    check('button visible when signed in', pg.is_visible('#acOthers'))
    pg.click('#acOthers'); pg.wait_for_timeout(300); pg.click('#confirm button[value=cancel]'); pg.wait_for_timeout(200)
    check('cancel makes no request', not calls)
    pg.click('#acOthers'); pg.wait_for_timeout(300); pg.click('#cOk'); pg.wait_for_timeout(600)
    check('logout called with scope=others', len(calls) == 1 and 'scope=others' in calls[0])
    check('this device stays signed in', ev("!!SESSION"))
    check('message confirms', 'signed out' in ev("$('acMsg').textContent"))
    fail[0] = True
    pg.click('#acOthers'); pg.wait_for_timeout(300); pg.click('#cOk'); pg.wait_for_timeout(600)
    check('failure shows the error and stays signed in', 'boom' in ev("$('acMsg').textContent") and ev("!!SESSION"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
