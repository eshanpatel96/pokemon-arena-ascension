"""Wildlands V5 biome layer: clearings, routes, biomes and belts.

Builds on the cleaned concept plan (island_plan.build). Adds:
- a biome per cell (woodland / desert / highlands / volcano / beach) and the
  Emerald SECONDARY tileset each biome needs (Fortree, Mauville, Fallarbor,
  Lavaridge, Slateport). Only one secondary fits in VRAM, so different
  secondaries are kept >= BELT metatiles apart: the cells in between use the
  General primary only, and the runtime swaps the secondary while the camera
  window sees nothing but primary tiles;
- large combat clearings with a landmark, cover and several exits;
- routes between clearings (two-wide, winding, with natural water fords).
"""
from collections import deque
import math, random

from autotile import OCEAN, WATER, GRASS, TALL, PATH, SAND, TREE, ROCK, STONE
from concept_plan import W, H
from island_plan import BRIDGE, LAIR, nbrs4

BELT = 18                     # >= camera window (16 metatiles) + slack

# secondary tileset per biome (index into SECONDARIES; 0 = primary only)
SECONDARIES = ['fortree', 'mauville', 'fallarbor', 'lavaridge', 'slateport']
FORTREE, MAUVILLE, FALLARBOR, LAVARIDGE, SLATEPORT = 1, 2, 3, 4, 5
BIOME_NAMES = {FORTREE: 'woodland', MAUVILLE: 'desert', FALLARBOR: 'highlands',
               LAVARIDGE: 'volcano', SLATEPORT: 'beach'}


def sector(col, row):
    return (ord(col) - 65) * 16 + 8, (row - 1) * 16 + 8


def desired_biome(x, y):
    """Biome regions with organic (low-frequency wavy) borders."""
    wx = 9 * math.sin(y / 13.0) + 5 * math.sin(y / 5.3 + 1.7)
    wy = 8 * math.sin(x / 11.0 + 0.6) + 4 * math.sin(x / 4.7 + 2.1)
    if x + wx >= 176 and y + wy >= 138:
        return LAVARIDGE
    if x + wx >= 168 and y + wy < 128:
        return MAUVILLE
    if 100 <= x - wx * 0.5 <= 158 and y + wy * 0.7 < 54:
        return FALLARBOR
    if 92 <= x + wx * 0.5 <= 164 and y + wy * 0.5 >= 156:
        return SLATEPORT
    return FORTREE


def biome_cores(g):
    """Per-cell secondary allowance after belts: a cell keeps its biome's
    secondary only if no cell of a DIFFERENT biome lies within BELT/2
    (Chebyshev), so any two different secondaries are >= BELT apart."""
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view as swv
    des = np.array([desired_biome(x, y) for y in range(H) for x in range(W)], dtype=np.int8).reshape(H, W)
    half = BELT // 2
    core = np.zeros_like(des)
    # Sea and inland water are drawn with primary tiles only: neutral, they
    # never force a belt (so cores reach the coast).
    neutral = np.array([c in (OCEAN, WATER) for c in g], dtype=bool).reshape(H, W) if g is not None else np.zeros_like(des, dtype=bool)
    for k in np.unique(des):
        other = ((des != k) & ~neutral).astype(np.int8)
        pad = np.pad(other, half, mode='edge')
        m = swv(pad, 2 * half + 1, axis=1).max(axis=-1)
        m = swv(m, 2 * half + 1, axis=0).max(axis=-1)
        core[(des == k) & (m == 0) & ~neutral] = k
    return des.flatten().tolist(), core.flatten().tolist()


CLEARINGS = [
    # name, sector, radius, biome, landmark key (or None)
    ('lugia', ('B', 3), 14, FORTREE, 'lugia'),
    ('kyogre', ('C', 11), 15, FORTREE, 'kyogre'),
    ('research', ('E', 6), 14, FORTREE, 'research'),
    ('tomb', ('H', 8), 14, FORTREE, 'tomb'),
    ('tempest', ('C', 8), 10, FORTREE, 'house1'),
    ('glade', ('F', 10), 10, FORTREE, 'house2'),
    ('north_wood', ('E', 3), 10, FORTREE, 'house3'),
    ('rayquaza', ('H', 2), 12, FALLARBOR, 'rayquaza'),
    ('mewtwo', ('N', 3), 12, MAUVILLE, 'mewtwo'),
    ('ruins', ('O', 6), 11, MAUVILLE, 'ruins'),
    ('dunes', ('M', 8), 11, MAUVILLE, None),
    ('hooh', ('N', 11), 12, LAVARIDGE, 'hooh'),
    ('beach', ('H', 12), 13, SLATEPORT, 'seashore'),
    ('east_wood', ('L', 5), 10, FORTREE, None),
    ('south_wood', ('K', 10), 10, FORTREE, None),
    ('sky_meadow', ('J', 5), 10, FORTREE, None),
]

