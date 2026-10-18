"""UX review items: undo toast, short status line, filter badge, hidden inert controls. Run: python tests/review_test.py"""
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
SEED = """(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/x/',starred:%s,t:5}); ROWSET.add(id); if(%s) FAVS.add(id);
  META[id]={t:'post '+id,o:0,th:'https://i.redd.it/a.jpg',m:'image',u:'https://i.redd.it/a.jpg',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360}; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(SEED % ('aaa01', 'true', 'true')); ev(SEED % ('bbb02', 'false', 'false'))
    ev('state.hideBroken=false; state.nsfw="show"'); ev('startCsvMode()'); pg.wait_for_timeout(1200)
    # filter badge: defaults do not count, changes do
    ev('state.hideBroken=true; state.nsfw="hide"; state.showText=false; state.cats.clear(); refresh(true)'); pg.wait_for_timeout(300)
    check('badge empty with default filters', ev("document.getElementById('decktoggle').dataset.n") is None)
    ev('state.fav=true; refresh(true)'); pg.wait_for_timeout(300)
    check('badge counts a user-changed filter', ev("document.getElementById('decktoggle').dataset.n") == '1')
    ev('state.fav=false; state.hideBroken=false; state.nsfw="show"; refresh(true)'); pg.wait_for_timeout(300)
    # undo delete
    pg.dispatch_event('article.card[data-id=aaa01] button.save:not(.nsfwb)', 'click'); pg.wait_for_timeout(600)
    check('delete needs no confirm dialog and removes the card', ev("!ROWSET.has('aaa01') && !document.querySelector('article.card[data-id=aaa01]')"))
    check('toast offers Undo', ev("!!document.querySelector('#toast .tact')"))
    pg.click('#toast .tact'); pg.wait_for_timeout(1500)
    check('undo restores row, star and card', ev("ROWSET.has('aaa01') && FAVS.has('aaa01') && !!document.querySelector('article.card[data-id=aaa01]') && !TOMBS.has('aaa01')"))
    check('restored row is newer than the tombstone', ev("ROWS.find(r=>r.id==='aaa01').t") > 5)
    # tile size hidden in list
    pg.dispatch_event('#layoutseg [data-l=list]', 'click')
    pg.wait_for_timeout(300)
    check('tile size hidden in List', not ev("document.getElementById('sizerow').offsetParent"))
    check('layout hint is short', len(ev("document.getElementById('layouthint').textContent")) < 30)
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
