"""Display / Filters / Source panels (Nov 2026): view settings live in their own Display panel, every panel is a manual popover in the top layer,
opening one closes the others, phone sheets drag down to close (a short drag springs back), and a hint toast never covers an open sheet.
Run: python tests/sheets_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
DRAG = """([dy, ms])=>new Promise(res=>{ const el=document.getElementById('viewpanel'), r=el.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+12;
  const T=(type,yy)=>{ const t=new Touch({identifier:1,target:el,clientX:x,clientY:yy}); el.dispatchEvent(new TouchEvent(type,{bubbles:true,cancelable:true,touches:type==='touchend'?[]:[t],changedTouches:[t]})); };
  T('touchstart',y); let k=0; const n=6; const step=()=>{ k++; T('touchmove', y+dy*k/n); if(k<n) setTimeout(step, ms/n); else { T('touchend', y+dy); setTimeout(res, 450); } }; setTimeout(step, ms/n); })"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(600); ev = pg.evaluate; ev("openSample()"); pg.wait_for_timeout(800)
    check('Display holds Layout, Columns, Card info, Autoplay and Theme', ev("['layoutseg','size','fullw','cardmode','autohover','autoplayall','theme'].every(id=>document.getElementById('viewpanel').contains(document.getElementById(id)))"))
    check('Filters no longer holds the view settings', ev("!document.getElementById('panel').querySelector('#layoutseg,#size,#cardmode,#theme')"))
    pg.click('#viewtoggle'); pg.wait_for_timeout(300)
    check('Display opens as a popover in the top layer', ev("document.getElementById('viewpanel').matches(':popover-open')") and ev("$('viewtoggle').getAttribute('aria-expanded')") == 'true')
    r = ev("(()=>{const p=$('viewpanel').getBoundingClientRect(), n={right:Math.max(...[...document.querySelectorAll('#navbtns .pill')].map(x=>x.getBoundingClientRect().right))}, d=document.querySelector('.deck').getBoundingClientRect(); return [Math.round(p.top-d.bottom), Math.round(n.right-p.right)]})()")
    check('desktop: it sits just under the bar, right edge under the buttons (%s)' % r, 4 <= r[0] <= 12 and abs(r[1]) <= 16)
    pg.click('#decktoggle'); pg.wait_for_timeout(300)
    fr = ev("(()=>{const p=$('panel').getBoundingClientRect(); return [Math.round(p.left), Math.round(p.right)]})()")
    check('desktop: Filters is fully on screen at the right (%s)' % fr, fr[0] > 0 and 1380 <= fr[1] <= 1400)
    check('opening Filters closes Display', ev("document.getElementById('panel').matches(':popover-open') && !document.getElementById('viewpanel').matches(':popover-open')") and ev("document.body.classList.contains('view-collapsed')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('Esc closes it and focus goes back to its button', ev("!document.getElementById('panel').matches(':popover-open') && document.activeElement.id==='decktoggle'"))
    ctx.close()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(600); ev = pg.evaluate; ev("openSample()"); pg.wait_for_timeout(800)
    check('phone: five buttons in the bottom bar', ev("document.querySelectorAll('#navbtns > .pill').length") == 5)
    ev("toast('Tap a picture to show its details and controls.')"); pg.wait_for_timeout(100)
    ev("$('viewtoggle').click()"); pg.wait_for_timeout(400)
    check('phone: opening a sheet clears a passing hint toast', not ev("$('toast').classList.contains('on')"))
    ev("toast('Saved', {label:'Undo', fn:()=>{}})"); pg.wait_for_timeout(250)
    top = ev("(()=>{const t=$('toast').getBoundingClientRect(); const e=document.elementFromPoint(t.left+t.width/2, t.top+t.height/2); return !!e && !!e.closest('#toast')})()")
    check('phone: a toast that comes later shows above the open sheet', top)
    ev(DRAG, [40, 700])
    check('phone: a short slow drag springs back', ev("$('viewpanel').matches(':popover-open')") and ev("$('viewpanel').style.transform") in ('', 'none'))
    ev(DRAG, [160, 90])
    check('phone: a quick flick down closes the sheet', not ev("$('viewpanel').matches(':popover-open')") and ev("document.body.classList.contains('view-collapsed')"))
    check('no page errors', not errs)
    print('ALL PASS' if not bad else 'FAILED: %d' % len(bad))
