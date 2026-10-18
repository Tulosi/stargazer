"""First-run screen: Open CSV button and dropping a CSV open a list. Run: python tests/intro_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
CSV = 'id,permalink,starred,updated,deleted\r\n' + ''.join('a%05d,/r/pics/comments/a%05d/t/,0,1,0\r\n' % (i, i) for i in range(3))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 900, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.add_init_script("window.showOpenFilePicker = undefined;")
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""async()=>{ await idbReq('csv','readwrite',s=>s.clear()); await persistRec({id:'e',name:'e.csv',text:'id,permalink,starred,updated,deleted\\r\\n',handle:null,updated:1}); await activate(await idbReq('csv','readonly',s=>s.get('e'))); startCsvMode(); }""")
    pg.wait_for_timeout(400)
    check('intro shows an Open CSV button', pg.is_visible('#introOpen'))
    with pg.expect_file_chooser() as fc: pg.click('#introOpen')
    fc.value.set_files({'name': 'saved_posts.csv', 'mimeType': 'text/csv', 'buffer': CSV.encode()}); pg.wait_for_timeout(600)
    check('button opens the picked CSV', ev("ROWS.length") == 3 and ev("LIB.cur.name") == 'saved_posts.csv')
    ev("""async()=>{ await persistRec({id:'e2',name:'e2.csv',text:'id,permalink,starred,updated,deleted\\r\\n',handle:null,updated:3}); await activate(await idbReq('csv','readonly',s=>s.get('e2'))); startCsvMode(); }""")
    pg.wait_for_timeout(300)
    ev("""(csv)=>{ const dt = new DataTransfer(); dt.items.add(new File([csv],'dropped.csv',{type:'text/csv'}));
      for(const t of ['dragenter','dragover','drop']) window.dispatchEvent(new DragEvent(t,{dataTransfer:dt,bubbles:true,cancelable:true})); }""", CSV)
    pg.wait_for_timeout(700)
    check('dropping a CSV opens it', ev("LIB.cur.name") == 'dropped.csv' and ev("ROWS.length") == 3)
    check('drop veil is dismissed', not pg.is_visible('.dropveil'))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
