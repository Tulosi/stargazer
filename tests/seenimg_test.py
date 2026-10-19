"""Pictures that loaded before skip the paced image queue, so a refresh shows them at once. Run: python tests/seenimg_test.py"""
import os, base64
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(12))
def run(pg, seed):
    pg.goto(PAGE); pg.wait_for_timeout(600); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(400)
    ev("""()=>{ POSTS.forEach((p,i)=>{ META[p.id] = {t:'T'+i,o:0,th:'https://i.redd.it/'+i+'.png',m:'image',u:'',n:0,s:0,a:'',c:0,w:400,h:400}; }); state.hideBroken=false; refresh(); }""")
    return ev
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1100, 'height': 900}); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.fulfill(body=PNG, content_type='image/png') if 'redd.it' in r.request.url else (r.continue_() if r.request.url.startswith('file:') else r.abort()))
    ev = run(pg, False)
    pg.wait_for_timeout(7500)
    n1 = ev("document.querySelectorAll('#grid .card img.still, #grid .card .thumb img').length")
    check('first visit: pictures load through the queue', n1 >= 6)
    check('loaded pictures are remembered (hashes only)', ev("localStorage.getItem('saved-posts-seenimg')") not in (None, '[]') and 'redd.it' not in ev("localStorage.getItem('saved-posts-seenimg')"))
    pg.wait_for_timeout(1800)
    ev = run(pg, True)
    pg.wait_for_timeout(1300)   # well under the ~3.5 s that 12 paced starts would take (180-430 ms apart)
    n2 = ev("document.querySelectorAll('#grid .card .thumb img').length")
    check('after a reload the pictures appear at once, unpaced', n2 >= 10)
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
