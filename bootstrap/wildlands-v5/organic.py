from collections import Counter
import random
def organic_edges(g, W, H, C, rng):
    TREE, WATER, ROCK, OCEAN, LAIR, BRIDGE, GRASS, TALL, FORTREE = C['TREE'], C['WATER'], C['ROCK'], C['OCEAN'], C['LAIR'], C['BRIDGE'], C['GRASS'], C['TALL'], C['FORTREE']
    hard = (OCEAN, WATER, LAIR, BRIDGE, TREE, ROCK)
    def n3(g, x, y, c):
        return sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if g[(y + dy) * W + x + dx] == c)
    for c, passes in ((TREE, ((4, .85), (5, .4), (6, .07))), (WATER, ((4, .9), (5, .45), (6, .06))), (ROCK, ((4, .7), (5, .3)))):
        for limit, p in passes:
            out = g[:]
            core = [False] * (W * H)
            for yy in range(1, H - 1):
                for xx in range(1, W - 1):
                    if g[yy * W + xx] == c and n3(g, xx, yy, c) == 9:
                        core[yy * W + xx] = True
            for y in range(1, H - 1):
                for x in range(1, W - 1):
                    if g[y * W + x] != c:
                        continue
                    n = n3(g, x, y, c)
                    # Only masses round off: 2-wide rivers, ridges and tree
                    # lines keep their shape (and stay continuous).
                    if not any(core[(y + dy) * W + x + dx] for dy in range(-2, 3) for dx in range(-2, 3)
                               if 0 <= x + dx < W and 0 <= y + dy < H):
                        continue
                    if n > limit or (limit == 6 and n != 6) or rng.random() >= p:
                        continue
                    v = Counter(g[(y + dy) * W + x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                if g[(y + dy) * W + x + dx] not in hard)
                    if v:
                        out[y * W + x] = v.most_common(1)[0][0]
            g = out
    return g
def tall_blobs(g, W, H, des, C, rng, n=160):
    GRASS, TALL, FORTREE = C['GRASS'], C['TALL'], C['FORTREE']
    for _ in range(n * 6):
        if n <= 0: break
        x, y = rng.randrange(5, W - 5), rng.randrange(5, H - 5)
        if des[y * W + x] != FORTREE: continue
        if any(g[(y + j) * W + x + i] != GRASS for j in range(-4, 5) for i in range(-4, 5)): continue
        r = rng.choice((1.6, 2.2, 2.8))
        for j in range(-3, 4):
            for i in range(-3, 4):
                if (i * i + j * j) ** .5 <= r + rng.uniform(-.5, .5):
                    g[(y + j) * W + x + i] = TALL
        n -= 1
    return g
