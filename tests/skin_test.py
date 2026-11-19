"""Theme (Nov 2026): two skins, Lemondrop (default) and Legacy, each with a Dark mode switch (dark by default). Full screen stays dark in both modes.
Run: python tests/skin_test.py"""
import os
from playwright.sync_api import sync_playwright
PAGE = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site', 'index.html'))
bad = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: bad.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:')) else r.abort())
    pg.goto(PAGE); pg.wait_for_timeout(600); ev = pg.evaluate
    root = lambda: ev("[document.documentElement.dataset.skin, document.documentElement.dataset.theme]")
    bg = lambda: ev("getComputedStyle(document.body).backgroundColor")
    check('a first visit opens on Lemondrop, dark', root() == ['lemondrop', 'dark'])
    check('Lemondrop dark paints the near-black background', bg() == 'rgb(11, 11, 10)')
    check('the Lemondrop logo shows and the drawn wordmark hides', ev("getComputedStyle(document.querySelector('.brand .sglogo')).display") != 'none' and ev("getComputedStyle(document.querySelector('.brand .logo')).display") == 'none')
    check('Theme lives in Display: Lemondrop / Legacy plus a Dark mode switch', ev("!!document.querySelector('#viewpanel #theme [data-skin=lemondrop]') && !!document.querySelector('#viewpanel #theme [data-skin=legacy]') && !!document.querySelector('#viewpanel #darkmode')"))
    check('there is no System choice any more', ev("!document.querySelector('#theme option, #theme [value=system]')"))
    check('Lemondrop is pressed and Dark mode is on', ev("document.querySelector('#theme [data-skin=lemondrop]').getAttribute('aria-pressed')") == 'true' and ev("document.getElementById('darkmode').checked"))
    ev("document.getElementById('viewtoggle').click()"); pg.wait_for_timeout(300)
    ev("const d=document.getElementById('darkmode'); d.click()"); pg.wait_for_timeout(200)
    check('switching Dark mode off gives Lemondrop light', root() == ['lemondrop', 'light'] and bg() == 'rgb(238, 237, 232)')
    pg.click('#theme [data-skin=legacy]'); pg.wait_for_timeout(200)
    check('Legacy keeps the light / dark choice', root() == ['legacy', 'light'] and bg() == 'rgb(244, 244, 245)')
    check('Legacy shows the gradient wordmark again', ev("getComputedStyle(document.querySelector('.brand .logo')).display") != 'none' and ev("getComputedStyle(document.querySelector('.brand .sglogo')).display") == 'none')
    pg.reload(); pg.wait_for_timeout(500)
    check('both choices are remembered across a reload', root() == ['legacy', 'light'] and ev("document.querySelector('#theme [data-skin=legacy]').getAttribute('aria-pressed')") == 'true' and not ev("document.getElementById('darkmode').checked"))
    ev("localStorage.setItem('saved-posts-skin','lemondrop')"); pg.reload(); pg.wait_for_timeout(500)
    ev("openSample()"); pg.wait_for_timeout(900)
    ev("openViewer(list[0])"); pg.wait_for_timeout(500)
    check('full screen stays black in Lemondrop light', ev("getComputedStyle(document.getElementById('viewer')).backgroundColor") == 'rgb(0, 0, 0)')
    check('Fit / Fill is one bare toggle that names the current framing', ev("getComputedStyle(document.querySelector('#viewer .vfill'),'::after').content") == '"FIT"' and ev("getComputedStyle(document.querySelector('#viewer .vfill')).backgroundColor") == 'rgba(0, 0, 0, 0)')
    check('no page errors', not errs)
    b.close()
raise SystemExit(1 if bad else 0)
