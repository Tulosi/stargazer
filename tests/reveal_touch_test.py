"""On a touch screen the Reveal button unblurs an NSFW card and Blur blurs it again. Run: python tests/reveal_touch_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/?nsfw=1,0,1000,0\r\n' % (i, i) for i in range(2))
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach(p=>{ META[p.id]={t:'T'+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; setNsfw('blur'); onMeta(POSTS); refresh(); }"""
filt = "(()=>getComputedStyle(document.querySelector('.card .thumb.nsfw img')).filter)()"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(1500)
    check('starts blurred', 'blur' in ev(filt))
    pg.tap('.card .reveal'); pg.wait_for_timeout(500)
    check('Reveal unblurs and the button says Blur', ev(filt) == 'none' and ev("document.querySelector('.card .reveal').textContent") == 'Blur')
    pg.tap('.card .reveal'); pg.wait_for_timeout(500)
    check('Blur blurs it again and the button says Reveal', 'blur' in ev(filt) and ev("document.querySelector('.card .reveal').textContent") == 'Reveal')
    pg.tap('.card .reveal'); pg.wait_for_timeout(500)
    check('and Reveal works a second time', ev(filt) == 'none')
    ev("(()=>{ const el=document.querySelector('.card'); fillCard(el, el._p); })()"); pg.wait_for_timeout(300)
    check('a card rebuild keeps a revealed card revealed', ev(filt) == 'none' and ev("document.querySelector('.card .reveal').textContent") == 'Blur')
    pg.tap('.card .reveal'); pg.wait_for_timeout(500)
    check('and Blur still works after a rebuild', 'blur' in ev(filt))
    ev("setNsfw('show'); setNsfw('blur')"); pg.wait_for_timeout(400)
    check('changing the NSFW mode blurs everything again', 'blur' in ev(filt))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
