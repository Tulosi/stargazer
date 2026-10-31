"""A refresh keeps filters/search/scroll for the tab; Back closes the full screen viewer; swiping down closes it. Run: python tests/view_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
CSV = 'id,permalink,starred,updated,deleted\r\n' + ''.join('a%05d,/r/pics/comments/a%05d/post_number_%d/,%d,1,0\r\n' % (i, i, i, 1 if i % 3 == 0 else 0) for i in range(60))
import base64
PNGB = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
PNG = 'https://i.redd.it/test.png'
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 400, 'height': 700}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else (r.fulfill(status=200, content_type='image/png', body=PNGB) if 'i.redd.it' in r.request.url else r.abort()))
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }""", CSV)
    pg.wait_for_timeout(600)
    ev("document.getElementById('favonly').click()"); pg.wait_for_timeout(300)
    ev("(()=>{ const q=document.getElementById('q'); q.value='post'; q.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(700)
    check('filters applied before refresh', ev("state.fav") is True and ev("state.q") == 'post')
    pg.reload(); pg.wait_for_timeout(1500)
    check('refresh keeps starred-only and the search text', ev("state.fav") is True and ev("state.q") == 'post' and ev("document.getElementById('q').value") == 'post')
    # viewer
    ev("""()=>{ const p=POSTS[0]; META[p.id]={t:'x',o:0,th:'',m:'video',u:'',yt:'abcdefghijk',n:0,s:0,a:'',c:0}; openViewer(p); }"""); pg.wait_for_timeout(600)
    check('viewer is open and a history step was added', ev("!document.getElementById('viewer').hidden") and ev("VIEW.hist") is True)
    ev("history.back()"); pg.wait_for_timeout(500)
    check('Back closes the viewer and stays on the page', ev("document.getElementById('viewer').hidden") is True and 'index.html' in pg.url)
    ev("""()=>{ openViewer(POSTS[0]); const im=new Image(); im.src='%s'; VIEW.stage.appendChild(im); }""" % PNG); pg.wait_for_timeout(700)
    ev("""()=>{ const st=VIEW.stage; const im=st.querySelector('img'); const mk=(t,y)=>new Touch({identifier:1,target:im,clientX:200,clientY:y});
      const fire=(type,y)=>im.dispatchEvent(new TouchEvent(type,{touches:type==='touchend'?[]:[mk(type,y)],changedTouches:[mk(type,y)],bubbles:true,cancelable:true}));
      fire('touchstart',200); fire('touchmove',260); fire('touchmove',360); fire('touchend',360); }""")
    pg.wait_for_timeout(500)
    check('swiping down no longer closes the viewer (it goes to the previous post; the first post has none)', ev("document.getElementById('viewer').hidden") is False)
    check('no page errors', not errs)
    if errs: print(errs)
    b.close()
raise SystemExit(1 if bad else 0)
