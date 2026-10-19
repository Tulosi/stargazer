"""Comment counts link to the comments page, and no card ever links to an archive's raw JSON. Run: python tests/links_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(4))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1100, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("""async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); }""", H + rows)
    pg.wait_for_timeout(500)
    ev("""()=>{ const base={o:0,th:'',m:'image',u:'',n:14,s:5,a:'',c:1700000000,w:400,h:300};
      META['p00000']=Object.assign({},base,{t:'Live post',u:'https://i.redd.it/a.jpg'});
      META['p00001']=Object.assign({},base,{t:'Recovered, no media',m:'text',rec:'Arctic Shift'});
      META['p00002']=Object.assign({},base,{t:'Recovered with Wayback',m:'text',rec:'PullPush',wb:'https://web.archive.org/web/2020/https://old.reddit.com/r/pics/comments/p00002/'});
      META['p00003']=Object.assign({},base,{t:'Odd source',m:'image',th:'https://i.redd.it/x.jpg',u:'https://arctic-shift.photon-reddit.com/api/posts/ids?ids=p00003'});
      state.showText=true; document.getElementById('showtext').checked=true; onMeta(POSTS); refresh(); }""")
    pg.wait_for_timeout(600)
    hrefs = ev("""()=>{ const o={}; document.querySelectorAll('#grid .card').forEach(c=>{ const id=c._p.id; o[id]={cm:(c.querySelector('a.cm')||{}).href||'', all:[...c.querySelectorAll('a[href]')].map(a=>a.href)}; }); return o; }""")
    check('comment count is a link', all(v['cm'] for v in hrefs.values()))
    check('live post: comments link to its Reddit page', hrefs['p00000']['cm']=='https://www.reddit.com/r/pics/comments/p00000/')
    check('recovered post without a Wayback copy: Wayback address (the reader opens on click)', hrefs['p00001']['cm'].startswith('https://web.archive.org/web/') and 'p00001' in hrefs['p00001']['cm'])
    check('Reveddit is not used anywhere', not any('reveddit.com' in u for v in hrefs.values() for u in v['all']))
    check('recovered post with a Wayback copy: that copy', hrefs['p00002']['cm'].startswith('https://web.archive.org/'))
    check('no link on any card is an archive API/JSON address', not any('/api/' in u or 'api.pullpush.io' in u for v in hrefs.values() for u in v['all']))
    check('a post whose source is an archive JSON address does not offer it', not any('arctic-shift' in u for u in hrefs['p00003']['all']))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
