"""A RedGifs post that cannot be looked up (blocked API, no file name in Reddit's data) still plays on hover through RedGifs' own embed. Run: python tests/rg_embed_test.py (serves over http because embeds need a web origin)"""
import os, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())   # RedGifs API unreachable
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev("""(()=>{ const id='newrg1'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id);
      META[id]={t:'clip',o:0,th:'https://i.redd.it/a.jpg',m:'gif',u:'https://www.redgifs.com/watch/afraidobedientseabird',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360}; })()""")
    ev('startCsvMode()'); pg.wait_for_timeout(2500)
    check('card is marked playable through the embed', ev("(document.querySelector('article.card[data-id=newrg1] .thumb')||{dataset:{}}).dataset.v") == 'rg:afraidobedientseabird')
    pg.hover('article.card[data-id=newrg1] .thumb'); pg.wait_for_timeout(600)
    check('hover shows RedGifs embed', ev("(()=>{ const f=document.querySelector('article.card[data-id=newrg1] iframe.clip'); return !!f && f.src.includes('redgifs.com/ifr/afraidobedientseabird'); })()"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(600)
    check('leaving removes it', ev("!document.querySelector('article.card[data-id=newrg1] iframe.clip')"))
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
