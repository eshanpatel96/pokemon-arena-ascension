#!/usr/bin/env python3
"""Full Wildlands island (4096x3072 px, 256x192 metatiles) for the Arena world.

Drop-in alternative to generate_world.py (same output files and header
macros), selected with WILDLANDS_WORLD=island.

Pipeline (all native Emerald data, nothing painted):
1. concept map -> cleaned semantic plan (island_plan.py);
2. biome layer (biome_plan.py): woodland / desert / highlands / volcano /
   beach, large combat clearings with landmarks, two-wide winding routes
   between them (MST + nearest neighbours: every clearing has >= 2 exits),
   natural fords over inland water;
3. per-cell autotiling: biome cores use a model trained on that biome's real
   routes (Fortree 119-120, Mauville 110-111, Fallarbor 113-115, Lavaridge
   112, Slateport 108-109); belts between cores use the General primary only,
   so the runtime can swap the one secondary tileset in VRAM unseen;
4. seam repair against real neighbour pairs; landmark prefabs (real route
   crops with their doors) and cover props (real boulders, outcrops, bushes,
   hedges, sea rocks mined from routes) stamped with their own collision;
5. collision/material flags per cell from that cell's own tileset pair.
"""
from pathlib import Path
import json, random, struct, sys, re

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
repo = here.parents[1]
sys.path.insert(0, str(repo / 'bootstrap/wildlands-map'))
sys.path.insert(0, str(here))

from island_plan import build, BRIDGE, LAIR, LAIRS, W, H, despeckle, min_blocks, connect_land   # noqa: E402
from autotile import (train, train_primary, repair, violations, PATH, GRASS, WATER, OCEAN,     # noqa: E402
                      TALL, SAND, TREE, ROCK, STONE)
from terrain_flags import FlagModel, words                                                     # noqa: E402
import biome_plan as bp                                                                         # noqa: E402
from props import mine as mine_props                                                            # noqa: E402

out = root / 'data/wildlands_world'
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(5)

# ---- 1-2. plan + biome layer ---------------------------------------------
plan, boxes = build(repo / 'docs/art/wildlands-map-concept-v3.png')
g = plan[:]
g, clearings = bp.carve_clearings(g, rng)
g, routes = bp.carve_routes(g, clearings, rng)
des, core = bp.biome_cores(g)
g = bp.biome_ground(g, des)
g = bp.texture_fields(g, des, rng)
g = despeckle(g, sweeps=2, keep=(BRIDGE, LAIR, OCEAN))
g = min_blocks(g, {WATER, TREE, ROCK})
# Beta map polish: round the corners and bite the long straight edges of tree
# masses, ponds and rock fields (thin rivers/ridges/tree lines untouched), and
# scatter irregular tall-grass patches in the woodland, so the island reads
# like an overworld route instead of a grid of blocks.
from organic import organic_edges, tall_blobs, organic_coast
_oc = dict(TREE=TREE, WATER=WATER, ROCK=ROCK, OCEAN=OCEAN, LAIR=LAIR, BRIDGE=BRIDGE, GRASS=GRASS, TALL=TALL, SAND=SAND, FORTREE=bp.FORTREE)
_before = g[:]
g = organic_edges(g, W, H, _oc, random.Random(31))
g = organic_coast(g, W, H, _oc, random.Random(41))
g = tall_blobs(g, W, H, des, _oc, random.Random(37))
g = min_blocks(g, {WATER, TREE, ROCK, OCEAN})
# V6.6 map pass: no stray sea islets, no specks on open desert/highland
# ground, bays and capes along long straight coasts.
from organic import map_cleanup
_oc.update(STONE=STONE, PATH=PATH)
g, cleanup_log = map_cleanup(g, W, H, des, clearings, _oc, random.Random(53))
print('map cleanup:', cleanup_log)
organic_changed = sum(1 for i in range(W * H) if _before[i] != g[i])
g = connect_land(g, rng)
plan = g
# Crossings are natural land necks (grass fords): shores get real edge art.
cls = [GRASS if c in (BRIDGE, LAIR) else c for c in plan]

# ---- 3. models -----------------------------------------------------------
LAYOUTS = json.load(open(root / 'data/layouts/layouts.json'))['layouts']
SEC_KEY = {'fortree': 'gTileset_Fortree', 'mauville': 'gTileset_Mauville', 'fallarbor': 'gTileset_Fallarbor',
           'lavaridge': 'gTileset_Lavaridge', 'slateport': 'gTileset_Slateport'}
