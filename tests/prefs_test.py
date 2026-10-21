"""Sort, Starred only, Show text posts (once toggled) and tile size are remembered across visits. Run: python tests/prefs_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(6))
OPEN = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }"""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1100, 'height': 800}); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(OPEN, H + rows); pg.wait_for_timeout(400)
    ev("""()=>{ const s=document.getElementById('sort'); s.value='saved'; s.dispatchEvent(new Event('change')); const f=document.getElementById('favonly'); f.checked=true; f.dispatchEvent(new Event('change')); const t=document.getElementById('showtext'); t.checked=true; t.dispatchEvent(new Event('change')); const z=document.getElementById('size'); z.value=300; z.dispatchEvent(new Event('input')); }""")
    pg.wait_for_timeout(300)
    # a brand-new tab (no sessionStorage) in the same browser
    pg2 = ctx.new_page(); pg2.on('pageerror', lambda e: errs.append(str(e)))
    pg2.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg2.goto(PAGE); pg2.wait_for_timeout(900); e2 = pg2.evaluate
    e2(OPEN, H + rows); pg2.wait_for_timeout(500)
    check('sort remembered', e2("state.sort")=='saved' and e2("document.getElementById('sort').value")=='saved')
    check('Starred only remembered', e2("state.fav")==True and e2("document.getElementById('favonly').checked")==True)
    check('Show text posts remembered', e2("state.showText")==True)
    check('tile size remembered', e2("document.documentElement.style.getPropertyValue('--card')")=='300px' and e2("document.getElementById('size').value")=='300')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
