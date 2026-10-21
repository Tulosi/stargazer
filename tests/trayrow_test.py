"""Open post, Comments and the card controls always sit on one line, from 3-across phone tiles to wide desktop tiles; icons replace words on narrow tiles. Run: python tests/trayrow_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
ROW = """()=>{ const out=[]; document.querySelectorAll('.card').forEach(c=>{ const l=c.querySelector('.layer'); if(!l) return; const lr=l.getBoundingClientRect(); if(!lr.width) return;
  const els=[...l.querySelectorAll('.actions .btn, .lay-cap button')].filter(e=>e.offsetParent!==null); if(!els.length) return;
  const ys=els.map(e=>{const r=e.getBoundingClientRect(); return r.top+r.height/2;}); const spread=Math.max(...ys)-Math.min(...ys);
  const inside=els.every(e=>{const r=e.getBoundingClientRect(); return r.left>=lr.left-1&&r.right<=lr.right+1;});
  const w=c.getBoundingClientRect().width; const icon=getComputedStyle(l.querySelector('.actions .btn .bt')||l).display==='none';
  out.push({w:Math.round(w),spread:Math.round(spread),inside,icon,n:els.length,minbtn:Math.round(Math.min(...els.map(e=>e.getBoundingClientRect().width)))}); }); return out; }"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def run(vp, mobile, setup, label):
        ctx = b.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, device_scale_factor=1)
        ctx.add_init_script("localStorage.setItem('saved-posts-cardmode','always')")
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
        pg.goto(PAGE); pg.wait_for_timeout(800); pg.click('#introSample'); pg.wait_for_timeout(1500)
        setup(pg); pg.wait_for_timeout(700)
        rows = pg.evaluate(ROW); pg.screenshot(path=os.path.join(os.environ.get('TRAYSHOTS','/tmp'), 'tray_%s.png' % label)) if os.environ.get('TRAYSHOTS') else None
        ctx.close(); return rows
    for px in (150, 230, 300, 360, 420, 560):
        rows = run({'width': 1500, 'height': 900}, False, lambda pg, px=px: pg.evaluate("(px)=>{ document.documentElement.style.setProperty('--card', px+'px'); relayoutAll(); }", px), 'd%d' % px)
        ok = rows and all(r['spread'] <= 3 and r['inside'] for r in rows)
        widths = sorted(set(r['w'] for r in rows))
        check('desktop tile ~%dpx (widths %s): one line, inside the tray, icons=%s' % (px, widths[:3], rows[0]['icon'] if rows else '?'), ok)
    def three(pg): pg.evaluate("()=>{const s=document.getElementById('size'); s.value=2; s.dispatchEvent(new Event('input'))}")
    for w in (320, 360, 390):
        rows = run({'width': w, 'height': 780}, True, three, 'p%d' % w)
        ok = rows and all(r['spread'] <= 3 and r['inside'] for r in rows)
        check('phone %dpx, 3 across (tile %s): one line, inside the tray' % (w, sorted(set(r['w'] for r in rows))[:2]), ok)
        check('  and no control narrower than 16px', all(r['minbtn'] >= 16 for r in rows))
    rows = run({'width': 1500, 'height': 900}, False, lambda pg: pg.evaluate("()=>{ document.documentElement.style.setProperty('--card','560px'); relayoutAll(); }"), 'wide')
    check('wide tiles keep words (Open post, Comments) not icons', rows and not rows[0]['icon'])
    rows = run({'width': 1500, 'height': 900}, False, lambda pg: None, 'default')
    check('default desktop tile uses icons', rows and rows[0]['icon'])
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
