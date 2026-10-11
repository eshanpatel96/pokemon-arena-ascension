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
# checks collision/water. Bridge anchors use the exact 32 px lane centerline
# rather than a 16 px metatile center so the unchanged 10 px Arena body radius
# fits between both native bridge edges.
desired=[
 (5,16,True),(9,16,True),(10,16,True),(15,16,True),(22,16,True),(28,16,True),(30,16,True),
 (30,8,False),(34,6,False),(30,25,False),(34,30,False),(30,38,False),(22,30,False),
 (15,30,False),(8,30,False),(5,25,False),(18,40,False),(28,42,False),(24,38,False)
]
nav_pixels=[]
for x,y,bridge_center in desired:
    q=nearest(x,y)
    if bridge_center:
        px=(BASE_X+q[0])*16+8
        py=(BASE_Y+16)*16
    else:
        px=(BASE_X+q[0])*16+8
        py=(BASE_Y+q[1])*16+8
    if (px,py) not in nav_pixels:
        nav_pixels.append((px,py))

# Important validation positions: player/enemy are on opposite sides of the
# native Route 120 bridge. Their Y coordinate is deliberately on the 16 px
# boundary between the two bridge metatile rows, so Arena's unchanged 10 px
# body radius fits the native 32 px-wide bridge without touching its cliff edge.
PLAYER=(10,16)
ENEMY=(30,16)
PLAYER_Y_PX=PLAYER[1]*16
ENEMY_Y_PX=ENEMY[1]*16
assert walkable(*PLAYER) and walkable(*ENEMY)

# Use a native Route120 water metatile outside the validation slice. Runtime
# collision treats outside the slice as solid; this is visual only.
void_entry=route[14*40+15]
assert deep_water(void_entry)

(out/'slice.bin').write_bytes(struct.pack('<%dH'%len(world),*world))
# Precomputed per-metatile terrain flags (ROM). Same semantics as the former
# runtime MetatileBehavior_* chain; see terrain_flags.py.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from terrain_flags import build_table
terrain=build_table(root,world,primary_attr,secondary_attr)
(out/'terrain.bin').write_bytes(terrain)
assert len(terrain)==W*H
from minimap import emit as _emit_minimap
_emit_minimap(terrain, W, H, root/'include/wildlands_minimap.inc')

nav_inc='\n'.join(
    f'    {{{x}, {y}}},'
    for x,y in nav_pixels
)+'\n'
(root/'include/wildlands_world_nav.inc').write_text(nav_inc)
(root/'include/wildlands_nav_graph.inc').write_text('#define WL_NAV_GRAPH 0\n')

# Team-upgrade pickups: legal dry ground (not water, not solid, not concealed),
# spread >= 6 metatiles apart, types cycling ATK/DEF/SPD. Spot 0 sits on the
# bridge lane east of the player start so the runtime smoke test walks over it.
def loot_ok(x,y):
    if not walkable(x,y): return False
    e=world[y*W+x]
    b=attr(e)&0xff
    return b not in (2,3,9)
loot=[((BASE_X+14)*16+8, BASE_Y*16+PLAYER_Y_PX, 0)]
assert walkable(14,16)
taken=[(14,16)]
types=[1,2,0]
for gy in range(3,H-2,7):
    for gx in range(3,W-2,7):
        cand=None
        for dy in range(0,5):
            for dx in range(0,5):
                if loot_ok(gx+dx,gy+dy): cand=(gx+dx,gy+dy); break
            if cand: break
        if not cand: continue
        if any(abs(cand[0]-tx)+abs(cand[1]-ty)<6 for tx,ty in taken): continue
        taken.append(cand)
        loot.append(((BASE_X+cand[0])*16+8,(BASE_Y+cand[1])*16+8,types[len(loot)%3]))
        if len(loot)>=12: break
    if len(loot)>=12: break
