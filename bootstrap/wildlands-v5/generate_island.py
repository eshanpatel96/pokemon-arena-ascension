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
for i, c in enumerate(plan):
    if c in (BRIDGE, PATH, LAIR) and not walkable(i % W, i // W):
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
    x0, y0, w, h = b[:4]
    lair_reach[name] = any((x, y) in seen for y in range(y0, y0 + h) for x in range(x0, x0 + w))

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

# Navigation anchors: reachable lattice every 8 metatiles (bounded scan at runtime).
nav = []
for y in range(4, H, 8):
    for x in range(4, W, 8):
        if (x, y) in seen:
            nav.append((x * 16 + 8, y * 16 + 8))

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

(out / 'slice.bin').write_bytes(struct.pack('<%dH' % len(world), *world))
(out / 'terrain.bin').write_bytes(terrain)
(root / 'include/wildlands_world_nav.inc').write_text(''.join(f'    {{{x}, {y}}},\n' for x, y in nav))
(root / 'include/wildlands_loot.inc').write_text(''.join(f'    {{{x}, {y}, {t}}},\n' for x, y, t in loot))
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
#define WL_SLICE_H {H}
#define WL_VOID_ENTRY 0x{void_entry:04X}
#define WL_PLAYER_START_X {P[0] * 16 + 8}
#define WL_PLAYER_START_Y {P[1] * 16 + 8}
#define WL_ENEMY_START_X {E[0] * 16 + 8}
#define WL_ENEMY_START_Y {E[1] * 16 + 8}
#define WL_NAV_POINT_COUNT {len(nav)}
#define WL_ZONE_RADII {{2600, 1500, 850, 450, 180}}
#define WL_ISLAND 1
#endif
''')
manifest = {
    'world': 'island', 'format': 'ROM-resident 16x16 Emerald metatile entries (General+Fortree)',
    'world_metatiles': [W, H], 'world_pixels': [W * 16, H * 16],
    'source_plan': 'docs/art/wildlands-map-concept-v3.png -> island_plan.py (semantic only)',
    'land_metatiles': land, 'reachable_metatiles': reach,
    'reachable_pct': round(100 * reach / max(1, land), 2),
    'lairs': {k: {'box': list(v[:4]), 'approaches': list(v[4]) if len(v) > 4 else [], 'reachable': lair_reach[k]}
              for k, v in boxes.items()},
    'bridge_fallbacks': fixed, 'nav_anchors': len(nav), 'loot_spots': len(loot),
    'player_start': P, 'enemy_start': E,
    'not_claimed': ['landmark prefabs', 'region secondary tilesets', 'enterable buildings', 'destructible cover'],
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
