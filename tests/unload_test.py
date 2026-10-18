"""Unload CSV removes the active list from this browser; the account hint says sign-in is optional. Run: python tests/unload_test.py (network blocked)"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
A = H + 'aaa111,/r/pics/comments/aaa111/one/,0,1000,0\r\nbbb222,/r/pics/comments/bbb222/two/,1,1000,0\r\n'
B = H + 'ccc333,/r/aww/comments/ccc333/three/,0,1000,0\r\n'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 400, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1000); ev = pg.evaluate
    pg.click('#srctoggle')
    pg.evaluate("document.getElementById('acct').open=true")
    check('signed out: account is marked optional and needed only for sync', pg.is_visible('#acHint') and 'Optional' in pg.inner_text('#acHint') and 'sync' in pg.inner_text('#acHint'))
    pg.evaluate("document.getElementById('csvMore').open=true")
    check('empty starting list: Unload is disabled', ev("$('csvUnload').disabled"))
    ev("""async([a,b])=>{
      await idbReq('csv','readwrite',s=>s.delete('builtin'));   // start from just the two test lists
      for(const [id,name,text] of [['csv-a','a.csv',a],['csv-b','b.csv',b]]) await persistRec({id,name,text,handle:null,updated:Date.now()});
      await activate(await idbReq('csv','readonly',s=>s.get('csv-b'))); startCsvMode();
    }""", [A, B]); pg.wait_for_timeout(300)
    check('list with posts: Unload is enabled', not ev("$('csvUnload').disabled") and ev("LIB.cur.name") == 'b.csv')
    (pg.evaluate("document.getElementById('csvMore').open=true"), pg.click('#csvUnload')); pg.wait_for_timeout(200)
    check('confirm warns a browser-only list will be lost and offers a download', 'only in this browser' in pg.inner_text('#cBody') and pg.is_visible('#cOptWrap'))
    pg.click('button[value=cancel]'); pg.wait_for_timeout(200)
    check('cancel keeps the list', ev("LIB.cur.name") == 'b.csv' and ev("ROWS.length") == 1)
    (pg.evaluate("document.getElementById('csvMore').open=true"), pg.click('#csvUnload')); pg.wait_for_timeout(200)
    with pg.expect_download() as dl:
        pg.check('#cOpt'); pg.click('#cOk')
    pg.wait_for_timeout(400)
    check('download a copy first saves the CSV', dl.value.suggested_filename == 'b.csv')
    check('next list in the library becomes active', ev("LIB.cur.name") == 'a.csv' and ev("ROWS.length") == 2 and 'Unloaded "b.csv"' in pg.inner_text('#csvStatus'))
    check('unloaded list is gone from the library', ev("(async()=>(await libAll()).map(r=>r.name))()") == ['a.csv'] and 'b.csv' not in pg.inner_text('#csvSel'))
    (pg.evaluate("document.getElementById('csvMore').open=true"), pg.click('#csvUnload')); pg.wait_for_timeout(200); pg.click('#cOk'); pg.wait_for_timeout(400)
    check('unloading the last list leaves an empty one', ev("ROWS.length") == 0 and 'empty' in pg.inner_text('#csvStatus') and ev("$('csvUnload').disabled"))
    pg.reload(); pg.wait_for_timeout(1000)
    check('after reload the unloaded lists stay gone', ev("ROWS.length") == 0 and ev("(async()=>(await libAll()).length)()") == 1)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
