#!/usr/bin/env python3
"""Generate native district-map miniatures from the actual source layouts."""
from pathlib import Path
from PIL import Image
import sys,json,struct
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
def put(p,s):(root/p).write_text(s)
def render_city(area,side):
 doc=json.loads((root/f'data/maps/{area}/map.json').read_text())
 L=next(l for l in json.loads((root/'data/layouts/layouts.json').read_text())['layouts'] if l['id']==doc['layout'])
 w,h=L['width'],L['height'];words=struct.unpack('<'+str(w*h)+'H',(root/L['blockdata_filepath']).read_bytes())
 ts=[root/'data/tilesets/primary/general',root/f'data/tilesets/secondary/battle_frontier_outside_{side}']
 imgs=[Image.open(t/'tiles.png') for t in ts];meta=[struct.unpack('<'+str(len((t/'metatiles.bin').read_bytes())//2)+'H',(t/'metatiles.bin').read_bytes()) for t in ts]
 pal=[list(tuple(map(int,s.split())) for s in (ts[0 if i<6 else 1]/'palettes'/f'{i:02}.pal').read_text().splitlines()[3:19]) for i in range(16)]
 cache={};im=Image.new('RGB',(w*16,h*16))
 for n,word in enumerate(words):
  mid=word&1023
  if mid not in cache:
   chunk=meta[mid>=512][(mid%512)*8:(mid%512)*8+8];tile=Image.new('RGB',(16,16))
   for layer in (0,1):
    for k in range(4):
     v=chunk[layer*4+k];tileID=v&1023;tx=(tileID%512%16)*8;ty=(tileID%512//16)*8
     pixels=imgs[tileID>=512].load()
     for yy in range(8):
      for xx in range(8):
       raw=pixels[tx+(7-xx if v&1024 else xx),ty+(7-yy if v&2048 else yy)]
       if layer==1 and not raw:continue
       tile.putpixel((k%2*8+xx,k//2*8+yy),pal[v>>12][raw])
   cache[mid]=tile
  im.paste(cache[mid],(n%w*16,n//w*16))
 im.save(out/f'{area}-native-map.png')
 box=Image.new('RGB',(112,112),'white'); thumb=im.copy();thumb.thumbnail((112,112),Image.Resampling.LANCZOS);box.paste(thumb,((112-thumb.width)//2,0))
 return box,doc,w,h,thumb.width
cities=[render_city('AscensionCity','west'),render_city('AscensionCityEast','east')]
combined=Image.new('RGB',(224,112));combined.paste(cities[0][0],(0,0));combined.paste(cities[1][0],(112,0))
q=combined.quantize(colors=12,method=Image.Quantize.MEDIANCUT)
palette=[(0,0,0),(255,255,255),(24,32,40),(176,176,176)]+[tuple(q.getpalette()[i*3:i*3+3]) for i in range(12)]
asset='/* Native district miniatures, generated from the actual source map. */\nstatic const u16 sRefreshMapPalette[16]={' + ','.join('RGB(%d,%d,%d)'%tuple(v//8 for v in c) for c in palette)+'};\n'
for j in range(2):
 pixels=q.crop((j*112,0,j*112+112,112));data=[]
 for ty in range(0,112,8):
  for tx in range(0,112,8):
   for y in range(8):
    for x in range(0,8,2):data.append((pixels.getpixel((tx+x,ty+y))+4)|((pixels.getpixel((tx+x+1,ty+y))+4)<<4))
 asset+=f'static const u8 sRefreshMap{j}[6272]={{\n'+''.join(','.join(str(v) for v in data[i:i+32])+',\n' for i in range(0,len(data),32))+'};\n'
put('src/ascension_city_map_assets.inc',asset)
