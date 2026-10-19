"""A CSV list opens sorted newest first (Saved order stays available). Run: python tests/sort_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(6))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    check('sort defaults to Newest posts', ev("state.sort")=='new' and ev("document.getElementById('sort').value")=='new')
    check('Saved order is still offered', ev("!document.querySelector('#sort option[value=saved]').disabled"))
    # post p00002 is the newest, p00004 the oldest, regardless of the saved order
    ev("""()=>{ const t={p00000:300,p00001:500,p00002:900,p00003:400,p00004:100,p00005:700}; POSTS.forEach(p=>{ META[p.id]={t:'T'+p.id,o:0,th:'https://i.redd.it/a.jpg',m:'image',u:'',n:0,s:0,a:'',c:t[p.id]*1e6,w:400,h:300}; }); refresh(); }""")
    pg.wait_for_timeout(500)
    order = ev("list.map(p=>p.id)")
    check('newest post comes first, oldest last', order[0]=='p00002' and order[-1]=='p00004')
    ev("""()=>{ const s=document.getElementById('sort'); s.value='saved'; s.dispatchEvent(new Event('change')); }"""); pg.wait_for_timeout(300)
    check('choosing Saved order restores the file order', ev("list.map(p=>p.id)")[0]=='p00000')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
