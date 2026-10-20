"""UX pass: Theme sits in Filters > View, list facts come before the actions, the Source button shows a dot when the pull is stale, Shuffle is dimmed with no list, phone nav labels are on screen. Run: python tests/uxpass_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n' + ''.join('p%05d,/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(5))
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    check('no list: Shuffle is disabled, Filters is not', ev("document.getElementById('shufflebtn').disabled") and not ev("document.getElementById('decktoggle').disabled"))
    check('first-run order: steps come before Open CSV', ev("(()=>{ const a=document.querySelector('.intro .steps').getBoundingClientRect().top, c=document.getElementById('introOpen').getBoundingClientRect().top; return a<c; })()"))
    ev("async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); startCsvMode(); }", H); pg.wait_for_timeout(500)
    check('Shuffle is enabled once a list is open', not ev("document.getElementById('shufflebtn').disabled"))
    check('Theme lives in the Filters panel, not Source', ev("!!document.querySelector('#panel #theme') && !document.querySelector('#srcpanel #theme')"))
    check('Filters has View and Filter and sort columns', ev("[...document.querySelectorAll('#panel h2')].map(h=>h.textContent).slice(0,2).join('|')") == 'View|Filter and sort')
    ev("document.getElementById('srctoggle').click()"); pg.wait_for_timeout(300)
    check('list facts sit above the Open CSV button', ev("document.getElementById('csvStatus').getBoundingClientRect().top < document.getElementById('csvOpen').getBoundingClientRect().top"))
    check('no dot on a fresh list', not ev("document.getElementById('srctoggle').hasAttribute('data-attn')"))
    ev("localStorage.setItem('saved-posts-lastmerge', JSON.stringify({x:{t:Date.now()-45*864e5,snooze:0,src:'file'}})); csvInfo()")
    check('stale pull puts a dot on Source', ev("document.getElementById('srctoggle').hasAttribute('data-attn')") and 'attention' in ev("document.getElementById('srctoggle').getAttribute('aria-label')"))
    check('only one warning at a time (backup hint hidden)', ev("document.getElementById('expHint').hidden"))
    ev("document.getElementById('mrgLater').click()")
    check('Remind me later clears the dot', not ev("document.getElementById('srctoggle').hasAttribute('data-attn')"))
    m = b.new_page(viewport={'width': 390, 'height': 780}, is_mobile=True, has_touch=True)
    m.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    m.goto(PAGE); m.wait_for_timeout(800)
    check('phone: every nav label is on screen', m.evaluate("[...document.querySelectorAll('.navbtns .nl')].every(e=>e.getBoundingClientRect().bottom <= innerHeight)"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
