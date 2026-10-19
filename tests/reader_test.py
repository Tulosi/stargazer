"""Posts recovered from an archive open in the built-in reader (text, comments on request), never a raw JSON page. Run: python tests/reader_test.py"""
import os, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(3))
COMMENTS = {'data': [
  {'id': 'c1', 'parent_id': 't3_p00000', 'author': 'alice', 'score': 12, 'created_utc': 1700000000, 'body': 'Top level comment'},
  {'id': 'c2', 'parent_id': 't1_c1', 'author': 'bob', 'score': 3, 'created_utc': 1700000100, 'body': 'A reply'},
  {'id': 'c3', 'parent_id': 't3_p00000', 'author': '[deleted]', 'score': 1, 'created_utc': 1700000200, 'body': '[removed]'}]}
mode = {'comments': 'ok'}; hits = []
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    hits.append(u)
    if 'comments/search' in u:
        if mode['comments'] == 'ok': return r.fulfill(body=json.dumps(COMMENTS), content_type='application/json')
        return r.abort()
    if 'posts/ids' in u: return r.fulfill(body=json.dumps({'data': [{'id': 'p00001', 'title': 'Recovered', 'selftext': 'Late text from the archive'}]}), content_type='application/json')
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', route)
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    ev("""()=>{ const base={o:0,th:'',m:'text',u:'',n:14,s:5,a:'dusk_walker',c:1700000000,w:0,h:0};
      META['p00000']=Object.assign({},base,{t:'Recovered with text',rec:'Arctic Shift',x:'First paragraph of the post.\\n\\nSecond paragraph.'});
      META['p00001']=Object.assign({},base,{t:'Recovered, text kept only later',rec:'PullPush'});
      META['p00002']=Object.assign({},base,{t:'From a Wayback snapshot',rec:'Wayback',wb:'https://web.archive.org/web/2020/https://old.reddit.com/r/pics/comments/p00002/'});
      state.showText=true; document.getElementById('showtext').checked=true; onMeta(POSTS); refresh(); }""")
    pg.wait_for_timeout(600)
    card = lambda id: "#grid .card:has(a.cm)" 
    # 1. comment count on a recovered post opens the reader
    ev("""()=>{ [...document.querySelectorAll('#grid .card')].find(c=>c._p.id==='p00000').querySelector('a.cm').click(); }""")
    pg.wait_for_timeout(300)
    check('comment count opens the reader', ev("document.getElementById('reader').open"))
    check('reader shows title, author and the saved text', 'Recovered with text' in pg.inner_text('#rdTitle') and 'dusk_walker' in pg.inner_text('#rdMeta') and 'Second paragraph.' in pg.inner_text('#rdBody'))
    check('reader links are readable pages (Wayback, Reddit), not JSON', all(('web.archive.org' in u or 'www.reddit.com' in u) for u in ev("[...document.querySelectorAll('#rdLinks a')].map(a=>a.href)")))
    # 2. comments on request, as a tree
    pg.click('#rdCm button'); pg.wait_for_timeout(500)
    txt = pg.inner_text('#rdCm')
    check('comments load on request and nest replies', 'Top level comment' in txt and 'A reply' in txt and ev("!!document.querySelector('#rdCm .rc .rc')"))
    check('removed comment shown as [removed]', '[removed]' in txt)
    pg.click('#rdClose'); pg.wait_for_timeout(200)
    check('close button closes the reader', not ev("document.getElementById('reader').open"))
    # 3. failure is graceful and retryable
    mode['comments'] = 'fail'
    ev("""()=>{ [...document.querySelectorAll('#grid .card')].find(c=>c._p.id==='p00000').querySelector('a.cm').click(); }"""); pg.wait_for_timeout(300)
    pg.click('#rdCm button'); pg.wait_for_timeout(1500)
    check('unreachable archive: message and a retry button', 'could not be reached' in pg.inner_text('#rdCm') and 'Try again' in pg.inner_text('#rdCm'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    # 4. text missing from an earlier recovery is fetched once
    ev("""()=>{ [...document.querySelectorAll('#grid .card')].find(c=>c._p.id==='p00001').querySelector('a.cm').click(); }"""); pg.wait_for_timeout(900)
    check('missing text is fetched from the archive', 'Late text from the archive' in pg.inner_text('#rdBody'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    # 5. a Wayback snapshot opens the snapshot, not the reader
    h = ev("""()=>[...document.querySelectorAll('#grid .card')].find(c=>c._p.id==='p00002').querySelector('a.cm').href""")
    check('Wayback-recovered post links straight to its snapshot', h.startswith('https://web.archive.org/web/2020/'))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
