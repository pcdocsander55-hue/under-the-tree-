import math
from PIL import Image, ImageDraw
PINE=(31,59,45,255); GOLD=(201,162,39,255); WHITE=(255,255,255,255); CRAN=(164,36,59,255)
def rot(pts,c,a):
    ca,sa=math.cos(a),math.sin(a)
    return [(c[0]+(x-c[0])*ca-(y-c[1])*sa, c[1]+(x-c[0])*sa+(y-c[1])*ca) for x,y in pts]
def draw(S, pad=0.0, rounded=False):
    B=S*4; im=Image.new('RGBA',(B,B),(0,0,0,0) if rounded else PINE); d=ImageDraw.Draw(im)
    if rounded: d.rounded_rectangle([0,0,B-1,B-1],radius=B*0.22,fill=PINE)
    k=1-2*pad; o=B*pad; P=lambda x,y:(o+x*B*k,o+y*B*k); u=B*k
    c=P(0.53,0.56); a=math.radians(28)
    w,h=0.52*u,0.32*u; x0,y0,x1,y1=c[0]-w/2,c[1]-h/2,c[0]+w/2,c[1]+h/2; n=h*0.5
    tag=rot([(x0,c[1]),(x0+n,y0),(x1,y0),(x1,y1),(x0+n,y1)],c,a)
    hole=rot([(x0+n*0.6,c[1])],c,a)[0]
    d.line([P(0.12,0.26),hole],fill=GOLD,width=int(u*0.02))
    d.polygon(tag,fill=WHITE)
    r=u*0.03; d.ellipse([hole[0]-r,hole[1]-r,hole[0]+r,hole[1]+r],fill=GOLD); r2=r*0.5; d.ellipse([hole[0]-r2,hole[1]-r2,hole[0]+r2,hole[1]+r2],fill=PINE)
    tc=rot([(c[0]+w*0.12,c[1])],c,a)[0]; th=h*0.62; top=tc[1]-th/2; base=tc[1]+th/2; tx=tc[0]
    d.polygon([(tx,top),(tx-th*0.28,top+th*0.5),(tx+th*0.28,top+th*0.5)],fill=PINE)
    d.polygon([(tx,top+th*0.25),(tx-th*0.42,base),(tx+th*0.42,base)],fill=PINE)
    d.rectangle([tx-th*0.06,base,tx+th*0.06,base+th*0.12],fill=PINE)
    s=u*0.018; d.regular_polygon((tx,top-s*0.4,s*1.5),6,fill=GOLD)
    for dx,dy in [(-0.12,0.45),(0.14,0.62),(-0.2,0.82),(0.22,0.9)]:
        px,py=tx+th*dx,top+th*dy; d.ellipse([px-s,py-s,px+s,py+s],fill=CRAN)
    return im.resize((S,S),Image.LANCZOS)
draw(180).convert('RGB').save('apple-touch-icon.png')
draw(192).convert('RGB').save('icon-192.png')
draw(512).convert('RGB').save('icon-512.png')
draw(512,pad=0.1).convert('RGB').save('icon-maskable-512.png')
draw(64,rounded=True).save('favicon-64.png')
