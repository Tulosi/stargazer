"""Full screen: the Fit / Fill button (crop to fill the screen) and RedGifs clips opening on their HD file. Run: python tests/viewfill_test.py (needs ffmpeg-made fixtures in tests/fixtures)"""
import os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', 'site'))
SIL = open(os.path.join(HERE, 'fixtures', 'clip_silent.webm'), 'rb').read()
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0f01f0005000201a5c3d8a20000000049454e44ae426082')
bad = []; HITS = []; LOOKUPS = []
import time
FUTURE = int(time.time()) + 86400; PAST = int(time.time()) - 3600
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ACAO = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*'}
def handle(r):
    u = r.request.url
    if u.startswith('http://127.0.0.1'): return r.continue_()
    if 'api.redgifs.com/v2/auth/temporary' in u: return r.fulfill(status=200, content_type='application/json', headers=ACAO, body='{"token":"t"}')
    if 'api.redgifs.com/v2/gifs?ids=' in u:
        ids = u.split('ids=')[1].split(',')
        LOOKUPS.extend(ids)
        gifs = [{'id': i, 'hasAudio': False, 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % i, 'hd': 'https://media.redgifs.com/%s.mp4' % i}} for i in ids if i == 'quietone']
        gifs += [{'id': i, 'hasAudio': False, 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4?expires=%d&signature=new' % (i.capitalize(), FUTURE), 'hd': 'https://media.redgifs.com/%s.mp4?expires=%d&signature=new' % (i.capitalize(), FUTURE)}} for i in ids if i in ('staleone', 'badsig')]
        return r.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps({'gifs': gifs}))
    if 'api.redgifs.com' in u: return r.abort()
    if u.startswith('https://media.redgifs.com/'):
        HITS.append(u)
        if 'Nohd.mp4' in u or 'signature=old' in u: return r.fulfill(status=403 if 'signature=old' in u else 404, body='')
        return r.fulfill(status=200, content_type='video/webm', headers=ACAO, body=SIL)
    if u.startswith('https://i.example.com/'): return r.fulfill(status=200, content_type='image/png', body=PNG)
    return r.abort()
def seed(id, meta):
    return "(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); META[id]=Object.assign({t:'clip',o:0,th:'',m:'gif',n:0,s:0,a:'',c:1700000000,w:160,h:90}, %s); })()" % (id, json.dumps(meta))
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); ctx = b.new_context(viewport={'width': 1000, 'height': 700}); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', handle)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(seed('quiet1', {'u': 'https://www.redgifs.com/watch/quietone', 'v': 'https://v.redd.it/q/silent.mp4'}))
    # lookup refused (so no HD address from RedGifs), but the clip's SD file is known: full screen should still ask for NAME.mp4
    ev(seed('mobil1', {'u': 'https://www.redgifs.com/watch/mobileone', 'v': 'https://media.redgifs.com/MobileOne-mobile.mp4', 'rgDone': 1, 'ha': 0}))
    ev(seed('nohd11', {'u': 'https://www.redgifs.com/watch/nohd', 'v': 'https://media.redgifs.com/Nohd-mobile.mp4', 'rgDone': 1, 'ha': 0}))
    ev(seed('pic111', {'m': 'image', 'u': 'https://i.example.com/a.png', 'th': 'https://i.example.com/a.png', 'w': 100, 'h': 300}))
    ev(seed('nofile', {'u': 'https://www.redgifs.com/watch/nofileone', 'v': '', 'rgDone': 1}))
    ev('startCsvMode()'); pg.wait_for_timeout(3000)
    check('the card keeps the light SD file for a silent clip', ev("META.quiet1.v")=='https://media.redgifs.com/quietone-mobile.mp4' and ev("META.quiet1.vh")=='https://media.redgifs.com/quietone.mp4')
    open_ = lambda id: (ev("openViewer(POSTS.find(x=>x.id==='%s'))" % id), pg.wait_for_timeout(1500))
    vsrc = lambda: ev("(document.querySelector('#viewer video')||{}).currentSrc||''")
    open_('quiet1')
    check('full screen opens a RedGifs clip on its HD file', vsrc()=='https://media.redgifs.com/quietone.mp4')
    # Fit / Fill
    fill = lambda: ev("getComputedStyle(document.querySelector('#viewer .vstage video')).objectFit")
    check('the Fill screen button shows on a clip, and the clip starts fitted', ev("getComputedStyle(document.querySelector('#viewer .vfill')).display")!='none' and fill()=='contain' and ev("document.querySelector('#viewer .vfill').getAttribute('aria-label')")=='Fill screen')
    pg.click('#viewer .vfill'); pg.wait_for_timeout(200)
    check('pressing it fills the screen (crops), and the viewer stays open', fill()=='cover' and not ev("document.getElementById('viewer').hidden") and ev("document.querySelector('#viewer .vfill').getAttribute('aria-pressed')")=='true' and ev("document.querySelector('#viewer .vfill').getAttribute('aria-label')")=='Fit to screen')
    ev("document.activeElement.blur()"); pg.keyboard.press('f'); pg.wait_for_timeout(200)
    check('F switches back to fit', fill()=='contain')
    pg.keyboard.press('F'); pg.wait_for_timeout(200)
    open_('mobil1')
    check('Fill is per post: the next post opens fitted', fill()=='contain' and ev("document.querySelector('#viewer .vfill').getAttribute('aria-pressed')")=='false')
    open_('quiet1')
    check('going back, the filled post is still filled', fill()=='cover')
    # readable over a white frame: the corner buttons carry their own dark glass
    lum = ev("(()=>{ const c=getComputedStyle(document.querySelector('#viewer .vclose')).backgroundColor.match(/[0-9.]+/g).map(Number); return {a:c[3]===undefined?1:c[3], rgb:c.slice(0,3)}; })()")
    check('the close and Fit / Fill buttons are dark glass, not a faint white tint', lum['a'] >= 0.5 and max(lum['rgb']) < 60)
    check('a filled post lights the Fit / Fill button solid', ev("getComputedStyle(document.querySelector('#viewer .vfill')).backgroundColor").startswith('rgba(255, 255, 255, 0.9'))
    open_('mobil1')
    check('a known SD RedGifs file is swapped for its HD name in full screen', vsrc()=='https://media.redgifs.com/MobileOne.mp4')
    open_('nohd11')
    check('when the HD file is missing, full screen falls back to the SD file', vsrc()=='https://media.redgifs.com/Nohd-mobile.mp4' and any('Nohd.mp4' in h for h in HITS))
    # RedGifs signs its file addresses for one visitor and they run out: an old address must not leave full screen on RedGifs' own (SD) player
    ev(seed('stale1', {'u': 'https://www.redgifs.com/watch/staleone', 'v': 'https://media.redgifs.com/Staleone-mobile.mp4?expires=%d&signature=old' % PAST, 'vh': 'https://media.redgifs.com/Staleone.mp4?expires=%d&signature=old' % PAST, 'rgDone': 1, 'ha': 0}))
    ev(seed('badsg1', {'u': 'https://www.redgifs.com/watch/badsig', 'v': 'https://media.redgifs.com/Badsig-mobile.mp4?expires=%d&signature=old' % FUTURE, 'vh': 'https://media.redgifs.com/Badsig.mp4?expires=%d&signature=old' % FUTURE, 'rgDone': 1, 'ha': 0}))
    ev('startCsvMode()'); pg.wait_for_timeout(1500)
    open_('stale1')
    check('a run-out RedGifs address is looked up again and full screen plays the fresh HD file', 'staleone' in LOOKUPS and vsrc().startswith('https://media.redgifs.com/Staleone.mp4?') and 'signature=new' in vsrc() and not ev("!!document.querySelector('#viewer iframe')"))
    open_('badsg1'); pg.wait_for_timeout(1500)
    check('when every kept address is refused, full screen looks the clip up once more and plays it in HD in our own player', 'badsig' in LOOKUPS and vsrc().startswith('https://media.redgifs.com/Badsig.mp4?') and 'signature=new' in vsrc() and not ev("!!document.querySelector('#viewer iframe')") and not ev("!!META.badsg1.rgGone"))
    check('a signed SD address is not turned into a made-up HD one', ev("rgHd('https://media.redgifs.com/A-mobile.mp4?expires=1&signature=x')") == '' and ev("rgHd('https://media.redgifs.com/A-mobile.mp4')") == 'https://media.redgifs.com/A.mp4')
    open_('pic111'); ev("document.querySelector('#viewer .vfill').click()"); pg.wait_for_timeout(200)
    check('pictures fill the screen too', ev("(()=>{ const i=document.querySelector('#viewer .vstage img'); return !!i && getComputedStyle(i).objectFit==='cover'; })()"))
    ev("closeViewer()"); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(1500)
    ev(seed('pic111', {'m': 'image', 'u': 'https://i.example.com/a.png', 'th': 'https://i.example.com/a.png', 'w': 100, 'h': 300})); ev(seed('nofile', {'u': 'https://www.redgifs.com/watch/nofileone', 'v': '', 'rgDone': 1})); ev('startCsvMode()'); pg.wait_for_timeout(1500)
    open_('pic111')
    check('Fill screen is remembered for that post after a reload', ev("document.getElementById('viewer').classList.contains('vcover')") and ev("document.querySelector('#viewer .vfill').getAttribute('aria-pressed')")=='true')
    open_('nofile')
    check('no Fit / Fill button over RedGifs\' own player', bool(ev("!!document.querySelector('#viewer iframe.vrg')")) and ev("getComputedStyle(document.querySelector('#viewer .vfill')).display")=='none')
    check('the shortcut is listed', 'fills the screen' in ev("document.getElementById('kbhelp').textContent"))
    # phone
    ph = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pp = ph.new_page(); pp.route('**/*', handle)
    pp.goto('http://127.0.0.1:%d/index.html' % port); pp.wait_for_timeout(1000)
    pp.evaluate(seed('quiet1', {'u': 'https://www.redgifs.com/watch/quietone', 'v': 'https://v.redd.it/q/silent.mp4'})); pp.evaluate('startCsvMode()'); pp.wait_for_timeout(2500)
    pp.evaluate("openViewer(POSTS.find(x=>x.id==='quiet1'))"); pp.wait_for_timeout(1500)
    r = pp.evaluate("(()=>{ const a=document.querySelector('#viewer .vfill').getBoundingClientRect(), c=document.querySelector('#viewer .vclose').getBoundingClientRect(); return {l:a.left, t:a.top, w:a.width, cl:c.left}; })()")
    check('phone: the button sits top left, clear of the close button', r['l'] < 40 and r['t'] < 40 and r['w'] >= 40 and r['cl'] > 300)
    pp.tap('#viewer .vfill'); pp.wait_for_timeout(200)
    check('phone: a tap fills the screen', pp.evaluate("getComputedStyle(document.querySelector('#viewer .vstage video')).objectFit")=='cover')
    pp.screenshot(path=os.path.join(os.environ.get('SHOT_DIR', '/tmp'), 'viewfill_phone.png'))
    check('no page errors', not errs)
    if errs: print(errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
