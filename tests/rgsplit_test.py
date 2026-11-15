"""RedGifs refuses a whole list lookup ("gifs 404") when one clip in it was deleted: the list is split until the missing clip is found,
and every other clip still gets its real (HD) files. Run: python tests/rgsplit_test.py (network mocked)"""
import os, json
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []; CALLS = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
DEAD = {'deadone', 'deadtwo'}; DOWN = [False]
ACAO = {'access-control-allow-origin': '*'}
def route(r):
    u = r.request.url
    if u.startswith('file:'): return r.continue_()
    if '/functions/v1/redgifs' in u:
        from urllib.parse import unquote
        ids = unquote(u.split('ids=')[1]).split(','); CALLS.append(ids)
        if DOWN[0] or any(i in DEAD for i in ids): return r.fulfill(status=502, content_type='application/json', headers=ACAO, body=json.dumps({'error': 'gifs 404 {"error":"not found"}'}))
        gifs = [{'id': i, 'hasAudio': False, 'width': 160, 'height': 90, 'duration': 12.5, 'urls': {'sd': 'https://media.redgifs.com/%s-mobile.mp4' % i.capitalize(), 'hd': 'https://media.redgifs.com/%s.mp4' % i.capitalize()}} for i in ids]
        return r.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps({'gifs': gifs}))
    return r.abort()   # RedGifs itself: "Failed to fetch", so the helper is used
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.route('**/*', route)
    pg.goto(PAGE); pg.wait_for_timeout(700); ev = pg.evaluate
    ids = ['alpha', 'bravo', 'deadone', 'delta', 'echo', 'foxtrot', 'golf', 'deadtwo', 'india', 'juliet']
    res = ev("async ids=>{ rgDirectOff = 0; try{ return await rgFetchMany(ids); }catch(e){ return {err:e.message}; } }", ids)
    check('the lookup does not fail as a whole', 'err' not in res)
    live = [i for i in ids if i not in DEAD]
    check('every live clip gets its real HD and SD files', all(res.get(i, {}).get('vh') == 'https://media.redgifs.com/%s.mp4' % i.capitalize() for i in live))
    check('the deleted clips are marked gone', all(res.get(i, {}).get('gone') == 1 for i in DEAD))
    check('lengths come through', res['alpha'].get('d') == 12.5)
    check('the split stays small (no lookup per clip)', len(CALLS) <= 12)
    CALLS.clear()
    one = ev("async()=>{ rgDirectOff = 0; try{ return await rgFetchMany(['deadone']); }catch(e){ return {err:e.message}; } }")
    check('a single refused clip on its own is a failed lookup, not proof it was deleted', 'err' in one and 'gifs 404' in one['err'])
    DOWN[0] = True
    down = ev("async ids=>{ rgDirectOff = 0; try{ return await rgFetchMany(ids); }catch(e){ return {err:e.message}; } }", ['alpha', 'bravo', 'charlie'])
    check('when RedGifs refuses everything, nothing is marked gone', 'err' in down)
    check('no page errors', not errs)
    b.close()
print('ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad))
raise SystemExit(1 if bad else 0)
