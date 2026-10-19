"""The Filters panel shows how many posts in the list are NSFW next to the NSFW label. Run: python tests/nsfwcount_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/%s,0,1000,0\r\n' % (i, i, '?nsfw=1' if i < 3 else '') for i in range(7))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    check('no count with nothing loaded', ev("document.getElementById('nsfwcount').textContent") == '')
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    txt = lambda: ev("document.querySelector('.nsfwlbl').textContent.replace(/\\s+/g,' ').trim()")
    check('label shows NSFW (3) even while NSFW is hidden', txt() == 'NSFW (3)')
    ev("setNsfw('show')"); pg.wait_for_timeout(300)
    check('count does not change with the mode', txt() == 'NSFW (3)')
    ev("toggleNsfw(POSTS.find(p=>!isNsfw(p)))"); pg.wait_for_timeout(500)
    check('marking another post updates the count', txt() == 'NSFW (4)')
    ev("POSTS.forEach(p=>{ if(isNsfw(p)) toggleNsfw(p); }); refresh();"); pg.wait_for_timeout(500)
    check('count disappears at zero', txt() == 'NSFW')
    # text posts count, shown beside the Show text posts toggle
    ev("""()=>{ POSTS.slice(0,2).forEach(p=>{ META[p.id]={t:'Words '+p.id,o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000,w:0,h:0}; }); onMeta(POSTS); refresh(); }"""); pg.wait_for_timeout(500)
    tt = lambda: ev("document.querySelector('label[for=showtext]').textContent.replace(/\\s+/g,' ').trim()")
    check('Show text posts shows how many text posts there are', tt() == 'Show text posts (2)')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
