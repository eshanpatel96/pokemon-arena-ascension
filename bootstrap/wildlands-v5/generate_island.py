#!/usr/bin/env python3
"""Full Wildlands island (4096x3072 px, 256x192 metatiles) for the Arena world.

Drop-in alternative to generate_world.py (same output files and header
macros), selected with WILDLANDS_WORLD=island. Terrain comes from the
approved concept map (docs/art/wildlands-map-concept-v3.png) turned into a
semantic plan (bootstrap/wildlands-map/island_plan.py), then into native
General+Fortree metatiles by learned autotiling from real Hoenn layouts in
this engine tree. Collision/material flags are derived from those metatiles
(terrain_flags.py), never from the picture.

Status: island art/collision PROTOTYPE. Lair pockets are reserved ground with
multiple approaches; landmark prefabs and per-region secondary tilesets are
later work and are not claimed here.
"""
from pathlib import Path
import json, random, struct, sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
repo = here.parents[1]
sys.path.insert(0, str(repo / 'bootstrap/wildlands-map'))
sys.path.insert(0, str(here))

from island_plan import build, BRIDGE, LAIR, LAIRS, W, H          # noqa: E402
from autotile import train, PATH, GRASS, WATER, OCEAN           # noqa: E402
from terrain_flags import build_table, words                    # noqa: E402

out = root / 'data/wildlands_world'
out.mkdir(parents=True, exist_ok=True)

plan, boxes = build(repo / 'docs/art/wildlands-map-concept-v3.png')
pair, model = train(root, 'fortree', 'gTileset_Fortree')
cls = [PATH if c == BRIDGE else GRASS if c == LAIR else c for c in plan]
rng = random.Random(3)
world = []
for y in range(H):
    for x in range(W):
        e, _ = model.pick(cls[y * W + x], cls, x, y, W, H, rng)
        world.append((e if e is not None else 1) & 0x0FFF)

