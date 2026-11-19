"""Full screen on a phone: swipe up / down moves between posts over every kind of post, not only pictures and clips (Nov 2026). A YouTube
player keeps its own touches, so the swipe works on the black around it; a post that failed to load ("Nothing to show") and a "Watch on YouTube"
post swipe on the empty stage. Buttons still work as buttons. Run: python tests/swipeall_test.py"""
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
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('http://127.0.0.1', 'data:')) else r.abort())
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(600)
    pg.evaluate("openSample()"); pg.wait_for_timeout(900)
    cdp = ctx.new_cdp_session(pg)
    def swipe(x, y0, y1):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y0}]})
        for k in range(1, 6): cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y0 + (y1 - y0) * k / 5}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(800)
    cur = lambda: pg.evaluate("list.indexOf(VIEW.cur)")
    # a YouTube post: the real player is an iframe in the middle; the black above and below takes the swipe
    pg.evaluate("(()=>{ const p=list[3], m=metaOf(p); m.yt='abcdefghijk'; m.m='video'; m.u='https://www.youtube.com/watch?v=abcdefghijk'; openViewer(p); })()"); pg.wait_for_timeout(700)
    check('the YouTube post shows its player', pg.evaluate("!!document.querySelector('#viewer .vstage:not(.vghost) iframe.vyt')"))
    box = pg.evaluate("(()=>{ const r=document.querySelector('#viewer .vstage:not(.vghost) iframe.vyt').getBoundingClientRect(); return [r.top, r.bottom]; })()")
    y0 = min(760, box[1] + 200)
    start = cur(); swipe(150, y0, y0 - 260)
    check('swipe up on the black below the YouTube player goes to the next post (was stuck)', cur() == start + 1)
    swipe(150, box[0] - 40 if box[0] > 120 else 120, (box[0] - 40 if box[0] > 120 else 120) + 260)
    check('swipe down above it goes back', cur() == start)
    # a post with nothing that loads, opened directly: "Nothing to show for this post." in place
    pg.evaluate("(()=>{ openViewer(list[5]); })()"); pg.wait_for_timeout(500)
    pg.evaluate("(()=>{ VIEW.dir = 0; viewerFail(); })()"); pg.wait_for_timeout(300)   # what a post whose every address fails ends in
    check('a failed post says so in place', 'Nothing to show' in pg.evaluate("document.querySelector('#viewer .vstage:not(.vghost)').textContent"))
    start = cur(); swipe(195, 600, 300)
    check('swipe up on a failed post goes to the next post (was stuck)', cur() == start + 1)
    # a tap on the black is not swallowed by the swipe watcher (its touchend is left alone, so the browser's click follows), and that click
    # still shows / hides the overlay. (Chromium's test touch input does not always synthesise the click, so the click is sent directly.)
    pg.evaluate("openViewer(list[3])"); pg.wait_for_timeout(700)
    idle = lambda: pg.evaluate("VIEW.root.classList.contains('vidle')")
    pg.evaluate("(()=>{ window._te = null; addEventListener('touchend', e=>{ window._te = e.defaultPrevented; }); })()")
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 150, 'y': y0}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(200)
    check('a tap on the black is left to the browser (not cancelled) and does not move', pg.evaluate("window._te") is False and cur() == 3)
    before = idle(); pg.evaluate("VIEW.stage.dispatchEvent(new MouseEvent('click',{bubbles:true}))"); pg.wait_for_timeout(200)
    check('its click still toggles the overlay', idle() != before)
    pg.evaluate("VIEW.root.classList.remove('vidle')"); pg.wait_for_timeout(200)
    pg.tap('#viewer .vpn'); pg.wait_for_timeout(800)
    check('the Next post button still works', cur() == 4)
    check('no page errors', not errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
