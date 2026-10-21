"""Card controls scale down with the tile: on a 3-across phone layout every button stays inside its card, in all three modes. Run: python tests/ctlfit_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
N = 24
H = 'id,permalink,starred,updated,deleted\r\n' + ''.join('v%05d,https://www.reddit.com/r/vids/comments/v%05d/t/,0,1000,0\r\n' % (i, i) for i in range(N))
SEED = """async(t)=>{ localStorage.clear(); await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode();
  POSTS.forEach((p,i)=>{ META[p.id]={t:'Clip '+i,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'video',u:'https://v.redd.it/'+i+'/DASH_360.mp4',n:0,s:0,a:'',c:1700000000,w:400,h:300,v:'https://v.redd.it/'+i+'/DASH_360.mp4'}; }); state.hideBroken=false; onMeta(POSTS); refresh(); }"""
# for the first card: every visible-capable button's box must sit inside the card's box
FIT = """()=>{ const c=document.querySelector('.card'); const cr=c.getBoundingClientRect(); const out=[];
  for(const b of c.querySelectorAll('.star,.fs,.save,.morebtn')){ if(getComputedStyle(b).display==='none') continue; const r=b.getBoundingClientRect(); if(r.left<cr.left-0.5||r.right>cr.right+0.5||r.top<cr.top-0.5) out.push(b.className+' '+Math.round(r.left-cr.left)+'..'+Math.round(r.right-cr.left)+' of '+Math.round(cr.width)); }
  const bs=[...c.querySelectorAll('.star,.fs,.save:not(.nsfwb),.nsfwb,.morebtn')].filter(b=>getComputedStyle(b).display!=='none').map(b=>b.getBoundingClientRect()).sort((a,b)=>a.left-b.left);
  let ov=0; for(let i=1;i<bs.length;i++) if(bs[i].left<bs[i-1].right-0.5) ov++;
  return {out, ov, w:Math.round(cr.width), size:Math.round(c.querySelector('.star').getBoundingClientRect().width)} }"""
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H); pg.wait_for_timeout(800)
    # three across: make the tile size ask for ~3 columns on the phone
    ev("(()=>{ const s=document.getElementById('size'); if(s){ s.value=s.max; s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true})); } })()")
    pg.wait_for_timeout(500)
    w = ev("document.querySelector('.card').getBoundingClientRect().width")
    check('tiles are small (3 across or narrower), width %d' % w, w < 150)
    for mode in ('always', 'hover', 'collapsed'):
        ev("(m)=>{ const s=document.getElementById('ctlmode'); const i=[...s.querySelectorAll('button,input')].find(x=>(x.dataset.v||x.value)===m); if(i) i.click(); else { document.body.classList.remove('ctl-always','ctl-hover','ctl-collapsed'); document.body.classList.add('ctl-'+m); } }", mode)
        pg.wait_for_timeout(300)
        ev("document.querySelector('.card').classList.add('btns-open','is-focus')"); pg.wait_for_timeout(400)
        r = ev(FIT)
        check('%s: all buttons inside the %dpx tile (%s)' % (mode, r['w'], r['out']), not r['out'])
        check('%s: no buttons overlap each other' % mode, r['ov'] == 0)
        check('%s: buttons shrank below full size (%dpx)' % (mode, r['size']), r['size'] < 30)
    # a wide tile keeps full size
    ev("document.querySelector('.card').classList.add('btns-open')")
    pg.set_viewport_size({'width': 1100, 'height': 800}); ev("document.documentElement.style.setProperty('--card','320px')"); pg.wait_for_timeout(500)
    r = ev(FIT); check('wide tile: full-size buttons (%dpx)' % r['size'], r['size'] >= 30 and not r['out'])
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
