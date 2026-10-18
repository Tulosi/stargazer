"""Cards built before their preview data arrives get their image when it does; on touch screens a short first card at the top is in focus. Run: python tests/first_load_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(6))
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 400, 'height': 800}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(300)
    check('cards start without previews', ev("document.querySelectorAll('#grid .card .thumb img').length") == 0)
    ev("""()=>{ const ch = POSTS.slice(0,6); ch.forEach(p=>{ META[p.id] = {t:'T'+p.id,o:0,th:'https://i.redd.it/'+p.id+'.jpg',m:'image',u:'https://i.redd.it/'+p.id+'.jpg',n:0,s:0,a:'',c:0}; }); onMeta(ch); }""")
    pg.wait_for_timeout(300)
    check('after preview data arrives the visible cards have an image to load', ev("document.querySelectorAll('#grid .card .thumb img').length") >= 1)
    ev("""()=>{ const g=$('grid'); [...g.children].forEach((c,i)=>{ c.style.height = (i===0?60:500)+'px'; c.style.minHeight = '0'; }); scrollTo(0,0); schedFocus(); }""")
    pg.wait_for_timeout(300)
    check('short first card at the top is in focus', ev("$('grid').firstElementChild.classList.contains('is-focus')"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
