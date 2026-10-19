"""Header buttons sit on the right before and after data loads (desktop). Run: python tests/header_test.py"""
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
RIGHT = "(()=>{ const b=document.getElementById('navbtns').lastElementChild; const bar=document.querySelector('.deck-bar').getBoundingClientRect(); const r=[...document.querySelectorAll('#navbtns .pill')].filter(x=>x.offsetParent).pop().getBoundingClientRect(); return bar.right - r.right; })()"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1300, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(800); ev = pg.evaluate
    check('stats hidden before loading', ev("document.getElementById('stats').hidden"))
    check('buttons are on the right edge before loading', ev(RIGHT) < 40)
    ev("(()=>{ const id='h1'; ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); META[id]={t:'a',o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000,v:'',w:0,h:0}; startCsvMode(); })()"); pg.wait_for_timeout(1000)
    check('stats visible after loading', not ev("document.getElementById('stats').hidden"))
    check('buttons still on the right edge after loading', ev(RIGHT) < 40)
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