models = {}
pairs = {}
BIOME_ROUTES = {'mauville': {'Route111'}, 'fallarbor': {'Route113', 'Route114', 'Route115'},
                'lavaridge': {'Route112'}, 'slateport': {'Route109', 'Route108'}, 'fortree': None}
for k, name in enumerate(bp.SECONDARIES, start=1):
    pairs[k], models[k] = train(root, name, SEC_KEY[name], only=BIOME_ROUTES[name], boost=4)
pairs[0], models[0] = train_primary(root)
model = models[bp.FORTREE]

# ---- landmarks -------------------------------------------------------------
# (layout, crop x, y, w, h, biome secondary)
PREFABS = {
    'lugia':    ('OUTCROP', 0, 0, 7, 4, bp.FORTREE),          # Beta: free-standing rock outcrop on open ground, one cave mouth (huts snagged big Pokemon)
    'kyogre':   ('OUTCROP', 0, 0, 8, 4, bp.FORTREE),          # Beta: open outcrop with a wide approach (old pond mound entrance was tight)
    'research': ('Route119', 0, 22, 16, 14, bp.FORTREE),      # Weather Institute -> research facility
    'tomb':     ('Route120', 1, 48, 12, 16, bp.FORTREE),      # Ancient Tomb boulder ring
    'house1':   ('Route119', 32, 106, 4, 4, bp.FORTREE),
    'house2':   ('Route119', 32, 106, 4, 4, bp.FORTREE),
    'house3':   ('Route119', 32, 106, 4, 4, bp.FORTREE),
    'rayquaza': ('Route115', 22, 31, 11, 7, bp.FALLARBOR),    # Meteor Falls mouth in the stone highlands
    'mewtwo':   ('Route111', 15, 51, 9, 9, bp.MAUVILLE),      # Mirage Tower
    'ruins':    ('Route111', 24, 82, 10, 8, bp.MAUVILLE),     # Desert Ruins
    'hooh':     ('Route112', 6, 31, 11, 8, bp.LAVARIDGE),     # Fiery Path mouth in the volcano slopes
    'seashore': ('Route109', 7, 1, 12, 12, bp.SLATEPORT),     # Seashore House + umbrellas
}
keepout = {}
for c in clearings:
    if c['landmark']:
        _l, _sx, _sy, sw_, sh_, _sec = PREFABS[c['landmark']]
        keepout[c['name']] = (c['cx'] - sw_ // 2, c['cy'] - sh_ // 2, c['cx'] + sw_ // 2, c['cy'] + sh_ // 2)
cls = bp.clearing_cover(cls, clearings, rng, keepout)
stamped = {}
fixed_cells = {}        # cell -> (entry, secondary index) stamped over autotile
for c in clearings:
    key = c['landmark']
    if not key:
        continue
    layout, sx, sy, sw, sh, sec = PREFABS[key]
    if layout == 'OUTCROP':
        # Natural rock mass (autotiled cliff art) in the middle of an open
        # clearing; cave_mouth() opens its south face. 3-cell open apron.
        ox, oy = c['cx'] - sw // 2, c['cy'] - sh // 2
        for yy in range(oy - 3, oy + sh + 4):
            for xx in range(ox - 3, ox + sw + 3):
                if 0 <= xx < W and 0 <= yy < H and cls[yy * W + xx] != OCEAN:
                    inside = ox <= xx < ox + sw and oy <= yy < oy + sh
                    cls[yy * W + xx] = ROCK if inside else bp.FLOOR[sec]
        stamped[key] = (ox, oy, sw, sh, 'OUTCROP', 0, 0, sec)
        continue
    lay = next(l for l in LAYOUTS if l and l['name'] == layout + '_Layout')
    src = words(root / lay['blockdata_filepath'])
    ox, oy = c['cx'] - sw // 2, c['cy'] - sh // 2
    ox = max(2, min(W - sw - 2, ox)); oy = max(2, min(H - sh - 3, oy))
    for yy in range(oy - 1, oy + sh + 2):
        for xx in range(ox - 1, ox + sw + 1):
            if cls[yy * W + xx] not in (OCEAN,):
                cls[yy * W + xx] = bp.FLOOR[sec] if (yy >= oy + sh or yy < oy or xx < ox or xx >= ox + sw) else cls[yy * W + xx]
    for yy in range(sh):
        for xx in range(sw):
            e = src[(sy + yy) * lay['width'] + sx + xx] & 0x0FFF
            fixed_cells[(oy + yy) * W + ox + xx] = (e, sec if (e & 0x3FF) >= 512 else 0)
    stamped[key] = (ox, oy, sw, sh, layout, sx, sy, sec)

# ---- 3b. autotile per cell (core model or primary-only in belts) -----------
world = [0] * (W * H)
secmap = [0] * (W * H)       # secondary index each cell's tile depends on
for y in range(H):
    for x in range(W):
        i = y * W + x
        k = core[i]
        m = models[k] if k else models[0]
        e, _ = m.pick(cls[i], cls, x, y, W, H, rng)
        if e is None:
            e, _ = models[0].pick(cls[i], cls, x, y, W, H, rng)
        e = (e if e is not None else 1) & 0x0FFF
        if (e & 0x3FF) >= 512 and not k:
            e, _ = models[0].pick(cls[i], cls, x, y, W, H, rng)
            e = (e or 1) & 0x0FFF
        world[i] = e
        secmap[i] = k if (e & 0x3FF) >= 512 else 0
# Seam repair per region with that region's model (others frozen).
def region_violations():
    from autotile import pair_ok
    v = 0
    for i in range(W * H):
        x, y = i % W, i // W
        m = models[core[i]] if core[i] else models[0]
        if x + 1 < W and not pair_ok(m, world[i], world[i + 1], True): v += 1
        if y + 1 < H and not pair_ok(m, world[i], world[i + W], False): v += 1
    return v
seam_before = region_violations()
for k in [0] + list(range(1, len(bp.SECONDARIES) + 1)):
    frozen = [(core[i] != k) or (i in fixed_cells) for i in range(W * H)]
    world, _ = repair(models[k], world, cls, W, H, sweeps=3, frozen=frozen)
for i in range(W * H):
    secmap[i] = core[i] if (world[i] & 0x3FF) >= 512 else 0
seam_after = region_violations()

# ---- 4. cover props ----------------------------------------------------------
fm = FlagModel(root)
PROPS = mine_props(root, fm)
SEC_NAME_TO_IDX = {n: k for k, n in enumerate(bp.SECONDARIES, start=1)}
def prop_ok_for(p, biome):
    if p['w'] * p['h'] > 4:
        return False
    return p['need'] == 'general' or SEC_NAME_TO_IDX.get(p['need']) == biome
WALKCLS = (GRASS, PATH, SAND, STONE, TALL)
prop_log = []
for c in clearings:
    biome = c['biome']
    land_props = [p for p in PROPS if p['kind'] == 'land' and prop_ok_for(p, biome)]
    if biome == bp.FORTREE:
        land_props = [p for p in land_props if p['look'] == 'green'] * 2 + [p for p in land_props if p['look'] == 'rock']
    else:
        land_props = [p for p in land_props if p['look'] == 'rock' or p['need'] != 'general']
    want = max(5, c['r'] * 3 // 4)
    lm = stamped.get(c['landmark'])
    placed = []
    for attempt in range(400):
        if len(placed) >= want or not land_props:
            break
        p = rng.choice(land_props)
        a = rng.random() * 6.283; rr = c['r'] * (0.35 + 0.6 * rng.random())
        x0 = int(c['cx'] + rr * __import__('math').cos(a)) - p['w'] // 2
        y0 = int(c['cy'] + rr * __import__('math').sin(a)) - p['h'] // 2
        if not (3 <= x0 < W - 6 and 3 <= y0 < H - 6):
            continue
        # ring of 2 cells of open floor, away from the landmark and other props
        area = [(x0 + dx, y0 + dy) for dy in range(-2, p['h'] + 2) for dx in range(-2, p['w'] + 2)]
        if any(cls[yy * W + xx] not in WALKCLS or (yy * W + xx) in fixed_cells for xx, yy in area):
            continue
        # a prop that needs a secondary may only sit inside that biome's core
        need = SEC_NAME_TO_IDX.get(p['need'], 0)
        if need and any(core[(y0 + j) * W + x0 + i2] != need for j in range(p['h']) for i2 in range(p['w'])):
            continue
        if lm and not (x0 + p['w'] + 3 < lm[0] or x0 > lm[0] + lm[2] + 3 or y0 + p['h'] + 3 < lm[1] or y0 > lm[1] + lm[3] + 3):
            continue
        if any(abs(x0 - qx) < 5 and abs(y0 - qy) < 5 for qx, qy in placed):
            continue
        for j, row in enumerate(p['rows']):
            for i2, e in enumerate(row):
                fixed_cells[(y0 + j) * W + x0 + i2] = (e, SEC_NAME_TO_IDX.get(p['need'], 0) if (e & 0x3FF) >= 512 else 0)
        placed.append((x0, y0))
    # concealment: one or two tall-grass patches in woodland/beach clearings
    if biome in (bp.FORTREE, bp.SLATEPORT):
        for _ in range(2):
            a = rng.random() * 6.283; rr = c['r'] * 0.6
            tx = int(c['cx'] + rr * __import__('math').cos(a)); ty = int(c['cy'] + rr * __import__('math').sin(a))
            for yy in range(ty, ty + 3):
                for xx in range(tx, tx + 4):
                    if 2 <= xx < W - 2 and 2 <= yy < H - 2 and cls[yy * W + xx] in (GRASS, SAND) and (yy * W + xx) not in fixed_cells:
                        cls[yy * W + xx] = TALL
                        e, _ = models[0].pick(TALL, cls, xx, yy, W, H, rng)
                        if e is not None:
                            world[yy * W + xx] = e & 0x0FFF
    prop_log.append((c['name'], len(placed)))

# Pond interiors: the General shallow-puddle fill (0x19E, walkable, flat
# lavender) reads as a palette glitch when used for whole ponds; use the
# native deep pond fill so water looks and behaves like water.
puddle_fix = 0
for i in range(W * H):
    if cls[i] == WATER and (world[i] & 0x3FF) == 0x19E:
        world[i] = 0xA1; secmap[i] = 0; puddle_fix += 1
for i, (e, k) in fixed_cells.items():
    world[i] = e
    secmap[i] = k

# ---- 5. collision per cell from its own pair ------------------------------
attr_cache = {}
def sec_attrs(k):
    if k not in attr_cache:
        name = bp.SECONDARIES[k - 1] if k else 'fortree'
        attr_cache[k] = words(root / f'data/tilesets/secondary/{name}/metatile_attributes.bin')
    return attr_cache[k]
primary_attr = words(root / 'data/tilesets/primary/general/metatile_attributes.bin')
def build_terrain(world):
    out_t = bytearray()
    for i, e in enumerate(world):
        mid = e & 0x3FF
        if mid < 512:
            a = primary_attr[mid]
        else:
            t = sec_attrs(secmap[i] or bp.FORTREE)
            a = t[mid - 512] if mid - 512 < len(t) else 0
        out_t.append(fm.flags(e, a & 0xff))
    return bytes(out_t)
terrain = build_terrain(world)
SOLID, DEEP = 1, 2

# Belt invariant over the REAL tiles: no 17x17 window may contain secondary
# tiles of two different biomes.
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
S = np.array(secmap, dtype=np.int8).reshape(H, W)
belt_ok = True
for k in range(1, len(bp.SECONDARIES) + 1):
    mk = (S == k).astype(np.int8)
    if not mk.any():
        continue
    pad = np.pad(mk, 8)
    dil = swv(swv(pad, 17, axis=1).max(axis=-1), 17, axis=0).max(axis=-1)
    clash = (dil > 0) & (S != 0) & (S != k)
    if clash.any():
        belt_ok = False
        ys, xs = np.nonzero(clash)
        print('BELT CLASH', bp.SECONDARIES[k - 1], 'near', list(zip(xs[:5].tolist(), ys[:5].tolist())))


def walkable(x, y):
    if not (0 <= x < W and 0 <= y < H):
        return False
    f = terrain[y * W + x]
    return not (f & SOLID) and (not (f & DEEP) or (f & 16))


# Planned crossings must be walkable in the real metatiles.
path_tile = models[0].t0[PATH].most_common(1)[0][0] & 0x0FFF
grass_tile = models[0].t0[GRASS].most_common(1)[0][0] & 0x0FFF
fixed = 0
for i, c in enumerate(plan):
    if c in (BRIDGE, PATH) and i not in fixed_cells and not walkable(i % W, i // W):
        world[i] = grass_tile if c == BRIDGE else path_tile
        secmap[i] = 0
        fixed += 1
terrain = build_terrain(world)

# No invisible walls: a metatile whose art is ordinary ground (walkable in
# most of the island) but carries a collision bit is a wall the player cannot
# see wherever it touches the same ground art. Clear the collision on those
# cells, flooding through same-art neighbours, so every blocked cell reads as
# blocked (tree, rock, cliff edge, building, prop) and open ground is open.
from collections import Counter as _Cnt, deque as _dq
def _art(i):
    return (world[i] & 0x3FF, secmap[i] if (world[i] & 0x3FF) >= 512 else 0)
_tot = _Cnt(_art(i) for i in range(W * H))
_sol = _Cnt(_art(i) for i in range(W * H) if terrain[i] & SOLID)
_floorlike = {k for k in _sol if _sol[k] < _tot[k] * 0.5}
def _n4(i):
    x, y = i % W, i // W
    if x + 1 < W: yield i + 1
    if x: yield i - 1
    if y + 1 < H: yield i + W
    if y: yield i - W
_q = _dq(i for i in range(W * H) if terrain[i] & SOLID and (world[i] >> 10) & 3 and _art(i) in _floorlike
         and i not in fixed_cells and any(not terrain[j] & SOLID and _art(j) == _art(i) for j in _n4(i)))
invisible_walls_cleared = 0
while _q:
    i = _q.popleft()
    if not ((world[i] >> 10) & 3) or i in fixed_cells:
        continue
    world[i] &= ~0x0C00
    invisible_walls_cleared += 1
    for j in _n4(i):
        if (world[j] >> 10) & 3 and _art(j) == _art(i):
            _q.append(j)
terrain = build_terrain(world)
invisible_walls_left = sum(1 for i in range(W * H) if terrain[i] & SOLID and _art(i) in _floorlike and i not in fixed_cells
                           and any(not terrain[j] & SOLID and _art(j) == _art(i) for j in _n4(i)))

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
    # Landmark prefabs are mostly solid art (cliff caves, towers); measure the
    # fighting ground: the prefab plus a 4-cell apron of its clearing.
    lair_reach[name] = sum(1 for y in range(y0 - 4, y0 + h + 4) for x in range(x0 - 4, x0 + w + 4) if (x, y) in seen)

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


# Loot: two orbs per clearing (fights happen there) plus spread singles on
# routes; one on the player's spawn approach for the runtime pickup test.
loot = [(P[0] * 16 + 8 + 48, P[1] * 16 + 8, 0)] if (P[0] + 3, P[1]) in seen else []
def free_spot(cx, cy, r):
    for _ in range(80):
        x = cx + rng.randint(-r, r); y = cy + rng.randint(-r, r)
        if (x, y) in seen and not terrain[y * W + x] & 8 and all(
                abs(x * 16 + 8 - lx) + abs(y * 16 + 8 - ly) > 64 for lx, ly, _ in loot):
            return x * 16 + 8, y * 16 + 8
    return None
for c in clearings:
    for _ in range(2):
        p = free_spot(c['cx'], c['cy'], c['r'] - 2)
        if p and len(loot) < 40:
            loot.append((p[0], p[1], len(loot) % 3))
cells = sorted(seen)
rng2 = random.Random(11)
rng2.shuffle(cells)
for (x, y) in cells:
    if len(loot) >= 44:
        break
    if terrain[y * W + x] & 8:
        continue
    px, py = x * 16 + 8, y * 16 + 8
    if all(abs(px - lx) + abs(py - ly) > 360 for lx, ly, _ in loot):
        loot.append((px, py, len(loot) % 3))

# ---- Enterable interiors -------------------------------------------------
# Doors are the landmarks' own native warp events; Kyogre's mound only has a
# water door, so its land entrance is a cliff cave mouth.
CAVE_CLOSED, CAVE_OPEN = 0x1B0, 0x1B1
DEST_ROOM = {
    'FORTREE_CITY_HOUSE1': 'treehouse1', 'FORTREE_CITY_HOUSE2': 'treehouse2',
    'FORTREE_CITY_HOUSE3': 'treehouse3', 'FORTREE_CITY_HOUSE4': 'lugia',
    'ROUTE119_WEATHER_INSTITUTE_1F': 'research', 'ANCIENT_TOMB': 'tomb',
    'METEOR_FALLS_1F_1R': 'rayquaza', 'MIRAGE_TOWER_1F': 'mewtwo', 'DESERT_RUINS': 'ruins',
    'FIERY_PATH': 'hooh', 'ROUTE109_SEASHORE_HOUSE': 'seashore',
}
doors = []
for key, (ox, oy, sw, sh, layout, sx, sy, sec) in stamped.items():
    if layout == 'OUTCROP':
        continue
    mj = json.load(open(root / f'data/maps/{layout}/map.json'))
    for w_ in mj.get('warp_events', []):
        dest = w_['dest_map'].replace('MAP_', '')
        if not (sx <= w_['x'] < sx + sw and sy <= w_['y'] < sy + sh):
            continue
        room = key if dest == 'ROUTE119_HOUSE' else DEST_ROOM.get(dest)
        if not room or any(d['room'] == room for d in doors):
            continue
        doors.append(dict(cell=(ox + w_['x'] - sx, oy + w_['y'] - sy), room=room, kind='door'))
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
    secmap[yy * W + xx] = 0
    doors.append(dict(cell=(xx, yy), room=room, kind='cave'))
cave_mouth('kyogre', 'kyogre')
cave_mouth('lugia', 'lugia')
terrain = build_terrain(world)
door_audit = {}
for d in doors:
    x, y = d['cell']
    door_audit['%s@%d,%d' % (d['room'], x, y)] = (x, y + 1) in seen
from interiors import build as build_rooms
LOOT_HEAL, LOOT_CACHE = 3, 4
ROOMS = {
    'treehouse1': dict(layout='FortreeCity_House1', loot=[LOOT_HEAL]),
    'treehouse2': dict(layout='FortreeCity_House2', loot=[LOOT_HEAL]),
    'treehouse3': dict(layout='FortreeCity_House1', loot=[LOOT_HEAL]),
    'mewtwo':  dict(layout='TerraCave_End', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='MEWTWO'),
    'lugia':   dict(layout='FarawayIsland_Interior', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='LUGIA'),
    'hooh':    dict(layout='BirthIsland_Exterior', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='HO_OH'),
    'kyogre':  dict(layout='SeafloorCavern_Room9', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='KYOGRE'),
    'rayquaza': dict(layout='AlteringCave', loot=[LOOT_CACHE, LOOT_HEAL], lair=True, legend='RAYQUAZA'),
    'research': dict(layout='Route119_WeatherInstitute_2F', loot=[LOOT_HEAL]),
    'tomb':    dict(layout='AncientTomb', loot=[LOOT_HEAL]),
    'ruins':   dict(layout='DesertRuins', loot=[LOOT_HEAL]),
    'seashore': dict(layout='Route109_SeashoreHouse', loot=[LOOT_HEAL]),
    'house1':  dict(layout='House1', loot=[LOOT_HEAL]),
    'house2':  dict(layout='House1', loot=[LOOT_HEAL]),
    'house3':  dict(layout='House1', loot=[LOOT_HEAL]),
}
used_rooms = {d['room'] for d in doors}
ROOMS = {k: v for k, v in ROOMS.items() if k in used_rooms}
outdoor_terrain = terrain
world, terrain, TOTAL_H, rooms_src, room_loot, rooms_manifest = build_rooms(
    root, world, terrain, W, H, (0, 0), ('General', 'Fortree'), doors, ROOMS)
loot = loot[:64 - len(room_loot)] + room_loot
(root / 'include/wildlands_rooms.inc').write_text(rooms_src)
(root / 'include/wildlands_loot.inc').write_text(''.join(f'    {{{x}, {y}, {t}}},\n' for x, y, t in loot))

# ---- runtime biome streaming tables -------------------------------------
from collections import Counter as _C
BLOCK = 8
GWb, GHb = W // BLOCK, H // BLOCK
blocks = []
for by in range(GHb):
    for bx in range(GWb):
        v = _C(core[(by * BLOCK + j) * W + bx * BLOCK + i] for j in range(BLOCK) for i in range(BLOCK))
        nz = [(n, k) for k, n in v.items() if k]
        blocks.append(max(nz)[1] if nz else 0)
(out / 'biome.bin').write_bytes(bytes(secmap[:W * H]))
start_biome = core[P[1] * W + P[0]] or blocks[(P[1] // BLOCK) * GWb + P[0] // BLOCK] or bp.FORTREE
def stand_spot(c):
    st = stamped.get(c['landmark'])
    tx, ty = (c['cx'], st[1] + st[3] + 2) if st else (c['cx'], c['cy'])
    for r in range(0, 20):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = tx + dx, ty + dy
                if max(abs(dx), abs(dy)) == r and (x, y) in seen and all(
                        (x + i, y + j) in seen for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    return x * 16 + 8, y * 16 + 8
    return c['cx'] * 16 + 8, c['cy'] * 16 + 8
landmark_pts = [stand_spot(c) for c in clearings]
(root / 'include/wildlands_biomes.inc').write_text(
    '// Generated by generate_island.py: biome secondary streaming.\n'
    f'#define WL_BIOME_COUNT {len(bp.SECONDARIES)}\n'
    + ''.join(f'extern const struct Tileset {SEC_KEY[n]};\n' for n in bp.SECONDARIES)
    + 'extern const struct Tileset gTileset_General;\n'
    + 'static const struct Tileset *const sWlOutdoorPairs[WL_BIOME_COUNT][2] = {'
    + ','.join(f'{{&gTileset_General,&{SEC_KEY[n]}}}' for n in bp.SECONDARIES) + '};\n'
    f'#define WL_BIOME_BLOCK {BLOCK}\n#define WL_BIOME_GW {GWb}\n#define WL_BIOME_GH {GHb}\n'
    'static const u8 sWlBiomeBlocks[WL_BIOME_GW * WL_BIOME_GH] = {' + ','.join(map(str, blocks)) + '};\n'
    'static const u8 sWlBiomeCells[] = INCBIN_U8("data/wildlands_world/biome.bin");\n'
    f'#define WL_BIOME_START {start_biome - 1}\n'
    f'#define WL_LANDMARK_COUNT {len(landmark_pts)}\n'
    'static const s16 sWlLandmarks[WL_LANDMARK_COUNT][2] = {' + ','.join(f'{{{x},{y}}}' for x, y in landmark_pts) + '};\n')

(out / 'design-classes.bin').write_bytes(bytes(cls))   # design/audit only (not linked)
(out / 'slice.bin').write_bytes(struct.pack('<%dH' % len(world), *world))
from minimap import emit as _emit_minimap
_emit_minimap(outdoor_terrain, W, H, root / 'include/wildlands_minimap.inc')
(out / 'terrain.bin').write_bytes(terrain)
(root / 'include/wildlands_world_nav.inc').write_text(''.join(f'    {{{x}, {y}}},\n' for x, y in nav))
void_entry = models[0].t0[OCEAN].most_common(1)[0][0] & 0x0FFF
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
#define WL_DIRECTOR_DUOS 40
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
    'bridge_fallbacks': fixed, 'pond_puddle_fixes': puddle_fix, 'invisible_walls_cleared': invisible_walls_cleared, 'invisible_walls_left': invisible_walls_left, 'seam_violations': [seam_before, seam_after], 'nav_anchors': len(nav), 'nav_edges': edges, 'nav_giant_component_pct': comp_ok, 'loot_spots': len(loot), 'organic_cells_changed': organic_changed,
    'player_start': P, 'enemy_start': E,
    'interiors': rooms_manifest, 'doors_reachable': door_audit,
    'biomes': {bp.BIOME_NAMES[k]: sum(1 for v in core if v == k) for k in bp.BIOME_NAMES},
    'belt_ok': belt_ok, 'clearings': clearings, 'routes': routes, 'props_per_clearing': prop_log,
    'landmarks': {k: list(v[:4]) + [bp.SECONDARIES[v[7] - 1]] for k, v in stamped.items()},
    'landmark_spots': [[c['name'], bp.BIOME_NAMES[c['biome']], x, y] for c, (x, y) in zip(clearings, landmark_pts)],
    'not_claimed': ['destructible cover', 'legendary boss encounters'],
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
