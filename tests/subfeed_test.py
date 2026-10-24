"""Subreddit mode on a hosted page: a missing relay (404 from the page's own host) is never the reported reason, an empty archive answer says what it usually means, and a list hidden wholly by filters says which ones with a fix button. Run: python tests/subfeed_test.py"""
import os, json
from playwright.sync_api import sync_playwright
HTML = open(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'), encoding='utf-8').read()
ORIGIN = 'https://example.github.io/stargazer/'
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
def posts(n, nsfw):
    return {'data': [{'id': 'zz%04d' % i, 'title': 'Post %d' % i, 'subreddit': 'testsub', 'permalink': '/r/testsub/comments/zz%04d/post/' % i,
                      'created_utc': 1760000000 - i * 60, 'over_18': nsfw, 'author': 'someone', 'score': 5, 'num_comments': 1,
                      'url': 'https://i.redd.it/zz%04d.jpg' % i, 'post_hint': 'image',
                      'preview': {'images': [{'source': {'url': 'https://i.redd.it/zz%04d.jpg' % i, 'width': 600, 'height': 400}}]}} for i in range(n)]}
def run(arctic, check_fn):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1200, 'height': 800}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        def route(r):
            u = r.request.url
            if u.startswith(ORIGIN) and not '/relay/' in u:
                return r.fulfill(status=200, content_type='text/html', body=HTML) if u.rstrip('/').endswith('stargazer') or u.endswith('index.html') else r.fulfill(status=404, body='')
            if '/relay/' in u and u.startswith('https://example.github.io'): return r.fulfill(status=404, content_type='text/html', body='<h1>404</h1>')
            if 'arctic-shift' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps(arctic))
            if 'pullpush' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps({'data': []}))
            return r.abort()
        pg.route('**/*', route)
        pg.goto(ORIGIN); pg.wait_for_timeout(600)
        pg.evaluate("startSubMode(['testsub'])"); pg.wait_for_timeout(4000)
        check_fn(pg)
        check('no page errors', not errs)
        b.close()
def empty(pg):
    t = pg.evaluate("document.getElementById('loadText').textContent")
    check('the note blames Reddit refusing web pages, not the missing relay', 'does not let web pages read its live feed' in t and '404' not in t)
    check('an empty archive answer explains itself', 'archives returned no posts for r/testsub' in pg.evaluate("document.querySelector('#grid .empty').textContent"))
run({'data': []}, empty)
def hidden(pg):
    e = pg.evaluate("document.querySelector('#grid .empty') && document.querySelector('#grid .empty').textContent") or ''
    check('a list hidden wholly by the NSFW filter says so', '6 posts loaded, all hidden by filters: 6 NSFW' in e)
    pg.click('[data-empty=nsfw]'); pg.wait_for_timeout(500)
    check('Blur NSFW instead brings the posts back', pg.evaluate("document.querySelectorAll('#grid .card').length") == 6 and pg.evaluate("state.nsfw") == 'blur')
run(posts(6, True), hidden)
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
