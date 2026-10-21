"""A GIF post's tile must show a still picture, not the animated file (browsers play GIFs on their own). Run: python tests/gifstill_test.py"""
import os, io
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
from PIL import Image
def make_gif():
    fr = [Image.new('RGB', (120, 80), c) for c in ((220, 40, 40), (40, 200, 60), (40, 60, 220))]; b = io.BytesIO(); fr[0].save(b, 'GIF', save_all=True, append_images=fr[1:], duration=200, loop=0); return b.getvalue()
def make_png():
    b = io.BytesIO(); Image.new('RGB', (120, 80), (90, 90, 90)).save(b, 'PNG'); return b.getvalue()
GIF, PNG = make_gif(), make_png()
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def run(label, th, check_fn, th_ok=True):
        ctx = b.new_context(viewport={'width': 1200, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        def fulfil(r):
            u = r.request.url
            if u.startswith('file:'): return r.continue_()
            if 'i.redd.it/g1.gif' in u or 'imgur-x.gif' in u: return r.fulfill(body=GIF, content_type='image/gif')
            if 'preview.redd.it/g1.gif' in u: return r.fulfill(body=PNG, content_type='image/png') if th_ok else r.abort()
            return r.abort()
        pg.route('**/*', fulfil); pg.goto(PAGE); pg.wait_for_timeout(800)
        csv = 'id,permalink,starred,updated,deleted\r\ng00001,https://www.reddit.com/r/gifs/comments/g00001/a_gif/,0,1000,0\r\n'
        pg.evaluate("async(t)=>{ await persistRec({id:'demo',name:'x.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; startCsvMode(); }", csv); pg.wait_for_timeout(700)
        pg.evaluate("(th)=>{ META[POSTS[0].id]={t:'A gif',o:0,th:th,m:'gif',u:'https://i.redd.it/g1.gif',n:3,s:10,a:'u',c:1,w:120,h:80}; refresh(); }", th); pg.wait_for_timeout(2500)
        res = check_fn(pg); ctx.close(); return res
    # 1. a normal preview exists: it is the picture, the animated file is never fetched as the still
    r = run('preview', 'https://preview.redd.it/g1.gif?format=png8&s=x', lambda pg: pg.evaluate("()=>{ const t=document.querySelector('.card .thumb'); const i=t.querySelector('img'); return {img:!!i, src:i?i.src:'', canvas:!!t.querySelector('canvas.still'), order:imgCandidates(POSTS[0]).map(u=>u.replace(/\\?.*/,''))}; }"))
    check('candidates put the still preview before the animated file (%s)' % r['order'], r['order'][0].endswith('preview.redd.it/g1.gif') and r['order'].index('https://i.redd.it/g1.gif') > 0)
    check('with a working preview the tile shows it as a plain picture', r['img'] and 'preview.redd.it' in r['src'])
    # 2. the preview fails: the animated file is the only picture left, and must be frozen on its first frame
    r = run('frozen', 'https://preview.redd.it/g1.gif?format=png8&s=x', lambda pg: pg.evaluate("()=>{ const t=document.querySelector('.card .thumb'); return {gifimg:[...t.querySelectorAll('img')].some(i=>/\\.gif/.test(i.src)&&!/preview/.test(i.src)), canvas:!!t.querySelector('canvas.still')}; }"), th_ok=False)
    check('when only the animated file is left the tile holds a frozen canvas, not the playing GIF (%s)' % r, r['canvas'] and not r['gifimg'])
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
