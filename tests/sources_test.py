"""A clip that links straight at an imgur .mp4 plays from that file first; Reddit's own mp4 preview (g.redditmedia.com ...gif?fm=mp4) is the fallback, and a failing source hands over to the next. Needs ffmpeg for a tiny test clip (skipped without it). Run: python tests/sources_test.py"""
import os, subprocess, shutil, tempfile
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
if not shutil.which('ffmpeg'):
    print('skip (no ffmpeg)'); raise SystemExit(0)
tmp = os.path.join(tempfile.mkdtemp(), 't.webm')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=3:size=160x120:rate=15', '-c:v', 'libvpx', '-b:v', '200k', tmp], check=True)
VID = open(tmp, 'rb').read()
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def run(imgur_ok):
        ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        def f(r):
            u = r.request.url
            if u.startswith('file:'): return r.continue_()
            if 'i.imgur.com/bGMep3M.mp4' in u: return r.fulfill(body=VID, content_type='video/mp4') if imgur_ok else r.abort()
            if 'g.redditmedia.com' in u: return r.fulfill(body=VID, content_type='video/mp4')
            return r.abort()
        pg.route('**/*', f); pg.goto(PAGE); pg.wait_for_timeout(800)
        csv = 'id,permalink,starred,updated,deleted\r\ng00001,https://www.reddit.com/r/gifs/comments/g00001/a/,0,1000,0\r\n'
        pg.evaluate("async(t)=>{ await persistRec({id:'demo',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; startCsvMode(); }", csv); pg.wait_for_timeout(700)
        pg.evaluate("()=>{ META[POSTS[0].id]={t:'Pesto',o:0,th:'',m:'gif',u:'http://i.imgur.com/bGMep3M.mp4',v:'https://g.redditmedia.com/FVpX.gif?fm=mp4&mp4-fragmented=false&s=1',n:3,s:10,a:'u',c:1,w:160,h:120}; refresh(); }"); pg.wait_for_timeout(1500)
        first = pg.evaluate("document.querySelector('.card .thumb').dataset.v")
        bx = pg.query_selector('.card').bounding_box(); pg.mouse.move(bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 3); pg.wait_for_timeout(2500)
        st = pg.evaluate("()=>{ const v=document.querySelector('.card video.clip'); return {first:document.querySelector('.card .thumb').dataset.v, vid:!!v, playing:!!v && !v.paused, src:v?v.currentSrc:'', ctl:!!document.querySelector('.card .ctl .seek')}; }")
        ctx.close(); return first, st
    first, st = run(True)
    check('the imgur file is the first source (https) (%s)' % first, first == 'https://i.imgur.com/bGMep3M.mp4')
    check('hover plays it with a scrub bar (%s)' % st, st['vid'] and st['playing'] and st['ctl'] and 'imgur' in st['src'])
    first, st = run(False)
    check('when imgur fails the Reddit preview takes over and plays (%s)' % st, st['vid'] and st['playing'] and 'g.redditmedia' in st['src'] and st['ctl'])
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
