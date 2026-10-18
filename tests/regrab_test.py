"""A RedGifs post saved without its exact file name gets it from the archive copy, then plays the real file. Run: python tests/regrab_test.py"""
import os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
bad = []; CALLS = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
ARCH = {'data': [{'id': 'rgnew1', 'title': 'clip', 'over_18': True, 'url': 'https://www.redgifs.com/watch/afraidobedientseabird', 'domain': 'redgifs.com', 'author': 'u', 'created_utc': 1700000000, 'score': 1, 'num_comments': 0,
  'media': {'oembed': {'provider_name': 'RedGifs', 'thumbnail_url': 'https://thumbs44.redgifs.com/AfraidObedientSeabird-mobile.jpg', 'html': ''}}}]}
def handle(r):
    u = r.request.url
    if u.startswith('http://127.0.0.1'): return r.continue_()
    if 'arctic-shift' in u:
        CALLS.append(u); return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps(ARCH))
    return r.abort()
H = 'id,permalink,starred,updated,deleted\r\n'
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', handle)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k];
      startCsvMode(); }""", H + 'rgnew1,/r/gifs/comments/rgnew1/x/,0,1000,0\r\n')
    pg.wait_for_timeout(500)
    # as if it had been saved from the Subreddit viewer without the file name, and cached
    ev("""()=>{ META.rgnew1 = {t:'clip',o:1,th:'https://i.redd.it/a.jpg',m:'gif',u:'https://www.redgifs.com/watch/afraidobedientseabird',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360}; state.nsfw='show'; state.hideBroken=false; loadGen++; loading=false; loadAll(); }""")
    pg.wait_for_timeout(2500)
    check('the archive copy was asked for', len(CALLS) >= 1)
    check('the exact file name is now known', ev("META.rgnew1.g") == 'AfraidObedientSeabird')
    check('the card plays the real file (native controls), not the embed', ev("(()=>{ const t=document.querySelector('article.card[data-id=rgnew1] .thumb'); return !!t && /media\\.redgifs\\.com\\/AfraidObedientSeabird\\.mp4/.test(t.dataset.v||''); })()"))
    n = len(CALLS)
    ev("loadGen++; loading=false; loadAll()"); pg.wait_for_timeout(1200)
    check('it is only asked once a day', len(CALLS) == n)
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
