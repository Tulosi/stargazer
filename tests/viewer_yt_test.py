"""YouTube full screen and the empty Browse column. Run: python tests/viewer_yt_test.py (http page so the player is used)"""
import os, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SEED = """(()=>{ const id='ytyt11'; ROWS.push({id,perma:'https://www.reddit.com/r/videos/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id);
  META[id]={t:'A video',o:0,th:'',m:'video',u:'',n:0,s:0,a:'',c:1700000000,yt:'dQw4w9WgXcQ',w:1280,h:720}; startCsvMode(); })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    check('Browse column hidden before anything is loaded', ev("$('browseCol').hidden") is True)
    pg.click('#decktoggle'); check('and not shown in the Filters panel', not pg.is_visible('#browseCol'))
    pg.click('#decktoggle')
    ev(SEED); pg.wait_for_timeout(800)
    check('Browse column appears once there are posts', ev("$('browseCol').hidden") is False)
    pg.dispatch_event('article.card[data-id="ytyt11"] button.fs', 'click'); pg.wait_for_timeout(600)
    src = ev("(document.querySelector('#viewer iframe.vyt')||{}).src")
    check('full screen embeds the YouTube player', src.startswith('https://www.youtube.com/embed/dQw4w9WgXcQ') and 'autoplay=1' in src)
    check('player has controls (not controls=0) and fullscreen allowed', 'controls=0' not in src and 'fullscreen' in ev("document.querySelector('#viewer iframe.vyt').getAttribute('allow')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('closing removes the player (stops playback)', ev("!document.querySelector('#viewer iframe')") and ev("$('viewer').hidden"))
    check('no page errors', not errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