FLOOR = {FORTREE: GRASS, MAUVILLE: SAND, FALLARBOR: STONE, LAVARIDGE: STONE, SLATEPORT: SAND}
ROUTE = {FORTREE: PATH, MAUVILLE: SAND, FALLARBOR: STONE, LAVARIDGE: STONE, SLATEPORT: SAND}


def _land_near(g, x, y, r=30):
    for d in range(r):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                xx, yy = x + dx, y + dy
                if 4 <= xx < W - 4 and 4 <= yy < H - 4 and g[yy * W + xx] not in (OCEAN, WATER):
                    return xx, yy
    return x, y


def carve_clearings(g, rng):
    """Open combat areas: noisy ellipses of the biome floor. Inland water
    inside a clearing becomes floor unless it is a pond big enough to read
    as a feature (kept, it is cover for swimmers only)."""
    placed = []
    for name, sec, r, biome, land in CLEARINGS:
        cx, cy = _land_near(g, *sector(*sec))
        floor = FLOOR[biome]
        ph = rng.random() * 6.28
        for y in range(max(2, cy - r - 2), min(H - 2, cy + r + 3)):
            for x in range(max(2, cx - r - 2), min(W - 2, cx + r + 3)):
                a = math.atan2(y - cy, x - cx)
                rr = r * (1 + 0.12 * math.sin(3 * a + ph) + 0.08 * math.sin(5 * a + ph * 2))
                if (x - cx) ** 2 + ((y - cy) * 1.15) ** 2 > rr * rr:
                    continue
                i = y * W + x
                if g[i] == OCEAN:
                    continue
                g[i] = floor
        placed.append(dict(name=name, cx=cx, cy=cy, r=r, biome=biome, landmark=land))
    return g, placed


def clearing_cover(g, clearings, rng, keepout):
    """Terrain-level cover inside each clearing, away from its centre (the
    landmark) and from each other: tree groves and tall grass in woodland,
    rock outcrops in desert / highlands / volcano, grass tufts and rocks on
    beaches. Everything is >= 2x2 so the art reads (and min_blocks keeps it)."""
    feats = {FORTREE: [(TREE, 2, 2), (TREE, 3, 2), (TREE, 2, 3), (TALL, 4, 3), (TALL, 3, 3)],
             MAUVILLE: [(ROCK, 2, 2), (ROCK, 3, 2), (ROCK, 2, 3)],
             FALLARBOR: [(ROCK, 2, 2), (ROCK, 3, 2), (GRASS, 4, 3)],
             LAVARIDGE: [(ROCK, 2, 2), (ROCK, 3, 2), (ROCK, 2, 2)],
             SLATEPORT: [(TALL, 3, 3), (ROCK, 2, 2)]}
    for c in clearings:
        kinds = feats[c['biome']]
        floor = FLOOR[c['biome']]
        want = 3 + c['r'] // 4
        done = []
        for _ in range(300):
            if len(done) >= want:
                break
            cl, w, h = rng.choice(kinds)
            a = rng.random() * 6.283
            rr = c['r'] * (0.45 + 0.4 * rng.random())
            x0 = int(c['cx'] + rr * math.cos(a)) - w // 2
            y0 = int(c['cy'] + rr * math.sin(a)) - h // 2
            box = [(x0 + i, y0 + j) for j in range(-1, h + 1) for i in range(-1, w + 1)]
            if any(not (0 <= x < W and 0 <= y < H) or g[y * W + x] not in (floor, GRASS, SAND, STONE)
                   for x, y in box):
                continue
            kx0, ky0, kx1, ky1 = keepout.get(c['name'], (0, 0, -1, -1))
            if not (x0 + w + 3 < kx0 or x0 > kx1 + 3 or y0 + h + 3 < ky0 or y0 > ky1 + 3):
                continue
            if any(abs(x0 - qx) < w + 4 and abs(y0 - qy) < h + 4 for qx, qy in done):
                continue
            for j in range(h):
                for i in range(w):
                    g[(y0 + j) * W + x0 + i] = cl
            done.append((x0, y0))
        c['cover'] = len(done)
    return g


def texture_fields(g, des, rng):
    """Break up big uniform fields: grassy patches and small outcrops on
    the highland / volcano stone, scattered outcrops and oasis grass in the
    desert. Only on open ground with a margin, never on routes."""
    for _ in range(900):
        x, y = rng.randrange(4, W - 8), rng.randrange(4, H - 8)
        b = des[y * W + x]
        base = g[y * W + x]
        if b in (FALLARBOR, LAVARIDGE) and base == STONE:
            cl, w, h = (GRASS, rng.randint(3, 5), rng.randint(2, 4)) if rng.random() < 0.55 else (ROCK, 2, 2)
        elif b == MAUVILLE and base == SAND:
            cl, w, h = (ROCK, rng.choice((2, 3)), 2) if rng.random() < 0.7 else (GRASS, 3, 2)
        else:
            continue
        box = [(x + i, y + j) for j in range(-2, h + 2) for i in range(-2, w + 2)]
        if any(g[yy * W + xx] != base for xx, yy in box):
            continue
        for j in range(h):
            for i in range(w):
                g[(y + j) * W + x + i] = cl
    return g


