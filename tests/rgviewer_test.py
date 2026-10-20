"""The RedGifs player in the full screen viewer leaves room for the previous/next post buttons. Run: python tests/rgviewer_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
GEO = """()=>{ const v=document.getElementById('viewer'); v.hidden=false; const st=v.querySelector('.vstage'); const f=document.createElement('iframe'); f.className='vyt vrg'; st.replaceChildren(f);
  const fb=f.getBoundingClientRect(), pb=v.querySelector('.vposts').getBoundingClientRect(); return {frameBottom:fb.bottom, frameTop:fb.top, postsTop:pb.top, w:fb.width, h:innerHeight}; }"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    for vp in ({'width': 1100, 'height': 700}, {'width': 390, 'height': 780}):
        pg = b.new_page(viewport=vp); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
        pg.goto(PAGE); pg.wait_for_timeout(700)
        g = pg.evaluate(GEO)
        check('%dpx: the RedGifs frame ends above the post buttons' % vp['width'], g['frameBottom'] <= g['postsTop'] - 4)
        check('%dpx: and still fills the width and the top' % vp['width'], g['w'] >= vp['width'] - 1 and g['frameTop'] < 2)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
