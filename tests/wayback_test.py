"""Wayback recovery runs in parallel and gives up sooner. Run: python tests/wayback_test.py  (about 40 s; Wayback is mocked; hung requests are dropped quietly at the end, so a Traceback here is a real problem; fake hung request open)"""
import os, time, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
SEED = """(n=>{ for(let i=0;i<n;i++){ const id='gone'+String(i).padStart(2,'0'); ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id);
  META[id]={t:'',o:0,th:'',m:'removed',u:'',n:0,s:0,a:'',c:0,miss:1}; } startCsvMode(); })(%d)"""
def run(mode, n):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        calls = {'max': 0, 'cur': 0, 'n': 0}; hung = []
        def route(r):
            u = r.request.url
            if u.startswith('file:'): return r.continue_()
            if 'web.archive.org/cdx' in u:
                calls['n'] += 1
                if mode == 'hang': hung.append(r); return   # never answers: the page's own time limit ends it
                return r.fulfill(status=200, content_type='application/json', body='[["timestamp","original"]]', headers={'access-control-allow-origin': '*'})
            return r.abort()
        pg.route('**/*', route)
        pg.goto(PAGE); pg.wait_for_timeout(800)
        t0 = time.time(); pg.evaluate(SEED % n)
        while time.time() - t0 < 90:   # poll (the page's CSP forbids wait_for_function's eval)
            if pg.evaluate("(/Recovered|not responding|too long|Stopped/.test($('recText').textContent) && !recovering)"): break
            time.sleep(0.5)
        el = time.time() - t0; txt = pg.inner_text('#recText'); stop_hidden = pg.evaluate("$('recStop').hidden")
        for r in hung:   # answer the requests left hanging on purpose, so closing the browser does not print asyncio tracebacks
            try: r.abort()
            except Exception: pass
        pg.unroute_all(behavior='ignoreErrors')
        b.close(); return el, txt, calls['n'], stop_hidden, errs
el, txt, n, sh, errs = run('empty', 6)
check('empty answers finish: %.1fs, %d lookups' % (el, n), 'Recovered 0 of 6' in txt and n == 12 and el < 20)
check('stop button hidden afterwards', sh)
el, txt, n, sh, errs2 = run('hang', 8)
check('hung Wayback: gives up in %.1fs (%s)' % (el, txt[:70]), 'not responding' in txt and 'Skipped the last' in txt and el < 45 and n < 16)
check('no page errors', not errs and not errs2)
raise SystemExit(1 if bad else 0)
