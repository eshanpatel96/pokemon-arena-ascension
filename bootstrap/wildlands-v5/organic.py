from collections import Counter
import random
def organic_edges(g, W, H, C, rng):
    TREE, WATER, ROCK, OCEAN, LAIR, BRIDGE, GRASS, TALL, FORTREE = C['TREE'], C['WATER'], C['ROCK'], C['OCEAN'], C['LAIR'], C['BRIDGE'], C['GRASS'], C['TALL'], C['FORTREE']
    hard = (OCEAN, WATER, LAIR, BRIDGE, TREE, ROCK)
    def n3(g, x, y, c):
        return sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if g[(y + dy) * W + x + dx] == c)
    for c, passes in ((TREE, ((4, .85), (5, .4), (6, .07))), (WATER, ((4, .9), (5, .45), (6, .06))), (ROCK, ((4, .7), (5, .3))),
                      (TALL, ((4, .85), (5, .4)))):
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


def organic_coast(g, W, H, C, rng):
    """Round the coastline: fill the ocean's convex corners (land notches) and
    trim the land's convex corners into the sea, two passes, so the shore
    reads as a curve instead of 2-cell stairs. Thin channels are kept."""
    OCEAN, SAND, LAIR, BRIDGE = C['OCEAN'], C['SAND'], C['LAIR'], C['BRIDGE']
    def n3(g, x, y, c):
        return sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if g[(y + dy) * W + x + dx] == c)
    for limit, p in ((4, .85), (5, .4)):
        core = [False] * (W * H)
        for yy in range(1, H - 1):
            for xx in range(1, W - 1):
                if g[yy * W + xx] == OCEAN and n3(g, xx, yy, OCEAN) == 9:
                    core[yy * W + xx] = True
        out = g[:]
        for y in range(2, H - 2):
            for x in range(2, W - 2):
                c = g[y * W + x]
                if c == OCEAN:
                    if n3(g, x, y, OCEAN) <= limit and rng.random() < p and not any(
                            g[(y + dy) * W + x + dx] in (LAIR, BRIDGE) for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                        # Only a notch in an open-sea edge (not a channel).
                        if any(core[(y + dy) * W + x + dx] for dy in range(-2, 3) for dx in range(-2, 3)):
                            out[y * W + x] = SAND
                elif c == SAND:
                    if n3(g, x, y, OCEAN) >= 9 - limit and rng.random() < p:
                        out[y * W + x] = OCEAN
        g = out
    return g


def _comps(g, W, H, want):
    """4-connected components of cells where want(class) is true."""
    seen = bytearray(W * H)
    out = []
    for s in range(W * H):
        if seen[s] or not want(g[s]):
            continue
        stack, comp = [s], []
        seen[s] = 1
        while stack:
            i = stack.pop()
            comp.append(i)
            x, y = i % W, i // W
            for j in ((i - 1) if x else -1, (i + 1) if x + 1 < W else -1, i - W, i + W):
                if 0 <= j < W * H and not seen[j] and want(g[j]):
                    seen[j] = 1
                    stack.append(j)
        out.append(comp)
    return out


def _vnoise(W, H, cell, rng):
    gw, gh = W // cell + 2, H // cell + 2
    grid = [rng.random() for _ in range(gw * gh)]
    def at(x, y):
        fx, fy = x / cell, y / cell
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = grid[y0 * gw + x0]; b = grid[y0 * gw + x0 + 1]
        c = grid[(y0 + 1) * gw + x0]; d = grid[(y0 + 1) * gw + x0 + 1]
        return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty
    return at


def map_cleanup(g, W, H, des, clearings, C, rng):
    """V6.6 map pass:
    1. stray sea islets and sea rocks (small land specks in the ocean) go;
    2. specks on open desert/highland ground (1-6 cell trees, grass, ponds,
       most lone rocks) go, so cover reads as deliberate outcrops;
    3. long straight coasts get coherent bays and capes from smooth noise."""
    OCEAN, SAND, LAIR, BRIDGE = C['OCEAN'], C['SAND'], C['LAIR'], C['BRIDGE']
    TREE, ROCK, GRASS, TALL, WATER, STONE = C['TREE'], C['ROCK'], C['GRASS'], C['TALL'], C['WATER'], C['STONE']
    g = g[:]
    log = {}
    def near_clearing(x, y, pad):
        return any((x - c['cx']) ** 2 + (y - c['cy']) ** 2 <= (c['r'] + pad) ** 2 for c in clearings)
    # 1. islets
    n = 0
    for comp in _comps(g, W, H, lambda c: c != OCEAN):
        if len(comp) >= 40 or any(g[i] in (LAIR, BRIDGE) for i in comp):
            continue
        if any(near_clearing(i % W, i // W, 0) for i in comp[:1]):
            continue
        for i in comp:
            g[i] = OCEAN
        n += len(comp)
    log['islet_cells'] = n
    # 2. specks on open ground
    ground = (SAND, STONE)
    n = kept = 0
    for cls_ in (TREE, GRASS, TALL, WATER, ROCK):
        for comp in _comps(g, W, H, lambda c, k=cls_: c == k):
            if len(comp) > 6:
                continue
            nb = []
            cs = set(comp)
            for i in comp:
                x, y = i % W, i // W
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    if 0 <= x + dx < W and 0 <= y + dy < H and (y + dy) * W + x + dx not in cs:
                        nb.append(g[(y + dy) * W + x + dx])
            if not nb or any(c not in ground for c in nb):
                continue
            if cls_ == ROCK and rng.random() < 0.35:
                kept += 1
                continue
            fill = max(set(nb), key=nb.count)
            for i in comp:
                g[i] = fill
            n += len(comp)
    log['speck_cells'] = n
    log['rocks_kept'] = kept
    # 3. coast bays and capes
    noise = _vnoise(W, H, 9, rng)
    def ring(x, y, r):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    yield g[(y + dy) * W + x + dx]
    out = g[:]
    bays = capes = 0
    for y in range(3, H - 3):
        for x in range(3, W - 3):
            c = g[y * W + x]
            if c == SAND:
                if noise(x, y) < 0.70:
                    continue
                r2 = list(ring(x, y, 2))
                if OCEAN not in r2:
                    continue
                if any(v not in (SAND, OCEAN) for v in ring(x, y, 3)) or near_clearing(x, y, 4):
                    continue
                out[y * W + x] = OCEAN; bays += 1
            elif c == OCEAN:
                if noise(x, y) > 0.30 or x < 4 or y < 4 or x >= W - 4 or y >= H - 4:
                    continue
                r1 = list(ring(x, y, 1))
                if SAND not in r1 or any(v not in (SAND, OCEAN) for v in r1):
                    continue
                # open sea only: the cell two steps further out is still sea
                if sum(1 for v in ring(x, y, 2) if v == OCEAN) < 14:
                    continue
                out[y * W + x] = SAND; capes += 1
    g = out
    log['bays'] = bays
    log['capes'] = capes
    return g, log