# Enterable interior: the stamped Fortree building's native door leads to a
# real Fortree house interior (Building+GenericBuilding pair) with supplies.
from interiors import build as build_rooms
DOOR=(DX+(22-SX), DY+(11-SY))
assert (fortree[11*40+22]&0x3ff) in (0x21,0x41,0x61,0x1cd,0x1db,0xa7,0x235,0x2ca), hex(fortree[11*40+22])
world,terrain,TOTAL_H,rooms_src,room_loot,rooms_manifest=build_rooms(
    root,world,terrain,W,H,(BASE_X,BASE_Y),('General','Fortree'),
    [dict(cell=DOOR,room='house',kind='door')],
    {'house':dict(layout='FortreeCity_House1',loot=[3])})
loot=loot+room_loot
(root/'include/wildlands_rooms.inc').write_text(rooms_src)
# Biome streaming tables: the slice is one biome (General + Fortree).
(out/'biome.bin').write_bytes(bytes(1 if (world[i] & 0x3ff) >= 512 and i < W*H else 0 for i in range(W*H)))
(root/'include/wildlands_biomes.inc').write_text(
    '#define WL_BIOME_COUNT 1\nextern const struct Tileset gTileset_General;\nextern const struct Tileset gTileset_Fortree;\n'
    'static const struct Tileset *const sWlOutdoorPairs[1][2] = {{&gTileset_General,&gTileset_Fortree}};\n'
    f'#define WL_BIOME_BLOCK 8\n#define WL_BIOME_GW {(W+7)//8}\n#define WL_BIOME_GH {(H+7)//8}\n'
    'static const u8 sWlBiomeBlocks[WL_BIOME_GW * WL_BIOME_GH] = {' + ','.join(['1'] * (((W+7)//8) * ((H+7)//8))) + '};\n'
    'static const u8 sWlBiomeCells[] = INCBIN_U8("data/wildlands_world/biome.bin");\n'
    '#define WL_BIOME_START 0\n#define WL_LANDMARK_COUNT 1\n'
    f'static const s16 sWlLandmarks[1][2] = {{{{{(BASE_X+DOOR[0])*16+8},{(BASE_Y+DOOR[1]+1)*16+8}}}}};\n')
(out/'slice.bin').write_bytes(struct.pack('<%dH'%len(world),*world))
(out/'terrain.bin').write_bytes(terrain)
(root/'include/wildlands_loot.inc').write_text(''.join(f'    {{{x}, {y}, {t}}},\n' for x,y,t in loot))

header=f'''#ifndef GUARD_WILDLANDS_WORLD_DATA_H
#define GUARD_WILDLANDS_WORLD_DATA_H
#define WL_WORLD_PIXEL_W 4096
#define WL_WORLD_PIXEL_H 3072
#define WL_WORLD_METATILE_W 256
#define WL_WORLD_METATILE_H 192
#define WL_SLICE_BASE_X {BASE_X}
#define WL_SLICE_BASE_Y {BASE_Y}
#define WL_SLICE_W {W}
#define WL_SLICE_H {TOTAL_H}
#define WL_OUTDOOR_H {H}
#define WL_VOID_ENTRY 0x{void_entry:04X}
#define WL_PLAYER_START_X {(BASE_X+PLAYER[0])*16+8}
#define WL_PLAYER_START_Y {BASE_Y*16+PLAYER_Y_PX}
#define WL_ENEMY_START_X {(BASE_X+ENEMY[0])*16+8}
#define WL_ENEMY_START_Y {BASE_Y*16+ENEMY_Y_PX}
#define WL_NAV_POINT_COUNT {len(nav_pixels)}
#define WL_DIRECTOR_DUOS 4
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
   'fortree_structure':'cover; its native door enters a Fortree house interior'
 },
 'interiors':rooms_manifest,
 'nav_points_world_pixels':nav_pixels,
 'player_start_local':PLAYER,
 'enemy_start_local':ENEMY,
 'void_entry':void_entry,
 'loot_spots':loot
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
