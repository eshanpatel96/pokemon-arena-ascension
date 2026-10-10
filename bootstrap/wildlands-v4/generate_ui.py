#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys, math, random

root=Path(sys.argv[1])
out=root/'graphics/title_screen/wildlands_v4'
out.mkdir(parents=True,exist_ok=True)

def font(size,bold=True):
    paths=[
      '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
      '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
    ]
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def gba_export(img, stem):
    q=img.convert('RGB').quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    q.save(out/f'{stem}.png')
    (out/f'{stem}.raw').write_bytes(q.tobytes())
    pal=q.getpalette()[:768]
    data=bytearray()
    for i in range(256):
        r,g,b=pal[i*3:i*3+3]
        c=(r>>3)|((g>>3)<<5)|((b>>3)<<10)
        data += bytes((c&255,c>>8))
    (out/f'{stem}.gbapal').write_bytes(data)

# --- Title ---
im=Image.new('RGB',(240,160),(7,18,28)); d=ImageDraw.Draw(im)
# sky gradient
for y in range(92):
    t=y/91
    d.line((0,y,239,y),fill=(int(8+12*t),int(22+30*t),int(36+25*t)))
# moon/cloud banks
d.ellipse((177,12,211,46),fill=(174,202,196))
for x,y,w in [(14,34,60),(68,25,55),(142,38,70)]:
    d.ellipse((x,y,x+w,y+13),fill=(33,53,65))
    d.ellipse((x+12,y-5,x+w-13,y+10),fill=(39,60,72))
# distant mountains
d.polygon([(0,100),(36,61),(68,99)],fill=(35,55,62))
d.polygon([(38,100),(91,48),(138,100)],fill=(42,62,65))
d.polygon([(108,100),(156,58),(199,100)],fill=(31,49,57))
d.polygon([(163,100),(211,52),(239,97),(239,120),(160,120)],fill=(50,47,49))
# snow / spire
d.polygon([(78,62),(91,48),(104,67),(95,62),(89,66),(85,60)],fill=(176,196,186))
d.polygon([(146,72),(156,58),(165,75),(157,70),(152,74)],fill=(161,183,177))
# volcano glow
d.polygon([(176,101),(211,52),(239,99)],fill=(64,45,42))
d.polygon([(205,60),(211,52),(218,62),(214,61),(210,64)],fill=(233,123,46))
d.line((211,51,216,28),fill=(196,97,42),width=2)
# water / river
d.polygon([(0,116),(72,111),(111,119),(143,109),(240,118),(240,160),(0,160)],fill=(20,69,84))
d.polygon([(105,92),(116,92),(137,160),(114,160)],fill=(42,112,126))
# forest silhouettes
for x in range(2,96,8):
    h=15+(x*7)%15
    d.polygon([(x,116),(x+5,116-h),(x+10,116)],fill=(12,48,37))
for x in range(148,190,7):
    h=12+(x*3)%14
    d.polygon([(x,116),(x+4,116-h),(x+8,116)],fill=(18,45,35))
# five distant lair signals
stars=[(91,49),(25,77),(211,53),(186,85),(222,95)]
for x,y in stars:
    d.ellipse((x-2,y-2,x+2,y+2),fill=(255,221,91))
# title text
f1=font(18); f2=font(29); f3=font(8,False)
def centered(text,y,f,fill,stroke=0,sc=(0,0,0)):
    box=d.textbbox((0,0),text,font=f,stroke_width=stroke)
    x=(240-(box[2]-box[0]))//2
    d.text((x,y),text,font=f,fill=fill,stroke_width=stroke,stroke_fill=sc)
centered('POKEMON',4,f1,(244,206,72),2,(24,55,104))
centered('WILDLANDS',22,f2,(231,241,218),2,(24,70,55))
centered('THE ARENA HAS NO WALLS',146,f3,(221,233,220),1,(4,12,18))
gba_export(im,'title')

# --- World map ---
m=Image.new('RGB',(240,160),(15,30,31)); d=ImageDraw.Draw(m)
d.rectangle((5,7,234,133),fill=(23,53,47),outline=(159,184,144),width=2)
# region polygons
d.polygon([(7,9),(72,9),(81,54),(54,75),(7,64)],fill=(38,89,57))       # forest
d.polygon([(72,9),(161,9),(170,49),(135,63),(82,54)],fill=(78,88,80))   # highland
d.polygon([(161,9),(232,9),(232,66),(189,70),(170,49)],fill=(72,77,87)) # research
d.polygon([(7,64),(54,75),(64,110),(7,131)],fill=(36,93,103))           # coast
d.polygon([(54,75),(135,63),(189,70),(171,112),(64,110)],fill=(83,115,66)) # center
d.polygon([(189,70),(232,66),(232,131),(171,112)],fill=(135,100,58))    # badlands
d.polygon([(7,131),(64,110),(112,114),(96,131)],fill=(27,77,105))       # abyss
d.polygon([(112,114),(171,112),(232,131),(96,131)],fill=(115,57,42))   # ember
# river
d.line([(117,10),(114,35),(121,57),(119,82),(128,106),(126,130)],fill=(48,133,155),width=5)
# grid 16 x 12
x0,y0,x1,y1=7,9,232,131
for i in range(1,16):
    x=x0+(x1-x0)*i//16; d.line((x,y0,x,y1),fill=(46,67,61))
for j in range(1,12):
    y=y0+(y1-y0)*j//12; d.line((x0,y,x1,y),fill=(46,67,61))
# lairs
boss=[('L',1,2),('R',7,1),('M',13,2),('K',2,10),('H',13,10)]
for code,cx,cy in boss:
    x=x0+(x1-x0)*(2*cx+1)//32
    y=y0+(y1-y0)*(2*cy+1)//24
    d.ellipse((x-4,y-4,x+4,y+4),fill=(245,210,75),outline=(20,25,24))
    d.text((x-2.5,y-4),code,font=font(7),fill=(25,30,30))
# labels
d.text((8,136),'B3 LUGIA   H2 RAYQUAZA   N3 MEWTWO',font=font(7,False),fill=(229,236,215))
d.text((8,147),'C11 KYOGRE              N11 HO-OH',font=font(7,False),fill=(229,236,215))
d.text((8,1),'WILDLANDS FIELD MAP  •  16 x 12 SECTORS',font=font(8),fill=(237,237,214))
gba_export(m,'world_map')

print(out/'title.raw')
print(out/'world_map.raw')
