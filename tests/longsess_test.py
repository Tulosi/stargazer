"""Long sessions: off-screen cards are skipped (content-visibility), far cards drop their picture address and get it back on approach, a re-filter that keeps
the head of the list keeps the cards on the page, and a slow Arctic Shift is backed up by PullPush. Run: python tests/longsess_test.py"""
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
def post(i, k):
    u = 'https://i.redd.it/%s.jpg' % i
    return {'id': i, 'title': 'Post %d' % k, 'subreddit': 'pics', 'over_18': False, 'url': u, 'domain': 'i.redd.it', 'num_comments': 1, 'score': 1, 'author': 'a', 'created_utc': 1700000000 - k*60,
            'post_hint': 'image', 'preview': {'images': [{'source': {'url': u, 'width': 400, 'height': 400}, 'resolutions': [{'url': u, 'width': 320, 'height': 320}]}]}}
def open_list(pg, text):
    pg.evaluate("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }""", text)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ids = ['a%04d' % i for i in range(600)]; idx = {i: k for k, i in enumerate(ids)}; seen = {'arctic': 0, 'pull': 0}
    def handler(r):
        u = r.request.url
        if u.startswith('file:'): return r.continue_()
        if 'arctic-shift' in u and '/posts/ids' in u:
            seen['arctic'] += 1
            q = parse_qs(urlparse(u).query)['ids'][0].split(',')
            return r.fulfill(body=json.dumps({'data': [post(i, idx[i]) for i in q if i in idx]}), content_type='application/json', headers={'access-control-allow-origin': '*'})
        if 'i.redd.it' in u: return r.fulfill(body=PNG, content_type='image/png')
        return r.abort()
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); ctx.route('**/*', handler)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(PAGE); pg.wait_for_timeout(400); open_list(pg, csv(ids)); pg.wait_for_timeout(5000)
    check('cards use content-visibility:auto', pg.evaluate("getComputedStyle(document.querySelector('#grid .card')).contentVisibility") == 'auto')
    check('first screen has pictures', pg.evaluate("document.querySelector('#grid .card .thumb img[src]')!==null"))
    first = pg.evaluate("document.querySelector('#grid .card').dataset.id")
    for _ in range(12): pg.mouse.wheel(0, 2500); pg.wait_for_timeout(200)
    pg.wait_for_timeout(800)
    far = pg.evaluate("(()=>{const c=document.querySelector('#grid .card[data-id=\"%s\"]');const i=c.querySelector('.thumb img');return {far:!!c._far, src:i&&i.getAttribute('src'), keep:i&&i.dataset.far}})()" % first)
    check('a card far above lets go of its picture (%s)' % far, far['far'] and not far['src'] and bool(far['keep']))
    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(800)
    back = pg.evaluate("(()=>{const i=document.querySelector('#grid .card[data-id=\"%s\"] .thumb img');return i&&i.getAttribute('src')})()" % first)
    check('back on screen it has its picture again', bool(back) and 'i.redd.it' in back)
    n = pg.evaluate("document.querySelectorAll('#grid .card').length")
    pg.evaluate("window.__c0=document.querySelector('#grid .card'); refresh()")
    check('a re-filter with the same head keeps the cards in place', pg.evaluate("document.querySelector('#grid .card')===window.__c0 && document.querySelectorAll('#grid .card').length") == n)
    ctx.close()
    # Hedge: Arctic Shift hangs, PullPush answers, and the batch completes well before Arctic Shift would
    ctx = b.new_context(viewport={'width': 1200, 'height': 800})
    hang = []
    def h2(r):
        u = r.request.url
        if u.startswith('file:'): return r.continue_()
        if 'arctic-shift' in u: hang.append(r); return
        if 'pullpush' in u:
            q = parse_qs(urlparse(u).query)['ids'][0].split(',')
            return r.fulfill(body=json.dumps({'data': [post(i, 0) for i in q]}), content_type='application/json', headers={'access-control-allow-origin': '*'})
        return r.abort()
    ctx.route('**/*', h2); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(PAGE); pg.wait_for_timeout(400)
    t = pg.evaluate("(async()=>{const t=performance.now(); const r=await fetchBatch(['abc1','abc2']); return [r.length, Math.round(performance.now()-t)]})()")
    check('slow Arctic Shift: PullPush answers the batch (%s)' % t, t[0] == 2 and 2400 <= t[1] < 6000)
    check('hedge waits 2.5s before asking PullPush', 'HEDGE_MS = 2500' in open(PAGE[7:]).read())
    for r in hang:
        try: r.abort()
        except Exception: pass
    ctx.close()
    check('no page errors', not errs)
    print('ALL PASS' if not bad else 'FAILED: %d' % len(bad))
