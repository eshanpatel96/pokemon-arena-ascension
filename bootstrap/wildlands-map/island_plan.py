"""Semantic island plan: concept guide -> cleaned, playable 256x192 class grid.

Gameplay rules enforced here (not left to the art):
- every walkable cell belongs to one connected land network (no islands of
  land that need Surf/Fly to leave), with explicit bridges over the river;
- tiny noise features are removed so terrain reads clearly at 240x160;
- five legendary lair pockets are reserved with >=2 approaches each;
- tall-grass concealment patches are placed in open ground.
"""
from collections import deque, Counter
import random
from autotile import OCEAN, WATER, GRASS, TALL, PATH, SAND, TREE, ROCK, OTHER
from concept_plan import W, H, plan_from_concept, majority

BRIDGE = 20     # plan-only class: bridge deck over water (stamped later)
LAIR = 21       # plan-only class: reserved landmark pocket

WALK = {GRASS, TALL, PATH, SAND, BRIDGE, LAIR}

# Concept sector labels (A..P x 1..12, 16x16 metatiles each)
def sector(col, row, dx=8, dy=8):
    return (ord(col) - 65) * 16 + dx, (row - 1) * 16 + dy

LAIRS = {
    'lugia':    dict(sector=('B', 3), size=(14, 12)),
    'rayquaza': dict(sector=('H', 2), size=(14, 12)),
    'mewtwo':   dict(sector=('N', 3), size=(16, 12)),
    'kyogre':   dict(sector=('C', 11), size=(14, 12)),
    'hooh':     dict(sector=('N', 11), size=(16, 12)),
}


def nbrs4(x, y):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        xx, yy = x + dx, y + dy
        if 0 <= xx < W and 0 <= yy < H:
            yield xx, yy


def fill_other(g):
    q = deque((x, y) for y in range(H) for x in range(W) if g[y * W + x] != OTHER)
    seen = set(q)
    while q:
        x, y = q.popleft()
        for xx, yy in nbrs4(x, y):
            if (xx, yy) not in seen and g[yy * W + xx] == OTHER:
                g[yy * W + xx] = g[y * W + x]; seen.add((xx, yy)); q.append((xx, yy))
    return g


