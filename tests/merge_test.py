"""Checks the merge rules in the page. Run: python tests/merge_test.py   (needs: pip install playwright; playwright install chromium)"""
import os, sys
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
JS = """()=>{
  const T=csv=>csvToRows(csv), P='https://www.reddit.com/r/a/comments/', out={};
  const local=T('id,permalink,starred,updated,deleted\\r\\naaaaa1,'+P+'aaaaa1/x/,1,10,\\r\\nbbbbb1,'+P+'bbbbb1/x/,,50,1\\r\\n');
  const legacy=T('id,permalink,starred\\r\\naaaaa1,x,\\r\\nbbbbb1,x,1\\r\\nccccc1,x,1\\r\\n');
  let m=mergeSets(local,legacy);
  out.legacyKeepsDelete = m.tombs.has('bbbbb1') && !m.rows.some(r=>r.id==='bbbbb1');
  out.legacyAddsNew = m.rows.some(r=>r.id==='ccccc1');
  out.legacyKeepsStar = m.rows.find(r=>r.id==='aaaaa1').starred===true;
  const A=T('id,permalink,starred,updated,deleted\\r\\naaaaa1,x,,100,1\\r\\nbbbbb1,x,,50,1\\r\\nccccc1,x,,5,\\r\\n');
  const B=T('id,permalink,starred,updated,deleted\\r\\naaaaa1,x,1,10,\\r\\nbbbbb1,x,,200,\\r\\nccccc1,x,1,120,\\r\\n');
  m=mergeSets(A,B); const m2=mergeSets(B,A);
  out.newerDeleteWins = m.tombs.has('aaaaa1'); out.newerResaveWins = m.rows.some(r=>r.id==='bbbbb1'); out.newerStarWins = m.rows.find(r=>r.id==='ccccc1').starred;
  const key=x=>JSON.stringify([x.rows.map(r=>r.id+r.starred+r.t).sort(),[...x.tombs.keys()].sort()]);
  out.symmetric = key(m)===key(m2);
  const m3=mergeSets({rows:m.rows,tombs:m.tombs},{rows:m.rows,tombs:m.tombs}); out.idempotent = sameState(m.rows,m.tombs,m3.rows,m3.tombs);
  const x=mergeSets(T('id,permalink,starred,updated,deleted\\r\\nddddd1,x,,7,\\r\\n'),T('id,permalink,starred,updated,deleted\\r\\nddddd1,x,,7,1\\r\\n')); out.tieTombstoneWins = x.rows.length===0 && x.tombs.size===1;
  return out; }"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1500)
    res = pg.evaluate(JS); b.close()
bad = [k for k, v in res.items() if not v]
print(res); sys.exit('FAILED: ' + ', '.join(bad) if bad else 0)
