"""A RedGifs clip whose files are gone (404) is caught as broken media and full screen says it was removed, instead of showing RedGifs' "Error loading" player;
a network failure is not taken for a deletion. Run: python tests/rggone_test.py"""
import os, functools, http.server, socketserver, threading
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', 'site')
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
def run(mode):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        def route(r):
            u = r.request.url
            if u.startswith('http://127.0.0.1'): return r.continue_()
            if 'media.redgifs.com' in u or 'v.redd.it' in u:
                return r.fulfill(status=404, content_type='text/html', body='not found') if mode == 'gone' else r.abort('connectionreset')
            return r.abort()   # RedGifs' API unreachable, as on the hosted page
        pg.route('**/*', route)
        pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(600)
        pg.evaluate("openSample()"); pg.wait_for_timeout(800)
        pg.evaluate("(()=>{ const p=POSTS[0], m=META[p.id]; m.m='gif'; m.u='https://www.redgifs.com/watch/goneclip'; m.g='GoneClip'; m.v='https://media.redgifs.com/GoneClip.mp4'; delete m.rgDone; openViewer(p); })()")
        pg.wait_for_timeout(3000)
        out = pg.evaluate("({gone: !!META[POSTS[0].id].rgGone, note: (document.querySelector('#viewer .vgone')||{}).textContent||'', iframe: !!document.querySelector('#viewer iframe'), dead: isUnavailable(POSTS[0])})")
        check('%s: no page errors' % mode, not errs)
        b.close(); return out
o = run('gone')
check('files 404: the clip is marked gone and counts as broken media (%s)' % o, o['gone'] and o['dead'])
check('files 404: full screen says it was removed, no RedGifs error player', 'removed from RedGifs' in o['note'] and not o['iframe'])
o = run('network')
check('network failure: not taken for a deletion; RedGifs player is the fallback (%s)' % o, not o['gone'] and o['iframe'])
srv.shutdown()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
