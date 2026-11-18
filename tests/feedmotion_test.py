"""Feed motion (Nov 2026 audit, items 15-18): pinch the feed on a phone to change the columns, cards glide (FLIP) when the column count
changes, the feed fades in after a filter / sort / shuffle change (not while previews stream in), and Masonry's last cards grow so the
columns end together. Run: python tests/feedmotion_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
# bottoms of each column: the lowest card bottom per column (wide cards count in each column they cover)
BOTTOMS = """(()=>{ const g=document.getElementById('grid'), gl=g.getBoundingClientRect().left, p=colW+6, low=[];
  for(const c of g.children){ if(!c._p) continue; const r=c.getBoundingClientRect(), a=Math.round((r.left-gl)/p), w=Math.max(1,Math.round((r.width+6)/p));
    for(let k=a;k<a+w;k++) low[k]=Math.max(low[k]||0, r.bottom); }
  return low.filter(x=>x).map(x=>Math.round(x)); })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(1200)
    ev("state.showText=true; state.nsfw='show'; refresh()"); pg.wait_for_timeout(600)
    # (18) holes
    filled = ev("[...document.getElementById('grid').children].filter(c=>c._fill).length")
    bt = ev(BOTTOMS)
    check('Masonry: some last cards grew (%d) and the columns end within one card row of each other (%s)' % (filled, bt), filled >= 1 and max(bt) - min(bt) <= 60)
    ev("relayoutAll()")
    check('a relayout keeps the columns even', max(ev(BOTTOMS)) - min(ev(BOTTOMS)) <= 60)
    # (16) FLIP when the column count changes
    ev("(()=>{ const s=document.getElementById('size'); s.value = Math.max(0, +s.value-1); s.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(40)
    n = ev("[...document.querySelectorAll('#grid .card')].filter(c=>c.getAnimations().some(a=>a.playState==='running')).length")
    check('changing the columns makes the cards on screen glide (%d animating)' % n, n >= 3)
    pg.wait_for_timeout(400)
    check('and the glide ends', ev("[...document.querySelectorAll('#grid .card')].every(c=>!c.getAnimations().length)"))
    # (17) fade on a sort / filter / shuffle, none while previews stream
    ev("refresh.quiet=true; state.sort = state.sort; list.reverse(); [...document.getElementById('grid').children].reverse().forEach(c=>c.remove()); refresh(); refresh.quiet=false")
    check('a refresh while previews stream in does not fade', not ev("document.getElementById('grid').getAnimations().length"))
    ev("document.getElementById('shufflebtn').click()")
    check('shuffling fades the new feed in', ev("document.getElementById('grid').getAnimations().length") >= 1)
    check('no page errors', not errs)
    ctx.close()

    # (15) pinch on a phone
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=1); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(1200)
    across = lambda: ev("COL_STEPS.cols[+document.getElementById('size').value]")
    check('phone feed: page zoom is off over the feed', ev("getComputedStyle(document.getElementById('grid')).touchAction") == 'pan-x pan-y')
    start = across()
    PINCH = """(([a0, a1])=>{ const g=document.getElementById('grid'), r=g.getBoundingClientRect(), cy=Math.max(r.top,0)+200, cx=195;
      const mk=(id,x)=>new Touch({identifier:id, target:g, clientX:x, clientY:cy});
      const fire=(type,ts)=>g.dispatchEvent(new TouchEvent(type,{touches:ts, targetTouches:ts, changedTouches:ts, bubbles:true, cancelable:true}));
      fire('touchstart',[mk(1,cx-a0),mk(2,cx+a0)]);
      for(let k=1;k<=10;k++){ const a=a0+(a1-a0)*k/10; fire('touchmove',[mk(1,cx-a),mk(2,cx+a)]); }
      fire('touchend',[]); })"""
    ev(PINCH, [120, 60]); pg.wait_for_timeout(400)
    after = across()
    check('pinching the feed in shows more tiles across (%d -> %d)' % (start, after), after > start)
    ev(PINCH, [40, 120]); pg.wait_for_timeout(400)
    check('spreading it shows fewer, bigger tiles (%d -> %d)' % (after, across()), across() < after)
    check('the choice is remembered', ev("localStorage.getItem('saved-posts-tile-phonecols')") == str(across()))
    check('no page errors on the phone', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
