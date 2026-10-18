"""Stock 'it was probably deleted' picture is treated as broken. Run: python tests/gone_pic_test.py"""
import os, io, base64
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
def uri(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
sample = os.path.join(os.path.dirname(__file__), 'fixtures', 'gone_sample.png')
imgs = {}
if os.path.exists(sample): imgs['stock picture, scaled'] = (uri(Image.open(sample).convert('RGB')), True)
imgs['161x81 anything'] = (uri(Image.new('RGB', (161, 81), (200, 40, 40))), True)
photo = Image.new('RGB', (320, 200), (180, 120, 60)); ImageDraw.Draw(photo).rectangle((40, 40, 200, 150), fill=(30, 90, 160))
imgs['ordinary picture'] = (uri(photo), False)
dark = Image.new('RGB', (320, 200), (0, 0, 0)); ImageDraw.Draw(dark).text((20, 90), 'a dark meme with a caption', fill=(255, 255, 255))
imgs['dark picture with caption'] = (uri(dark), False)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(1000)
    for name, (u, want) in imgs.items():
        got = pg.evaluate("""u=>new Promise(res=>{ const im=new Image(); im.onload=()=>res(isGonePic(im)); im.src=u; })""", u)
        check(name + (' -> broken' if want else ' -> fine'), got == want)
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
