"""The Subreddit dropdown lists the loaded subreddits and keeps showing the chosen one when picked from a card. Run: python tests/subsel_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
def row(i, sub): return 'p%05d,https://www.reddit.com/r/%s/comments/p%05d/t/,0,1000,0\r\n' % (i, sub, i)
rows = ''.join(row(i, 'pics') for i in range(4)) + ''.join(row(10 + i, 'cats') for i in range(3)) + row(20, 'rare')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    opts = ev("[...document.querySelectorAll('#subsel option')].map(o=>o.value)")
    check('dropdown lists subreddits with 3+ posts, biggest first', opts == ['', 'pics', 'cats'])
    check('option shows the count', 'pics (4)' in ev("document.querySelector('#subsel option[value=pics]').textContent"))
    ev("state.sub='cats'; document.getElementById('subsel').value='cats'; refresh();"); pg.wait_for_timeout(200)
    check('choosing from the dropdown filters and keeps the label', ev("list.length") == 3 and ev("document.getElementById('subsel').selectedOptions[0].textContent").startswith('r/cats'))
    ev("state.sub='rare'; document.getElementById('subsel').value='rare'; refresh();"); pg.wait_for_timeout(200)
    check('a small subreddit chosen from a card still shows its name', ev("document.getElementById('subsel').selectedOptions[0].value") == 'rare' and ev("list.length") == 1)
    ev("state.sub=''; refresh();"); pg.wait_for_timeout(200)
    check('clearing returns to All subreddits', ev("document.getElementById('subsel').value") == '')
    # clicking a subreddit name on a card filters, says so, and offers a way back
    ev("state.sub=''; refresh();"); pg.wait_for_timeout(200)
    check('card subreddit button explains itself', 'Show only r/' in (ev("document.querySelector('.card .meta .sub').title") or ''))
    pg.click('.card .meta .sub'); pg.wait_for_timeout(300)
    sub = ev("state.sub")
    check('clicking filters to that subreddit', bool(sub) and ev("list.every(p=>p.sub===state.sub)") and ev("document.getElementById('subsel').value") == sub)
    check('toast says what happened', ('Showing only r/' + sub) in ev("document.getElementById('toast').textContent"))
    pg.click('#toast .tact'); pg.wait_for_timeout(300)
    check('Show all clears the filter and the dropdown', ev("state.sub") == '' and ev("document.getElementById('subsel').value") == '')
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
