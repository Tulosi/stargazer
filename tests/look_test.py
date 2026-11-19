"""Quieter look (Nov 2026 audit): neutral smoked-glass tray with no gradient line, plain header line, one accent, one stat on desktop too,
short first-run screen, "(optional)" as text, varied sample posts (a clip, a text post, an NSFW one). Run: python tests/look_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1400, 'height': 900}, color_scheme='dark'); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    intro = ev("document.querySelector('.intro').innerText")
    check('first run: one short pitch, no italics, sentence-case heading', ev("document.querySelectorAll('.intro > p.introlead, .intro > p.introsave').length")==0
          and ev("getComputedStyle(document.querySelector('.intro .introh')).textTransform")=='none' and 'Get your Reddit data' in intro)
    check('header line is plain (no gradient line under the top bar)', ev("getComputedStyle(document.querySelector('.deck'),'::after').content") in ('none', 'normal'))
    check('Optional reads as plain text', ev("(()=>{const o=document.querySelector('.optbadge'); return !o || (o.textContent==='(optional)' && getComputedStyle(o).textTransform==='none')})()"))
    ev("openSample()"); pg.wait_for_timeout(1500)
    check('samples: 15 posts with a clip, a text post and an NSFW one', ev("POSTS.length")==15 and ev("POSTS.some(p=>META[p.id].m==='gif' && META[p.id].v)") and ev("POSTS.some(p=>META[p.id].m==='text')") and ev("POSTS.some(p=>META[p.id].o===1)"))
    hues = ev("new Set(POSTS.map(p=>(decodeURIComponent(META[p.id].th||'').match(/hsl\\((\\d+)/)||[])[1]).filter(Boolean)).size")
    check('samples come in many colours (%d hues)' % hues, hues >= 8)
    check('the sample clip plays as a GIF clip', ev("(()=>{const t=[...document.querySelectorAll('#grid .card a.thumb')].find(a=>a.dataset.v&&a.dataset.v.startsWith('data:image/gif')); return !!t && isGifFile(t.dataset.v)})()"))
    ev("toggleLayer(document.querySelector('#grid .card'))"); pg.wait_for_timeout(500)
    lay = "document.querySelector('#grid .card.lay-open .layer')"
    bg = ev("getComputedStyle(%s).backgroundImage" % lay); col = ev("getComputedStyle(%s).backgroundColor" % lay)
    check('tray is neutral smoked glass (%s)' % col, bg == 'none' and col.startswith('rgba(20, 20, 24'))
    check('tray has no gradient top line', ev("getComputedStyle(%s,'::before').content" % lay) in ('none', 'normal'))
    ev("state.showText=true; state.nsfw='show'; refresh(); updateStats()"); pg.wait_for_timeout(500)
    check('desktop shows one number reading "N posts" when nothing is filtered', ev("[...document.querySelectorAll('#stats .st')].filter(e=>e.offsetParent!==null).length")==1 and ev("document.getElementById('stLb').textContent")=='posts' and ev("getComputedStyle(document.querySelector('#stats .sof')).display")=='none')
    check('one accent: the star accent matches the page accent', ev("getComputedStyle(document.body).getPropertyValue('--hot').trim()==getComputedStyle(document.body).getPropertyValue('--accent').trim()"))
    check('no page errors', not errs)
    print('ALL PASS' if not bad else 'FAILED: %d' % len(bad))
