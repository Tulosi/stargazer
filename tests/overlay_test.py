"""Full-screen overlay (Nov 2026 audit, item 9, option A): caption bottom left (r/sub · age, title, u/author · points), a labelled rail on
the right (Star, Saved, comments, Open, one NS/FW mark lit for NSFW posts), and three ways to see the media alone: it clears by itself after
3s, a tap toggles it, press and hold clears it. Run: python tests/overlay_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ev("openSample()"); pg.wait_for_timeout(1000)
    ev("state.nsfw='show'; refresh()"); pg.wait_for_timeout(300)
    pg.tap('#grid .card a.thumb'); pg.wait_for_timeout(600)
    idle = lambda: ev("document.getElementById('viewer').classList.contains('vidle')")
    cap = ev("document.querySelector('#viewer .vcap').innerText")
    t0 = ev("titleOf(VIEW.cur)")
    check('caption: subreddit and age, title, author and points', ev("'r/'+VIEW.cur.sub") in cap and t0 in cap and 'ago' in cap and 'u/' in cap and 'points' in cap)
    check('the dialog is named after the post', ev("document.getElementById('viewer').getAttribute('aria-label')") == t0)
    order = ev("[...document.querySelectorAll('#viewer .vrail > *')].map(x=>x.className)")
    check('rail: Star, comments, Open, NS/FW, then Remove last (%s)' % order, order == ['vr-star', 'vr-cm', 'vr-open', 'vr-nsfw', 'vr-save'])
    check('rail buttons are at least 44px tall', ev("[...document.querySelectorAll('#viewer .vrail > :not([hidden])')].every(x=>x.getBoundingClientRect().height>=44)"))
    check('only one NSFW control in full screen', ev("document.querySelectorAll('#viewer [class*=nsfw]').length") == 1)
    check('caption and rail do not overlap the post buttons', ev("""(()=>{ const a=document.querySelector('#viewer .vcap').getBoundingClientRect(), r=document.querySelector('#viewer .vrail').getBoundingClientRect(), p=document.querySelector('#viewer .vposts').getBoundingClientRect(); return a.bottom<=p.top && r.bottom<=p.top && a.right<=r.left; })()"""))
    # clears on its own, a tap toggles
    check('overlay shows when full screen opens', not idle())
    pg.wait_for_timeout(3300)
    check('it clears by itself after about 3s on a picture', idle())
    pg.tap('#viewer .vstage img'); pg.wait_for_timeout(400)
    check('a tap brings it back', not idle())
    pg.wait_for_timeout(500); pg.tap('#viewer .vstage img'); pg.wait_for_timeout(400)
    check('another tap clears it', idle())
    pg.keyboard.press('h'); pg.wait_for_timeout(200)
    check('H shows it', not idle())
    pg.keyboard.press('h'); pg.wait_for_timeout(200)
    check('and H hides it', idle())
    pg.keyboard.press('h')
    # star
    was = ev("FAVS.has(VIEW.cur.id)")
    pg.tap('#viewer .vr-star'); pg.wait_for_timeout(300)
    check('Star stars the post and the rail says so', ev("FAVS.has(VIEW.cur.id)") != was and ev("document.querySelector('#viewer .vr-star').getAttribute('aria-pressed')") == str(not was).lower())
    pg.tap('#viewer .vr-star'); pg.wait_for_timeout(300)
    # NSFW mark
    n0 = ev("isNsfw(VIEW.cur)")
    check('NS/FW is dim on a post that is not NSFW', not n0 and ev("document.querySelector('#viewer .vr-nsfw').getAttribute('aria-pressed')") == 'false')
    pg.tap('#viewer .vr-nsfw'); pg.wait_for_timeout(500)
    check('pressing it marks the post NSFW and lights it', ev("isNsfw(VIEW.cur)") and ev("document.querySelector('#viewer .vr-nsfw').getAttribute('aria-pressed')") == 'true' and '?nsfw=1' in ev("VIEW.cur.perma"))
    pg.tap('#viewer .vr-nsfw'); pg.wait_for_timeout(500)
    check('and pressing again unmarks it', not ev("isNsfw(VIEW.cur)"))
    ev("closeViewer()"); pg.wait_for_timeout(300)
    ev("openViewer(POSTS.find(p=>META[p.id].o===1))"); pg.wait_for_timeout(500)
    check('on an NSFW post the one NS/FW mark is lit', ev("document.querySelector('#viewer .vr-nsfw').getAttribute('aria-pressed')") == 'true')
    ev("closeViewer()"); pg.wait_for_timeout(300)
    # Remove: removes the post and keeps it on screen with Put back
    pg.tap('#grid .card a.thumb'); pg.wait_for_timeout(600)
    first = ev("VIEW.cur.id"); n = ev("POSTS.length")
    pg.tap('#viewer .vr-save'); pg.wait_for_timeout(700)
    check('Remove takes the post out of the list (with a tombstone) and keeps it on screen, offering Put back', ev("POSTS.length") == n - 1 and ev("TOMBS.has('%s')" % first) and ev("VIEW.cur.id") == first and not ev("document.getElementById('viewer').hidden") and 'Put back' in ev("document.querySelector('#viewer .vr-save').textContent"))
    check('with Undo offered', 'Undo' in ev("document.getElementById('toast').innerText"))
    nav = ev("[document.querySelector('#viewer .vpp').disabled, document.querySelector('#viewer .vpn').disabled]")
    ev("viewerPost(1)"); pg.wait_for_timeout(500)
    check('the next swipe or button moves on from the removed post', ev("VIEW.cur.id") != first)
    # after moving on in the same session the overlay stays down: mouse movement and repaints do not bring it back, a tap does
    check('after moving to another post the overlay stays down', ev("VIEW.root.classList.contains('vidle')"))
    pg.mouse.move(200, 200); pg.mouse.move(400, 300); ev("viewerWake(); paintChrome(VIEW.cur)"); pg.wait_for_timeout(150)
    check('mouse movement and repaints leave it down', ev("VIEW.root.classList.contains('vidle')"))
    # a tap on the black beside the post toggles the overlay and never closes full screen
    ev("VIEW.root.dispatchEvent(new MouseEvent('click',{bubbles:true}))"); pg.wait_for_timeout(200)
    check('a tap on the black around the post brings it back, still in full screen', not ev("VIEW.root.hidden") and not ev("VIEW.root.classList.contains('vidle')"))
    ev("VIEW.stage.dispatchEvent(new MouseEvent('click',{bubbles:true}))"); pg.wait_for_timeout(200)
    check('another tap hides it, still in full screen', not ev("VIEW.root.hidden") and ev("VIEW.root.classList.contains('vidle')"))
    ev("VIEW.stage.dispatchEvent(new MouseEvent('click',{bubbles:true}))"); pg.wait_for_timeout(200)
    ev("viewerPost(1)"); pg.wait_for_timeout(500)
    check('shown by hand on one post, it is down again on the next', ev("VIEW.root.classList.contains('vidle')"))
    ev("const q = VIEW.cur; closeViewer(); openViewer(q)"); pg.wait_for_timeout(500)
    check('leaving and opening full screen again shows it on the first post', not ev("VIEW.root.classList.contains('vidle')"))
    ev("closeViewer(); openViewer(list.find(p=>{ const m=metaOf(p); return m && m.m==='image'; }))"); pg.wait_for_timeout(600)   # back on a picture for the press-and-hold checks
    check('previous / next still work after the removal', nav != [True, True])
    # press and hold on a picture
    box = ev("(()=>{ const r=document.querySelector('#viewer .vstage img').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; })()")
    pg.mouse.move(*box); pg.mouse.down(); pg.wait_for_timeout(550)
    check('press and hold clears everything on a picture', ev("document.getElementById('viewer').classList.contains('vpeek')"))
    pg.mouse.up(); pg.wait_for_timeout(300)
    check('letting go brings it back', not ev("document.getElementById('viewer').classList.contains('vpeek')") and not idle())
    check('the shortcuts list tells about tap, hold and H', ev("(()=>{ const t=document.getElementById('kbhelp').textContent; return /press and hold for a clean look/.test(t) && /hides or shows the caption/.test(t); })()"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
