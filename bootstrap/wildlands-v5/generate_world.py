#!/usr/bin/env python3
from pathlib import Path
import struct, hashlib, json, sys

root=Path(sys.argv[1])
out=root/'data/wildlands_world'
out.mkdir(parents=True,exist_ok=True)

W,H=40,48
BASE_X,BASE_Y=108,72  # metatiles inside the final 256x192 / 4096x3072 world

def words(path):
    b=path.read_bytes()
    return list(struct.unpack('<%dH'%(len(b)//2),b))

route=words(root/'data/layouts/Route120/map.bin')
fortree=words(root/'data/layouts/FortreeCity/map.bin')
primary_attr=words(root/'data/tilesets/primary/general/metatile_attributes.bin')
secondary_attr=words(root/'data/tilesets/secondary/fortree/metatile_attributes.bin')

# Start with an exact native Route 120 crop. This already contains the river,
# long bridge, forest canopy, cliffs, water and tall grass from Emerald.
world=[]
for y in range(H):
    world.extend(route[y*40:(y+1)*40])

# Stamp a small Fortree structure into the south-east clearing as the first
# structure layering/cover test. Same General+Fortree tileset pair, so these
# are still native metatile ids/palettes, not a rendered image.
# Source: around the central Fortree building and its immediate ground.
SX,SY,SW,SH=18,6,9,7
DX,DY=28,39
for y in range(SH):
    for x in range(SW):
        world[(DY+y)*W+(DX+x)]=fortree[(SY+y)*40+(SX+x)]

# Carve a native Route120 path to the outpost using an existing route metatile.
# The structure itself remains solid according to its original collision bits.
path_entry=route[5*40+15]
grass_entry=route[6*40+20]
for x in range(25,33):
    world[38*W+x]=path_entry
for y in range(34,39):
    world[y*W+25]=path_entry

def attr(entry):
    mid=entry & 0x3ff
    return primary_attr[mid] if mid<512 else secondary_attr[mid-512]

def deep_water(entry):
    b=attr(entry)&0xff
    # MB_POND_WATER..MB_OCEAN_WATER except puddle/shallow water.
    return 16 <= b <= 21

def blocked(entry):
    return ((entry>>10)&3)!=0

def walkable(x,y):
    if not(0<=x<W and 0<=y<H): return False
    e=world[y*W+x]
    return not blocked(e) and not deep_water(e)

def nearest(x,y):
    if walkable(x,y): return (x,y)
    for r in range(1,9):
        for yy in range(max(0,y-r),min(H,y+r+1)):
            for xx in range(max(0,x-r),min(W,x+r+1)):
                if walkable(xx,yy): return (xx,yy)
    raise SystemExit(f'no walkable nav point near {(x,y)}')

# Navigation anchors follow the bridge/path/open areas. Runtime pathing still
# checks line-of-sight/collision, so these are guides, not teleport nodes.
desired=[
 (5,15),(9,15),(15,15),(22,15),(28,15),(33,15),
 (30,8),(34,6),(30,25),(34,30),(30,38),(22,30),
 (15,30),(8,30),(5,25),(18,40),(28,42),(24,38)
]
nav=[]
for p in desired:
    q=nearest(*p)
    if q not in nav: nav.append(q)

# Important validation positions: player/enemy are on opposite sides of the
# native bridge; tall grass and water are one short movement away.
PLAYER=(5,15)
ENEMY=(33,15)
assert walkable(*PLAYER) and walkable(*ENEMY)

# Use a native Route120 water metatile outside the validation slice. Runtime
# collision treats outside the slice as solid; this is visual only.
void_entry=route[14*40+15]
assert deep_water(void_entry)

(out/'slice.bin').write_bytes(struct.pack('<%dH'%len(world),*world))

nav_inc='\n'.join(
    f'    {{{(BASE_X+x)*16+8}, {(BASE_Y+y)*16+8}}},'
    for x,y in nav
)+'\n'
(out/'nav.inc').write_text(nav_inc)

header=f'''#ifndef GUARD_WILDLANDS_WORLD_DATA_H
#define GUARD_WILDLANDS_WORLD_DATA_H
#define WL_WORLD_PIXEL_W 4096
#define WL_WORLD_PIXEL_H 3072
#define WL_WORLD_METATILE_W 256
#define WL_WORLD_METATILE_H 192
#define WL_SLICE_BASE_X {BASE_X}
#define WL_SLICE_BASE_Y {BASE_Y}
#define WL_SLICE_W {W}
#define WL_SLICE_H {H}
#define WL_VOID_ENTRY 0x{void_entry:04X}
#define WL_PLAYER_START_X {(BASE_X+PLAYER[0])*16+8}
#define WL_PLAYER_START_Y {(BASE_Y+PLAYER[1])*16+8}
#define WL_ENEMY_START_X {(BASE_X+ENEMY[0])*16+8}
#define WL_ENEMY_START_Y {(BASE_Y+ENEMY[1])*16+8}
#define WL_NAV_POINT_COUNT {len(nav)}
#endif
'''
(root/'include/wildlands_world_data.h').write_text(header)

manifest={
 'format':'ROM-resident 16x16 Emerald metatile entries; runtime streamed as native 8x8 BG tiles',
 'world_pixels':[4096,3072],
 'validation_slice_metatiles':[W,H],
 'validation_slice_pixels':[W*16,H*16],
 'slice_world_metatile_origin':[BASE_X,BASE_Y],
 'sources':{
   'route120':'data/layouts/Route120/map.bin',
   'fortree':'data/layouts/FortreeCity/map.bin',
   'primary_tileset':'General',
   'secondary_tileset':'Fortree'
 },
 'roles':{
   'trees_cliffs_building':'solid cover; block bodies, projectiles and LOS',
   'bridge':'walkable crossing; does not count as water',
   'tall_long_grass':'concealment; walkable',
   'deep_water':'blocks ordinary land bodies; Water/Flying traversal allowed',
   'puddles_shallow':'walkable wet terrain',
   'fortree_structure':'cover/scenery only in validation build; not enterable'
 },
 'nav_points_local':nav,
 'player_start_local':PLAYER,
 'enemy_start_local':ENEMY,
 'void_entry':void_entry
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