def _route_cost(c):
    return {OCEAN: None, WATER: 9, TREE: 3, ROCK: 7, TALL: 1, GRASS: 1, PATH: 1, SAND: 1, STONE: 1,
            BRIDGE: 1, LAIR: 1}.get(c, 2)


def carve_routes(g, clearings, rng, extra=1):
    """Each clearing links to its nearest 2-3 neighbours (Gabriel-style) plus a
    spanning tree, so every clearing has >= 2 exits and no long dead ends.
    Routes follow cheap ground with a little noise (they wind), are two cells
    wide, and cross inland water on natural fords (land necks)."""
    n = len(clearings)
    pts = [(c['cx'], c['cy']) for c in clearings]
    edges = set()
    # MST (Prim)
    inside = {0}
    while len(inside) < n:
        best = None
        for a in inside:
            for b in range(n):
                if b in inside:
                    continue
                d = math.dist(pts[a], pts[b])
                if best is None or d < best[0]:
                    best = (d, a, b)
        edges.add(tuple(sorted(best[1:])))
        inside.add(best[2])
    # plus nearest neighbours
    for a in range(n):
        near = sorted(range(n), key=lambda b: math.dist(pts[a], pts[b]))[1:2 + extra]
        for b in near:
            edges.add(tuple(sorted((a, b))))
    noise = [rng.random() for _ in range(W * H)]
    routes = []
    import heapq
    for a, b in sorted(edges):
        (sx, sy), (tx, ty) = pts[a], pts[b]
        dist = {(sx, sy): 0}; prev = {}
        pq = [(0, sx, sy)]
        while pq:
            d, x, y = heapq.heappop(pq)
            if (x, y) == (tx, ty):
                break
            if d > dist.get((x, y), 1e18):
                continue
            for xx, yy in nbrs4(x, y):
                c = _route_cost(g[yy * W + xx])
                if c is None or not (3 <= xx < W - 3 and 3 <= yy < H - 3):
                    continue
                nd = d + c + noise[yy * W + xx] * 1.5
                if nd < dist.get((xx, yy), 1e18):
                    dist[(xx, yy)] = nd; prev[(xx, yy)] = (x, y)
                    heapq.heappush(pq, (nd, xx, yy))
        if (tx, ty) not in prev:
            continue
        path = []
        p = (tx, ty)
        while p != (sx, sy):
            path.append(p); p = prev[p]
        biome_a, biome_b = clearings[a]['biome'], clearings[b]['biome']
        for k, (x, y) in enumerate(path):
            biome = biome_a if k > len(path) // 2 else biome_b
            for xx, yy in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)):
                i = yy * W + xx
                if g[i] == OCEAN:
                    continue
                if g[i] == WATER:
                    g[i] = BRIDGE           # rendered as a grass ford
                elif g[i] in (TREE, ROCK, TALL, LAIR) or g[i] not in (PATH, SAND, STONE, GRASS, BRIDGE):
                    g[i] = ROUTE[biome] if g[i] != LAIR else LAIR
                elif g[i] == GRASS and biome != FORTREE:
                    g[i] = ROUTE[biome]
        routes.append((clearings[a]['name'], clearings[b]['name'], len(path)))
    return g, routes


def biome_ground(g, des):
    """Repaint generic ground by biome so each region reads differently:
    desert grass -> sand, highland/volcano open ground -> stone (rock masses
    stay rock), beach band (within 5 of the sea) -> sand."""
    dist = [10 ** 6] * (W * H)
    q = deque()
    for i in range(W * H):
        if g[i] == OCEAN:
            dist[i] = 0; q.append(i)
    while q:
        i = q.popleft()
        x, y = i % W, i // W
        for xx, yy in nbrs4(x, y):
            j = yy * W + xx
            if dist[j] > dist[i] + 1:
                dist[j] = dist[i] + 1; q.append(j)
    for i in range(W * H):
        c, b = g[i], des[i]
        if c in (OCEAN, WATER, BRIDGE, LAIR):
            continue
        if b == MAUVILLE and c in (GRASS, TALL, PATH):
            g[i] = SAND
        elif b in (FALLARBOR, LAVARIDGE) and c in (GRASS, PATH, SAND):
            g[i] = STONE
        elif dist[i] <= 4 and c in (GRASS, PATH):
            g[i] = SAND
    return g
