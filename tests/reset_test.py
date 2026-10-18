"""Password reset: the email link leads to a "choose a new password" form. Run: python tests/reset_test.py (Supabase is mocked)"""
import os, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
HASH = '#access_token=AAA.BBB.CCC&refresh_token=RRR&expires_in=3600&token_type=bearer&type=recovery'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 400, 'height': 800}); errs = []; puts = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    def route(r):
        u = r.request.url; h = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*'}
        if u.startswith('file:'): return r.continue_()
        if r.request.method == 'OPTIONS': return r.fulfill(status=204, headers=h)
        if '/auth/v1/user' in u:
            if r.request.method == 'PUT':
                puts.append((r.request.headers.get('authorization'), json.loads(r.request.post_data)))
                return r.fulfill(status=200, content_type='application/json', body=json.dumps({'id': 'u1', 'email': 'a@b.c'}), headers=h)
            return r.fulfill(status=200, content_type='application/json', body=json.dumps({'id': 'u1', 'email': 'a@b.c'}), headers=h)
        if '/rest/v1/' in u: return r.fulfill(status=200, content_type='application/json', body='[]', headers=h)
        return r.abort()
    pg.route('**/*', route)
    pg.goto(PAGE + HASH); pg.wait_for_timeout(1500); ev = pg.evaluate
    check('address hash is cleared', ev("location.hash") == '')
    check('Source panel opens by itself', pg.is_visible('#srcpanel'))
    check('new-password form is shown, sign-in form is not', pg.is_visible('#acReset') and not pg.is_visible('#acctOut') and not pg.is_visible('#acctIn'))
    pg.fill('#acNew', 'short'); pg.fill('#acNew2', 'short'); pg.click('#acSetPw')
    check('too short is refused', 'at least 8' in ev("$('acMsg').textContent") and not puts)
    pg.fill('#acNew', 'longenough1'); pg.fill('#acNew2', 'different22'); pg.click('#acSetPw')
    check('mismatch is refused', 'do not match' in ev("$('acMsg').textContent") and not puts)
    pg.fill('#acNew2', 'longenough1'); pg.click('#acSetPw'); pg.wait_for_timeout(800)
    check('password is sent with the reset session', puts and puts[0][0] == 'Bearer AAA.BBB.CCC' and puts[0][1] == {'password': 'longenough1'})
    check('form closes and you are signed in', not pg.is_visible('#acReset') and pg.is_visible('#acctIn') and 'updated' in ev("$('acMsg').textContent"))
    # not now
    pg2 = b.new_page(viewport={'width': 400, 'height': 800}); pg2.route('**/*', route)
    pg2.goto(PAGE + HASH); pg2.wait_for_timeout(1200); pg2.click('#acSkipPw'); pg2.wait_for_timeout(300)
    check('"Not now" keeps you signed in without changing anything', pg2.is_visible('#acctIn') and not pg2.is_visible('#acReset') and len(puts) == 1)
    # expired link
    pg3 = b.new_page(viewport={'width': 400, 'height': 800}); pg3.route('**/*', route)
    pg3.goto(PAGE + '#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired'); pg3.wait_for_timeout(1200)
    check('expired link explains what to do', 'expired' in pg3.evaluate("$('acMsg').textContent") and pg3.is_visible('#srcpanel') and pg3.is_visible('#acctOut'))
    # normal load is untouched
    pg4 = b.new_page(viewport={'width': 400, 'height': 800}); pg4.route('**/*', route)
    pg4.goto(PAGE); pg4.wait_for_timeout(1000)
    check('normal load: no form, panel closed', not pg4.is_visible('#srcpanel') and pg4.evaluate("$('acReset').hidden"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
