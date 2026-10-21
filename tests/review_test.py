"""UX review items: undo toast, short status line, filter badge, hidden inert controls. Run: python tests/review_test.py"""
import os, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
SEED = """(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/x/',starred:%s,t:5}); ROWSET.add(id); if(%s) FAVS.add(id);
  META[id]={t:'post '+id,o:0,th:'https://i.redd.it/a.jpg',m:'image',u:'https://i.redd.it/a.jpg',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360}; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0f01f0005000201a0b3a5d70000000049454e44ae426082')
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else (r.fulfill(status=200, content_type='image/png', body=PNG) if 'redd.it' in r.request.url else r.abort()))
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(SEED % ('aaa01', 'true', 'true')); ev(SEED % ('bbb02', 'false', 'false'))
    ev('state.hideBroken=false; state.nsfw="show"'); ev('startCsvMode()'); pg.wait_for_timeout(1200)
    # filter badge: defaults do not count, changes do
    ev('state.hideBroken=true; state.nsfw="hide"; state.showText=false; state.cats.clear(); refresh(true)'); pg.wait_for_timeout(300)
    check('badge empty with default filters', ev("document.getElementById('decktoggle').dataset.n") is None)
    ev('state.fav=true; refresh(true)'); pg.wait_for_timeout(300)
    check('badge counts a user-changed filter', ev("document.getElementById('decktoggle').dataset.n") == '1')
    ev('state.fav=false; state.hideBroken=false; state.nsfw="show"; refresh(true)'); pg.wait_for_timeout(300)
    # undo delete
    pg.dispatch_event('article.card[data-id=aaa01] button.save:not(.nsfwb)', 'click'); pg.wait_for_timeout(600)
    check('delete needs no confirm dialog and removes the card', ev("!ROWSET.has('aaa01') && !document.querySelector('article.card[data-id=aaa01]')"))
    check('toast offers Undo', ev("!!document.querySelector('#toast .tact')"))
    pg.click('#toast .tact'); pg.wait_for_timeout(1500)
    check('undo restores row, star and card', ev("ROWSET.has('aaa01') && FAVS.has('aaa01') && !!document.querySelector('article.card[data-id=aaa01]') && !TOMBS.has('aaa01')"))
    check('restored row is newer than the tombstone', ev("ROWS.find(r=>r.id==='aaa01').t") > 5)
    # tile size hidden in list
    pg.dispatch_event('#layoutseg [data-l=list]', 'click')
    pg.wait_for_timeout(300)
    check('tile size hidden in List', not ev("document.getElementById('sizerow').offsetParent"))
    check('layout hint is short', len(ev("document.getElementById('layouthint').textContent")) < 30)
    # theme lives in Filters > View
    check('Theme sits in Filters, not Source', ev("!!document.querySelector('#panel #theme') && !document.querySelector('#srcpanel #theme')"))
    check('no developer-facing Supabase notice in Advanced', ev("!/supabase/i.test(document.getElementById('advBox').textContent)"))
    check('Advanced keeps the status and retry button', ev("!!document.getElementById('advRg') && !!document.getElementById('advRgRetry')"))
    # stats note opens on tap
    ev("document.getElementById('stats').hidden=false")
    pg.dispatch_event('.stats .st', 'click'); pg.wait_for_timeout(100)
    check('tapping a count opens its note', ev("document.querySelector('.stats .st').classList.contains('open')"))
    pg.dispatch_event('body', 'click'); pg.wait_for_timeout(100)
    check('tapping elsewhere closes it', not ev("document.querySelector('.stats .st').classList.contains('open')"))
    # back to top
    check('back-to-top hidden near the top', ev("document.getElementById('totop').hidden"))
    ev("document.body.style.minHeight='6000px'; window.scrollTo(0,3000)"); pg.wait_for_timeout(400)
    check('back-to-top shows after a long scroll', ev("!document.getElementById('totop').hidden"))
    pg.dispatch_event('#totop', 'click'); pg.wait_for_timeout(1200)
    check('back-to-top returns to the top', ev('scrollY') < 5)
    # list rows carry a date (wide screens)
    check('list rows carry a date', ev("[...document.querySelectorAll('body.layout-list .meta .dt')].some(e=>e.offsetParent && e.textContent.length>5)"))
    # pending card actions
    ev("(()=>{ const id='pend01'; ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); delete META[id]; })()")
    ev('startCsvMode()'); pg.wait_for_timeout(600)
    check('not-loaded card offers Open on Reddit and Retry', ev("(()=>{ const c=document.querySelector('article.card[data-id=pend01]'); return !!c && !!c.querySelector('.retry1') && /Open on Reddit/.test(c.textContent); })()"))
    # layout remembered per list
    ev("setListLayout(LIB.cur.id,'grid'); LAYOUT='masonry'; applyListLayout()")
    check('layout remembered per list', ev("LAYOUT")=='grid')
    # viewer: previous / next post
    ev("document.body.style.minHeight=''; state.fav=false; state.showText=true; state.hideBroken=false; state.nsfw='show'; refresh(true)"); pg.wait_for_timeout(400)
    ids = ev("list.filter(viewable).map(p=>p.id)")
    check('at least two viewable posts', len(ids) >= 2)
    if len(ids) >= 2:
        ev('VIEW.root.requestFullscreen = () => Promise.reject(new Error("no full screen in tests")); 0')   # headless has no real full screen
        ev("openViewer(list.filter(viewable)[0])"); pg.wait_for_timeout(500)
        check('first post: previous disabled, next enabled', ev("document.querySelector('#viewer .vpp').disabled") and not ev("document.querySelector('#viewer .vpn').disabled"))
        pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(500)
        check('Down arrow shows the next post', ev("VIEW.cur.id") == ids[1])
        pg.dispatch_event('#viewer .vpp', 'click'); pg.wait_for_timeout(500)
        check('Previous button goes back', ev("VIEW.cur.id") == ids[0])
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # bulk selection
    ev("document.body.style.minHeight=''; window.scrollTo(0,0)")
    check('Select button visible with a list open', ev("!document.getElementById('selbtn').hidden"))
    pg.dispatch_event('#selbtn', 'click'); pg.wait_for_timeout(200)
    check('selection bar appears', ev("!document.getElementById('selbar').hidden && document.body.classList.contains('selecting')"))
    check('desktop: selection strip is docked under the top bar, not floating at the bottom', ev("(()=>{ const b=document.getElementById('selbar'), d=document.querySelector('.deck'); const r=b.getBoundingClientRect(), dr=d.getBoundingClientRect(); return getComputedStyle(b).position!=='fixed' && d.contains(b) && r.top < 200 && Math.abs(r.bottom-dr.bottom)<2 && r.width > innerWidth*0.9; })()"))
    pg.dispatch_event('#selbar [data-a=all]', 'click'); pg.wait_for_timeout(200)
    nsel = ev("SEL.ids.size"); check('Select all picks every listed post', nsel == ev("list.length") and nsel >= 2)
    pg.dispatch_event('#selbar [data-a=nsfw]', 'click'); pg.wait_for_timeout(700)
    check('bulk Mark NSFW marks them all', ev("list.every(p=>isNsfw(p))") and ev("ROWS.every(r=>/nsfw=1/.test(r.perma))"))
    pg.dispatch_event('#selbar [data-a=sfw]', 'click'); pg.wait_for_timeout(700)
    check('bulk Unmark clears them', ev("list.every(p=>!isNsfw(p))"))
    pg.dispatch_event('#selbar [data-a=star]', 'click'); pg.wait_for_timeout(500)
    check('bulk Star stars them', ev("list.every(p=>FAVS.has(p.id))"))
    check('bulk Star updates the cards and the CSV rows', ev("[...document.querySelectorAll('article.card button.star')].every(b=>b.getAttribute('aria-pressed')==='true') && ROWS.every(r=>r.starred)"))
    check('button now offers Unstar', ev("document.querySelector('#selbar [data-a=star]').textContent")=='Unstar')
    pg.dispatch_event('#selbar [data-a=star]', 'click'); pg.wait_for_timeout(500)
    check('Unstar clears them again', ev("list.every(p=>!FAVS.has(p.id)) && ROWS.every(r=>!r.starred)"))
    pg.dispatch_event('#selbar [data-a=star]', 'click'); pg.wait_for_timeout(500)
    cnt = ev("ROWS.length")
    pg.dispatch_event('#selbar [data-a=del]', 'click'); pg.wait_for_timeout(400)
    pg.dispatch_event('#cOk', 'click'); pg.wait_for_timeout(900)
    check('bulk delete removes them after one confirm', ev("ROWS.length") == 0 and cnt >= 2)
    pg.dispatch_event('#toast .tact', 'click'); pg.wait_for_timeout(1500)
    check('Undo brings them all back', ev("ROWS.length") == cnt)
    if ev("document.body.classList.contains('selecting')"): pg.dispatch_event('#selbtn', 'click'); pg.wait_for_timeout(200)
    check('Cancel leaves selection mode', ev("!document.body.classList.contains('selecting')"))
    # clips fade in over the still instead of flashing the card colour
    ev("document.body.style.minHeight=''; window.scrollTo(0,0)")
    ev("(()=>{ const id='vid01'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); META[id]={t:'clip',o:0,th:'https://i.redd.it/a.jpg',m:'gif',u:'',n:0,s:0,a:'',c:1700000000,v:'https://v.redd.it/none/DASH_360.mp4',w:640,h:360}; })()")
    ev("startCsvMode()"); pg.wait_for_timeout(1000)
    r = ev("""(()=>{ const t=document.querySelector('article.card[data-id=vid01] .thumb'); startPlay(t); const c=t.querySelector('video.clip'); if(!c) return null; const s=getComputedStyle(c); const first={op:s.opacity,bg:s.backgroundColor}; c.dispatchEvent(new Event('playing')); return {first, on:c.classList.contains('on')}; })()""")
    check('clip starts see-through, with a transparent background', bool(r) and r['first']['op']=='0' and r['first']['bg']=='rgba(0, 0, 0, 0)')
    check('clip is marked visible once it is playing', bool(r) and r['on'])
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
