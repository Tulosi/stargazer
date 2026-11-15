"""Sort by clip length: Longest clips / Shortest clips, lengths from Reddit, RedGifs and from clips that load. Run: python tests/lensort_test.py (needs ffmpeg-made fixtures in tests/fixtures)"""
import os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', 'site'))
SIL = open(os.path.join(HERE, 'fixtures', 'clip_silent.webm'), 'rb').read()
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
def handle(r):
    u = r.request.url
    if u.startswith('http://127.0.0.1'): return r.continue_()
    if u.startswith('https://i.example.com/'): return r.fulfill(status=200, content_type='video/webm', body=SIL)
    return r.abort()
def seed(id, meta, i):
    return "(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/',starred:false,t:5}); ROWSET.add(id); META[id]=Object.assign({t:'post '+id,o:0,th:'',m:'video',n:0,s:0,a:'',c:%d,w:160,h:90}, %s); })()" % (id, 1700000000 + i, json.dumps(meta))
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1000, 'height': 800}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', handle)
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(seed('mid111', {'d': 30}, 1)); ev(seed('long11', {'d': 125.5}, 2)); ev(seed('short1', {'d': 4}, 3))
    ev(seed('pic111', {'m': 'image', 'u': 'https://i.example.com/a.png'}, 4)); ev(seed('unk111', {'m': 'video'}, 5))
    ev('startCsvMode()'); pg.wait_for_timeout(800); ev('state.hideBroken=false; refresh()'); pg.wait_for_timeout(300)   # these made-up clips have no files, so they would count as broken media
    check('both length sorts are offered', ev("!!document.querySelector('#sort option[value=long]') && !!document.querySelector('#sort option[value=short]')"))
    pick = lambda v: (ev("(()=>{ const s=document.getElementById('sort'); s.value='%s'; s.dispatchEvent(new Event('change')); })()" % v), pg.wait_for_timeout(400))
    order = lambda: ev("[...document.querySelectorAll('#grid article.card')].map(c=>c.dataset.id)")
    pick('long'); o = order()
    check('Longest clips: longest first, posts with no known length last', o[:3] == ['long11', 'mid111', 'short1'] and set(o[3:]) == {'pic111', 'unk111'})
    pick('short'); o = order()
    check('Shortest clips: shortest first, posts with no known length still last', o[:3] == ['short1', 'mid111', 'long11'] and set(o[3:]) == {'pic111', 'unk111'})
    check('the choice is remembered for the list', json.loads(ev("localStorage.getItem('saved-posts-listprefs')") or '{}') and 'short' in ev("localStorage.getItem('saved-posts-listprefs')"))
    # lengths from the post data
    d = ev("""slim({id:'x', title:'t', url:'https://v.redd.it/abc', media:{reddit_video:{fallback_url:'https://v.redd.it/abc/DASH_720.mp4', duration:42}}}).d""")
    check('Reddit video length is read from the post data', d == 42)
    d = ev("""slim({id:'x', title:'t', url:'https://i.imgur.com/a.gifv', preview:{reddit_video_preview:{fallback_url:'https://v.redd.it/p/DASH_480.mp4', duration:9}}}).d""")
    check("and from Reddit's video preview of a GIF", d == 9)
    check('RedGifs length is read from its lookup', ev("rgShape({urls:{sd:'https://media.redgifs.com/A-mobile.mp4', hd:'https://media.redgifs.com/A.mp4'}, duration:17.04}).d") == 17)
    # a clip that loads tells its length
    ev("(()=>{ const v=document.createElement('video'); v.muted=true; v.src='https://i.example.com/unk.webm'; document.querySelector('article.card[data-id=\"unk111\"]').appendChild(v); })()"); pg.wait_for_timeout(1500)
    check('a clip that loads records its length on the post', (ev("META.unk111.d") or 0) > 0)
    pick('long'); o = order()
    check('and then sorts with the other clips', 'unk111' in o[:4] and o[-1] == 'pic111')
    check('no page errors', not errs)
    if errs: print(errs)
    b.close()
srv.shutdown()
raise SystemExit(1 if bad else 0)
