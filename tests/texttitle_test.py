"""Text-only posts always show their title in Masonry/Grid, even with Card info hidden or on hover. Run: python tests/texttitle_test.py"""
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
vis = lambda kind: "(()=>{ const c=document.querySelector('.card%s'); const i=c.querySelector('.info'); const s=getComputedStyle(i); return s.display!=='none' && +s.opacity===1; })()" % kind
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={'width': 1100, 'height': 800}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev(SEED, H + rows); pg.wait_for_timeout(1000)
    check('text cards are marked', ev("document.querySelectorAll('.card.is-text').length") == 2)
    setmode = lambda m: (ev("document.getElementById('infomode').value='%s'; document.getElementById('infomode').dispatchEvent(new Event('change'))" % m), pg.wait_for_timeout(400))
    shown = lambda sel: ev("(()=>{ const e=document.querySelector('%s'); if(!e || !e.getClientRects().length) return false; const i=e.closest('.info'); return +getComputedStyle(e).opacity>0 && (!i || +getComputedStyle(i).opacity>0); })()" % sel)
    pressed = lambda: ev("document.querySelector('.card.is-text .ibtn').getAttribute('aria-pressed')")
    setmode('off')
    check('info mode off: the (i) button starts off on a text card', not ev("document.querySelector('.card.is-text').classList.contains('info-open')") and pressed() == 'false')
    check('info mode off: text card shows just its title', shown('.card.is-text .title') and not shown('.card.is-text .meta') and not shown('.card.is-text .actions'))
    check('info mode off: picture card shows nothing', not shown('.card:not(.is-text) .title'))
    pg.hover('.card.is-text'); pg.click('.card.is-text .ibtn'); pg.wait_for_timeout(300)
    check('the (i) button opens the full info on a text card', pressed() == 'true' and shown('.card.is-text .meta'))
    pg.hover('.card.is-text'); pg.click('.card.is-text .ibtn'); pg.wait_for_timeout(300)
    check('and closes it back to the title', pressed() == 'false' and shown('.card.is-text .title') and not shown('.card.is-text .meta'))
    setmode('hover'); pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    check('info mode hover: text card shows just its title', shown('.card.is-text .title') and not shown('.card.is-text .meta'))
    check('info mode hover: picture card shows nothing until hovered', not shown('.card:not(.is-text) .title'))
    pg.hover('.card:not(.is-text)'); pg.wait_for_timeout(400)
    check('info mode hover: hovering a picture card shows its info', shown('.card:not(.is-text) .title'))
    # Show on hover fades the info in and out
    setmode('hover')
    dur = lambda sel: ev("(()=>{ const s=getComputedStyle(document.querySelector('%s')); const i=s.transitionProperty.split(', ').indexOf('opacity'); return i<0 ? 0 : parseFloat(s.transitionDuration.split(', ')[i]); })()" % sel)
    check('Show on hover: info fades (even while hovered)', dur('.card:not(.is-text) .info') >= 0.15)
    sample = """()=>new Promise(res=>{ const e=document.querySelector('.card:not(.is-text) .info'); const out=[]; const t0=performance.now(); const f=()=>{ out.push(+getComputedStyle(e).opacity); if(performance.now()-t0<450) requestAnimationFrame(f); else res(out); }; f(); })"""
    pg.mouse.move(5, 5); pg.wait_for_timeout(600)
    box = pg.locator('.card:not(.is-text)').first.bounding_box()
    pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    up = pg.evaluate(sample)
    check('Show on hover: opacity eases up instead of jumping', up[-1] == 1 and any(0 < v < 1 for v in up))
    pg.mouse.move(5, 5)
    down = pg.evaluate(sample)
    check('Show on hover: and eases back down', down[-1] == 0 and any(0 < v < 1 for v in down))
    ev("document.getElementById('infomode').value='show'; document.getElementById('infomode').dispatchEvent(new Event('change'))"); pg.wait_for_timeout(300)
    check('info mode show: both visible', ev(vis('.is-text')) and ev(vis(':not(.is-text)')))
    # lavender tile with a picture-off mark for text posts that have no thumbnail
    setmode('off')
    lav = ev("getComputedStyle(document.documentElement).getPropertyValue('--lav').trim()")
    check('a lavender colour is defined', bool(lav))
    check('text card tile is lavender, picture card is not', ev("(()=>{ const bg=e=>getComputedStyle(e).backgroundColor; const t=document.querySelector('.card.is-text .thumb .ph'), n=document.querySelector('.card:not(.is-text) .thumb .ph'); return bg(t)!==bg(n) && /rgb\\(2[0-9]{2}, 2[0-9]{2}, 2[0-9]{2}\\)|rgb\\(5[0-9], 5[0-9], 9[0-9]\\)/.test(bg(t)); })()"))
    check('text card tile carries an icon, with no words written on it', ev("(()=>{ const t=document.querySelector('.card.is-text .thumb .ph'); const b=getComputedStyle(t,'::before'); return b.content!=='none' && b.maskImage!=='none' && getComputedStyle(t.querySelector('span')).display==='none'; })()"))
    ratio = ev("(()=>{ const t=document.querySelector('.card.is-text .thumb .ph'); const b=getComputedStyle(t,'::before'); return [parseFloat(b.width), parseFloat(b.height), t.getBoundingClientRect().width]; })()")
    check('icon is 3:2', abs(ratio[0] / ratio[1] - 3 / 2) < 0.05)
    check('icon fills a good share of the card width', ratio[0] / ratio[2] > 0.45)
    check('picture card placeholder has no icon', ev("getComputedStyle(document.querySelector('.card:not(.is-text) .thumb .ph'),'::before').content") in ('none', 'normal'))
    # touch screen: Show on hover means the tile in focus
    ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    tp = ctx.new_page(); tp.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    tp.goto(PAGE); tp.wait_for_timeout(700); tev = tp.evaluate
    tev(SEED, H + rows); tp.wait_for_timeout(1200)
    tev("document.getElementById('infomode').value='hover'; document.getElementById('infomode').dispatchEvent(new Event('change'))"); tp.wait_for_timeout(500)
    vis2 = "(()=>{ const out={}; document.querySelectorAll('.card').forEach(c=>{ const s=getComputedStyle(c.querySelector('.info')); out[c.dataset.id]=[c.classList.contains('is-focus'), c.classList.contains('is-text'), s.display!=='none' && +s.opacity>0]; }); return out; })()"
    got = tev(vis2)
    foc = [v for v in got.values() if v[0]]
    check('touch + Show on hover: exactly one tile is in focus', len(foc) == 1)
    check('touch + Show on hover: the tile in focus shows its info', all(v[2] for v in foc))
    check('touch + Show on hover: picture tiles out of focus hide theirs', all(not v[2] for v in got.values() if not v[0] and not v[1]))
    check('touch + Show on hover: text tiles still show a title', all(v[2] for v in got.values() if v[1]))
    tev("document.getElementById('infomode').value='show'; document.getElementById('infomode').dispatchEvent(new Event('change'))"); tp.wait_for_timeout(400)
    check('touch + Always visible: every tile shows its info', all(v[2] for v in tev(vis2).values()))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
