"""With Auto-play off a clip plays only while hovered or keyboard-focused: clicking a tile with the mouse and moving away must stop it. Run: python tests/focusplay_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800)
    csv = 'id,permalink,starred,updated,deleted\r\n' + ''.join('v%05d,https://www.reddit.com/r/gifs/comments/v%05d/a/,0,1000,0\r\n' % (i, i) for i in range(3))
    pg.evaluate("async(t)=>{ await persistRec({id:'demo',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; startCsvMode(); }", csv); pg.wait_for_timeout(700)
    pg.evaluate("()=>{ POSTS.forEach((p,i)=>{ META[p.id]={t:'Clip '+i,o:0,th:'https://b.thumbs.redditmedia.com/t.jpg',m:'video',u:'https://i.imgur.com/abc123'+i+'.mp4',v:'https://i.imgur.com/abc123'+i+'.mp4',n:3,s:10,a:'u',c:1,w:160,h:120}; }); refresh(); }"); pg.wait_for_timeout(2000)
    pg.evaluate("()=>{ state.hideBroken=false; refresh(); }"); pg.wait_for_timeout(300)
    st = lambda: pg.evaluate("()=>[...document.querySelectorAll('.card')].map(c=>!!c.querySelector('.thumb')._playing)")
    check('only Autoplay active card is on in this test', pg.evaluate("auto.hover===true && auto.all===false && auto.focus===false"))
    bx = pg.query_selector_all('.card')[0].bounding_box(); cx, cy = bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 3
    pg.mouse.move(cx, cy); pg.wait_for_timeout(500); check('hover plays the clip', st()[0])
    pg.mouse.move(5, 700); pg.wait_for_timeout(500); check('moving away stops it', not st()[0])
    pg.mouse.click(cx, cy); pg.wait_for_timeout(500); pg.mouse.move(5, 700); pg.wait_for_timeout(1500)
    check('after a mouse click and moving away the clip is stopped (focus is not hover)', not st()[0])
    pg.evaluate("document.activeElement && document.activeElement.blur()"); pg.keyboard.press('Shift'); pg.evaluate("document.querySelector('.card a.thumb').focus()")
    pg.wait_for_timeout(100); check('keyboard focus on a tile still plays its clip', any(st()))
    pg.evaluate("document.activeElement && document.activeElement.blur()"); pg.mouse.move(5, 700); pg.wait_for_timeout(400)
    check('Play on hover toggle exists and is on by default', pg.evaluate("document.getElementById('autohover').checked && auto.hover===true"))
    pg.evaluate("(()=>{ const c=document.getElementById('autohover'); c.checked=false; c.dispatchEvent(new Event('change')); })()")
    pg.mouse.move(cx, cy); pg.wait_for_timeout(500); check('with Play on hover off, hovering does not play', not st()[0])
    pg.mouse.dblclick(cx, cy); pg.wait_for_timeout(600); check('with it off, a double click starts the clip by hand', st()[0])
    pg.mouse.move(5, 700); pg.wait_for_timeout(1300); check('a clip started by hand keeps playing when the pointer leaves', st()[0])
    pg.evaluate("(()=>{ const t=document.querySelector('.card .thumb'); t._manual=false; syncPlay(t); })()"); pg.mouse.move(cx, cy)
    pg.evaluate("(()=>{ const c=document.getElementById('autohover'); c.checked=true; c.dispatchEvent(new Event('change')); })()")
    pg.wait_for_timeout(500); check('turning it back on plays the hovered clip', st()[0])
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
