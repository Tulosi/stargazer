"""Generates the original artwork used by shoot.py (no real posts or photos). Run: python tools/screenshots/make_images.py [palette]
Palettes: dusk (the old muted purples), graphite, graphite-soft, graphite-dark, field, lemon. With no name it uses DEFAULT (graphite-dark)."""
import os, sys, random, math
from PIL import Image, ImageDraw, ImageFilter
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_work')   # scratch folder, ignored by git
OUT = os.environ.get('SG_IMG') or WORK+'/img'
os.makedirs(OUT, exist_ok=True)
# each palette: sky-to-ground colour triples (top, middle, bottom), the soft glow, and the colour the ridges darken towards
PALETTES = {
  # muted purples and magentas (the old logo's colours)
  'dusk': ([((142,108,170),(98,68,138),(44,34,78)),((168,112,156),(118,70,124),(50,32,74)),((128,114,176),(88,74,142),(40,34,84)),((160,100,146),(108,62,114),(46,30,68)),((138,100,162),(94,66,124),(40,32,72)),((176,128,166),(124,84,134),(52,38,80)),((120,100,160),(84,66,126),(38,30,70)),((150,104,150),(102,64,112),(44,30,64))],(222,186,214),(34,26,64)),
  # warm neutral greys, like black-and-white film: the chrome carries no competing colour
  'graphite': ([((168,164,156),(116,112,104),(40,38,35)),((150,148,144),(102,100,96),(34,33,31)),((186,180,168),(128,122,112),(46,43,39)),((140,138,134),(92,90,86),(30,29,27)),((176,172,164),(120,116,108),(42,40,37)),((158,154,146),(108,104,98),(36,34,32)),((194,190,182),(136,132,124),(50,48,44)),((146,142,136),(98,94,88),(32,31,29))],(236,232,222),(22,21,19)),
  # graphite with the range pulled in: lighter ground, dimmer sky, ridges that only step down a little, a faint glow
  'graphite-soft': ([((140,137,131),(112,109,104),(78,76,71)),((128,126,122),(102,100,96),(72,70,67)),((150,145,136),(120,115,107),(84,80,74)),((122,120,117),(98,96,93),(68,67,64)),((144,140,133),(114,110,104),(80,77,72)),((134,130,124),(106,103,98),(74,72,68)),((156,152,145),(124,120,113),(88,85,80)),((126,123,118),(100,97,92),(70,68,64))],(176,172,163),(60,58,54)),
  # quiet real-world hues, all desaturated: sea, sage, sand, slate, rust, fog, olive, stone
  'field': ([((150,170,182),(92,116,132),(34,44,52)),((160,172,150),(106,122,98),(38,46,36)),((196,180,150),(150,128,96),(56,46,34)),((140,150,166),(90,100,118),(32,36,44)),((190,156,132),(140,98,76),(52,36,30)),((176,178,176),(122,126,126),(42,44,46)),((168,168,132),(116,116,82),(42,42,30)),((172,164,156),(120,112,104),(42,40,38))],(238,232,218),(22,22,22)),
  # graphite nights with the odd lemon-and-amber sunset: the theme's one colour, used sparingly
  'lemon': ([((150,146,138),(100,96,90),(34,32,30)),((214,196,120),(150,128,74),(44,38,28)),((140,138,134),(92,90,86),(30,29,27)),((166,160,150),(110,106,98),(38,36,33)),((226,206,110),(170,138,62),(52,42,26)),((146,142,136),(98,94,88),(32,31,29)),((176,170,160),(118,112,104),(40,38,35)),((200,180,112),(140,116,70),(42,36,28))],(250,234,150),(20,19,17)),
}
# the soft graphite range, the whole scene darker (about 70% brightness): sits low and quiet under Lemondrop's black chrome
_dim = lambda c, f=.7: tuple(int(v*f) for v in c)
PALETTES['graphite-dark'] = ([tuple(_dim(c) for c in tri) for tri in PALETTES['graphite-soft'][0]], _dim(PALETTES['graphite-soft'][1]), _dim(PALETTES['graphite-soft'][2]))
DEFAULT = 'graphite-dark'   # the README's look since Nov 2026 (Lemondrop): quiet, low-contrast, dark grey scenes
name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
PAL, GLOW, RIDGE = PALETTES[name]
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def scene(seed,w,h,path):
    r=random.Random(seed); top,mid,bot=PAL[seed%len(PAL)]
    im=Image.new('RGB',(w,h)); px=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; c=lerp(top,mid,t/0.6) if t<0.6 else lerp(mid,bot,(t-0.6)/0.4); px.line([(0,y),(w,y)],fill=c)
    # a soft, dim glow instead of a bright sun
    glow=Image.new('L',(w,h),0); gd=ImageDraw.Draw(glow); cx,cy,rad=r.randint(w//5,4*w//5),int(h*r.uniform(.3,.55)),int(min(w,h)*r.uniform(.10,.18))
    gd.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=120); glow=glow.filter(ImageFilter.GaussianBlur(rad*.8))
    im=Image.composite(Image.new('RGB',(w,h),GLOW),im,glow.point(lambda v:int(v*.55)))
    d=ImageDraw.Draw(im)
    for k in range(4):
        base=h*(.55+k*.1); amp=h*(.12-k*.015); ph=r.uniform(0,6); fr=r.uniform(1.5,3.5)
        col=lerp(bot,RIDGE,.15+k*.14)
        pts=[(0,h)]+[(x,base-amp*abs(math.sin(x/w*fr*3+ph))-amp*.4*math.sin(x/w*fr*9+ph*2)) for x in range(0,w+8,8)]+[(w,h)]
        d.polygon(pts,fill=col)
    im=im.filter(ImageFilter.GaussianBlur(.8)); im.save(path,quality=82)
sizes=[(800,560),(560,800),(800,800),(900,520),(640,800),(800,600),(520,800),(800,640)]
for i in range(24):
    w,h=sizes[i%len(sizes)]; scene(i+3,w,h,f'{OUT}/{i}.jpg')
print('ok', name)
