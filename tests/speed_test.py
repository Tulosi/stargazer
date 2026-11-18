"""Loading speed: Reddit-CDN thumbnails start close together, other hosts keep the polite spacing, on-screen posts are asked of the archive first in a small
first batch, and a preview cache too big for localStorage moves to IndexedDB and is used on the next visit. Run: python tests/speed_test.py"""
import os, base64, json, time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
def csv(ids): return H + ''.join('%s,/r/pics/comments/%s/t/,0,1000,0\r\n' % (i, i) for i in ids)
def post(i, k, host):
    u = 'https://%s/%s.jpg' % (host, i)
    return {'id': i, 'title': 'Post %d' % k, 'subreddit': 'pics', 'over_18': False, 'url': u, 'domain': host, 'num_comments': 1, 'score': 1, 'author': 'a', 'created_utc': 1700000000 - k*60,
            'post_hint': 'image', 'preview': {'images': [{'source': {'url': u, 'width': 400, 'height': 400}, 'resolutions': [{'url': u, 'width': 320, 'height': 320}]}]}}
def open_list(pg, text):
    pg.evaluate("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }""", text)
def setup(ctx, ids, host, reqs, starts):
    idx = {i: k for k, i in enumerate(ids)}
    def handler(r):
        u = r.request.url
        if u.startswith('file:'): return r.continue_()
        if 'arctic-shift' in u and '/posts/ids' in u:
            q = parse_qs(urlparse(u).query)['ids'][0].split(','); reqs.append(q)
            return r.fulfill(body=json.dumps({'data': [post(i, idx[i], host) for i in q if i in idx]}), content_type='application/json', headers={'access-control-allow-origin': '*'})
        if host in u:
            starts.append(time.time()); return r.fulfill(body=PNG, content_type='image/png')
        return r.abort()
    ctx.route('**/*', handler)
def loaded(pg): return pg.evaluate("(()=>{ const cs=[...document.querySelectorAll('#grid .card')].filter(c=>{const r=c.getBoundingClientRect(); return r.top<innerHeight && r.bottom>0;}); return [cs.length, cs.filter(c=>!c.querySelector('.thumb .ph')).length]; })()")
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    # 1. Reddit CDN: a screen of thumbnails in well under the old ~6 s; first archive batch is small and starts with the posts on the page
    ids = ['a%04d' % i for i in range(400)]; reqs = []; starts = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    setup(ctx, ids, 'i.redd.it', reqs, starts)
    pg.goto(PAGE); pg.wait_for_timeout(500)
    open_list(pg, csv(ids)); t0 = time.time()
    tot, vis = 0, 0
    while time.time()-t0 < 8:
        pg.wait_for_timeout(150); tot, vis = loaded(pg)
        if tot >= 10 and vis >= tot: break
    el = time.time()-t0
    check('Reddit thumbnails: a screenful loads in under 3 s (%.1fs, %d tiles)' % (el, vis), tot >= 10 and vis >= tot and el < 3)
    check('first archive batch is small (%d ids)' % (len(reqs[0]) if reqs else -1), bool(reqs) and len(reqs[0]) <= 30)
    check('first archive batch holds the posts on the page', bool(reqs) and reqs[0][:5] == ids[:5])
    pg.wait_for_timeout(5000)
    check('later batches are 100', len(reqs) > 2 and len(reqs[1]) == 100)
    check('fast-host thumbnails start close together', len(starts) > 10 and (starts[10]-starts[0]) < 1.5)
    ctx.close()
    # 2. Other hosts (imgur) keep the slow spacing
    ids2 = ['b%04d' % i for i in range(40)]; reqs = []; starts = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    setup(ctx, ids2, 'i.imgur.com', reqs, starts)
    pg.goto(PAGE); pg.wait_for_timeout(500); open_list(pg, csv(ids2)); pg.wait_for_timeout(6000)
    gaps = [starts[i+1]-starts[i] for i in range(min(8, len(starts)-1))]
    check('imgur thumbnails keep the ~180-430 ms spacing (min gap %.0f ms)' % (min(gaps or [0])*1000), len(gaps) >= 5 and min(gaps) > 0.15)
    ctx.close()
    # 3. A preview cache too big for localStorage moves to IndexedDB and is used next visit
    ids3 = ['c%04d' % i for i in range(150)]; reqs = []; starts = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    ctx.add_init_script("""(()=>{ const set = Storage.prototype.setItem; Storage.prototype.setItem = function(k,v){ if(k==='saved-posts-meta-v7') throw new DOMException('full','QuotaExceededError'); return set.call(this,k,v); }; })()""")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    setup(ctx, ids3, 'i.redd.it', reqs, starts)
    pg.goto(PAGE); pg.wait_for_timeout(500); open_list(pg, csv(ids3)); pg.wait_for_timeout(4000)
    check('previews loaded on the first visit', len(reqs) >= 2 and pg.evaluate("Object.keys(META).length") >= 150)
    check('cache flagged as living in IndexedDB', bool(pg.evaluate("localStorage.getItem('saved-posts-meta-idb')")) and pg.evaluate("localStorage.getItem('saved-posts-meta-v7')") is None)
    n = len(reqs)
    pg.reload(); pg.wait_for_timeout(500)
    pg.wait_for_timeout(3000)   # the page reopens the last list by itself
    check('next visit: previews come from IndexedDB, no archive requests', len(reqs) == n and pg.evaluate("Object.keys(META).length") >= 150)
    check('cards show the cached titles', pg.evaluate("[...document.querySelectorAll('#grid .card')].some(c=>/Post \\d/.test(c.textContent))"))
    ctx.close()
    # 4. Static checks
    src = open(PAGE[7:]).read()
    check('preview cache lasts 30 days', 'CACHE_TTL = 30*24*3600*1000' in src)
    check('web font stylesheet does not block the first paint', 'rel="stylesheet" media="print" onload=' in src)
    check('no page errors', not errs)
    if errs: print(errs[:3])
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
