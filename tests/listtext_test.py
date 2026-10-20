"""Text posts default on in List, off in Masonry/Grid, unless toggled by hand; the hint note follows. Run: python tests/listtext_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(4))
SEED = """async(t)=>{ localStorage.clear(); await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach((p,i)=>{ META[p.id]= i<2 ? {t:'Words only '+p.id,o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000,w:0,h:0} : {t:'Picture '+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(800)
    txt = lambda: ev("document.querySelectorAll('.card.is-text').length")
    note = lambda: ev("(document.getElementById('layouthint').querySelector('.laynote')||{}).textContent||''")
    lay = lambda l: (ev("document.querySelector('#layoutseg [data-l=%s]').click()" % l), pg.wait_for_timeout(500))
    check('masonry: text hidden, note shown', txt() == 0 and 'default to hidden' in note())
    lay('list')
    check('list: text on by default, box ticked, no note', txt() == 2 and ev("document.getElementById('showtext').checked") and note() == '')
    check('list default is not counted as a changed filter', ev("document.getElementById('showtext').checked") and ev("(document.querySelector('#filtbadge, .badge-count')||{textContent:''}).textContent") in ('', '0'))
    lay('grid')
    check('grid: back to hidden with the note', txt() == 0 and not ev("document.getElementById('showtext').checked") and 'default to hidden' in note())
    lay('list'); pg.click('#showtext') if False else ev("document.getElementById('showtext').click()"); pg.wait_for_timeout(300)
    check('manually turned off in list', txt() == 0)
    lay('masonry'); lay('list')
    check('manual choice is respected across layouts (stays off)', txt() == 0)
    ev("document.getElementById('showtext').click()"); pg.wait_for_timeout(300); lay('grid')
    check('manually on: stays on in grid, no note', txt() == 2 and note() == '')
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
