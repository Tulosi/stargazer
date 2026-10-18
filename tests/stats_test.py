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
    check('hidden-by-filters note explains the gap', ev("document.getElementById('summary').textContent.includes('hidden by filters')") )
    check('Filters button carries a count of active rules', ev("document.getElementById('decktoggle').dataset.n") not in (None, '0'))
    check('card shows a title strip when card info is off', ev("(()=>{ document.body.classList.add('info-off'); document.body.classList.remove('info-hover'); const t=document.querySelector('#grid .card .thumb .tstrip'); return !!t && getComputedStyle(t).display==='block'; })()"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    pg.click('#rvw'); pg.wait_for_timeout(250)
    check('Review opens the Filters panel and it stays open', not ev("document.body.classList.contains('deck-collapsed')"))
    ev("document.getElementById('rvw').click()"); pg.wait_for_timeout(250)   # on a wide screen the open panel covers the button; on phones it stays reachable above the sheet
    check('Review again closes it', ev("document.body.classList.contains('deck-collapsed')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    check('notes hidden until hover', not pg.is_visible('#stats .st em'))
    pg.hover('#stats .st'); pg.wait_for_timeout(150)
    check('note shows on hover', pg.is_visible('#stats .st em') and 'Excludes filtered' in pg.inner_text('#stats .st em'))
    ev("scrollTo(0,400)"); pg.wait_for_timeout(200)
    check('strip stays on screen when scrolled', ev("document.getElementById('stats').getBoundingClientRect().top") < 120)
    # phone: folds to one line on scroll down, stays folded on scroll up, opens only at the very top
    m = b.new_page(viewport={'width': 400, 'height': 700}); m.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    m.goto(PAGE); m.wait_for_timeout(800)
    m.evaluate("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }""", H + rows * 1)
    m.wait_for_timeout(600)
    m.evaluate("document.body.style.minHeight='3000px'"); m.wait_for_timeout(200)
    r = m.evaluate("""()=>{ const l=document.querySelector('.brand').getBoundingClientRect(), s=document.getElementById('stats').getBoundingClientRect(), d=document.querySelector('.deck').getBoundingClientRect(); return [l.top, l.bottom, s.top, s.bottom, s.right, innerWidth, d.height]; }""")
    check('phone: counts sit beside the logo on one row', r[2] < r[1] and r[3] > r[0])
    check('phone: counts are right-aligned', r[5] - r[4] < 24)
    check('phone: header is a single slim row', r[6] < 60)
    for y in (60, 200): m.evaluate("y=>scrollTo(0,y)", y); m.wait_for_timeout(150)
    check('phone: header height does not change while scrolling', abs(m.evaluate("document.querySelector('.deck').getBoundingClientRect().height") - r[6]) < 1)
    m.evaluate("""()=>{ POSTS.forEach((p,i)=>{ META[p.id] = {t:'t',o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:0}; }); }""")
    check('no page errors', not errs)
    pg.screenshot(path=os.environ.get('SHOT','/tmp/stats.png'))
    b.close()
raise SystemExit(1 if bad else 0)
