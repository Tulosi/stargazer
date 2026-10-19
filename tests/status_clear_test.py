"""The 'Recovered N removed posts' message (and other status text) is cleared when the list is unloaded or the account signs out. Run: python tests/status_clear_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(3))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    msg = lambda: ev("document.getElementById('recText').textContent + document.getElementById('loadText').textContent")
    ev("""()=>{ document.getElementById('recText').textContent='Recovered 265 removed posts from archives'; document.getElementById('loadText').textContent='3 posts loaded'; document.getElementById('loadBar').style.width='100%'; }""")
    check('message is showing', 'Recovered 265' in msg())
    # unload the list: confirm dialog, then it is replaced by an empty one
    ev("document.getElementById('csvUnload').click()"); pg.wait_for_timeout(300)
    pg.click('#cOk'); pg.wait_for_timeout(1200)
    check('unloading the list clears the message', msg()=='' and ev("document.getElementById('loadBar').style.width") in ('0px','0'))
    check('the status strip is hidden when nothing is left to report', not ev("(()=>{ const s=document.querySelector('.status'); return s && getComputedStyle(s).display!=='none'; })()"))
    # a recovery that finishes after the list changed must not write into the new one
    ev("""async()=>{ const gen = loadGen; startCsvMode(); window.__late = ()=>{ const t = document.getElementById('recText'); if(gen===loadGen) t.textContent='late write'; }; }"""); pg.wait_for_timeout(200)
    ev("window.__late()")
    check('a stale recovery cannot write into a newer list', 'late write' not in msg())
    # sign out path clears too
    ev("""()=>{ document.getElementById('recText').textContent='Recovered 9 removed posts from archives'; clearStatus(); }""")
    check('clearStatus empties the message', msg()=='')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
