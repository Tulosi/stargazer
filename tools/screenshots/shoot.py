"""Takes the README screenshots from invented sample posts (nothing from a real account). Run make_images.py first, then: python tools/screenshots/shoot.py"""
import os, re, random, time
from playwright.sync_api import sync_playwright
from PIL import Image
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_work')   # scratch folder, ignored by git
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PAGE='file://'+os.path.join(ROOT,'site','index.html')
IMG=WORK+'/img/%s.jpg'
subs=['pics','art','wallpapers','minimalism','CozyPlaces','itookapicture']
titles=['Sunrise over the ridge, 6am','Layers of dusk','Quiet valley after the storm','Evening glow, no filter','Mountain silhouettes at golden hour','Pastel horizon','Last light on the hills','Morning haze, three ridges deep','A calm blue ending to the day','Warm sky, cool hills','Hills in magenta','Where the sun meets the ridge','Late summer sunset','Foggy layers','Sunset study no. 4','Violet hour','Cloudless and quiet','Dawn colours','The long way home','Soft gradient skies','Mountain wallpaper 4K','Sleepy hills','Peach and plum sky','Twilight ridge line']
authors=['dusk_walker','paperlantern','hillside_notes','northwind42','quietframes','softfocus','roamingeye','lumen_lane']
H='id,permalink,starred,updated,deleted\r\n'
N=24
rows=''.join('s%05d,https://www.reddit.com/r/%s/comments/s%05d/%s/,%d,1000,0\r\n'%(i,subs[i%len(subs)],i,re.sub(r'\W+','_',titles[i].lower())[:30],1 if i in (1,4,9,14) else 0) for i in range(N))
sizes=[(800,560),(560,800),(800,800),(900,520),(640,800),(800,600),(520,800),(800,640)]
now=1760000000
def meta_js():
    out=[]
    for i in range(N):
        w,h=sizes[i%8]
        out.append("POSTS[%d] && (META[POSTS[%d].id]={t:%r,o:0,th:'https://i.redd.it/%d.jpg',m:'image',u:'https://i.redd.it/%d.jpg',n:%d,s:%d,a:%r,c:%d,w:%d,h:%d});"%(i,i,titles[i],i,i,(i*37)%210+4,(i*911)%9000+120,authors[i%8],now-i*86400*9,w,h))
    return '()=>{ '+''.join(out)+' refresh(); document.getElementById("loadText").textContent=""; }'
def fulfil(r):
    u=r.request.url
    if 'redd.it' in u:
        m=re.search(r'/(\d+)\.jpg',u); 
        if m: return r.fulfill(path=IMG%m.group(1),content_type='image/jpeg')
    return r.continue_() if u.startswith('file:') else r.abort()
def session(b,vp,theme,dpr=1,mobile=False):
    ctx=b.new_context(viewport=vp,device_scale_factor=dpr,is_mobile=mobile,has_touch=mobile)
    ctx.add_init_script("try{localStorage.setItem('saved-posts-theme-reset1','1');localStorage.setItem('saved-posts-theme','%s');localStorage.setItem('saved-posts-seenimg','[]');}catch(e){}"%theme)
    pg=ctx.new_page(); pg.route('**/*',fulfil); pg.goto(PAGE); pg.wait_for_timeout(800)
    pg.evaluate("""async(t)=>{ await persistRec({id:'demo',name:'my-saved-posts.csv',text:t,handle:null,updated:Date.now()}); await activate(await idbReq('csv','readonly',s=>s.get('demo'))); for(const k in META) delete META[k]; startCsvMode(); }""",H+rows)
    pg.wait_for_timeout(700); pg.evaluate(meta_js()); pg.wait_for_timeout(300)
    return pg
def settle(pg,ms=10000): pg.wait_for_timeout(ms)
def snap(pg,path):
    pg.evaluate('document.getElementById("loadText").textContent=""'); pg.wait_for_timeout(200); pg.screenshot(path=path)
os.makedirs(WORK,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch()
    # 1 gallery (dark, masonry)
    pg=session(b,{'width':1400,'height':860},'dark'); settle(pg); pg.evaluate("window.scrollTo(0,0)"); snap(pg,WORK+'/gallery.png')
    # 2 filters panel (dark)
    pg.click('#decktoggle'); pg.wait_for_timeout(500); snap(pg,WORK+'/filters.png'); pg.context.close()
    # 3 list 2 columns (light)
    pg=session(b,{'width':1400,'height':760},'light'); pg.evaluate("document.querySelector('#layoutseg [data-l=list]').click()"); settle(pg,6000); snap(pg,WORK+'/list.png'); pg.context.close()
    # 4 bulk actions (light masonry)
    pg=session(b,{'width':1400,'height':760},'light'); settle(pg); pg.evaluate("()=>{ document.getElementById('selbtn').click(); [0,2,3,5].forEach(i=>SEL.ids.add(POSTS[i].id)); selPaint(); }"); pg.wait_for_timeout(500); snap(pg,WORK+'/bulk.png'); pg.context.close()
    # 5 phone (dark)
    pg=session(b,{'width':390,'height':780},'dark',2,True); settle(pg); snap(pg,WORK+'/phone.png'); pg.context.close()
for n,w in (('gallery',1400),('list',1400),('filters',1400),('bulk',1400),('phone',500)):
    im=Image.open(WORK+'/'+n+'.png').convert('RGB')
    if im.width!=w: im=im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
    im.save(os.path.join(ROOT,'docs','screenshots',n+'.jpg'),quality=82,optimize=True,progressive=True)
print('done')
