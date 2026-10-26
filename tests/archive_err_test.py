"""Preview loading when an archive refuses a batch: a 400 is retried in smaller pieces, and when every archive fails the message names each one's answer. Run: python tests/archive_err_test.py"""
import os, json, re
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
IDS = ['k%05d' % i for i in range(60)]
IDS_MANY = ['m%05d' % i for i in range(400)]
CSV = 'id,permalink\r\n' + ''.join('%s,https://www.reddit.com/r/pics/comments/%s/a/\r\n' % (i, i) for i in IDS)
def item(i): return {'id': i, 'title': 'Title ' + i, 'subreddit': 'pics', 'permalink': '/r/pics/comments/%s/a/' % i, 'created_utc': 1700000000,
                     'url': 'https://i.redd.it/%s.jpg' % i, 'post_hint': 'image', 'author': 'x', 'score': 1, 'num_comments': 0}
def run(pull_ok, ids=None):
    ids = ids or IDS
    csv = 'id,permalink\r\n' + ''.join('%s,https://www.reddit.com/r/pics/comments/%s/a/\r\n' % (i, i) for i in ids)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); errs = []; asked = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        def route(r):
            u = r.request.url
            if u.startswith('file:') or u.startswith('data:'): return r.continue_()
            if 'pullpush' in u:
                ids = parse_qs(urlparse(u).query).get('ids', [''])[0].split(',')
                asked.append(len(ids))
                if not pull_ok or len(ids) > 25: return r.fulfill(status=400, content_type='application/json', body='{"detail":"bad request"}')
                return r.fulfill(status=200, content_type='application/json', body=json.dumps({'data': [item(i) for i in ids]}))
            return r.abort()   # Arctic Shift unreachable, pictures blocked
        pg.route('**/*', route)
        pg.goto(PAGE); pg.wait_for_timeout(500)
        pg.evaluate("async(t)=>{ await persistRec({id:'demo',name:'saved_posts.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; for(const h in APIH) APIH[h].gap = 50; startCsvMode(); loading = false; loadAll(); }", csv)
        pg.wait_for_timeout(15000)
        out = (pg.evaluate("Object.keys(META).filter(k=>META[k].t).length"), pg.evaluate("document.getElementById('loadText').textContent"), asked)
        check('no page errors', not errs)
        b.close()
        return out
n, text, asked = run(True)
check('a 400 for a full batch is retried in smaller pieces and the previews load', n == 60 and max(asked) > 25 and min(asked) <= 25)
check('pieces are not split again', min(asked) >= 15)
n, text, asked = run(False, IDS_MANY)
check('when every archive fails, the message names each archive', 'Arctic Shift: could not connect' in text and 'PullPush: HTTP 400' in text)
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
