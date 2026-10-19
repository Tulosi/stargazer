"""On a touch screen the card in focus gets a faint ring (Masonry/Grid), not on desktop or in List. Run: python tests/focusring_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(6))
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach(p=>{ META[p.id]={t:'T'+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); onMeta(POSTS); }"""
ring = "(()=>{ const c=document.querySelector('.card.is-focus'); if(!c) return -1; return +getComputedStyle(c,'::after').opacity; })()"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(1200)
    check('phone: one card is in focus and its ring shows', ev("document.querySelectorAll('.card.is-focus').length") == 1 and ev(ring) == 1)
    check('phone: other cards show no ring', ev("[...document.querySelectorAll('.card:not(.is-focus)')].every(c=>+getComputedStyle(c,'::after').opacity===0)"))
    ev("window.scrollTo(0, 400)"); pg.wait_for_timeout(900)
    check('phone: after scrolling still exactly one ringed card', ev("document.querySelectorAll('.card.is-focus').length") == 1 and ev(ring) == 1)
    ev("setLayout && setLayout('list')") if ev("typeof setLayout")=='function' else ev("document.body.classList.add('layout-list')"); pg.wait_for_timeout(500)
    check('phone List: no focus ring', ev("document.body.classList.contains('layout-list')") and ev("[...document.querySelectorAll('.card.is-focus')].every(c=>getComputedStyle(c,'::after').boxShadow.indexOf('inset 0px 0px 0px 2px')<0 || +getComputedStyle(c,'::after').opacity===0)"))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
