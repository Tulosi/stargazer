"""Text-only posts keep their title on the tile in Masonry/Grid while the card layer is down (Collapsed, or Show on hover / focus), and the layer fades in and out. Run: python tests/texttitle_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
H = 'id,permalink,starred,updated,deleted\r\n'
rows = ''.join('p%05d,https://www.reddit.com/r/pics/comments/p%05d/t/,0,1000,0\r\n' % (i, i) for i in range(4))
SEED = """async(t)=>{ await persistRec({id:'x',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('x'))); for(const k in META) delete META[k]; startCsvMode(); POSTS.forEach((p,i)=>{ META[p.id]= i<2 ? {t:'Words only '+p.id,o:0,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000,w:0,h:0} : {t:'Picture '+p.id,o:0,th:'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',m:'image',u:'',n:0,s:0,a:'',c:1700000000,w:400,h:300}; }); state.hideBroken=false; state.showText=true; document.getElementById('showtext').checked=true; onMeta(POSTS); refresh(); }"""
_unused = lambda kind: "(()=>{ const c=document.querySelector('.card%s'); const i=c.querySelector('.info'); const s=getComputedStyle(i); return s.display!=='none' && +s.opacity===1; })()" % kind
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(1000)
    check('text cards are marked', ev("document.querySelectorAll('.card.is-text').length") == 2)
    setmode = lambda m: (ev("document.getElementById('cardmode').value='%s'; document.getElementById('cardmode').dispatchEvent(new Event('change'))" % m), pg.wait_for_timeout(400))
    lay = lambda sel: ev("(()=>{ const e=document.querySelector('%s .layer'); return e ? +getComputedStyle(e).opacity : -1; })()" % sel)
    peek = lambda sel: ev("(()=>{ const e=document.querySelector('%s .peek'); return !!e && getComputedStyle(e).display!=='none'; })()" % sel)
    setmode('collapsed'); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    check('collapsed: text card keeps just its title on the tile', peek('.card.is-text') and lay('.card.is-text') == 0)
    check('collapsed: picture card shows nothing', lay('.card:not(.is-text)') == 0 and not peek('.card:not(.is-text)'))
    ev("document.querySelector('.card.is-text .lhandle').click()"); pg.wait_for_timeout(400)
    check('the handle opens the full layer on a text card (title row, meta, actions)', lay('.card.is-text') == 1 and not peek('.card.is-text'))
    ev("document.querySelector('.card.is-text .lh-close').click()"); pg.wait_for_timeout(400)
    check('and closes it back to the title', lay('.card.is-text') == 0 and peek('.card.is-text'))
    setmode('hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    check('hover: text card shows just its title', peek('.card.is-text'))
    check('hover: picture card shows nothing until hovered', lay('.card:not(.is-text)') == 0)
    pg.hover('.card:not(.is-text)'); pg.wait_for_timeout(500)
    check('hover: hovering a picture card raises its layer', lay('.card:not(.is-text)') == 1)
    # the layer fades in and out
    dur = lambda sel: ev("(()=>{ const s=getComputedStyle(document.querySelector('%s')); const i=s.transitionProperty.split(', ').indexOf('opacity'); return i<0 ? 0 : parseFloat(s.transitionDuration.split(', ')[i]); })()" % sel)
    check('the layer fades (even while hovered)', dur('.card:not(.is-text) .layer') >= 0.15)
    sample = """()=>new Promise(res=>{ const e=document.querySelector('.card:not(.is-text) .layer'); const out=[]; const t0=performance.now(); const f=()=>{ out.push(+getComputedStyle(e).opacity); if(performance.now()-t0<450) requestAnimationFrame(f); else res(out); }; f(); })"""
    pg.mouse.move(5, 5); pg.wait_for_timeout(600)
    box = pg.locator('.card:not(.is-text)').first.bounding_box()
    pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    up = pg.evaluate(sample)
    check('opacity eases up instead of jumping', up[-1] == 1 and any(0 < v < 1 for v in up))
    pg.mouse.move(5, 5)
    down = pg.evaluate(sample)
    check('and eases back down', down[-1] == 0 and any(0 < v < 1 for v in down))
    setmode('always'); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    check('always: every card has its layer up and no handle', lay('.card.is-text') == 1 and lay('.card:not(.is-text)') == 1 and ev("getComputedStyle(document.querySelector('.card .lhandle')).display") == 'none')
    # lavender tile with a picture-off mark for text posts that have no thumbnail
    setmode('collapsed')
    setmode('off')
    lav = ev("getComputedStyle(document.documentElement).getPropertyValue('--lav').trim()")
    check('a lavender colour is defined', bool(lav))
    check('text card tile is lavender, picture card is not', ev("(()=>{ const bg=e=>getComputedStyle(e).backgroundColor; const t=document.querySelector('.card.is-text .thumb .ph')||document.querySelector('.card.is-text .thumb'), n=document.querySelector('.card:not(.is-text) .thumb .ph')||document.querySelector('.card:not(.is-text) .thumb'); return bg(t)!==bg(n) && /rgb\\(2[0-9]{2}, 2[0-9]{2}, 2[0-9]{2}\\)|rgb\\(5[0-9], 5[0-9], 9[0-9]\\)/.test(bg(t)); })()"))
    check('text card tile carries an icon, with no words written on it', ev("(()=>{ const t=document.querySelector('.card.is-text .thumb .ph'); const b=getComputedStyle(t,'::before'); return b.content!=='none' && b.maskImage!=='none' && getComputedStyle(t.querySelector('span')).display==='none'; })()"))
    ratio = ev("(()=>{ const t=document.querySelector('.card.is-text .thumb .ph'); const b=getComputedStyle(t,'::before'); return [parseFloat(b.width), parseFloat(b.height), t.getBoundingClientRect().width]; })()")
    check('icon is 3:2', abs(ratio[0] / ratio[1] - 3 / 2) < 0.05)
    check('icon fills a good share of the card width', ratio[0] / ratio[2] > 0.45)
    check('picture card placeholder has no icon', ev("(document.querySelector('.card:not(.is-text) .thumb .ph') ? getComputedStyle(document.querySelector('.card:not(.is-text) .thumb .ph'),'::before').content : 'none')") in ('none', 'normal'))
    # touch screen: Show on hover / focus means the tile in focus
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    tp = ctx.new_page(); tp.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    tp.goto(PAGE); tp.wait_for_timeout(700); tev = tp.evaluate
    tev(SEED, H + rows); tp.wait_for_timeout(1200)
    tev("document.getElementById('cardmode').value='hover'; document.getElementById('cardmode').dispatchEvent(new Event('change'))"); tp.wait_for_timeout(500)
    vis2 = "(()=>{ const out={}; document.querySelectorAll('.card').forEach(c=>{ const l=getComputedStyle(c.querySelector('.layer')), pk=c.querySelector('.peek'); out[c.dataset.id]=[c.classList.contains('is-focus'), c.classList.contains('is-text'), +l.opacity>0, !!pk && getComputedStyle(pk).display!=='none']; }); return out; })()"
    got = tev(vis2)
    foc = [v for v in got.values() if v[0]]
    check('touch + hover/focus: exactly one tile is in focus', len(foc) == 1)
    check('touch + hover/focus: the tile in focus shows its layer', all(v[2] for v in foc))
    check('touch + hover/focus: tiles out of focus keep theirs down', all(not v[2] for v in got.values() if not v[0]))
    check('touch + hover/focus: text tiles out of focus still show a title', all(v[3] for v in got.values() if v[1] and not v[0]))
    tev("document.getElementById('cardmode').value='always'; document.getElementById('cardmode').dispatchEvent(new Event('change'))"); tp.wait_for_timeout(400)
    check('touch + always: every tile shows its layer', all(v[2] for v in tev(vis2).values()))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
