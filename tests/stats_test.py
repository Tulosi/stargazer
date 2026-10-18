"""Sticky Active / Retrieved / Total counts under the logo bar; bracketed notes only on hover. Run: python tests/stats_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(40))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 900, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(600)
    ev("""()=>{ POSTS.slice(0,25).forEach(p=>{ META[p.id] = {t:'T'+p.id,o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:0}; }); POSTS.slice(25,30).forEach(p=>{ META[p.id] = {t:'',o:0,th:'',m:'removed',u:'',n:0,s:0,a:'',c:0,miss:1}; }); refresh(); }""")
    pg.wait_for_timeout(400)
    check('strip visible', pg.is_visible('#stats'))
    check('total is every item in the source', pg.inner_text('#stAll') == '40')
    check('retrieved excludes items the archives could not return', pg.inner_text('#stGot') == '25')
    check('active excludes filtered results (text posts hidden by default)', int(pg.inner_text('#stActive')) < 40)
    check('notes hidden until hover', not pg.is_visible('#stats .st em'))
    pg.hover('#stats .st'); pg.wait_for_timeout(150)
    check('note shows on hover', pg.is_visible('#stats .st em') and 'Excludes filtered' in pg.inner_text('#stats .st em'))
    ev("scrollTo(0,400)"); pg.wait_for_timeout(200)
    check('strip stays on screen when scrolled', ev("document.getElementById('stats').getBoundingClientRect().top") < 120)
    check('no page errors', not errs)
    pg.screenshot(path=os.environ.get('SHOT','/tmp/stats.png'))
    b.close()
raise SystemExit(1 if bad else 0)
