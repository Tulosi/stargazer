"""NSFW toggle look and tooltips, left-aligned tags, RedGifs fallback player filling the screen. Run: python tests/polish_test.py"""
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
SEED = """(()=>{ const id='%s'; ROWS.push({id,perma:'https://www.reddit.com/r/gifs/comments/'+id+'/x/'+'%s',starred:false,t:5}); ROWSET.add(id);
  META[id]={t:'clip',o:%d,th:'https://i.redd.it/a.jpg',m:'gif',u:'https://www.redgifs.com/watch/afraidobedientseabird',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360}; })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 700}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto('http://127.0.0.1:%d/index.html' % port); pg.wait_for_timeout(1000); ev = pg.evaluate
    ev(SEED % ('nsfw01', '?nsfw=1', 0)); ev(SEED % ('safe01', '', 0))
    ev('state.hideBroken=false; state.nsfw="show"'); ev('startCsvMode()'); pg.wait_for_timeout(1500)
    on = 'article.card[data-id=nsfw01]'; off = 'article.card[data-id=safe01]'
    check('on: tooltip says Unmark as NSFW', ev("document.querySelector('%s .nsfwb').title" % on) == 'Unmark as NSFW')
    check('off: tooltip says Mark as NSFW', ev("document.querySelector('%s .nsfwb').title" % off) == 'Mark as NSFW')
    gc = lambda sel, prop: ev("getComputedStyle(document.querySelector('%s .nsfwb'))['%s']" % (sel, prop))
    check('on: glass button, full white 18+, gradient ring', gc(on, 'backgroundColor') == 'rgba(12, 12, 14, 0.26)' and gc(on, 'color') == 'rgb(255, 255, 255)' and 'gradient' in ev("getComputedStyle(document.querySelector('%s .nsfwb'),'::before').backgroundImage" % on))
    check('on: stays visible with the card at rest', gc(on, 'opacity') == '1')
    check('off: hidden until the card is hovered', gc(off, 'opacity') == '0')
    pg.hover(off + ' .thumb'); pg.wait_for_timeout(300)
    check('off: appears when the card is hovered', gc(off, 'opacity') == '1')
    pg.hover(off + ' .nsfwb'); pg.wait_for_timeout(300)
    check('off: hovering previews the gradient ring', 'gradient' in ev("getComputedStyle(document.querySelector('%s .nsfwb'),'::before').backgroundImage" % off))
    pg.hover(on + ' .nsfwb'); pg.wait_for_timeout(300)
    check('on: hovering shows an X in place of 18+', 'url' in ev("getComputedStyle(document.querySelector('%s .nsfwb'),'::after').backgroundImage" % on) and ev("getComputedStyle(document.querySelector('%s .nsfwb svg')).opacity" % on) == '0')
    pg.mouse.move(2, 2); pg.wait_for_timeout(200)
    check('off and on look different', gc(on, 'color') != gc(off, 'color'))
    check('off button blurs behind it and has no outline', ev("(()=>{ const c=getComputedStyle(document.querySelector('%s .nsfwb')); return c.backdropFilter.includes('blur') && c.boxShadow==='none'; })()" % off))
    ev("document.querySelectorAll('.card').forEach(c=>c.classList.add('is-focus'))")
    pg.hover(on + ' .thumb'); pg.wait_for_timeout(300)
    r = ev("""(()=>{ const c=document.querySelector('%s'), m=c.querySelector('.badge.media').getBoundingClientRect(), t=c.querySelector('.badge.tag').getBoundingClientRect(), n=c.querySelector('.nsfwb').getBoundingClientRect(), cc=c.getBoundingClientRect(); return {ml:m.left-cc.left, tl:t.left-m.right, tr:t.right, nl:n.left}; })()""" % on)
    check('tags sit together on the left', r['ml'] < 14 and 0 <= r['tl'] <= 10)
    check('NSFW tag is clear of the controls', r['tr'] < r['nl'])
    # RedGifs fallback player fills the viewer
    ev("(()=>{ const p=POSTS.find(x=>x.id==='safe01'); META.safe01.rgGone=0; })()")
    pg.dispatch_event(off + ' button.fs', 'click'); pg.wait_for_timeout(1500)
    sz = ev("""(()=>{ const f=document.querySelector('#viewer iframe.vyt'); if(!f) return null; const s=document.querySelector('#viewer .vstage').getBoundingClientRect(), a=f.getBoundingClientRect(); return {w:a.width/s.width, h:a.height/s.height, src:f.src}; })()""")
    check('RedGifs player fills the whole viewer', sz and sz['w'] > .98 and sz['h'] > .98 and 'redgifs.com/ifr/' in sz['src'])
    check('no page errors', not errs)
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
