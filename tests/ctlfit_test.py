"""The card layer scales down with the tile: on a 3-across phone layout the layer and every button stay inside the card, in all three modes. Run: python tests/ctlfit_test.py"""
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
# the layer must sit inside the card, and every button must sit inside the layer without overlapping
FIT = """()=>{ const c=document.querySelector('.card'); const cr=c.getBoundingClientRect(); const L=c.querySelector('.layer'); const lr=L.getBoundingClientRect(); const out=[];
  if(lr.left<cr.left-0.5||lr.right>cr.right+0.5||lr.top<cr.top-0.5||lr.bottom>cr.bottom+0.5) out.push('layer '+Math.round(lr.left-cr.left)+'..'+Math.round(lr.right-cr.left)+' of '+Math.round(cr.width));
  const bs=[...L.querySelectorAll('.lay-cap > *')].filter(b=>!b.hidden && b.offsetParent!==null).map(b=>b.getBoundingClientRect());
  for(const r of bs){ if(r.left<lr.left-0.5||r.right>lr.right+0.5) out.push('button out of layer'); }
  let ov=0; for(let i=1;i<bs.length;i++) if(bs[i].left<bs[i-1].right-0.5) ov++;
  return {out, ov, w:Math.round(cr.width), size:Math.round(bs[0].width)} }"""
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
        ev("(m)=>{ const s=document.getElementById('cardmode'); s.value=m; s.dispatchEvent(new Event('change')); }", mode)
        pg.wait_for_timeout(300)
        ev("document.querySelector('.card').classList.add('lay-open','is-focus')"); pg.wait_for_timeout(400)
        r = ev(FIT)
        check('%s: layer and buttons inside the %dpx tile (%s)' % (mode, r['w'], r['out']), not r['out'])
        check('%s: no buttons overlap each other' % mode, r['ov'] == 0)
        check('%s: buttons shrank below full size (%dpx)' % (mode, r['size']), r['size'] < 34)
    # a wide tile keeps full size
    ev("document.querySelector('.card').classList.add('lay-open')")
    pg.set_viewport_size({'width': 1100, 'height': 800}); ev("document.documentElement.style.setProperty('--card','320px')"); pg.wait_for_timeout(500)
    r = ev(FIT); check('wide tile: full-size buttons (%dpx)' % r['size'], r['size'] >= 34 and not r['out'])
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
