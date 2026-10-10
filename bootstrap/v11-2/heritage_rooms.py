#!/usr/bin/env python3
from pathlib import Path
from collections import Counter,deque
import hashlib,json,struct,sys
root=Path(sys.argv[1]); lp=root/'data/layouts/layouts.json'
d=json.loads(lp.read_text()); layouts={x['id']:x for x in d['layouts']}
rooms=json.loads((root/'v11-room-manifest.json').read_text())
sources=[
('LAYOUT_DESERT_RUINS',-1,5,'quarry'),
('LAYOUT_MT_CHIMNEY',11,12,'highland'),
('LAYOUT_PETALBURG_WOODS',15,9,'forest'),
('LAYOUT_MT_PYRE_SUMMIT',16,8,'crypt'),
('LAYOUT_TERRA_CAVE_END',4,4,'volcano'),
('LAYOUT_MARINE_CAVE_END',4,4,'ocean'),
('LAYOUT_NEW_MAUVILLE_INSIDE',11,10,'reactor'),
('LAYOUT_SKY_PILLAR_TOP',4,1,'sky-pillar'),
('LAYOUT_NAVEL_ROCK_TOP',3,5,'champion'),
('LAYOUT_SHOAL_CAVE_LOW_TIDE_ICE_ROOM',0,5,'ice'),
('LAYOUT_ANCIENT_TOMB',-1,5,'ancient-iron'),
('LAYOUT_MT_CHIMNEY',14,18,'storm'),
('LAYOUT_ISLAND_CAVE',-1,5,'crystal')]
assert len(rooms)==len(sources)==13
report=[]
for row,(sid,x0,y0,theme) in zip(rooms,sources):
    dst=layouts[row['layout']]; src=layouts[sid]
    assert(dst['width'],dst['height'])==(19,21)
    sw,sh=src['width'],src['height']
    a=struct.unpack('<%dH'%(sw*sh),(root/src['blockdata_filepath']).read_bytes())
    counts=Counter(x&0x3ff for x in a if not x&0xc00 and (x&0x3ff)>=512)
    if not counts:counts=Counter(x&0x3ff for x in a if not x&0xc00)
    assert counts
    floorid=counts.most_common(1)[0][0]; floor=0x3000|floorid
    default=a[(sh//2)*sw+sw//2]
    tiles=[a[(y+y0)*sw+x+x0] if 0<=x+x0<sw and 0<=y+y0<sh else default for y in range(21) for x in range(19)]
    def put(x,y,t):tiles[y*19+x]=t
    for y in range(6,16):
      for x in range(5,14):put(x,y,floor)
    for y in range(3,20):
      for x in range(8,11):put(x,y,floor)
    for y in (5,16,17,18,19):
      for x in range(7,13):put(x,y,floor)
    for y in range(8,13):
      for x in range(6,13):put(x,y,floor)
    other=Counter(x&0x3ff for x in a if not x&0xc00 and (x&0x3ff)>=512 and (x&0x3ff)!=floorid)
    if other:
      accent=0x3000|other.most_common(1)[0][0]
      for x,y in [(6,7),(12,7),(6,13),(12,13),(7,16),(11,16)]:put(x,y,accent)
    meta=json.loads((root/'data/maps'/row['name']/'map.json').read_text())
    occupied={(z['x'],z['y']) for z in meta['object_events']}
    for x,y in [(9,18),(9,4),(12,18),(9,5),(7,10),(11,10)]:
      assert not tiles[y*19+x]&0xc00,(theme,x,y)
    reached={(9,18)};todo=deque(reached)
    while todo:
      x,y=todo.popleft()
      for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
        xx,yy=q
        if 0<=xx<19 and 0<=yy<21 and q not in reached and q not in occupied and not tiles[yy*19+xx]&0xc00:
          reached.add(q);todo.append(q)
    assert (9,5) in reached and (11,18) in reached,(theme,'unreachable')
    dst['primary_tileset']=src['primary_tileset']
    dst['secondary_tileset']=src['secondary_tileset']
    (root/dst['border_filepath']).write_bytes((root/src['border_filepath']).read_bytes())
    raw=struct.pack('<399H',*tiles)
    (root/dst['blockdata_filepath']).write_bytes(raw)
    report.append({'room':row['name'],'theme':theme,'original_layout':sid,'reachable':len(reached),'map_sha256':hashlib.sha256(raw).hexdigest()})
lp.write_text(json.dumps(d,indent=2)+'\n')
(root/'v11-2-heritage-room-audit.json').write_text(json.dumps({'status':'STATIC_ONLY; DEVICE TEST PENDING','rooms':report,'save_title_move_battle_code':'UNCHANGED','warning':'V11.1 internal-refresh baseline only; latest off-repo candidate source kit unavailable'},indent=2)+'\n')
print(json.dumps({'count':len(report),'min_reachable':min(x['reachable'] for x in report),'native_theme_source':True},indent=2))
