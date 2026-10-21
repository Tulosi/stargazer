"""Autoplay all media in viewport: plays everything on screen (no cap), stops what scrolls away, off by default. Run: python tests/autoplayall_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
N = 60
H = 'id,permalink,starred,updated,deleted\r\n' + ''.join('v%05d,https://www.reddit.com/r/vids/comments/v%05d/t/,0,1000,0\r\n' % (i, i) for i in range(N))
SEED = """async(t)=>{ localStorage.clear(); await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode();
  POSTS.forEach((p,i)=>{ META[p.id]={t:'Clip '+i,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'video',u:'https://v.redd.it/'+i+'/DASH_360.mp4',n:0,s:0,a:'',c:1700000000,w:400,h:300,v:'https://v.redd.it/'+i+'/DASH_360.mp4'}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }"""
INVIEW = "[...document.querySelectorAll('.thumb[data-v]')].filter(t=>t._inView)"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 700}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H); pg.wait_for_timeout(1500)
    check('the toggle exists, is off by default and carries a warning', ev("!document.getElementById('autoplayall').checked") and 'resource intensive' in ev("document.getElementById('apwarn').textContent"))
    n_view = ev("%s.length" % INVIEW)
    check('there are clips in view to test with', n_view > 3)
    check('off: nothing plays on its own', ev("%s.filter(t=>t._playing).length" % INVIEW) == 0)
    ev("(()=>{ const c=document.getElementById('autoplayall'); c.checked=true; c.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(800)
    check('on: every clip in view plays (even past the normal cap)', ev("%s.every(t=>t._playing)" % INVIEW) and ev("%s.length" % INVIEW) > 3)
    check('on: clips out of view do not play', ev("[...document.querySelectorAll('.thumb[data-v]')].filter(t=>!t._inView && t._playing).length") == 0)
    ev("window.scrollTo(0, 3000)"); pg.wait_for_timeout(1200)
    check('scrolled away: the earlier clips stop and the new ones play', ev("[...document.querySelectorAll('.thumb[data-v]')].filter(t=>!t._inView && t._playing).length") == 0 and ev("%s.every(t=>t._playing)" % INVIEW))
    ev("(()=>{ const c=document.getElementById('autoplayall'); c.checked=false; c.dispatchEvent(new Event('change')); })()"); pg.wait_for_timeout(600)
    check('off again: everything stops', ev("[...document.querySelectorAll('.thumb[data-v]')].filter(t=>t._playing).length") == 0)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
