"""Full-screen player on a touch screen: once the bar has faded, a tap on the clip brings it back and it stays up; a second tap hides it. Run: python tests/viewtap_test.py (uses tests/fixtures/clip_audio.webm)"""
import os, functools, http.server, socketserver, threading
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', 'site')
CLIP = open(os.path.join(HERE, 'fixtures', 'clip_audio.webm'), 'rb').read()
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    def route(r):
        u = r.request.url
        if u.startswith('http://127.0.0.1'): return r.continue_()
        if 'media.redgifs.com' in u: return r.fulfill(status=200, content_type='video/webm', body=CLIP)
        return r.abort()
    pg.route('**/*', route)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(600)
    pg.evaluate("openSample()"); pg.wait_for_timeout(800)
    pg.evaluate("(()=>{ const p=POSTS[0], m=META[p.id]; m.m='gif'; m.u='https://www.redgifs.com/watch/tapclip'; m.g='TapClip'; m.v='https://media.redgifs.com/TapClip.mp4'; m.ha=1; m.rgDone=1; openViewer(p); })()")
    pg.wait_for_timeout(1200)
    idle = lambda: pg.evaluate("document.getElementById('viewer').classList.contains('vidle')")
    check('the clip plays in our own player', pg.evaluate("!!document.querySelector('#viewer .vctl') && !document.querySelector('#viewer video').paused"))
    pg.wait_for_timeout(3200)
    check('the bar fades while the clip plays untouched', idle())
    pg.tap('#viewer video'); pg.wait_for_timeout(400)
    check('a tap brings the bar back', not idle())
    pg.wait_for_timeout(1200)
    check('and it stays up (no flash and gone)', not idle())
    pg.tap('#viewer video'); pg.wait_for_timeout(400)
    check('a second tap hides it again', idle())
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
