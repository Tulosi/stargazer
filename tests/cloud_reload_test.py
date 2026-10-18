"""A signed-in Account list that was filled by a cloud sync must survive a page refresh. Run: python tests/cloud_reload_test.py (network mocked)"""
import os, json, time
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
now = int(time.time())
SESSION = {'access_token': 't', 'refresh_token': 'r', 'expires_at': now + 7200, 'uid': 'u1', 'email': 'a@b.c'}
REMOTE = [{'id': 'aaa111', 'permalink': '/r/pics/comments/aaa111/one/', 'starred': False, 'updated': 1000, 'deleted': False, 'synced_at': '2026-01-01T00:00:00Z'},
          {'id': 'bbb222', 'permalink': '/r/pics/comments/bbb222/two/', 'starred': True, 'updated': 1000, 'deleted': False, 'synced_at': '2026-01-01T00:00:01Z'}]
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    if '/rest/v1/saved_posts' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps(REMOTE), headers={'date': 'Thu, 01 Jan 2026 00:00:05 GMT'})
    if '/rest/v1/rpc/merge_posts' in u: return r.fulfill(status=200, content_type='application/json', body='[]')
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 800}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
    pg.add_init_script("try{ if(!sessionStorage.getItem('seeded')){ sessionStorage.setItem('seeded','1'); localStorage.setItem('saved-posts-session', %s); } }catch(e){}" % json.dumps(json.dumps(SESSION)))
    pg.goto(PAGE); pg.wait_for_timeout(1200); ev = pg.evaluate
    ev("""async()=>{ LIB.cur.cloud = true; LIB.cur.needFull = true; await autoSync(true); }"""); pg.wait_for_timeout(500)
    check('cloud sync filled the list', ev("ROWS.length") == 2)
    pg.route('**/rest/v1/**', lambda r: r.abort())   # offline on refresh
    pg.reload(); pg.wait_for_timeout(1500)
    check('after refresh the account list is still loaded', ev("ROWS.length") == 2 and ev("LIB.cur.cloud") is True)
    pg.click('#srctoggle'); pg.click('#acOut'); pg.wait_for_timeout(300); pg.click('#cOk'); pg.wait_for_timeout(800)
    check('sign out unloads the account list', ev("ROWS.length") == 0 and ev("LIB.cur.cloud") is not True)
    check('sign out clears the cached copy', ev("(async()=>(await libAll()).every(r=>!r.cloud && !/aaa111/.test(r.text)))()"))
    pg.reload(); pg.wait_for_timeout(1500)
    check('after refresh nothing is loaded and no session remains', ev("ROWS.length") == 0 and ev("SESSION") is None)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
