"""Sample posts never reach a real list (Nov 2026): signing in with the sample list open opens the account's list instead and drops the samples;
opening or merging a CSV drops them; an account that already received sample posts deletes them on its next sync (and fixes the list's name).
Run: python tests/sample_clear_test.py (network mocked)"""
import os, json, time
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
now = int(time.time())
SESSION = {'access_token': 't', 'refresh_token': 'r', 'expires_at': now + 7200, 'uid': 'u1', 'email': 'a@b.c'}
REAL = {'id': 'aaa111', 'permalink': '/r/pics/comments/aaa111/one/', 'starred': False, 'updated': 1000, 'deleted': False, 'synced_at': '2026-01-01T00:00:00Z'}
STRAY = {'id': 'zsmp001', 'permalink': 'https://www.reddit.com/r/pics/comments/zsmp001/sample/', 'starred': False, 'updated': 1000, 'deleted': False, 'synced_at': '2026-01-01T00:00:01Z'}
REMOTE = [REAL]; SENT = []
def route(r):
    u = r.request.url
    if u.startswith(('file:', 'data:')): return r.continue_()
    if '/rest/v1/saved_posts' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps(REMOTE))
    if '/rest/v1/rpc/merge_posts' in u:
        SENT.extend(json.loads(r.request.post_data or '{}').get('rows', [])); return r.fulfill(status=200, content_type='application/json', body='0')
    if '/auth/v1/user' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps({'id': 'u1', 'user_metadata': {}}))
    return r.abort()
CSV = 'id,permalink\r\nbbb222,https://www.reddit.com/r/pics/comments/bbb222/two/\r\n'
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def page(signed):
        ctx = b.new_context(viewport={'width': 1100, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
        if signed: pg.add_init_script("try{ localStorage.setItem('saved-posts-session', %s); }catch(e){}" % json.dumps(json.dumps(SESSION)))
        pg.goto(PAGE); pg.wait_for_timeout(1000); return pg
    libs = lambda pg: pg.evaluate("libAll().then(a=>a.map(r=>({name:r.name, sample:!!r.sample, cloud:!!r.cloud})))")
    ids = lambda pg: pg.evaluate("ROWS.map(r=>r.id)")
    # 1. signing in while the sample list is open
    pg = page(False); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(900)
    check('the sample list is open before signing in', ev("!!LIB.cur.sample") and len(ids(pg)) == 15)
    SENT.clear()
    ev("async s=>{ SESSION = s; saveSession(); acctRender(); await linkAccount(); }", SESSION); pg.wait_for_timeout(800)
    check('after signing in the open list is the account list, not the samples', not ev("!!LIB.cur.sample") and ev("LIB.cur.cloud") and ev("LIB.cur.name") == 'My saved posts')
    check('it holds the account\'s posts and no sample posts', ids(pg) == ['aaa111'])
    check('the sample list is gone from this browser', not any(x['sample'] for x in libs(pg)))
    check('no sample post was uploaded to the account', not any(x['id'].startswith('zsmp') and not x['deleted'] for x in SENT))
    pg.context.close()
    # 2. an account that already received the samples (a list made from the sample list before the fix)
    REMOTE[:] = [REAL, STRAY]; SENT.clear()
    pg = page(True); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(900)
    ev("async()=>{ LIB.cur.cloud = true; LIB.cur.needFull = true; LIB.cur.cloudUser = 'u1'; await autoSync(true); }"); pg.wait_for_timeout(800)
    check('the next sync removes every sample post from the list', not any(i.startswith('zsmp') for i in ids(pg)) and 'aaa111' in ids(pg))
    check('and deletes them in the account too (tombstones uploaded)', any(x['id'] == 'zsmp001' and x['deleted'] for x in SENT))
    check('the list loses the sample flag and its sample name', not ev("!!LIB.cur.sample") and ev("LIB.cur.name") == 'My saved posts')
    check('the deletions are kept (tombstones), so they cannot come back', ev("TOMBS.has('zsmp001')"))
    pg.context.close()
    REMOTE[:] = [REAL]
    # 3. opening a CSV while the samples are open
    pg = page(False); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(900)
    ev("t=>openCsvResult({name:'mine.csv', text:t, handle:null})", CSV); pg.wait_for_timeout(600)
    check('opening a CSV shows only its posts', ids(pg) == ['bbb222'])
    check('and drops the sample list', not any(x['sample'] for x in libs(pg)))
    # 4. Merge CSV while the samples are open opens the file as its own list
    ev("openSample()"); pg.wait_for_timeout(900)
    ev("t=>{ window.pickCsv = async()=>({name:'merge.csv', text:t, handle:null}); }", CSV)
    ev("document.getElementById('csvMerge').click()"); pg.wait_for_timeout(800)
    check('Merge CSV on the samples opens the file instead of mixing it in', ids(pg) == ['bbb222'] and not ev("!!LIB.cur.sample"))
    check('and drops the sample list', not any(x['sample'] for x in libs(pg)))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
