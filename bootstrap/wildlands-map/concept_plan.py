"""Concept map (approved visual direction) -> 256x192 semantic terrain plan.

The concept PNG is only a guide for *where* biomes go. Nothing from it is
rendered; every output cell later becomes a native Emerald metatile.
"""
from PIL import Image
from collections import Counter
from autotile import OCEAN, WATER, GRASS, TALL, PATH, SAND, TREE, ROCK, OTHER

W, H = 256, 192
FRAME = (0, 43, 1448, 1043)  # map area inside the concept image

PROTO = [
    ((57, 105, 223), WATER), ((56, 82, 141), WATER), ((70, 119, 169), WATER), ((90, 157, 162), WATER),
    ((26, 64, 53), TREE), ((50, 109, 81), TREE),
    ((131, 190, 123), GRASS), ((125, 175, 125), GRASS), ((138, 197, 133), GRASS),
    ((225, 196, 142), PATH), ((233, 214, 158), PATH), ((188, 169, 129), PATH),
    ((115, 69, 67), ROCK), ((136, 121, 110), ROCK),
    ((15, 26, 36), OTHER), ((240, 240, 240), OTHER), ((230, 100, 40), ROCK),
]


def nearest(c):
    best, bc = 1e9, OTHER
    for p, k in PROTO:
        d = sum((a - b) ** 2 for a, b in zip(c, p))
        if d < best:
            best, bc = d, k
    return bc


def plan_from_concept(path):
    im = Image.open(path).convert('RGB').crop(FRAME)
    sw, sh = im.width / W, im.height / H
    px = im.load()
    grid = []
    for y in range(H):
        for x in range(W):
            votes = Counter()
            for sy in range(3):
                for sx in range(3):
                    c = px[int((x + (sx + .5) / 3) * sw), int((y + (sy + .5) / 3) * sh)]
                    votes[nearest(c)] += 1
            grid.append(votes.most_common(1)[0][0])
    return grid


def majority(grid, passes=1, keep=()):
    for _ in range(passes):
        out = grid[:]
        for y in range(H):
            for x in range(W):
                c = grid[y * W + x]
                if c in keep:
                    continue
                v = Counter()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < W and 0 <= yy < H:
                            v[grid[yy * W + xx]] += 1
                k, n = v.most_common(1)[0]
                if n >= 5:
                    out[y * W + x] = k
        grid = out
    return grid


COLORS = {OCEAN: (40, 70, 200), WATER: (90, 150, 255), GRASS: (120, 200, 110), TALL: (60, 160, 60),
          PATH: (230, 205, 150), SAND: (245, 225, 170), TREE: (20, 90, 40), ROCK: (130, 80, 60), OTHER: (255, 0, 255)}


def preview(grid, scale=3, extra=None):
    im = Image.new('RGB', (W, H))
    im.putdata([COLORS.get(c, (255, 0, 255)) for c in grid])
    if extra:
        extra(im)
    return im.resize((W * scale, H * scale), Image.NEAREST)
