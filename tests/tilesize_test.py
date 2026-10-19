"""Tile size: free slider on desktop, snapped notches (1/2/3 across) on phones. Run: python tests/tilesize_test.py"""
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
    b = p.chromium.launch(); errs = []
    d = b.new_page(viewport={'width': 1200, 'height': 700}); d.on('pageerror', lambda e: errs.append(str(e)))
    d.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    d.goto('http://127.0.0.1:%d/index.html' % port); d.wait_for_timeout(800)
    check('desktop: free slider with no notches', d.evaluate("document.getElementById('size').step=='10' && !document.querySelector('.sizewrap').classList.contains('stepped')"))
    m = b.new_page(viewport={'width': 390, 'height': 780}, has_touch=True); m.on('pageerror', lambda e: errs.append(str(e)))
    m.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    m.goto('http://127.0.0.1:%d/index.html' % port); m.wait_for_timeout(800)
    k = m.evaluate("document.querySelectorAll('#sizerow .notches i').length")
    check('phone: three notches (1, 2, 3 across)', k == 3)
    check('phone: slider has exactly one step per notch', m.evaluate("document.getElementById('size').max=='2' && document.getElementById('size').step=='1'"))
    check('phone: tile size row is visible', m.evaluate("(()=>{ document.getElementById('decktoggle').click(); const r=document.getElementById('sizerow'); return !!r.offsetParent; })()"))
    check('phone: starts with one column', m.evaluate("getComputedStyle(document.getElementById('grid')).gridTemplateColumns.split(' ').length") == 1)
    for want in (1, 2, 0):
        m.evaluate("(i)=>{ const s=document.getElementById('size'); s.value=i; s.dispatchEvent(new Event('input',{bubbles:true})); }", want)
        m.wait_for_timeout(200)
        cols = m.evaluate("getComputedStyle(document.getElementById('grid')).gridTemplateColumns.split(' ').length")
        check('phone: step %d gives %d column(s)' % (want, want + 1), cols == want + 1)
    check('phone: current notch highlighted', m.evaluate("document.querySelector('#sizerow .notches i.on').textContent") == '1')
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
