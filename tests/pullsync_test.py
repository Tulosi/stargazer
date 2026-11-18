"""The "Last pulled from Reddit" date of an Account list follows the account, so a merge on one device clears the
reminder on the others. Run: python tests/pullsync_test.py (network mocked)"""
import os, json, time
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
now = int(time.time()); DAY = 864e5
SESSION = {'access_token': 't', 'refresh_token': 'r', 'expires_at': now + 7200, 'uid': 'u1', 'email': 'a@b.c'}
REMOTE = [{'id': 'aaa111', 'permalink': '/r/pics/comments/aaa111/one/', 'starred': False, 'updated': 1000, 'deleted': False, 'synced_at': '2026-01-01T00:00:00Z'}]
META = {}; PUTS = []; GETS = []
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    if '/rest/v1/saved_posts' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps(REMOTE))
    if '/rest/v1/rpc/merge_posts' in u: return r.fulfill(status=200, content_type='application/json', body='0')
    if u.endswith('/auth/v1/user'):
        if r.request.method == 'PUT':
            d = json.loads(r.request.post_data or '{}').get('data', {}); PUTS.append(d); META.update(d)
        else: GETS.append(1)
        return r.fulfill(status=200, content_type='application/json', body=json.dumps({'id': 'u1', 'user_metadata': META}))
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
    pg.add_init_script("try{ localStorage.setItem('saved-posts-session', %s); }catch(e){}" % json.dumps(json.dumps(SESSION)))
    pg.goto(PAGE); pg.wait_for_timeout(1200); ev = pg.evaluate
    ev("""async()=>{ LIB.cur.cloud = true; LIB.cur.needFull = true; await autoSync(true); }"""); pg.wait_for_timeout(400)
    cid = ev("LIB.cur.id")
    pl = lambda: ev("$('pullLine').textContent")
    hid = lambda: ev("$('mrgHint').hidden")
    sync = lambda: (ev("autoSync(true).then(()=>pullChain)"), pg.wait_for_timeout(300))
    check('a guessed date (first seen here) is not uploaded', ev("ROWS.length") == 1 and not PUTS)
    # this device last pulled 35 days ago; another device merged a fresh export 1 day ago
    ev("id => localStorage.setItem('saved-posts-lastmerge', JSON.stringify({[id]:{t:Date.now()-35*864e5, snooze:0, src:'file'}}))", cid)
    ev("csvInfo()"); check('stale on its own, this device asks for a merge', not hid())
    META['sg_pulled'] = int(time.time() * 1000 - DAY)
    sync()
    check('after a sync the account\'s newer date clears the reminder', hid() and '1 day ago' in pl() and 'Over' not in pl())
    check('the account date is not written back', not PUTS)
    # a merge here with a newer file goes up to the account
    PUTS.clear(); t = int(time.time() * 1000 - 3600e3)
    ev("([id,t]) => noteMerge(id, t)", [cid, t]); ev("pullChain"); pg.wait_for_timeout(300)
    check('a merge on this device uploads its pull date', PUTS and PUTS[-1].get('sg_pulled') == t)
    # an older date in the account never pulls this device back
    META['sg_pulled'] = int(time.time() * 1000 - 40 * DAY); PUTS.clear()
    sync()
    check('an older account date is replaced, not taken', hid() and PUTS and PUTS[-1].get('sg_pulled') == t)
    # a failing account lookup leaves the list synced and the page quiet
    pg.route('**/auth/v1/user', lambda r: r.abort())
    sync()
    check('a failed date lookup does not mark the sync as failed', ev("SYNC.state") == 'ok')
    # a Local list never touches the account
    pg.unroute('**/auth/v1/user'); GETS.clear()
    ev("async()=>{ LIB.cur.cloud = false; noteMerge(LIB.cur.id, Date.now()); await pullChain; }"); pg.wait_for_timeout(200)
    check('a Local list keeps its date to itself', not GETS)
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
raise SystemExit(1 if bad else 0)
