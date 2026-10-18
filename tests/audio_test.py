"""RedGifs sound, plus the sound controls on cards and in full screen. Run: python tests/audio_test.py (needs ffmpeg-made fixtures in tests/fixtures)"""
import os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', 'site'))
AUD = open(os.path.join(HERE, 'fixtures', 'clip_audio.webm'), 'rb').read(); SIL = open(os.path.join(HERE, 'fixtures', 'clip_silent.webm'), 'rb').read()
bad = []
FAIL_API = False
BATCH = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
def seed(id, slug, has_audio):
    return """(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id);
      META[id]={t:'clip',o:0,th:'',m:'gif',u:'https://www.redgifs.com/watch/%s',n:0,s:0,a:'',c:1700000000,v:'https://v.redd.it/%s/silent.mp4',w:160,h:90}; })()""" % (id, slug, id)
def handle(r):
    global FAIL_API
    u = r.request.url
    if u.startswith('http://127.0.0.1'): return r.continue_()
    if 'api.redgifs.com/v2/auth/temporary' in u: return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body='{"token":"t"}')
    if FAIL_API and 'api.redgifs.com' in u: return r.abort()
    if 'api.redgifs.com/v2/gifs?ids=' in u:
        BATCH.append(u); ids = u.split('ids=')[1].split(',')
        gifs = [{'id': i, 'hasAudio': i == 'loudone', 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % i, 'hd': 'https://media.redgifs.com/%s.mp4' % i}} for i in ids]
        return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'gifs': gifs}))
    if 'api.redgifs.com/v2/gifs/' in u:
        slug = u.rsplit('/', 1)[1]; ha = slug == 'loudone'
        body = json.dumps({'gif': {'hasAudio': ha, 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % slug, 'hd': 'https://media.redgifs.com/%s.mp4' % slug, 'poster': ''}}})
        return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*', 'access-control-allow-headers': '*'}, body=body)
    if u.startswith('https://media.redgifs.com/'): return r.fulfill(status=200, content_type='video/webm', headers={'access-control-allow-origin': '*'}, body=AUD if 'loudone' in u else SIL)
    if u.startswith('https://v.redd.it/'): return r.fulfill(status=200, content_type='video/webm', body=SIL)
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', handle)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(seed('loud11', 'loudone', True)); ev(seed('quiet2', 'quietone', False)); ev('startCsvMode()'); pg.wait_for_timeout(500)
    pg.wait_for_timeout(2500)
    check('both clips were looked up in a single request', len(BATCH)==1 and 'loudone' in BATCH[0] and 'quietone' in BATCH[0])
    m = ev("({v:META.loud11.v, ha:META.loud11.ha, q:META.quiet2.ha, qv:META.quiet2.v, done:META.loud11.rgDone})")
    check('loud clip now uses the full RedGifs file with sound', m['v'] == 'https://media.redgifs.com/loudone.mp4' and m['ha'] == 1 and m['done'] == 1)
    check('silent clip is marked as having no sound', m['q'] == 0)
    pg.hover('article.card[data-id="loud11"] .thumb'); pg.wait_for_timeout(1500)
    check('card shows toggle and slider for the clip with sound', ev("(()=>{ const c=document.querySelector('article.card[data-id=\"loud11\"] .ctl'); return !!c && c.classList.contains('has-sound') && getComputedStyle(c.querySelector('.volr')).display!=='none' && c.querySelector('.volr').getBoundingClientRect().width>20 && c.querySelector('.vol').getBoundingClientRect().width>10; })()"))
    # touch screens: no hover, so the speaker button itself must make the card audible
    pg.hover('article.card[data-id="loud11"] .thumb'); pg.wait_for_timeout(1000)
    pg.click('article.card[data-id="loud11"] .ctl .vol'); pg.wait_for_timeout(300)
    ev("(()=>{ const t=document.querySelector('article.card[data-id=\"loud11\"] .thumb'); t._hover=false; applyAudio(); })()")
    check('card stays audible after its speaker was pressed even without hover', ev("(()=>{ const v=document.querySelector('article.card[data-id=\"loud11\"] video.clip'); return !!v && v.muted===false; })()"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    ev("AUDIO.muted=true")
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    pg.hover('article.card[data-id="quiet2"] .thumb'); pg.wait_for_timeout(1500)
    check('no sound controls on the silent clip', ev("(()=>{ const c=document.querySelector('article.card[data-id=\"quiet2\"] .ctl'); return !!c && !c.classList.contains('has-sound'); })()"))
    check('pause button is an svg icon, not an emoji glyph', ev("!!document.querySelector('article.card[data-id=\"quiet2\"] .ctl .pp svg') && !/[\\u23F8\\u25B6]/.test(document.querySelector('article.card[data-id=\"quiet2\"] .ctl .pp').textContent)"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    pg.dispatch_event('article.card[data-id="loud11"] button.fs', 'click'); pg.wait_for_timeout(1500)
    check('full screen: video opens muted', ev("(()=>{ const v=document.querySelector('#viewer video'); return !!v && v.muted===true && /loudone\\.mp4/.test(v.src); })()"))
    check('full screen: global mute untouched', ev('AUDIO.muted') is True)
    check('full screen: toggle and slider visible', ev("!document.querySelector('#viewer .vsound').hidden && !document.querySelector('#viewer .vvol').hidden"))
    check('slider shows 0 while muted', ev("document.querySelector('#viewer .vvol').value==='0'"))
    pg.click('#viewer .vsound'); pg.wait_for_timeout(200)
    check('toggle unmutes', ev("document.querySelector('#viewer video').muted===false"))
    pg.click('#viewer .vsound'); pg.wait_for_timeout(200)
    check('toggle mutes again (slider to 0)', ev("document.querySelector('#viewer video').muted===true && document.querySelector('#viewer .vvol').value==='0'"))
    ev("(()=>{ const r=document.querySelector('#viewer .vvol'); r.value=40; r.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(200)
    check('slider unmutes and sets level', ev("(()=>{ const v=document.querySelector('#viewer video'); return v.muted===false && Math.abs(v.volume-0.4)<0.02; })()"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.dispatch_event('article.card[data-id="quiet2"] button.fs', 'click'); pg.wait_for_timeout(1500)
    check('full screen: no controls for a clip without sound', ev("document.querySelector('#viewer .vsound').hidden && document.querySelector('#viewer .vvol').hidden"))
    # RedGifs lookup blocked: fall back to RedGifs' own player in full screen, and say why
    FAIL_API = True
    ev(seed('blocked', 'blockedone', True)); ev('startCsvMode()'); pg.wait_for_timeout(500)
    pg.dispatch_event('article.card[data-id="blocked"] button.fs', 'click'); pg.wait_for_timeout(2000)
    check('blocked lookup: official RedGifs player shown', ev("(document.querySelector('#viewer iframe.vyt')||{}).src")=='https://www.redgifs.com/ifr/blockedone')
    check('blocked lookup: reason is shown', 'lookup failed' in ev("document.getElementById('toast').textContent"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('no page errors', not errs)
    if errs: print(errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