# Legendary lairs: authentic native-scale Route 119/120 + Fortree structures
# stamped into the reserved pockets (same General+Fortree tileset pair).
# (layout, x, y, w, h) crops; all are scenery/cover, none enterable.
PREFABS = {
    'mewtwo':   ('Route119', 0, 22, 16, 14),   # Weather Institute -> Research Facility
    'kyogre':   ('Route120', 12, 12, 18, 16),  # cave mound in bridged pond basin -> Abyssal Basin
    'rayquaza': ('Route119', 14, 18, 18, 20),  # waterfall gorge, log bridges, stairs -> Sky Highlands
    'hooh':     ('Route120', 1, 48, 16, 16),   # Ancient Tomb boulder ring -> Ember Temple (stone)
    'lugia':    ('FortreeCity', 8, 0, 28, 8),  # treetop lookouts + rope bridges + ladders -> Tempest Shrine
}
stamped = {}
for name, (layout, sx, sy, sw, sh) in PREFABS.items():
    L = json.load(open(root / 'data/layouts/layouts.json'))['layouts']
    lay = next(l for l in L if l and l['name'] == layout + '_Layout')
    src = words(root / lay['blockdata_filepath'])
    bx, by, bw, bh = boxes[name][:4]
    ox = max(1, min(W - sw - 1, bx + bw // 2 - sw // 2))
    oy = max(1, min(H - sh - 1, by + bh // 2 - sh // 2))
    for yy in range(sh):
        for xx in range(sw):
            world[(oy + yy) * W + ox + xx] = src[(sy + yy) * lay['width'] + sx + xx] & 0x0FFF
    stamped[name] = (ox, oy, sw, sh, layout)

# Wilderness houses: an authentic Route 119 house (General+Fortree), stamped
# whole onto open grass away from lairs; each door leads to its own interior.
_l119 = next(l for l in json.load(open(root / 'data/layouts/layouts.json'))['layouts']
             if l and l['name'] == 'Route119_Layout')
_b119 = words(root / _l119['blockdata_filepath'])
HOUSE = [[_b119[(106 + yy) * _l119['width'] + 32 + xx] & 0x0FFF for xx in range(4)] for yy in range(4)]
HOUSE_DOOR = (1, 3)
houses = []
for tx, ty in ((70, 100), (150, 150), (196, 96), (120, 40)):
    best = None
    for r in range(0, 40):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if best or max(abs(dx), abs(dy)) != r:
                    continue
                x0, y0 = tx + dx, ty + dy
                if not (2 <= x0 < W - 8 and 2 <= y0 < H - 9):
                    continue
                if any(cls[(y0 - 1 + yy) * W + x0 - 1 + xx] not in (GRASS,) for yy in range(7) for xx in range(6)):
                    continue
                if any(abs(x0 - bx - bw // 2) < bw // 2 + 14 and abs(y0 - by - bh // 2) < bh // 2 + 14
                       for (bx, by, bw, bh, *_r) in boxes.values()):
                    continue
                if any(abs(x0 - hx) + abs(y0 - hy) < 40 for hx, hy in houses):
                    continue
                best = (x0, y0)
    if best and len(houses) < 3:
        houses.append(best)
        for yy in range(4):
            for xx in range(4):
                world[(best[1] + yy) * W + best[0] + xx] = HOUSE[yy][xx]
        for xx in range(-1, 5):
            world[(best[1] + 4) * W + best[0] + xx] = model.t0[GRASS].most_common(1)[0][0] & 0x0FFF
        stamped['house%d' % len(houses)] = (best[0], best[1], 4, 5, 'Route119')

primary_attr = words(root / 'data/tilesets/primary/general/metatile_attributes.bin')
secondary_attr = words(root / 'data/tilesets/secondary/fortree/metatile_attributes.bin')
terrain = build_table(root, world, primary_attr, secondary_attr)
SOLID, DEEP = 1, 2


def walkable(x, y):
    if not (0 <= x < W and 0 <= y < H):
        return False
    f = terrain[y * W + x]
    return not (f & SOLID) and (not (f & DEEP) or (f & 16))


# Bridges in the plan must be walkable in the real metatiles: if the learned
# tile for a planned bridge/path cell over water is not, fall back to a plain
# native path metatile so routes never depend on Surf.
path_tile = model.t0[PATH].most_common(1)[0][0] & 0x0FFF
fixed = 0
in_prefab = set()
for ox, oy, sw, sh, _l in stamped.values():
    for yy in range(oy, oy + sh):
        for xx in range(ox, ox + sw):
            in_prefab.add(yy * W + xx)
for i, c in enumerate(plan):
    if c in (BRIDGE, PATH) and i not in in_prefab and not walkable(i % W, i // W):
        world[i] = path_tile
        fixed += 1
terrain = build_table(root, world, primary_attr, secondary_attr)

# Connectivity audit over the real collision data.
from collections import deque
start = None
for name, (x0, y0, w, h, *_rest) in boxes.items():
    pass
cx, cy = W // 2, H // 2
for r in range(0, 60):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if start is None and walkable(cx + dx, cy + dy):
                start = (cx + dx, cy + dy)
assert start, 'no walkable ground near island centre'
seen = {start}
q = deque([start])
while q:
    x, y = q.popleft()
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if (nx, ny) not in seen and walkable(nx, ny):
            seen.add((nx, ny)); q.append((nx, ny))
land = sum(1 for y in range(H) for x in range(W) if walkable(x, y))
reach = len(seen)
lair_reach = {}
for name, b in boxes.items():
    x0, y0, w, h = stamped[name][:4] if name in stamped else b[:4]
    lair_reach[name] = sum(1 for y in range(y0, y0 + h) for x in range(x0, x0 + w) if (x, y) in seen)

# Spawns for the duo practice match: two reachable points ~12 metatiles apart
# in the central wilds.
def nearest_reach(x, y):
    for r in range(0, 40):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if (x + dx, y + dy) in seen:
                    return x + dx, y + dy
    raise SystemExit('no reachable spawn')

P = nearest_reach(W // 2 - 6, H // 2 + 4)
E = nearest_reach(W // 2 + 6, H // 2 + 4)

# Navigation graph: lattice nodes every 8 metatiles on reachable ground whose
# 6px field footprint is clear; edges to the 8 lattice neighbours only where
# the straight segment passes the SAME land traversal test the runtime uses
# (footprint square + centre footing, water blocked unless bridge). All-pairs
# next hop is precomputed (Dijkstra, 10/14 costs) as a neighbour slot per pair.
STEP = int(__import__("os").environ.get("WL_NAV_STEP", "4"))
FOOT = 6
BRIDGE_F = 16
def solid_px(x, y):
    mx, my = x >> 4, y >> 4
    if not (0 <= mx < W and 0 <= my < H): return True
    return bool(terrain[my * W + mx] & SOLID)
def foot_clear(x, y, r=FOOT):
    for my in range((y - r) >> 4, ((y + r) >> 4) + 1):
        for mx in range((x - r) >> 4, ((x + r) >> 4) + 1):
            if not (0 <= mx < W and 0 <= my < H) or terrain[my * W + mx] & SOLID:
                return False
    return True
def footing(x, y):
    f = terrain[(y >> 4) * W + (x >> 4)]
    return not (f & DEEP) or bool(f & BRIDGE_F)
def land_line(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    steps = max(abs(dx), abs(dy)) // 8 + 1
    for i in range(steps + 1):
        x = x1 + dx * i // steps; y = y1 + dy * i // steps
        if not foot_clear(x, y) or not footing(x, y):
            return False
    return True
nodes = {}
for gy in range(4, H, STEP):
    for gx in range(4, W, STEP):
        best = None
        for r in range(0, 4):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = gx + dx, gy + dy
                    if best is None and (x, y) in seen and foot_clear(x * 16 + 8, y * 16 + 8) and footing(x * 16 + 8, y * 16 + 8):
                        best = (x * 16 + 8, y * 16 + 8)
        if best:
            nodes[(gx, gy)] = best
keys = sorted(nodes)
index = {k: i for i, k in enumerate(keys)}
nav = [nodes[k] for k in keys]
N = len(nav)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
nbr = [[0xFFFF] * 8 for _ in range(N)]
for k, i in index.items():
    for d, (dx, dy) in enumerate(DIRS):
        j = index.get((k[0] + dx * STEP, k[1] + dy * STEP))
        if j is not None and land_line(*nav[i], *nav[j]):
            nbr[i][d] = j
edges = sum(1 for i in range(N) for d in range(8) if nbr[i][d] != 0xFFFF)
GW, GH = (W + STEP - 1) // STEP, (H + STEP - 1) // STEP
grid = [0xFFFF] * (GW * GH)
for k, i in index.items():
    grid[(k[1] // STEP) * GW + k[0] // STEP] = i
masks = [sum(1 << d for d in range(8) if nbr[i][d] != 0xFFFF) for i in range(N)]
from collections import deque as _dq
comp_seen = set(); giant = 0
for s0 in range(N):
    if s0 in comp_seen: continue
    comp = {s0}; qq = _dq([s0])
    while qq:
        u = qq.popleft()
        for v in nbr[u]:
            if v != 0xFFFF and v not in comp: comp.add(v); qq.append(v)
    comp_seen |= comp; giant = max(giant, len(comp))
comp_ok = round(100 * giant / max(1, N), 1)
(root / 'include/wildlands_nav_graph.inc').write_text(
    f'#define WL_NAV_GRAPH 1\n#define WL_NAV_NODES {N}\n#define WL_NAV_STEP {STEP}\n'
    f'#define WL_NAV_GRID_W {GW}\n#define WL_NAV_GRID_H {GH}\n'
    'static const u8 sNavEdges[WL_NAV_NODES] = {' + ','.join(map(str, masks)) + '};\n'
    'static const u16 sNavGrid[WL_NAV_GRID_W * WL_NAV_GRID_H] = {' + ','.join(map(str, grid)) + '};\n'
    'static const u16 sNavCell[WL_NAV_NODES] = {' + ','.join(str((k[1] // STEP) * GW + k[0] // STEP) for k in keys) + '};\n')


# Loot: 32 reachable, non-concealed spots spread over the island, plus one on
# the player's spawn approach for the runtime pickup test.
loot = [(P[0] * 16 + 8 + 48, P[1] * 16 + 8, 0)] if (P[0] + 3, P[1]) in seen else []
cells = sorted(seen)
rng2 = random.Random(11)
rng2.shuffle(cells)
for (x, y) in cells:
    if len(loot) >= 32:
        break
    if terrain[y * W + x] & 8:
        continue
    px, py = x * 16 + 8, y * 16 + 8
    if all(abs(px - lx) + abs(py - ly) > 300 for lx, ly, _ in loot):
        loot.append((px, py, len(loot) % 3))

# ---- Enterable interiors -------------------------------------------------
# Doors come from the prefabs' own native warp events, plus a cliff cave
# mouth (Emerald's open secret-base cave metatile) where a lair has no door.
CAVE_CLOSED, CAVE_OPEN = 0x1B0, 0x1B1
doors = []
def door_at(name, cx, cy, room, kind='door'):
    ox, oy = stamped[name][:2]
    doors.append(dict(cell=(ox + cx, oy + cy), room=room, kind=kind))
door_at('mewtwo', 6, 10, 'mewtwo')                 # Weather Institute door
door_at('hooh', 6, 7, 'hooh')                      # Ancient Tomb door
door_at('lugia', 2, 3, 'treehouse1')
door_at('lugia', 9, 3, 'treehouse2')
door_at('lugia', 17, 3, 'treehouse3')
door_at('lugia', 24, 2, 'lugia')                   # far treehouse -> Tempest Shrine
for i in range(len(houses)):
    door_at('house%d' % (i + 1), *HOUSE_DOOR, 'house%d' % (i + 1))
def cave_mouth(name, room):
    ox, oy, sw, sh = stamped[name][:4]
    ccx, ccy = ox + sw // 2, oy + sh // 2
    cand = []
    for yy in range(oy, oy + sh):
        for xx in range(ox, ox + sw):
            i = yy * W + xx
            if not (terrain[i] & SOLID) or (xx, yy + 1) not in seen:
                continue
            native = (world[i] & 0x3FF) == CAVE_CLOSED
            wall = all(terrain[(yy + dy) * W + xx + dx] & SOLID for dx, dy in ((-1, 0), (1, 0), (0, -1)))
            if native or wall:
                cand.append((0 if native else 1, abs(xx - ccx) + abs(yy - ccy), xx, yy))
    assert cand, f'no cave mouth site for {name}'
    _, _, xx, yy = min(cand)
    world[yy * W + xx] = CAVE_OPEN | 0x0400
    doors.append(dict(cell=(xx, yy), room=room, kind='cave'))
cave_mouth('kyogre', 'kyogre')
cave_mouth('rayquaza', 'rayquaza')
terrain = build_table(root, world, primary_attr, secondary_attr)
door_audit = {}
for d in doors:
    x, y = d['cell']
    door_audit['%s@%d,%d' % (d['room'], x, y)] = d['kind'] == 'water' or (x, y + 1) in seen
from interiors import build as build_rooms
LOOT_HEAL, LOOT_CACHE = 3, 4
ROOMS = {
    'treehouse1': dict(layout='FortreeCity_House1', loot=[LOOT_HEAL]),
    'treehouse2': dict(layout='FortreeCity_House2', loot=[LOOT_HEAL]),
    'treehouse3': dict(layout='FortreeCity_House1', loot=[LOOT_HEAL]),
    'mewtwo':  dict(layout='Route119_WeatherInstitute_1F', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='MEWTWO'),
    'lugia':   dict(layout='NavelRock_Bottom', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='LUGIA'),
    'hooh':    dict(layout='NavelRock_Top', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='HO_OH'),
    'kyogre':  dict(layout='MarineCave_End', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='KYOGRE'),
    'rayquaza': dict(layout='SkyPillar_Top', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='RAYQUAZA'),
}
for i in range(len(houses)):
    ROOMS['house%d' % (i + 1)] = dict(layout='House1', loot=[LOOT_HEAL])
outdoor_terrain = terrain
world, terrain, TOTAL_H, rooms_src, room_loot, rooms_manifest = build_rooms(
    root, world, terrain, W, H, (0, 0), ('General', 'Fortree'), doors, ROOMS)
loot = loot[:64 - len(room_loot)] + room_loot
(root / 'include/wildlands_rooms.inc').write_text(rooms_src)
(root / 'include/wildlands_loot.inc').write_text(''.join(f'    {{{x}, {y}, {t}}},\n' for x, y, t in loot))

(out / 'slice.bin').write_bytes(struct.pack('<%dH' % len(world), *world))
from minimap import emit as _emit_minimap
_emit_minimap(outdoor_terrain, W, H, root / 'include/wildlands_minimap.inc')
(out / 'terrain.bin').write_bytes(terrain)
(root / 'include/wildlands_world_nav.inc').write_text(''.join(f'    {{{x}, {y}}},\n' for x, y in nav))
void_entry = model.t0[OCEAN].most_common(1)[0][0] & 0x0FFF
(root / 'include/wildlands_world_data.h').write_text(f'''#ifndef GUARD_WILDLANDS_WORLD_DATA_H
#define GUARD_WILDLANDS_WORLD_DATA_H
#define WL_WORLD_PIXEL_W 4096
#define WL_WORLD_PIXEL_H 3072
#define WL_WORLD_METATILE_W 256
#define WL_WORLD_METATILE_H 192
#define WL_SLICE_BASE_X 0
#define WL_SLICE_BASE_Y 0
#define WL_SLICE_W {W}
#define WL_SLICE_H {TOTAL_H}
#define WL_OUTDOOR_H {H}
#define WL_ARENA_MAX_Y {TOTAL_H * 16 - 32}
#define WL_VOID_ENTRY 0x{void_entry:04X}
#define WL_PLAYER_START_X {P[0] * 16 + 8}
#define WL_PLAYER_START_Y {P[1] * 16 + 8}
#define WL_ENEMY_START_X {E[0] * 16 + 8}
#define WL_ENEMY_START_Y {E[1] * 16 + 8}
#define WL_NAV_POINT_COUNT {len(nav)}
#define WL_ZONE_RADII {{2600, 1500, 850, 450, 180}}
#define WL_ISLAND 1
#define WL_DIRECTOR_DUOS 30
#endif
''')
manifest = {
    'world': 'island', 'format': 'ROM-resident 16x16 Emerald metatile entries (General+Fortree)',
    'world_metatiles': [W, H], 'world_pixels': [W * 16, H * 16],
    'source_plan': 'docs/art/wildlands-map-concept-v3.png -> island_plan.py (semantic only)',
    'land_metatiles': land, 'reachable_metatiles': reach,
    'reachable_pct': round(100 * reach / max(1, land), 2),
    'lairs': {k: {'box': list(v[:4]), 'approaches': list(v[4]) if len(v) > 4 else [],
                  'reachable': lair_reach[k] > 0, 'reachable_cells': lair_reach[k],
                  'prefab': stamped.get(k, [None])[-1] if k in stamped else None}
              for k, v in boxes.items()},
    'bridge_fallbacks': fixed, 'nav_anchors': len(nav), 'nav_edges': edges, 'nav_giant_component_pct': comp_ok, 'loot_spots': len(loot),
    'player_start': P, 'enemy_start': E,
    'interiors': rooms_manifest, 'doors_reachable': door_audit, 'wild_houses': houses,
    'not_claimed': ['destructible cover', 'legendary boss encounters'],
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
