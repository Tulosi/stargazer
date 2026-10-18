"""A post saved from the Subreddit viewer keeps its details (video, RedGifs name) in the list view even if no archive has it. Run: python tests/localmeta_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(800); ev = pg.evaluate
    ev("""()=>{ MODE='sub'; const id='abc123'; META[id]={t:'clip',o:0,th:'',m:'gif',u:'https://www.redgifs.com/watch/afraidobedientseabird',n:0,s:0,a:'',c:1700000000,v:'',w:640,h:360};
      toggleSave({id, perma:'/r/gifs/comments/abc123/x/', title:'clip'}); }""")
    pg.wait_for_timeout(500)
    check('details are kept for the saved post', ev("!!JSON.parse(localStorage.getItem('saved-posts-localmeta-v1')||'{}').abc123"))
    ev("localStorage.removeItem('saved-posts-meta-v7')")   # the 24 h cache is gone, the archives do not know the post
    pg.reload(); pg.wait_for_timeout(800)
    check('after a reload the details are back without any archive', ev("!!META.abc123 && /redgifs/.test(META.abc123.u)"))
    check('no page errors', not errs)
    b.close()
print('FAILED: ' + ', '.join(bad) if bad else 'ALL PASS')
