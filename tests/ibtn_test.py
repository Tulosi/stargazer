"""With Card info hidden, desktop cards get the (i) button on hover and it opens the info. Run: python tests/ibtn_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(4))
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach(p=>{ META[p.id]={t:'Title '+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }"""
op = "(()=>+getComputedStyle(document.querySelector('.card .ibtn')).opacity)()"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(800)
    sel = pg.query_selector('#infomode'); pg.select_option('#infomode', 'off') if sel and pg.is_visible('#infomode') else ev("document.getElementById('infomode').value='off'; document.getElementById('infomode').dispatchEvent(new Event('change'))")
    pg.wait_for_timeout(300)
    check('card info is hidden', ev("document.body.classList.contains('info-off')"))
    check('(i) button exists on desktop', ev("getComputedStyle(document.querySelector('.card .ibtn')).display") == 'grid')
    check('(i) button is hidden until hover', ev(op) == 0)
    pg.hover('.card'); pg.wait_for_timeout(900)
    check('(i) button shows on hover', ev(op) == 1)
    pg.click('.card .ibtn'); pg.wait_for_timeout(300)
    check('clicking it opens the info', ev("document.querySelector('.card').classList.contains('info-open')") and ev("getComputedStyle(document.querySelector('.card .info')).display") != 'none')
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    check('stays visible while the info is open', ev(op) == 1)
    pg.hover('.card'); pg.click('.card .ibtn'); pg.wait_for_timeout(300)
    check('clicking again closes it', not ev("document.querySelector('.card').classList.contains('info-open')"))
    ev("document.getElementById('infomode').value='hover'; document.getElementById('infomode').dispatchEvent(new Event('change'))"); pg.wait_for_timeout(300)
    check('no (i) button in the other modes', ev("getComputedStyle(document.querySelector('.card .ibtn')).display") == 'none')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