def components(g, pred):
    comp = [-1] * (W * H); sizes = []
    for i in range(W * H):
        if comp[i] >= 0 or not pred(g[i]):
            continue
        cid = len(sizes); n = 0; q = deque([i]); comp[i] = cid
        while q:
            j = q.popleft(); n += 1
            for xx, yy in nbrs4(j % W, j // W):
                k = yy * W + xx
                if comp[k] < 0 and pred(g[k]):
                    comp[k] = cid; q.append(k)
        sizes.append(n)
    return comp, sizes


def mark_ocean(g):
    comp, sizes = components(g, lambda c: c == WATER)
    border = {comp[y * W + x] for y in range(H) for x in (0, W - 1)} | {comp[y * W + x] for x in range(W) for y in (0, H - 1)}
    border.discard(-1)
    for i in range(W * H):
        if comp[i] in border:
            g[i] = OCEAN
    return g


def remove_small(g, cls, minsize, into_fn):
    comp, sizes = components(g, lambda c: c == cls)
    for i in range(W * H):
        if comp[i] >= 0 and sizes[comp[i]] < minsize:
            g[i] = into_fn(g, i)
    return g


def surrounding(g, i, exclude):
    x, y = i % W, i // W
    v = Counter()
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H and g[yy * W + xx] not in exclude:
                v[g[yy * W + xx]] += 1
    return v.most_common(1)[0][0] if v else GRASS


def thicken_water(g):
    # Emerald water edges need >=2-cell bodies; widen 1-cell river necks
    out = g[:]
    for y in range(H):
        for x in range(W - 1):
            i = y * W + x
            if g[i] == WATER and (x + 1 < W and g[i + 1] not in (WATER, OCEAN)) and (x > 0 and g[i - 1] not in (WATER, OCEAN)):
                out[i + 1] = WATER
    g = out; out = g[:]
    for y in range(H - 1):
        for x in range(W):
            i = y * W + x
            if g[i] == WATER and g[i + W] not in (WATER, OCEAN) and (y > 0 and g[i - W] not in (WATER, OCEAN)):
                out[i + W] = WATER
    return out


def connect_land(g, rng):
    """Join every walkable component to the largest by carving PATH (over trees/rock)
    or BRIDGE (over inland water). Ocean is never bridged."""
    while True:
        comp, sizes = components(g, lambda c: c in WALK)
        if len(sizes) <= 1:
            return g
        main = max(range(len(sizes)), key=lambda k: sizes[k])
        # pick the largest non-main component, BFS from it to main over passable-by-carving cells
        other = max((k for k in range(len(sizes)) if k != main), key=lambda k: sizes[k])
        if sizes[other] < 12:
            for i in range(W * H):
                if comp[i] >= 0 and comp[i] != main and sizes[comp[i]] < 12:
                    g[i] = surrounding(g, i, WALK | {OCEAN})
            continue
        start = [i for i in range(W * H) if comp[i] == other]
        prev = {i: None for i in start}; q = deque(start); hit = None
        while q and hit is None:
            j = q.popleft()
            for xx, yy in nbrs4(j % W, j // W):
                k = yy * W + xx
                if k in prev or g[k] == OCEAN:
                    continue
                prev[k] = j
                if comp[k] == main:
                    hit = k; break
                q.append(k)
        if hit is None:
            for i in start:
                g[i] = TREE
            continue
        k = prev[hit]
        while k is not None and comp[k] != other:
            g[k] = BRIDGE if g[k] == WATER else PATH
            k = prev[k]


def reserve_lairs(g):
    boxes = {}
    for name, d in LAIRS.items():
        cx, cy = sector(*d['sector'])
        w, h = d['size']
        x0, y0 = max(2, cx - w // 2), max(2, cy - h // 2)
        x0 = min(x0, W - w - 2); y0 = min(y0, H - h - 2)
        boxes[name] = (x0, y0, w, h)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                g[y * W + x] = LAIR
    return g, boxes


def lair_approaches(g, boxes):
    """Guarantee two separate walkable approaches into each lair pocket."""
    for name, (x0, y0, w, h) in boxes.items():
        sides = []
        for side, cells in (('S', [(x0 + w // 2, y0 + h + i) for i in range(1, 30)]),
                            ('E', [(x0 + w + i, y0 + h // 2) for i in range(1, 30)]),
                            ('W', [(x0 - i, y0 + h // 2) for i in range(1, 30)]),
                            ('N', [(x0 + w // 2, y0 - i) for i in range(1, 30)])):
            path = []
            ok = False
            ocean_run = 0
            for (x, y) in cells:
                if not (0 <= x < W and 0 <= y < H):
                    break
                if g[y * W + x] == OCEAN:
                    ocean_run += 1
                    if ocean_run > 12:
                        break
                if g[y * W + x] in WALK and g[y * W + x] != LAIR:
                    ok = True; break
                path.append((x, y))
            if ok:
                sides.append((len(path), side, path))
        sides.sort()
        for _, side, path in sides[:3]:
            for (x, y) in path:
                for o in (0, 1):
                    xx, yy = (x + o, y) if side in 'NS' else (x, y + o)
                    if 0 <= xx < W and 0 <= yy < H and g[yy * W + xx] != LAIR:
                        g[yy * W + xx] = BRIDGE if g[yy * W + xx] in (WATER, OCEAN) else PATH
        boxes[name] = boxes[name] + (tuple(s for _, s, _ in sides[:3]),)
    return g, boxes


def sprinkle_tall(g, rng):
    for _ in range(140):
        x, y = rng.randrange(W), rng.randrange(H)
        if g[y * W + x] != GRASS:
            continue
        rw, rh = rng.randint(3, 7), rng.randint(2, 5)
        for yy in range(y, min(H, y + rh)):
            for xx in range(x, min(W, x + rw)):
                if g[yy * W + xx] == GRASS:
                    g[yy * W + xx] = TALL
    return g


def coarsen(g, f=2):
    """Re-plan at f x f block resolution so coastlines, rivers and cliffs have
    the >=2-cell straight runs Emerald's edge metatiles are drawn for."""
    out = g[:]
    for by in range(0, H, f):
        for bx in range(0, W, f):
            v = Counter(g[(by + dy) * W + bx + dx] for dy in range(f) for dx in range(f))
            k = v.most_common(1)[0][0]
            for dy in range(f):
                for dx in range(f):
                    out[(by + dy) * W + bx + dx] = k
    return out


def banks(g):
    """Emerald never butts water straight against cliff tops or paths: put a
    one-cell grass bank between them (bridges excepted)."""
    out = g[:]
    for y in range(H):
        for x in range(W):
            c = g[y * W + x]
            if c not in (ROCK, PATH):
                continue
            for xx, yy in nbrs4(x, y):
                if g[yy * W + xx] in (WATER,):
                    out[y * W + x] = GRASS
                    break
    return out


def build(concept_path, seed=7):
    rng = random.Random(seed)
    g = plan_from_concept(concept_path)
    g = majority(g, 2)
    g = coarsen(g, 2)
    g = fill_other(g)
    g = mark_ocean(g)
    g = remove_small(g, WATER, 10, lambda g, i: surrounding(g, i, {WATER, OCEAN}))
    g = remove_small(g, ROCK, 6, lambda g, i: surrounding(g, i, {ROCK}))
    g = remove_small(g, TREE, 4, lambda g, i: surrounding(g, i, {TREE}))
    g = majority(g, 1, keep=(OCEAN,))
    g = coarsen(g, 2)
    g = thicken_water(g)
    g = banks(g)
    g, boxes = reserve_lairs(g)
    g, boxes = lair_approaches(g, boxes)
    g = connect_land(g, rng)
    g = sprinkle_tall(g, rng)
    return g, boxes
