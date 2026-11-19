"""Taps without waiting. (1) A tap on a clip tile brings its tray up at once (it used to wait 360ms for a possible second tap); a double tap still pauses / resumes
the clip and leaves the tray as it was. (2) Full screen: one tap plays / pauses; a double tap on the right half jumps 10s forward, on the left half 10s back,
with a mark on that side; a third quick tap adds another 10s. Run: python tests/tapseek_test.py (needs ffmpeg for a 40s test clip)"""
import os, functools, http.server, socketserver, threading, subprocess, tempfile
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', 'site')
tmp = os.path.join(tempfile.mkdtemp(), 'long.webm')
subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=160x120:rate=10:duration=40', '-c:v', 'libvpx', '-b:v', '60k', '-y', tmp], check=True)
CLIP = open(tmp, 'rb').read()
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
    ctx.add_init_script("try{localStorage.setItem('saved-posts-skin','legacy')}catch(e){}")   # these checks read Legacy's words and controls (Lemondrop shows some labels in caps and a bare Fit / Fill)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    def route(r):
        u = r.request.url
        if u.startswith('http://127.0.0.1'): return r.continue_()
        if 'media.redgifs.com' in u:   # answer byte ranges, or the clip cannot be seeked
            rg = r.request.headers.get('range', '')
            if rg.startswith('bytes='):
                a, _, z = rg[6:].partition('-'); a = int(a or 0); z = int(z) if z else len(CLIP) - 1
                return r.fulfill(status=206, content_type='video/webm', body=CLIP[a:z+1], headers={'Content-Range': 'bytes %d-%d/%d' % (a, z, len(CLIP)), 'Accept-Ranges': 'bytes'})
            return r.fulfill(status=200, content_type='video/webm', body=CLIP, headers={'Accept-Ranges': 'bytes'})
        return r.abort()
    pg.route('**/*', route)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(600)
    pg.evaluate("openSample()"); pg.wait_for_timeout(800)

    # (1) a tap on a tile opens full screen at once (no double-tap wait on tiles any more)
    pg.tap('.card a.thumb'); pg.wait_for_timeout(60)
    check('one tap on a tile opens it full screen straight away', pg.evaluate("!document.getElementById('viewer').hidden"))
    check('and leaves the tray as it was', not pg.evaluate("layerUp(document.querySelector('.card'))"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)

    # (2) full screen
    pg.evaluate("(()=>{ const p=POSTS[0], m=META[p.id]; m.m='gif'; m.u='https://www.redgifs.com/watch/seekclip'; m.g='SeekClip'; m.v='https://media.redgifs.com/SeekClip.mp4'; m.rgDone=1; openViewer(p); })()")
    pg.wait_for_timeout(1500)
    v = "document.querySelector('#viewer video')"
    check('the clip plays in our own player', pg.evaluate("!!document.querySelector('#viewer .vctl') && !%s.paused && %s.duration > 30" % (v, v)))
    paused = lambda: pg.evaluate(v + ".paused")
    ct = lambda: pg.evaluate(v + ".currentTime")
    box = pg.evaluate("(()=>{ const r=document.querySelector('#viewer video').getBoundingClientRect(); return {l:r.left, r:r.right, y:r.top+r.height/2}; })()")
    W = pg.evaluate("innerWidth"); R = (min(box['r'], W) - 30, box['y']); L = (max(box['l'], 0) + 30, box['y'])
    idle = lambda: pg.evaluate("document.getElementById('viewer').classList.contains('vidle')")
    was = idle()
    pg.touchscreen.tap(*R); pg.wait_for_timeout(450)
    check('one tap shows or hides the overlay and leaves the clip playing', idle() != was and not paused())
    pg.touchscreen.tap(*R); pg.wait_for_timeout(450)
    check('the next tap puts it back', idle() == was and not paused())
    pg.evaluate(v + ".currentTime = 5"); pg.wait_for_timeout(200); t0 = ct()
    pg.touchscreen.tap(*R); pg.wait_for_timeout(80); pg.touchscreen.tap(*R); pg.wait_for_timeout(120)
    t1 = ct()
    check('double tap on the right half jumps about 10s forward (%.1f -> %.1f)' % (t0, t1), 9 < t1 - t0 < 11.5)
    check('and the clip keeps playing (the first tap\'s pause was undone)', not paused())
    check('a mark shows on the right', pg.evaluate("(()=>{ const m=document.querySelector('#viewer .vseek'); return !!m && m.classList.contains('on') && !m.classList.contains('back') && /10s/.test(m.textContent); })()"))
    pg.wait_for_timeout(900)
    check('the mark fades', not pg.evaluate("document.querySelector('#viewer .vseek').classList.contains('on')"))
    pg.evaluate(v + ".currentTime = 25"); pg.wait_for_timeout(200); t0 = ct()
    pg.touchscreen.tap(*L); pg.wait_for_timeout(80); pg.touchscreen.tap(*L); pg.wait_for_timeout(120)
    t1 = ct()
    check('double tap on the left half jumps about 10s back (%.1f -> %.1f)' % (t0, t1), 8.5 < t0 - t1 < 11)
    check('the mark shows on the left', pg.evaluate("document.querySelector('#viewer .vseek').classList.contains('back')"))
    pg.wait_for_timeout(500)
    pg.evaluate(v + ".currentTime = 5"); pg.wait_for_timeout(200); t0 = ct()
    pg.touchscreen.tap(*R); pg.wait_for_timeout(80); pg.touchscreen.tap(*R); pg.wait_for_timeout(80); pg.touchscreen.tap(*R); pg.wait_for_timeout(120)
    t1 = ct()
    check('a third quick tap adds another 10s (%.1f -> %.1f)' % (t0, t1), 19 < t1 - t0 < 21.5)
    check('the mark counts 20s', '20s' in pg.evaluate("document.querySelector('#viewer .vseek').textContent"))
    pg.wait_for_timeout(500)
    w0 = idle(); pg.touchscreen.tap(*L); pg.wait_for_timeout(80); pg.touchscreen.tap(*L); pg.wait_for_timeout(150)
    check('a double tap leaves the overlay as it was', idle() == w0)
    pg.wait_for_timeout(500)
    peek = lambda: pg.evaluate("document.getElementById('viewer').classList.contains('vpeek')")
    pg.mouse.move(*R); pg.mouse.down(); pg.wait_for_timeout(600)
    check('press and hold clears everything and pauses the clip', peek() and paused() and float(pg.evaluate("getComputedStyle(document.querySelector('#viewer .vrail')).opacity")) < 0.05)
    pg.mouse.up(); pg.wait_for_timeout(450)
    check('letting go plays it again (the lift is not a click)', not peek() and not paused())
    pg.mouse.click(*R); pg.wait_for_timeout(450)
    check('a mouse click pauses (desktop)', paused())
    pg.mouse.click(*R); pg.wait_for_timeout(450)
    check('and plays again', not paused())
    pg.evaluate(v + ".pause()"); pg.wait_for_timeout(100)
    pg.evaluate(v + ".currentTime = 5"); pg.wait_for_timeout(200)
    pg.touchscreen.tap(*R); pg.wait_for_timeout(80); pg.touchscreen.tap(*R); pg.wait_for_timeout(200)
    check('a double tap on a paused clip seeks and leaves it paused', paused() and ct() > 14)
    check('the shortcuts list tells about it', pg.evaluate("/double tap[^<]*right half/i.test(document.getElementById('kbhelp').textContent)"))
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
