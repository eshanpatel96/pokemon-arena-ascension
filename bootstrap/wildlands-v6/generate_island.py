#!/usr/bin/env python3
from pathlib import Path
from collections import Counter, deque
import struct, json, math, sys

root=Path(sys.argv[1])
out=root/'data/wildlands_world'
out.mkdir(parents=True,exist_ok=True)

W,H=256,192

def words(path):
    b=path.read_bytes()
    return list(struct.unpack('<%dH'%(len(b)//2),b))

r119=words(root/'data/layouts/Route119/map.bin') # 40x140
r120=words(root/'data/layouts/Route120/map.bin') # 40x100
fortree=words(root/'data/layouts/FortreeCity/map.bin') # 40x20
primary_attr=words(root/'data/tilesets/primary/general/metatile_attributes.bin')
secondary_attr=words(root/'data/tilesets/secondary/fortree/metatile_attributes.bin')

def attr(entry):
    mid=entry & 0x3ff
    return primary_attr[mid] if mid<512 else secondary_attr[mid-512]

def behavior(entry): return attr(entry)&0xff
def blocked(entry): return ((entry>>10)&3)!=0
def deep_water(entry):
    b=behavior(entry)
    return 16 <= b <= 21
def conceal(entry): return behavior(entry) in (2,3,9)
def walkable(entry): return not blocked(entry) and not deep_water(entry)

# Known native Route120 entries already validated by V5.
grass_entry=r120[6*40+20]
path_entry=r120[5*40+15]
water_entry=r120[14*40+15]
bridge_entry=r120[16*40+15]
assert walkable(grass_entry) and walkable(path_entry)
assert deep_water(water_entry)

world=[water_entry]*(W*H)

# ---- island footprint: land dominant, meaningful coast/inlets ----
poly=[
 (8,45),(18,24),(42,12),(72,7),(99,9),(124,4),(153,9),(187,6),(216,15),
 (239,34),(249,57),(247,86),(252,111),(247,136),(238,158),(220,176),
 (196,184),(170,179),(145,189),(118,181),(91,187),(64,177),(39,163),
 (20,145),(10,122),(6,96),(4,70)
]
def point_in_poly(x,y,p):
    inside=False
    j=len(p)-1
    for i in range(len(p)):
        xi,yi=p[i];xj,yj=p[j]
        if ((yi>y)!=(yj>y)) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:
            inside=not inside
        j=i
    return inside

land=[[point_in_poly(x+.5,y+.5,poly) for x in range(W)] for y in range(H)]

# Carve a few coherent bays instead of flooding half the world.
bays=[
 [(0,132),(35,128),(48,142),(42,163),(20,181),(0,184)],
 [(92,170),(108,161),(128,164),(132,192),(84,192)],
 [(229,151),(256,145),(256,192),(224,192)]
]
for y in range(H):
    for x in range(W):
        for bp in bays:
            if point_in_poly(x+.5,y+.5,bp):
                land[y][x]=False
                break
        if land[y][x]:
            world[y*W+x]=grass_entry

def set_entry(x,y,e):
    if 0<=x<W and 0<=y<H:
        world[y*W+x]=e

def blit(src,sw,sh,sx,sy,bw,bh,dx,dy,land_only=True):
    for yy in range(bh):
        for xx in range(bw):
            tx,ty=dx+xx,dy+yy
            if not(0<=tx<W and 0<=ty<H): continue
            if land_only and not land[ty][tx]: continue
            set_entry(tx,ty,src[(sy+yy)%sh*sw+(sx+xx)%sw])

# ---- large real-map regions, same General+Fortree pair ----
# These are deliberate contiguous donor regions, not 16x16 image chunks.
blit(r119,40,140,0,0,40,62,24,18)       # NW forest/highland
blit(r119,40,140,0,48,40,70,28,74)      # west forest/waterfall
blit(r119,40,140,0,78,40,60,62,114)     # southwest forest
blit(r119,40,140,0,15,40,62,82,12)      # north highland approach
blit(r120,40,100,0,0,40,58,118,18)      # north-central river/bridge
blit(r120,40,100,0,34,40,60,116,72)     # central wilds
blit(r120,40,100,0,18,40,62,158,35)     # east-central routes
blit(r120,40,100,0,38,40,58,188,68)     # eastern cliffs/routes
blit(r120,40,100,0,40,40,56,148,126)    # south river country

# Fortree becomes central ruins/settlements and gives real foreground structures.
blit(fortree,40,20,0,0,40,20,95,83)
blit(fortree,40,20,0,0,30,20,188,114)

# ---- central river: continuous geography, explicit bridge crossings ----
river_x=136
for y in range(30,170):
    wobble=int(4*math.sin(y/13.0)+3*math.sin(y/31.0))
    cx=river_x+wobble
    for x in range(cx-3,cx+4):
        if 0<=x<W and land[y][x]:
            set_entry(x,y,water_entry)

# branch river toward west wetlands.
for step in range(72):
    x=136-step
    y=98+step//3
    for oy in range(-2,3):
        for ox in range(-2,3):
            if 0<=x+ox<W and 0<=y+oy<H and land[y+oy][x+ox]:
                set_entry(x+ox,y+oy,water_entry)

# ---- POIs / legendary hubs / secondary locations ----
nodes={
 'LUGIA':(25,43),'WESTPORT':(42,76),'FOREST_HUB':(77,95),
 'RAYQUAZA':(121,24),'NORTH_PASS':(100,52),
 'CENTRAL':(123,99),'RIVER_HUB':(155,104),
 'MEWTWO':(218,43),'EAST_OUTPOST':(201,91),
 'SOUTH_HUB':(128,151),'ABYSS_DOCK':(66,156),'KYOGRE':(42,170),
 'EMBER_GATE':(197,148),'HOOH':(218,170),
 'RUINS_W':(92,132),'RUINS_E':(177,127)
}
legendary={'LUGIA','RAYQUAZA','MEWTWO','KYOGRE','HOOH'}

# Route graph supplies multiple ways across the island rather than one corridor.
edges=[
 ('LUGIA','WESTPORT'),('WESTPORT','FOREST_HUB'),('FOREST_HUB','CENTRAL'),
 ('FOREST_HUB','NORTH_PASS'),('NORTH_PASS','RAYQUAZA'),
 ('RAYQUAZA','MEWTWO'),('CENTRAL','RIVER_HUB'),('RIVER_HUB','EAST_OUTPOST'),
 ('EAST_OUTPOST','MEWTWO'),('CENTRAL','SOUTH_HUB'),('SOUTH_HUB','ABYSS_DOCK'),
 ('ABYSS_DOCK','KYOGRE'),('SOUTH_HUB','EMBER_GATE'),('EMBER_GATE','HOOH'),
 ('WESTPORT','SOUTH_HUB'),('RIVER_HUB','SOUTH_HUB'),('CENTRAL','EAST_OUTPOST'),
 ('FOREST_HUB','RUINS_W'),('RUINS_W','SOUTH_HUB'),('RIVER_HUB','RUINS_E'),
 ('RUINS_E','EMBER_GATE'),('NORTH_PASS','CENTRAL')
]

def line_points(a,b):
    x0,y0=a;x1,y1=b
    dx=abs(x1-x0);dy=-abs(y1-y0)
    sx=1 if x0<x1 else -1;sy=1 if y0<y1 else -1
    err=dx+dy
    while True:
        yield x0,y0
        if x0==x1 and y0==y1: break
        e2=2*err
        if e2>=dy: err+=dy;x0+=sx
        if e2<=dx: err+=dx;y0+=sy

# Use two-bend paths so roads look route-like rather than arbitrary diagonals.
def route_points(a,b):
    x1,y1=nodes[a];x2,y2=nodes[b]
    if abs(x2-x1)>abs(y2-y1):
        mx=(x1+x2)//2
        bends=[(x1,y1),(mx,y1),(mx,y2),(x2,y2)]
    else:
        my=(y1+y2)//2
        bends=[(x1,y1),(x1,my),(x2,my),(x2,y2)]
    pts=[]
    for p0,p1 in zip(bends,bends[1:]):
        seg=list(line_points(p0,p1))
        if pts and seg: seg=seg[1:]
        pts.extend(seg)
    return pts

roads=set()
for a,b in edges:
    for x,y in route_points(a,b):
        for oy in range(-1,2):
            for ox in range(-1,2):
                tx,ty=x+ox,y+oy
                if 0<=tx<W and 0<=ty<H and land[ty][tx]:
                    roads.add((tx,ty))

# Clear hubs into real fight/readability spaces, larger for legendary lairs.
for name,(cx,cy) in nodes.items():
    rx,ry=(8,7) if name in legendary else (5,4)
    for y in range(cy-ry,cy+ry+1):
        for x in range(cx-rx,cx+rx+1):
            if 0<=x<W and 0<=y<H:
                if name=='KYOGRE':
                    # island within Abyssal water, still reachable by dock/bridge.
                    land[y][x]=True
                if land[y][x]:
                    set_entry(x,y,grass_entry)

# Stamp different real Fortree structure pieces into hubs.
def fortree_stamp(cx,cy,sx,sy,sw,sh):
    dx=cx-sw//2;dy=cy-sh//2
    for yy in range(sh):
        for xx in range(sw):
            tx,ty=dx+xx,dy+yy
            if 0<=tx<W and 0<=ty<H and land[ty][tx]:
                set_entry(tx,ty,fortree[((sy+yy)%20)*40+((sx+xx)%40)])

for idx,name in enumerate(['LUGIA','RAYQUAZA','MEWTWO','HOOH','RUINS_W','RUINS_E']):
    cx,cy=nodes[name]
    fortree_stamp(cx,cy,16+(idx%3)*5,3+(idx%2)*5,7,6)

# Re-carve roads last: obstacles never get to block the designed route network.
for x,y in roads:
    existing=world[y*W+x]
    set_entry(x,y,bridge_entry if deep_water(existing) else path_entry)

# Dock/causeway to Kyogre.
for x,y in route_points('ABYSS_DOCK','KYOGRE'):
    for oy in range(-1,2):
        for ox in range(-1,2):
            tx,ty=x+ox,y+oy
            if 0<=tx<W and 0<=ty<H:
                set_entry(tx,ty,bridge_entry if deep_water(world[ty*W+tx]) else path_entry)

# Re-open the middle of every hub after structure stamping for battle room.
for name,(cx,cy) in nodes.items():
    r=4 if name in legendary else 2
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            if 0<=x<W and 0<=y<H and land[y][x]:
                set_entry(x,y,path_entry)

# ---- land-only connectivity audit ----
def land_walkable(x,y):
    if not(0<=x<W and 0<=y<H): return False
    return walkable(world[y*W+x])

start=nodes['CENTRAL']
if not land_walkable(*start):
    raise SystemExit('central hub is not land-walkable')

dist={start:0}
q=deque([start])
while q:
    x,y=q.popleft()
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        p=(x+dx,y+dy)
        if p not in dist and land_walkable(*p):
            dist[p]=dist[(x,y)]+1
            q.append(p)

for name,p in nodes.items():
    if p not in dist:
        raise SystemExit(f'POI disconnected on ordinary land: {name} {p}')

# ---- certify 30 spawn zones in the same land component ----
exclusion=list(nodes[n] for n in legendary)
candidates=[]
for gy in range(8,184,12):
    for gx in range(8,248,12):
        best=None
        for rad in range(0,9):
            found=False
            for yy in range(max(1,gy-rad),min(H-1,gy+rad+1)):
                for xx in range(max(1,gx-rad),min(W-1,gx+rad+1)):
                    if (xx,yy) not in dist: continue
                    if any(abs(xx-lx)+abs(yy-ly)<14 for lx,ly in exclusion): continue
                    # 5x5 local room and an all-land cardinal exit.
                    room=sum(1 for oy in range(-2,3) for ox in range(-2,3)
                             if land_walkable(xx+ox,yy+oy))
                    if room<19: continue
                    best=(xx,yy);found=True;break
                if found: break
            if found: break
        if best and best not in candidates:
            candidates.append(best)

spawns=[]
for p in sorted(candidates,key=lambda p:dist[p],reverse=True):
    if all(abs(p[0]-q[0])+abs(p[1]-q[1])>=14 for q in spawns):
        spawns.append(p)
    if len(spawns)==30: break
if len(spawns)<30:
    raise SystemExit(f'only {len(spawns)} certified spawn zones')
min_sep=min(abs(a[0]-b[0])+abs(a[1]-b[1]) for i,a in enumerate(spawns) for b in spawns[i+1:])

# ---- bounded coarse navigation anchors sampled from designed routes ----
nav=[]
for a,b in edges:
    pts=route_points(a,b)
    for i in range(0,len(pts),12):
        p=pts[i]
        if p in dist and p not in nav: nav.append(p)
    p=pts[-1]
    if p in dist and p not in nav: nav.append(p)
# Keep a bounded set for realtime pathing.
if len(nav)>56:
    step=len(nav)/56.0
    nav=[nav[int(i*step)] for i in range(56)]

# Start near a real 256px streaming boundary on the central east-west road.
# Search around Central for a walkable road point whose camera X is <24 px
# from a chunk boundary.
player=None
for x,y in sorted(roads,key=lambda p:abs(p[0]-nodes['CENTRAL'][0])+abs(p[1]-nodes['CENTRAL'][1])):
    px=x*16+8
    cam=max(0,min(W*16-240,px-120))
    edge=(256-(cam&255))&255
    if edge<=24 and (x,y) in dist:
        player=(x,y);break
if player is None: player=nodes['CENTRAL']

# Enemy 14+ metatiles east along connected road if possible.
enemy=None
for x,y in sorted(roads,key=lambda p:abs(p[1]-player[1])+abs((p[0]-player[0])-20)):
    if (x,y) in dist and abs(x-player[0])+abs(y-player[1])>=16:
        enemy=(x,y);break
if enemy is None: enemy=nodes['RIVER_HUB']

(out/'slice.bin').write_bytes(struct.pack('<%dH'%len(world),*world))
nav_inc='\n'.join(f'    {{{x*16+8}, {y*16+8}}},' for x,y in nav)+'\n'
(out/'nav.inc').write_text(nav_inc)

spawn_inc='\n'.join(f'    {{{x*16+8}, {y*16+8}}},' for x,y in spawns)+'\n'
(out/'spawns.inc').write_text(spawn_inc)

header=f'''#ifndef GUARD_WILDLANDS_WORLD_DATA_H
#define GUARD_WILDLANDS_WORLD_DATA_H
#define WL_WORLD_PIXEL_W 4096
#define WL_WORLD_PIXEL_H 3072
#define WL_WORLD_METATILE_W {W}
#define WL_WORLD_METATILE_H {H}
#define WL_SLICE_BASE_X 0
#define WL_SLICE_BASE_Y 0
#define WL_SLICE_W {W}
#define WL_SLICE_H {H}
#define WL_VOID_ENTRY 0x{water_entry:04X}
#define WL_PLAYER_START_X {player[0]*16+8}
#define WL_PLAYER_START_Y {player[1]*16+8}
#define WL_ENEMY_START_X {enemy[0]*16+8}
#define WL_ENEMY_START_Y {enemy[1]*16+8}
#define WL_NAV_POINT_COUNT {len(nav)}
#define WL_CERTIFIED_SPAWN_COUNT {len(spawns)}
#endif
'''
(root/'include/wildlands_world_data.h').write_text(header)

travel={name:dist[p] for name,p in nodes.items()}
manifest={
 'version':'Wildlands V6 Island Alpha',
 'world_pixels':[4096,3072],
 'world_metatiles':[W,H],
 'representation':'full ROM-resident Emerald metatile world; no world bitmap/floor texture',
 'tilesets':['General','Fortree'],
 'source_maps':['Route119','Route120','FortreeCity'],
 'legendary_hubs':{name:list(nodes[name]) for name in legendary},
 'secondary_locations':{name:list(p) for name,p in nodes.items() if name not in legendary},
 'route_edges':[list(e) for e in edges],
 'certified_spawns_metatiles':[list(p) for p in spawns],
 'certified_spawn_count':len(spawns),
 'minimum_spawn_manhattan_tiles':min_sep,
 'all_spawns_land_connected':all(p in dist for p in spawns),
 'all_legendary_hubs_land_connected':all(nodes[n] in dist for n in legendary),
 'travel_tiles_from_central':travel,
 'nav_anchor_count':len(nav),
 'player_start':list(player),
 'enemy_start':list(enemy),
 'known_visual_limit':'V6 island alpha intentionally stays on the proven General+Fortree pair; biome-specific secondary tileset swaps are not yet enabled.',
 'combat_limit':'local combat remains V5 two-body Arena plus non-damaging highlighted partner; true 2v2 is not claimed.'
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
