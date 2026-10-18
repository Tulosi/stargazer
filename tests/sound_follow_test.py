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
        gifs = [{'id': i, 'hasAudio': i.startswith('loud'), 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % i, 'hd': 'https://media.redgifs.com/%s.mp4' % i}} for i in ids]
        return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'gifs': gifs}))
    if 'api.redgifs.com/v2/gifs/' in u:
        slug = u.rsplit('/', 1)[1]; ha = slug.startswith('loud')
        body = json.dumps({'gif': {'hasAudio': ha, 'width': 160, 'height': 90, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % slug, 'hd': 'https://media.redgifs.com/%s.mp4' % slug, 'poster': ''}}})
        return r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*', 'access-control-allow-headers': '*'}, body=body)
    if u.startswith('https://media.redgifs.com/'): return r.fulfill(status=200, content_type='video/webm', headers={'access-control-allow-origin': '*'}, body=AUD if '/loud' in u else SIL)
    if u.startswith('https://v.redd.it/'): return r.fulfill(status=200, content_type='video/webm', body=SIL)
    return r.abort()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', handle)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(seed('loudaa', 'loudone', True)); ev(seed('loudbb', 'loudtwo', True))
    for i in range(30): ev(seed('fill%02d' % i, 'quietone', False))
    ev('startCsvMode()'); pg.wait_for_timeout(3500)
    T = lambda id: "document.querySelector('article.card[data-id=" + id + "] .thumb')"
    ev("(()=>{ const a=%s, b=%s; AUDIO.muted=false; a._soundOn=true; soundOnlyFor(a); })()" % (T('loudaa'), T('loudbb')))
    # a second card's speaker is pressed: simulate by the same path the button uses
    ev("(()=>{ const b=%s; soundOnlyFor(b); b._soundOn=true; applyAudio(); })()" % T('loudbb'))
    check('turning sound on for B turns it off for A', ev("(()=>{ return !%s._soundOn && %s._soundOn; })()" % (T('loudaa'), T('loudbb'))))
    ev("leftSound(%s)" % T('loudbb'))
    check('moving on from B mutes it and the global switch', ev("(()=>{ return !%s._soundOn && AUDIO.muted; })()" % T('loudbb')))
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
