"""Manual NSFW override on a saved tile. Run: python tests/nsfw_test.py (needs playwright + chromium)."""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
SEED = """(()=>{
 const add=(id,o)=>{ ROWS.push({id,perma:'https://www.reddit.com/r/pics/comments/'+id+'/hello/',starred:false,t:5}); ROWSET.add(id);
   META[id]={t:'Post '+id,o,th:'',m:'text',u:'',n:0,s:0,a:'',c:1700000000}; };
 add('aaaa11',0); add('bbbb22',1); startCsvMode(); })()"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1200); ev = pg.evaluate
    pg.click('#decktoggle'); ev(SEED); pg.select_option('#nsfw', 'blur'); pg.wait_for_timeout(500)
    btn = lambda i: ev("document.querySelector('article.card[data-id=\"%s\"] .nsfwbtn').textContent" % i)
    click = lambda i: (pg.dispatch_event('article.card[data-id="%s"] .nsfwbtn' % i, 'click'), pg.wait_for_timeout(500))
    perma = lambda i: ev("ROWS.find(r=>r.id==='%s').perma" % i)
    check('buttons start as Mark NSFW / Not NSFW', btn('aaaa11') == 'Mark NSFW' and btn('bbbb22') == 'Not NSFW')
    click('aaaa11')
    check('mark stored as ?nsfw=1', perma('aaaa11').endswith('/hello/?nsfw=1') and ev("isNsfw(POSTS.find(p=>p.id==='aaaa11'))") and btn('aaaa11') == 'Not NSFW')
    check('row stamped for sync', ev("LIB.cur.dirty.includes('aaaa11')"))
    check('survives csv round trip', ev("csvToRows(rowsToCsv(ROWS,TOMBS)).rows.find(r=>r.id==='aaaa11').perma.endsWith('?nsfw=1')"))
    pg.select_option('#nsfw', 'hide'); pg.wait_for_timeout(400)
    check('hidden under Hide', not ev("!!document.querySelector('article.card[data-id=\"aaaa11\"]')"))
    pg.select_option('#nsfw', 'blur'); pg.wait_for_timeout(400)
    click('aaaa11')
    check('toggle back removes the mark', perma('aaaa11') == 'https://www.reddit.com/r/pics/comments/aaaa11/hello/' and btn('aaaa11') == 'Mark NSFW')
    click('bbbb22')
    check('reddit-NSFW post can be forced SFW (?nsfw=0)', perma('bbbb22').endswith('?nsfw=0') and not ev("isNsfw(POSTS.find(p=>p.id==='bbbb22'))"))
    click('bbbb22')
    check('and back to automatic', perma('bbbb22') == 'https://www.reddit.com/r/pics/comments/bbbb22/hello/')
    check('newer edit beats older copy in a merge', ev("""(()=>{ const a=csvToRows('id,permalink,starred,updated,deleted\\r\\naaaa11,x?nsfw=1,,50,\\r\\n'), b=csvToRows('id,permalink,starred,updated,deleted\\r\\naaaa11,x,,10,\\r\\n'); return mergeSets(b,a).rows[0].perma==='x?nsfw=1'; })()"""))
    ev("deleteRows(['aaaa11']); syncSaveButtons()")
    check('button hidden once unsaved', ev("document.querySelector('article.card[data-id=\"aaaa11\"] .nsfwbtn').hidden"))
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
