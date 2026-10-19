"""Generates the original artwork used by shoot.py (no real posts or photos). Run: python tools/screenshots/make_images.py"""
import os, random, math
from PIL import Image, ImageDraw, ImageFilter
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_work')   # scratch folder, ignored by git
os.makedirs(WORK+'/img', exist_ok=True)
# Muted purples and magentas (the logo's colours, desaturated and low in contrast so the screenshots stay calm in dark mode)
PAL=[((142,108,170),(98,68,138),(44,34,78)),((168,112,156),(118,70,124),(50,32,74)),((128,114,176),(88,74,142),(40,34,84)),((160,100,146),(108,62,114),(46,30,68)),((138,100,162),(94,66,124),(40,32,72)),((176,128,166),(124,84,134),(52,38,80)),((120,100,160),(84,66,126),(38,30,70)),((150,104,150),(102,64,112),(44,30,64))]
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def scene(seed,w,h,path):
    r=random.Random(seed); top,mid,bot=PAL[seed%len(PAL)]
    im=Image.new('RGB',(w,h)); px=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; c=lerp(top,mid,t/0.6) if t<0.6 else lerp(mid,bot,(t-0.6)/0.4); px.line([(0,y),(w,y)],fill=c)
    # a soft, dim glow instead of a bright sun
    glow=Image.new('L',(w,h),0); gd=ImageDraw.Draw(glow); cx,cy,rad=r.randint(w//5,4*w//5),int(h*r.uniform(.3,.55)),int(min(w,h)*r.uniform(.10,.18))
    gd.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=120); glow=glow.filter(ImageFilter.GaussianBlur(rad*.8))
    im=Image.composite(Image.new('RGB',(w,h),(222,186,214)),im,glow.point(lambda v:int(v*.55)))
    d=ImageDraw.Draw(im)
    for k in range(4):
        base=h*(.55+k*.1); amp=h*(.12-k*.015); ph=r.uniform(0,6); fr=r.uniform(1.5,3.5)
        col=lerp(bot,(34,26,64),.15+k*.14)
        pts=[(0,h)]+[(x,base-amp*abs(math.sin(x/w*fr*3+ph))-amp*.4*math.sin(x/w*fr*9+ph*2)) for x in range(0,w+8,8)]+[(w,h)]
        d.polygon(pts,fill=col)
    im=im.filter(ImageFilter.GaussianBlur(.8)); im.save(path,quality=82)
sizes=[(800,560),(560,800),(800,800),(900,520),(640,800),(800,600),(520,800),(800,640)]
for i in range(24):
    w,h=sizes[i%len(sizes)]; scene(i+3,w,h,f'{WORK}/img/{i}.jpg')
print('ok')
