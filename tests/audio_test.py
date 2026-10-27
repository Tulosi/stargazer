"""RedGifs sound, plus the sound controls on cards and in full screen. Run: python tests/audio_test.py (needs ffmpeg-made fixtures in tests/fixtures)"""
import os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', 'site'))
AUD = open(os.path.join(HERE, 'fixtures', 'clip_audio.webm'), 'rb').read(); SIL = open(os.path.join(HERE, 'fixtures', 'clip_silent.webm'), 'rb').read()
bad = []
FAIL_API = False
HELPER_OK = False
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
    global FAIL_API, HELPER_OK
    u = r.request.url
    if u.startswith('http://127.0.0.1'): return r.continue_()
    if 'api.redgifs.com/v2/auth/temporary' in u: return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body='{"token":"t"}')
    if '/functions/v1/redgifs' in u:
        if HELPER_OK:
            ids = u.split('ids=')[1].split(',')
            gifs = [{'id': i, 'hasAudio': True, 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % i, 'hd': 'https://media.redgifs.com/%s.mp4' % i}} for i in ids]
            return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'gifs': gifs}))
        return r.abort()
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
    pg.hover('article.card[data-id="loud11"] .thumb', position={'x': 6, 'y': 6}); pg.wait_for_timeout(1500)
    check('card shows the speaker for the clip with sound, with its volume flyout closed', ev("(()=>{ const c=document.querySelector('article.card[data-id=\"loud11\"] .ctl'); return !!c && c.classList.contains('has-sound') && !c.querySelector('.volwrap').classList.contains('open') && getComputedStyle(c.querySelector('.volfly')).display==='none' && c.querySelector('.vol').getBoundingClientRect().width>10; })()"))
    # touch screens: no hover, so the speaker button itself must make the card audible
    pg.hover('article.card[data-id="loud11"] .thumb', position={'x': 6, 'y': 6}); pg.wait_for_timeout(1000)
    pg.click('article.card[data-id="loud11"] .ctl .vol'); pg.wait_for_timeout(300)
    ev("(()=>{ const t=document.querySelector('article.card[data-id=\"loud11\"] .thumb'); t._hover=false; applyAudio(); })()")
    check('one press on the muted speaker turns sound on without opening the flyout', ev("!document.querySelector('article.card[data-id=\"loud11\"] .volwrap').classList.contains('open') && !AUDIO.muted"))
    pg.click('article.card[data-id="loud11"] .ctl .vol'); pg.wait_for_timeout(300)
    check('the next press opens a vertical volume slider', ev("(()=>{ const w=document.querySelector('article.card[data-id=\"loud11\"] .volwrap'); const r=w.querySelector('.volr').getBoundingClientRect(), f=w.querySelector('.volfly').getBoundingClientRect(); return w.classList.contains('open') && f.height>60 && f.width<50 && r.height>60 && r.width<40; })()"))
    pg.click('article.card[data-id="loud11"] .ctl .vol'); pg.wait_for_timeout(300)
    check('and the press after that closes it, sound still on', ev("!document.querySelector('article.card[data-id=\"loud11\"] .volwrap').classList.contains('open') && !AUDIO.muted"))
    check('card stays audible after its speaker was pressed even without hover', ev("(()=>{ const v=document.querySelector('article.card[data-id=\"loud11\"] video.clip'); return !!v && v.muted===false; })()"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    ev("AUDIO.muted=true")
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    pg.hover('article.card[data-id="quiet2"] .thumb', position={'x': 6, 'y': 6}); pg.wait_for_timeout(1500)
    check('no sound controls on the silent clip', ev("(()=>{ const c=document.querySelector('article.card[data-id=\"quiet2\"] .ctl'); return !!c && !c.classList.contains('has-sound'); })()"))
    check('pause button is an svg icon, not an emoji glyph', ev("!!document.querySelector('article.card[data-id=\"quiet2\"] .ctl .pp svg') && !/[\\u23F8\\u25B6]/.test(document.querySelector('article.card[data-id=\"quiet2\"] .ctl .pp').textContent)"))
    pg.mouse.move(5, 5); pg.wait_for_timeout(300); pg.hover('article.card[data-id="loud11"] .thumb', position={'x': 6, 'y': 6}); pg.wait_for_timeout(2200)   # pointer stays on the card, as when pressing its full screen button
    ev("(()=>{ const t=document.querySelector('article.card[data-id=\"loud11\"] .thumb'); t._soundOn=true; AUDIO.muted=false; applyAudio(); })()")
    check('card is audible before opening full screen', ev("(()=>{ const v=document.querySelector('article.card[data-id=\"loud11\"] video.clip'); return !!v && v.muted===false; })()"))
    ev("(()=>{ window._cv=document.querySelector('article.card[data-id=\"loud11\"] video.clip'); const p=POSTS.find(x=>x.id==='loud11'); openViewer(p); })()"); pg.wait_for_timeout(300)
    check('full screen open: the card behind it is silenced', ev("(()=>{ const v=window._cv; return !!v && (v.muted===true || v.paused); })()"))
    ev("(()=>{ closeViewer(); const t=document.querySelector('article.card[data-id=\"loud11\"] .thumb'); t._soundOn=false; AUDIO.muted=true; applyAudio(); })()"); pg.wait_for_timeout(200)
    pg.dispatch_event('article.card[data-id="loud11"] button.fs', 'click'); pg.wait_for_timeout(1500)
    check('full screen: video opens muted', ev("(()=>{ const v=document.querySelector('#viewer video'); return !!v && v.muted===true && /loudone\\.mp4/.test(v.src); })()"))
    check('full screen: global mute untouched', ev('AUDIO.muted') is True)
    check('full screen: our own player bar with a speaker (no browser controls)', ev("(()=>{ const c=document.querySelector('#viewer .vctl'); return !!c && c.classList.contains('has-sound') && !document.querySelector('#viewer video').controls; })()"))
    check('slider shows 0 while muted', ev("document.querySelector('#viewer .vctl .volr').value==='0'"))
    pg.click('#viewer .vctl .vol'); pg.wait_for_timeout(200)
    check('speaker unmutes', ev("document.querySelector('#viewer video').muted===false"))
    pg.click('#viewer .vctl .vol'); pg.wait_for_timeout(200)
    check('second press opens the volume flyout', ev("document.querySelector('#viewer .vctl .volwrap').classList.contains('open')"))
    ev("(()=>{ const r=document.querySelector('#viewer .vctl .volr'); r.value=0; r.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(200)
    check('slider to 0 mutes', ev("document.querySelector('#viewer video').muted===true"))
    ev("(()=>{ const r=document.querySelector('#viewer .vctl .volr'); r.value=40; r.dispatchEvent(new Event('input')); })()"); pg.wait_for_timeout(200)
    check('slider unmutes and sets level', ev("(()=>{ const v=document.querySelector('#viewer video'); return v.muted===false && Math.abs(v.volume-0.4)<0.02; })()"))
    check('a small clip is scaled to fill the full-screen stage', ev("(()=>{ const v=document.querySelector('#viewer video'), s=document.querySelector('#viewer .vstage').getBoundingClientRect(), r=v.getBoundingClientRect(); return Math.abs(r.width-s.width)<2 && Math.abs(r.height-s.height)<2; })()"))
    ev("document.querySelector('#viewer .vctl .volwrap').classList.remove('open')"); pg.mouse.move(600, 200); pg.wait_for_timeout(300)
    playing = lambda: ev("!document.querySelector('#viewer video').paused")
    ev("document.activeElement.blur()"); was = playing(); pg.keyboard.press(' '); pg.wait_for_timeout(300)
    check('Space plays / pauses the clip in full screen (and does not close it)', playing() != was and not ev("document.getElementById('viewer').hidden"))
    pg.click('#viewer .vctl .pp'); pg.wait_for_timeout(300)
    check('the play button toggles the clip', playing() == was)
    if not playing(): pg.click('#viewer .vctl .pp'); pg.wait_for_timeout(300)
    pg.mouse.move(600, 150); pg.wait_for_timeout(3200)
    check('the player bar fades while a clip plays untouched', ev("document.getElementById('viewer').classList.contains('vidle')"))
    pg.mouse.move(640, 160); pg.wait_for_timeout(200)
    check('moving the mouse brings it back', not ev("document.getElementById('viewer').classList.contains('vidle')"))
    pg.click('#viewer .vctl .vfs'); pg.wait_for_timeout(300)
    check('the exit full screen button in the player bar closes full screen', ev("document.getElementById('viewer').hidden"))
    pg.dispatch_event('article.card[data-id="quiet2"] button.fs', 'click'); pg.wait_for_timeout(1500)
    check('full screen: no speaker for a clip without sound', ev("(()=>{ const c=document.querySelector('#viewer .vctl'); return !!c && !c.classList.contains('has-sound'); })()"))
    # RedGifs refused in the browser, but the Supabase helper answers: the real file with sound is used
    HELPER_OK = True; FAIL_API = True; ev('rgDirectOff = 0; rgBlockedUntil = 0')
    ev(seed('viahelp', 'helperone', True)); ev('startCsvMode()'); pg.wait_for_timeout(3000)
    check('helper fallback gives the full file with sound', ev("META.viahelp.v")=='https://media.redgifs.com/helperone.mp4' and ev("META.viahelp.ha")==1 and ev("META.viahelp.rgDone")==1)
    HELPER_OK = False
    # RedGifs lookup blocked: fall back to RedGifs' own player in full screen, and say why
    FAIL_API = True; ev('rgDirectOff = 0; rgBlockedUntil = 0')
    ev(seed('blocked', 'blockedone', True)); ev('startCsvMode()'); pg.wait_for_timeout(500)
    pg.dispatch_event('article.card[data-id="blocked"] button.fs', 'click'); pg.wait_for_timeout(2000)
    check('blocked lookup: full screen plays the clip the card has, in our own player (no RedGifs player)', ev("(()=>{ const v=document.querySelector('#viewer video'); return !!v && /silent\\.mp4/.test(v.src) && !document.querySelector('#viewer iframe') && !!document.querySelector('#viewer .vctl'); })()"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # no clip file at all: RedGifs' own player is the fallback, and the page says why
    ev(seed('nofile', 'nofileone', True)); ev("META.nofile.v=''"); ev('startCsvMode()'); pg.wait_for_timeout(500)
    pg.dispatch_event('article.card[data-id="nofile"] button.fs', 'click'); pg.wait_for_timeout(2000)
    check('no clip file: official RedGifs player shown', ev("(document.querySelector('#viewer iframe.vyt')||{}).src")=='https://www.redgifs.com/ifr/nofileone')
    check('no clip file: plain-language reason is shown', 'RedGifs player' in ev("document.getElementById('toast').textContent"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # lookup blocked, but Reddit's embed data names the file: use it right away (it carries the sound)
    ev("(()=>{ const id='gues11'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); META[id]={t:'clip',o:0,th:'',m:'gif',u:'https://www.redgifs.com/watch/camelname',g:'CamelName',n:0,s:0,a:'',c:1700000000,v:'https://v.redd.it/x/silent.mp4',w:160,h:90}; startCsvMode(); })()")
    pg.wait_for_timeout(2500)
    check('blocked lookup: full file from the embed name replaces the silent preview', ev("META.gues11.v")=='https://media.redgifs.com/CamelName.mp4')
    check('no page errors', not errs)
    if errs: print(errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
