"""Text-only posts always show their title in Masonry/Grid, even with Card info hidden or on hover. Run: python tests/texttitle_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(4))
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach((p,i)=>{ META[p.id]= i<2 ? {t:'Words only '+p.id,o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000,w:0,h:0} : {t:'Picture '+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; state.showText=true; document.getElementById('showtext').checked=true; onMeta(POSTS); refresh(); }"""
vis = lambda kind: "(()=>{ const c=document.querySelector('.card%s'); const i=c.querySelector('.info'); const s=getComputedStyle(i); return s.display!=='none' && +s.opacity===1; })()" % kind
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(1000)
    check('text cards are marked', ev("document.querySelectorAll('.card.is-text').length") == 2)
    for mode in ('off', 'hover'):
        ev("document.getElementById('infomode').value='%s'; document.getElementById('infomode').dispatchEvent(new Event('change'))" % mode); pg.wait_for_timeout(400)
        check('info mode %s: text card shows its title' % mode, ev(vis('.is-text')) and ev("document.querySelector('.card.is-text .title').textContent").startswith('Words only'))
        check('info mode %s: picture card still follows the setting' % mode, not ev(vis(':not(.is-text)')))
    ev("document.getElementById('infomode').value='show'; document.getElementById('infomode').dispatchEvent(new Event('change'))"); pg.wait_for_timeout(300)
    check('info mode show: both visible', ev(vis('.is-text')) and ev(vis(':not(.is-text)')))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
