"""Touch: interacting with a card's controls or info makes that card the focused one. Run: python tests/touchpin_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n' + ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(12))
SEED = """async(t)=>{ localStorage.clear(); await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode();
  POSTS.forEach((p,i)=>{ META[p.id]={t:'T '+i,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H); pg.wait_for_timeout(1200)
    foc = "[...document.querySelectorAll('.card')].findIndex(c=>c.classList.contains('is-focus'))"
    f0 = ev(foc)
    # pick a visible card other than the focused one
    tgt = ev("(f)=>[...document.querySelectorAll('.card')].findIndex((c,i)=>i!==f && c.getBoundingClientRect().top>60 && c.getBoundingClientRect().bottom<780)", f0)
    check('a different card is on screen to test with (focus %d, target %d)' % (f0, tgt), tgt >= 0)
    ev("(i)=>document.querySelectorAll('.card')[i].querySelector('.star').click()", tgt); pg.wait_for_timeout(200)
    check('tapping a card button focuses that card', ev(foc) == tgt)
    other = ev("(t)=>[...document.querySelectorAll('.card')].findIndex((c,i)=>i!==t && c.getBoundingClientRect().top>60 && c.getBoundingClientRect().bottom<780)", tgt)
    ev("(i)=>document.querySelectorAll('.card')[i].querySelector('.lhandle').click()", other); pg.wait_for_timeout(200)
    check('tapping the handle focuses that card', ev(foc) == other)
    ev("(i)=>document.querySelectorAll('.card')[i].querySelector('.info').click()", tgt); pg.wait_for_timeout(200)
    check('tapping a card\'s info focuses that card', ev(foc) == tgt)
    # a touched card wins even when the card that had focus sits right at the middle of the screen
    ev("""(()=>{ const cs=[...document.querySelectorAll('.card')]; const top=document.querySelector('.deck').getBoundingClientRect().bottom, mid=(top+innerHeight)/2; const d=c=>{const r=c.getBoundingClientRect(); return Math.abs((r.top+r.bottom)/2-mid)}; const near=cs.reduce((a,c)=>d(c)<d(a)?c:a); cs.forEach(c=>c.classList.remove('is-focus')); near.classList.add('is-focus'); focusCard=near; pinned=null; })()""")
    other2 = ev("(()=>{ const f=document.querySelector('.card.is-focus'); return [...document.querySelectorAll('.card')].findIndex(c=>c!==f && c.getBoundingClientRect().top>60 && c.getBoundingClientRect().bottom<780); })()")
    ev("(i)=>document.querySelectorAll('.card')[i].querySelector('a.thumb').click()", other2); pg.wait_for_timeout(300)
    check('a touched card takes focus even from a card sitting at the middle of the screen', ev(foc) == other2)
    ev("window.scrollTo(0, 2000)"); pg.wait_for_timeout(600)
    check('after scrolling far the pin lets go', ev(foc) != tgt)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
