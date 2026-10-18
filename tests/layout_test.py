"""Layout switch: masonry by default, Grid makes every tile the same size. Run: python tests/layout_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(12))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(600)
    ev("""()=>{ POSTS.forEach((p,i)=>{ META[p.id] = {t:'T'+i,o:0,th:'https://i.redd.it/a.jpg',m:'img',u:'',n:0,s:0,a:'',c:0,w:i%2?1600:400,h:i%2?400:900}; }); refresh(); }""")
    pg.wait_for_timeout(400)
    ev('relayoutAll()')
    rows_ = lambda: ev("[...new Set([...document.querySelectorAll('#grid .card')].map(c=>c.style.gridRow))]")
    check('masonry is the default', ev("LAYOUT")=='masonry' and ev("document.querySelector('#layoutseg [data-l=masonry]').getAttribute('aria-pressed')")=='true')
    check('cards present', ev("document.querySelectorAll('#grid .card').length") > 5)
    check('masonry has mixed heights', len(rows_()) > 1)
    ev("document.querySelector('#layoutseg [data-l=grid]').click()")
    check('grid: all tiles same size', len(rows_()) == 1 and ev("[...document.querySelectorAll('#grid .card')].every(c=>!c.style.gridColumn)"))
    pg.reload(); pg.wait_for_timeout(800)
    check('grid choice is remembered', ev("LAYOUT")=='grid')
    ev("document.querySelector('#layoutseg [data-l=masonry]').click()")
    check('back to masonry', ev("LAYOUT")=='masonry')
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
