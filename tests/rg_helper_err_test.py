"""When the RedGifs helper answers 502, the message says which step failed. Run: python tests/rg_helper_err_test.py (network mocked)"""
import os, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
mode = ['json']
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    if '/functions/v1/redgifs' in u:
        if mode[0] == 'json': return r.fulfill(status=502, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'error': 'auth 403 blocked'}))
        return r.fulfill(status=502, content_type='text/plain', headers={'access-control-allow-origin': '*'}, body='Bad Gateway')
    return r.abort()   # RedGifs itself: "Failed to fetch"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    check('accounts config is on (helper reachable in this test)', ev("CLOUD_ON") is True)
    msg = lambda: ev("async()=>{ rgDirectOff = 0; try{ await rgFetchMany(['abcdef']); return 'no error'; }catch(e){ return e.message; } }")
    check('error body is included', msg() == 'helper 502: auth 403 blocked')
    mode[0] = 'text'
    check('a plain-text 502 still gives a clean message', msg() == 'helper 502')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
