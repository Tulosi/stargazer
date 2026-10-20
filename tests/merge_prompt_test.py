"""After 30 days without a merge the Source panel asks for a fresh Reddit export. Run: python tests/merge_prompt_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(5))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(400)
    hid = lambda: ev("document.getElementById('mrgHint').hidden")
    pl = lambda: ev("(()=>{ const e=document.getElementById('pullLine'); return {hidden:e.hidden, t:e.textContent, warn:e.dataset.warn}; })()")
    check('a fresh list shows no prompt but states the pull date', hid() and not pl()['hidden'] and 'Last pulled from Reddit' in pl()['t'] and 'today' in pl()['t'] and pl()['warn'] == '0')
    ev("localStorage.setItem('saved-posts-lastmerge', JSON.stringify({x:{t:Date.now()-31*864e5,snooze:0}})); csvInfo()")
    check('after 31 days the prompt shows', not hid())
    check('it names the number of days and links to Reddit', '31 days ago' in pl()['t'] and 'Over 30 days' in pl()['t'] and pl()['warn'] == '1' and 'data-request' in ev("document.querySelector('#mrgHint a').href"))
    ev("document.getElementById('mrgLater').click()")
    check('Remind me later hides it, the dated line stays', hid() and not pl()['hidden'])
    ev("noteMerge('x'); localStorage.setItem('saved-posts-lastmerge', JSON.stringify({x:{t:Date.now()-5*864e5,snooze:0}})); csvInfo()")
    check('a recent merge keeps it hidden', hid())
    ev("noteMerge('x')")
    check('noteMerge restarts the clock', abs(ev("JSON.parse(localStorage.getItem('saved-posts-lastmerge')).x.t") - ev("Date.now()")) < 5000)
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
