"""Triage mode and duplicate finder (Nov 2026 audit, items 32 and 34). Triage: random posts one at a time, right keeps, left removes (with a
tombstone), up stars, Undo steps back. Duplicates: the same picture saved twice is found and the extra copy removed, keeping the starred one.
Run: python tests/triage_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    ctx.add_init_script("try{localStorage.setItem('saved-posts-skin','legacy')}catch(e){}")   # these checks read Legacy's words and controls (Lemondrop shows some labels in caps and a bare Fit / Fill)
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(1200)
    ev("state.showText=true; state.nsfw='show'; refresh()"); pg.wait_for_timeout(300)
    n0 = ev("POSTS.length")
    check('Triage and Find duplicates sit in the list tools', ev("!!document.querySelector('#csvMore #triageBtn') && !!document.querySelector('#csvMore #dupBtn')"))
    ev("document.getElementById('triageBtn').click()"); pg.wait_for_timeout(300)
    cnt = lambda: ev("document.querySelector('#triage .tg-count').textContent")
    check('triage opens on card 1 of the posts on screen (%s)' % cnt(), not ev("document.getElementById('triage').hidden") and cnt().startswith('1 of %d' % n0))
    check('the page behind does not scroll', ev("document.body.classList.contains('triaging')"))
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(450)
    check('right arrow keeps and moves on', cnt().startswith('2 of') and ev("POSTS.length") == n0)
    gone = ev("TG.list[TG.i].id")
    pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(450)
    check('left arrow removes the post with a tombstone', ev("POSTS.length") == n0 - 1 and ev("TOMBS.has('%s')" % gone) and 'removed' in cnt())
    pg.click('#triage .tg-undo'); pg.wait_for_timeout(600)
    check('Undo brings it back and shows it again', ev("POSTS.length") == n0 and not ev("TOMBS.has('%s')" % gone) and ev("TG.list[TG.i].id") == gone)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(450)
    sid = ev("TG.list[TG.i].id"); was = ev("FAVS.has('%s')" % sid)
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(450)
    check('up arrow stars it', ev("FAVS.has('%s')" % sid))
    box = ev("(()=>{ const r=document.querySelector('#triage .tg-card:not(.next)').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; })()")
    before = cnt()
    pg.mouse.move(*box); pg.mouse.down(); pg.mouse.move(box[0] + 60, box[1], steps=3)
    check('dragging shows the KEEP stamp', float(ev("getComputedStyle(document.querySelector('#triage .tg-card:not(.next) .tg-stamp.keep')).opacity")) > 0.3)
    pg.mouse.move(box[0] + 200, box[1], steps=4); pg.mouse.up(); pg.wait_for_timeout(500)
    check('a drag to the right keeps (%s -> %s)' % (before, cnt()), cnt() != before and ev("POSTS.length") == n0)
    before = cnt()
    pg.mouse.move(*box); pg.mouse.down(); pg.mouse.move(box[0] + 40, box[1], steps=8); pg.wait_for_timeout(200); pg.mouse.up(); pg.wait_for_timeout(600)
    check('a short slow drag springs back', cnt() == before and ev("document.querySelector('#triage .tg-card:not(.next)').style.transform") in ('', 'none'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('Esc closes triage', ev("document.getElementById('triage').hidden") and not ev("document.body.classList.contains('triaging')"))
    # duplicates
    ev("""(()=>{ const a=POSTS[0], b=POSTS[1]; for(const p of [a,b]){ const m=META[p.id]; m.u='https://i.redd.it/samepic.jpg'; m.m='image'; } setStar(b, true); syncStars(); })()""")
    keep = ev("POSTS[1].id"); drop = ev("POSTS[0].id"); n1 = ev("POSTS.length")
    check('the same picture saved twice is found', ev("findDupes().length") == 1)
    ev("document.getElementById('dupBtn').click()"); pg.wait_for_timeout(300)
    check('a confirm says how many will go', 'Remove 1' in ev("document.getElementById('cOk').textContent"))
    pg.click('#cOk'); pg.wait_for_timeout(600)
    check('the extra copy goes and the starred one stays', ev("POSTS.length") == n1 - 1 and ev("TOMBS.has('%s')" % drop) and ev("POSTS.some(p=>p.id==='%s')" % keep))
    check('with Undo', 'Undo' in ev("document.getElementById('toast').innerText"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
