"""Recovered posts play like any other card: an imgur video whose files are gone plays from the Wayback Machine's copy of ID.mp4, and a GIF whose only
surviving copy is the archived picture plays that picture on hover. Needs ffmpeg for a tiny clip. Run: python tests/recplay_test.py"""
import os, subprocess, shutil, tempfile, base64
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
if not shutil.which('ffmpeg'):
    print('skip (no ffmpeg)'); raise SystemExit(0)
d = tempfile.mkdtemp(); vid = os.path.join(d, 't.webm'); gif = os.path.join(d, 't.gif'); jpg = os.path.join(d, 't.jpg')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=3:size=160x120:rate=15', '-c:v', 'libvpx', '-b:v', '200k', vid], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=160x120:rate=5', gif], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=size=160x120', '-frames:v', '1', jpg], check=True)
VID, GIF, JPG = open(vid, 'rb').read(), open(gif, 'rb').read(), open(jpg, 'rb').read()
CSV = 'id,permalink,starred,updated,deleted\r\ng00001,https://www.reddit.com/r/gifs/comments/g00001/a/,0,1000,0\r\n'
SEED = "async(t)=>{ await persistRec({id:'demo',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; startCsvMode(); }"
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def run(meta):
        ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); asked = []
        def f(r):
            u = r.request.url
            if u.startswith('file:'): return r.continue_()
            asked.append(u)
            if 'web.archive.org' in u and u.endswith('i.imgur.com/ASBjSi1.mp4'): return r.fulfill(body=VID, content_type='video/webm')
            if 'web.archive.org' in u and u.endswith('i.imgur.com/ASBjSi1.jpg'): return r.fulfill(body=JPG, content_type='image/jpeg')
            if 'web.archive.org' in u and u.endswith('.gif'): return r.fulfill(body=GIF, content_type='image/gif')
            if 'i.imgur.com' in u or 'i.redd.it' in u: return r.fulfill(status=404, body='gone')
            return r.abort()
        pg.route('**/*', f); pg.goto(PAGE); pg.wait_for_timeout(800)
        pg.evaluate(SEED, CSV); pg.wait_for_timeout(700)
        pg.evaluate("(m)=>{ META[POSTS[0].id]=m; refresh(); }", meta); pg.wait_for_timeout(9000)
        bx = pg.query_selector('.card').bounding_box(); pg.mouse.move(bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 3); pg.wait_for_timeout(4000)
        st = pg.evaluate("()=>{ const t=document.querySelector('.card .thumb'), v=t.querySelector('video.clip'), i=t.querySelector('img.clip'); return {v:t.dataset.v||'', vid:!!v, playing:!!v && !v.paused && v.readyState>=2, src:v?v.currentSrc:'', img: i ? i.src : '', ctl:!!document.querySelector('.card .ctl .pp')}; }")
        ctx.close(); return st
    st = run({'t': 'Video', 'o': 0, 'th': 'https://web.archive.org/web/20230509175231im_/https://i.imgur.com/ASBjSi1.jpg', 'm': 'video', 'u': 'https://i.imgur.com/ASBjSi1.mp4', 'n': 0, 's': 0, 'a': '', 'c': 1, 'rec': 'Wayback', 'v': 'https://i.imgur.com/ASBjSi1.mp4'})
    check('recovered imgur video: the archived ID.mp4 plays on hover with player controls (%s)' % st, st['vid'] and st['playing'] and 'web.archive.org' in st['src'] and st['src'].endswith('ASBjSi1.mp4') and st['ctl'])
    st = run({'t': 'Video', 'o': 0, 'th': 'https://web.archive.org/web/20230509175231im_/https://i.imgur.com/ASBjSi1.jpg', 'm': 'video', 'u': 'https://imgur.com/ASBjSi1', 'n': 0, 's': 0, 'a': '', 'c': 1, 'rec': 'Arctic Shift'})
    check('recovered imgur video linked as a page: i.imgur.com/ID.mp4 and its archive copy are tried, the copy plays (%s)' % st, st['vid'] and st['playing'] and st['src'].endswith('ASBjSi1.mp4') and 'web.archive.org' in st['src'])
    st = run({'t': 'Gif', 'o': 0, 'th': '', 'm': 'gif', 'u': 'https://i.redd.it/gonegif1.gif', 'n': 0, 's': 0, 'a': '', 'c': 1, 'rec': 'Arctic Shift'})
    check('recovered GIF with only an archived copy: it plays on hover as the clip (%s)' % st, st['img'].startswith('https://web.archive.org/') and st['img'].endswith('gonegif1.gif'))
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
