"""Generates the original artwork used by shoot.py (no real posts or photos). Run: python tools/screenshots/make_images.py"""
import os, random, math
from PIL import Image, ImageDraw, ImageFilter
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_work')   # scratch folder, ignored by git
os.makedirs(WORK+'/img', exist_ok=True)
PAL=[((255,183,94),(120,60,160),(30,20,70)),((255,120,120),(150,60,140),(25,25,80)),((140,220,255),(80,120,220),(20,30,90)),((255,230,150),(255,140,100),(90,40,110)),((170,255,210),(60,160,170),(15,50,90)),((255,170,220),(170,90,220),(40,25,100)),((255,200,120),(200,90,80),(60,20,60)),((190,200,255),(110,90,200),(25,20,70))]
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def scene(seed,w,h,path):
    r=random.Random(seed); top,mid,bot=PAL[seed%len(PAL)]
    im=Image.new('RGB',(w,h)); px=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; c=lerp(top,mid,t/0.6) if t<0.6 else lerp(mid,bot,(t-0.6)/0.4); px.line([(0,y),(w,y)],fill=c)
    sun=Image.new('RGB',(w,h),(0,0,0)); sd=ImageDraw.Draw(sun); cx,cy,rad=r.randint(w//5,4*w//5),int(h*r.uniform(.3,.55)),int(min(w,h)*r.uniform(.09,.17))
    sd.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=(255,245,220)); sun=sun.filter(ImageFilter.GaussianBlur(rad*.5))
    im=Image.blend(im,Image.composite(Image.new('RGB',(w,h),(255,240,210)),im,sun.convert('L')),.9) if False else Image.eval(Image.merge('RGB',[Image.blend(im.getchannel(i),sun.getchannel(i),.0) for i in range(3)]),lambda v:v)
    from PIL import ImageChops
    im=ImageChops.add(im,sun.point(lambda v:int(v*.8)))
    d=ImageDraw.Draw(im)
    for k in range(4):
        base=h*(.55+k*.1); amp=h*(.12-k*.015); ph=r.uniform(0,6); fr=r.uniform(1.5,3.5)
        col=lerp(bot,(10,10,35),.25+k*.2)
        pts=[(0,h)]+[(x,base-amp*abs(math.sin(x/w*fr*3+ph))-amp*.4*math.sin(x/w*fr*9+ph*2)) for x in range(0,w+8,8)]+[(w,h)]
        d.polygon(pts,fill=col)
    im=im.filter(ImageFilter.GaussianBlur(.6)); im.save(path,quality=82)
sizes=[(800,560),(560,800),(800,800),(900,520),(640,800),(800,600),(520,800),(800,640)]
for i in range(24):
    w,h=sizes[i%len(sizes)]; scene(i+3,w,h,f'{WORK}/img/{i}.jpg')
print('ok')
