"""Card info & controls: the per-card glass layer, its three modes, the handle, closing, tap to open, double tap to pause. Run: python tests/layer_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
N = 30
H = 'id,permalink,starred,updated,deleted\r\n' + ''.join('v%05d,https://www.reddit.com/r/vids/comments/v%05d/t/,0,1000,0\r\n' % (i, i) for i in range(N))
GIF = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode();
  POSTS.forEach((p,i)=>{ META[p.id]={t:'Clip '+i,o:0,th:'%s',m:'video',u:'https://v.redd.it/'+i+'/DASH_360.mp4',n:3,s:5,a:'',c:1700000000,w:400,h:300,v:'https://v.redd.it/'+i+'/DASH_360.mp4'}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }""" % GIF
SETM = "(m)=>{ const s=document.getElementById('cardmode'); s.value=m; s.dispatchEvent(new Event('change')); }"
LAY = "(i)=>{ const c=document.querySelectorAll('.card')[i||0]; return +getComputedStyle(c.querySelector('.layer')).opacity; }"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 700}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H); pg.wait_for_timeout(1000)
    check('desktop default is Show on hover / focus', ev("document.getElementById('cardmode').value") == 'hover')
    # the layer holds all three components
    ev(SETM, 'always'); pg.wait_for_timeout(300)
    check('the layer holds info, the action pill and the comments chip', ev("(()=>{ const l=document.querySelector('.card .layer'); return !!l.querySelector('.info .title') && l.querySelectorAll('.lay-cap > *').length>=3 && !!l.querySelector('.actions a.btn:not(.primary)'); })()"))
    check('Show always: layer up on every card, no handle', ev(LAY, 0) == 1 and ev(LAY, 5) == 1 and ev("getComputedStyle(document.querySelector('.card .lhandle')).display") == 'none')
    # playback lives in the layer: build controls on a clip tile
    ev("""(()=>{ const t=document.querySelector('.card .thumb'); const im=document.createElement('img'); im.src='%s'; t.appendChild(im); buildControls(t, im, true); })()""" % GIF)
    check('player controls are placed inside the layer', ev("!!document.querySelector('.card .layer .lay-play .ctl .pp')"))
    ev(SETM, 'collapsed'); pg.mouse.move(2, 2); pg.wait_for_timeout(400)
    check('Collapsed: nothing on the tile but the handle (layer, labels and player controls all down)', ev(LAY, 0) == 0 and ev("+getComputedStyle(document.querySelector('.card .badges')).opacity") == 0 and ev("getComputedStyle(document.querySelector('.card .lhandle')).display") == 'block' and ev("+getComputedStyle(document.querySelector('.card .layer')).opacity") == 0)
    check('Collapsed: no progress hairline either', ev("getComputedStyle(document.querySelector('.card .cprog') || document.body).display") in ('none', 'block') and not ev("!!document.querySelector('.card .cprog') && getComputedStyle(document.querySelector('.card .cprog')).display!=='none'"))
    check('a layer that is down does not catch taps (its buttons cannot be hit)', ev("(()=>{ const c=document.querySelectorAll('.card')[2]; const b=c.querySelector('.lay-cap > *').getBoundingClientRect(); const el=document.elementFromPoint(b.left+b.width/2,b.top+b.height/2); return !el.closest('.layer'); })()"))
    # handle opens, outside tap / Esc / second handle close
    ev("document.querySelectorAll('.card')[1].querySelector('.lhandle').click()"); pg.wait_for_timeout(400)
    check('the handle opens that card only', ev(LAY, 1) == 1 and ev(LAY, 0) == 0 and ev(LAY, 2) == 0)
    ev("document.querySelectorAll('.card')[2].querySelector('.lhandle').click()"); pg.wait_for_timeout(400)
    check('opening another card closes the first (one at a time)', ev(LAY, 2) == 1 and ev(LAY, 1) == 0)
    pg.mouse.click(1090, 300); pg.wait_for_timeout(400)
    check('a tap elsewhere closes the open layer', ev(LAY, 2) == 0)
    ev("document.querySelectorAll('.card')[3].querySelector('.lhandle').click()"); pg.wait_for_timeout(300)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    check('Esc closes the open layer', ev(LAY, 3) == 0)
    pg.mouse.move(2, 2)
    box = pg.locator('.card').nth(4).bounding_box()
    pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + 20); pg.keyboard.press('i'); pg.wait_for_timeout(400)
    check('I opens the layer of the card under the pointer', ev(LAY, 4) == 1)
    pg.keyboard.press('i'); pg.wait_for_timeout(400)
    check('and I again closes it', ev(LAY, 4) == 0)
    # swipe up on the handle
    h = pg.locator('.card').nth(5).locator('.lhandle').bounding_box()
    pg.mouse.move(h['x'] + h['width'] / 2, h['y'] + h['height'] / 2); pg.mouse.down(); pg.mouse.move(h['x'] + h['width'] / 2, h['y'] + h['height'] / 2 - 30, steps=4); pg.mouse.up(); pg.wait_for_timeout(400)
    check('swiping up on the handle opens the layer', ev(LAY, 5) == 1)
    pg.keyboard.press('Escape')
    # hover mode: hover raises it, clicking the grabber pins it
    ev(SETM, 'hover'); pg.mouse.move(2, 2); pg.wait_for_timeout(300)
    check('hover mode: down at rest', ev(LAY, 6) == 0)
    box = pg.locator('.card').nth(6).bounding_box()
    pg.mouse.move(box['x'] + 8, box['y'] + 8); pg.wait_for_timeout(400)
    check('hover mode: up while hovered', ev(LAY, 6) == 1)
    pg.mouse.click(box['x'] + 8, box['y'] + 8); pg.wait_for_timeout(500)
    check('hover mode: a tap on the tile puts the raised layer away', ev(LAY, 6) == 0 and ev("document.querySelectorAll('.card')[6].classList.contains('lay-shut')"))
    check('hover mode: and its handle comes back', ev("getComputedStyle(document.querySelectorAll('.card')[6].querySelector('.lhandle')).display") == 'block')
    pg.mouse.move(2, 2); pg.wait_for_timeout(300); pg.mouse.move(box['x'] + 8, box['y'] + 8); pg.wait_for_timeout(500)
    check('hover mode: it rises again once the pointer has left and come back', ev(LAY, 6) == 1)
    pg.mouse.move(2, 2); pg.wait_for_timeout(300)
    # Show always: collapse by hand with a tap or by swiping the grabber down; it stays down; the handle raises it again
    ev(SETM, 'always'); pg.wait_for_timeout(300)
    check('always: layer up', ev(LAY, 7) == 1)
    ev("document.querySelectorAll('.card')[7].querySelector('a.thumb').click()"); pg.wait_for_timeout(500)
    check('always: a tap on the tile collapses that card', ev(LAY, 7) == 0 and ev(LAY, 8) == 1)
    pg.mouse.move(box['x'] + 8, box['y'] + 8); pg.mouse.move(2, 2); pg.wait_for_timeout(400)
    check('always: it stays collapsed after the pointer comes and goes', ev(LAY, 7) == 0)
    ev("document.querySelectorAll('.card')[7].querySelector('.lhandle').click()"); pg.wait_for_timeout(500)
    check('always: the handle raises it again', ev(LAY, 7) == 1)
    b8 = pg.locator('.card').nth(8).bounding_box(); pg.mouse.move(b8['x'] + 6, b8['y'] + 6); pg.wait_for_timeout(700)   # let hover playback settle so the layer stops growing
    g = pg.locator('.card').nth(8).locator('.lh-close').bounding_box()
    pg.mouse.move(g['x'] + g['width'] / 2, g['y'] + g['height'] / 2); pg.mouse.down(); pg.mouse.move(g['x'] + g['width'] / 2, g['y'] + g['height'] / 2 + 30, steps=4); pg.mouse.up(); pg.wait_for_timeout(500)
    check('always: swiping the grabber down collapses that card', ev(LAY, 8) == 0 and ev(LAY, 7) == 1)
    ev(SETM, 'always'); pg.wait_for_timeout(300)
    check('changing the mode clears hand-collapsed cards', ev(LAY, 8) == 1)
    ev(SETM, 'hover'); pg.wait_for_timeout(200)
    # scrolling the card away closes it
    ev("window.scrollTo(0, 2500)"); pg.wait_for_timeout(700)
    check('scrolling a card out of view closes its layer', not ev("document.querySelectorAll('.card')[6].classList.contains('lay-open')"))
    ev("window.scrollTo(0, 0)"); pg.wait_for_timeout(300)
    # the choice is remembered
    ev(SETM, 'always'); pg.reload(); pg.wait_for_timeout(800)
    check('the mode is remembered across a reload', ev("document.getElementById('cardmode').value") == 'always' and ev("document.body.classList.contains('cm-always')"))
    ev("localStorage.removeItem('saved-posts-cardmode'); localStorage.setItem('saved-posts-ctlmode','collapsed')"); pg.reload(); pg.wait_for_timeout(800)
    check('an earlier Card controls choice carries over', ev("document.getElementById('cardmode').value") == 'collapsed')
    # double tap pauses; a single tap still opens the post
    ev(SEED, H); pg.wait_for_timeout(1000)
    ev("""(()=>{ const t=document.querySelector('.card .thumb'); const im=document.createElement('img'); im.src='%s'; t.appendChild(im); buildControls(t, im, true); window.__pp=0; t.closest('.card').querySelector('.ctl .pp').addEventListener('click',()=>window.__pp++); })()""" % GIF)
    pg.wait_for_timeout(200)
    tap = "(()=>{ const a=document.querySelector('.card a.thumb'); a.click(); %s })()"
    ev(tap % "setTimeout(()=>a.click(), 80);"); pg.wait_for_timeout(600)
    check('double tap on a clip toggles pause once', ev("window.__pp") == 1)
    ev(SETM, 'collapsed'); pg.mouse.move(2, 2); pg.wait_for_timeout(300)
    ev(tap % ""); pg.wait_for_timeout(600)
    check('a single tap on a clip opens its layer, a moment later (not the post)', ev(LAY, 0) == 1 and ev("window.__pp") == 1)
    ev(tap % ""); pg.wait_for_timeout(600)
    check('and another tap closes it', ev(LAY, 0) == 0)
    ev("document.querySelectorAll('.card')[3].querySelector('a.thumb').click()"); pg.wait_for_timeout(400)
    check('a tap on a tile without player controls opens its layer at once', ev(LAY, 3) == 1)
    check('the layer order is Source, Comments, then NSFW, Favourite, Saved, Fullscreen on the right', ev("(()=>{ const l=document.querySelectorAll('.card')[3].querySelector('.layer'); const a=[...l.querySelectorAll('.actions .btn')].map(x=>x.textContent.trim()); const c=[...l.querySelectorAll('.lay-cap > *')].map(x=>x.classList.contains('nsfwb')?'nsfw':x.classList.contains('star')?'star':x.classList.contains('fs')?'fs':'save'); const ar=l.querySelector('.actions').getBoundingClientRect(), cr=l.querySelector('.lay-cap').getBoundingClientRect(); return a[0]==='Source' && a[1]==='Comments' && c.join()==='nsfw,star,save,fs' && ar.left<cr.left; })()"))
    try:
        with pg.context.expect_page(timeout=2000):
            ev("document.querySelectorAll('.card')[3].querySelector('.actions a.btn.primary').click()")
        opened = True
    except Exception:
        opened = False
    check('the Source button goes to the post', opened)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
