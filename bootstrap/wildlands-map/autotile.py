"""Learned autotiling from real Emerald outdoor layouts.

Every General-primary metatile cell in real Hoenn layouts gets a semantic
class (from native behavior, collision bits and its rendered colors). We then
record, for each class and 8-neighbour class signature, which native metatile
Game Freak actually placed there. Synthesis looks up the most frequent real
choice for each planned cell, so shorelines, forest edges, cliff faces and
path borders come from authentic placements instead of hand-drawn guesses.

Only metatiles valid for the region's (primary, secondary) pair are learned.
"""
from collections import Counter, defaultdict
import json, struct
from pathlib import Path
from emerald_tiles import Pair

# semantic classes
OCEAN, WATER, GRASS, TALL, PATH, SAND, TREE, ROCK, OTHER = range(9)
NAMES = ['ocean', 'water', 'grass', 'tall', 'path', 'sand', 'tree', 'rock', 'other']
WATER_B = {0x10, 0x11, 0x12, 0x14, 0x15, 0x19, 0x1a}
OCEAN_B = {0x15}


def _rgb_stats(im):
    px = list(im.convert('RGB').getdata())
    r = sum(p[0] for p in px) / len(px); g = sum(p[1] for p in px) / len(px); b = sum(p[2] for p in px) / len(px)
    return r, g, b


def classify(pair, entry):
    mid = entry & 0x3ff
    beh = pair.behavior(mid)
    blocked = (entry >> 10) & 3
    if beh in OCEAN_B:
        return OCEAN
    if beh in WATER_B or beh == 0x13:  # waterfall counts as water
        return WATER
    if beh in (0x02, 0x03, 0x09, 0x24):
        return TALL
    if beh in (0x06, 0x21):
        return SAND
    r, g, b = _rgb_stats(pair.render_meta(mid))
    greenish = g > r + 12 and g > b
    if blocked:
        if greenish:
            return TREE
        return ROCK
    if b > r + 25 and b > g:
        return WATER  # drawn water edges with walkable behaviour are rare; treat as water visual
    if greenish:
        return GRASS
    if r > 150 and g > 130 and b < 140:
        return PATH
    return OTHER


def neigh_sig(cls, x, y, w, h, c0, mode):
    sig = []
    for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1)) if mode == 4 else ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)):
        xx, yy = x + dx, y + dy
        c = cls[yy * w + xx] if 0 <= xx < w and 0 <= yy < h else c0
        sig.append(c)
    return tuple(sig)


class Model:
    def __init__(self):
        self.t8 = defaultdict(Counter)
        self.t4 = defaultdict(Counter)
        self.t0 = defaultdict(Counter)
        self.pairs_h = set(); self.pairs_v = set()
        self.cell_class = {}

    def key8(self, c, sig, x, y):
        return (c, sig, (x & 1, y & 1) if c == TREE else None)

    def learn(self, pair, words, w, h, allow, foreign_secondary=False):
        cls = [OTHER if (foreign_secondary and (e & 0x3ff) >= 512) else classify(pair, e) for e in words]
        for y in range(h):
            for x in range(w):
                e = words[y * w + x]
                mid = e & 0x3ff
                if not allow(mid):
                    continue
                c = cls[y * w + x]
                ent = e & 0x0fff  # keep metatile id + collision, drop elevation
                self.t8[self.key8(c, neigh_sig(cls, x, y, w, h, c, 8), x, y)][ent] += 1
                self.t4[(c, neigh_sig(cls, x, y, w, h, c, 4))][ent] += 1
                self.t0[c][ent] += 1
                self.cell_class[mid] = c
                if x + 1 < w: self.pairs_h.add((mid, words[y * w + x + 1] & 0x3ff))
                if y + 1 < h: self.pairs_v.add((mid, words[(y + 1) * w + x] & 0x3ff))

    def finalize(self, pair, min_tile_uses=12, min_key=2):
        """Drop one-off object tiles (signs, doors, roofs, stairs) and rare
        patterns so free synthesis only uses terrain Game Freak repeats."""
        uses = Counter()
        for cnt in self.t0.values():
            uses.update({e & 0x3ff: n for e, n in cnt.items()})
        dark_water = {0x11, 0x12, 0x15}
        # Fortree's round bush-trees read as orchards at island scale; forests
        # use the dense Route 119/120 canopy family instead.
        bush = {0x1d4, 0x1d5, 0x1dc, 0x1dd, 0x1e4, 0x1e5, 0x1d6, 0x1d7, 0x1de, 0x1df, 0x1e6, 0x1e7, 0x1ec, 0x1ed}
        def ok(c, e):
            mid = e & 0x3ff
            if uses[mid] < min_tile_uses:
                return False
            if c == TREE and mid in bush:
                return False
            if c == WATER and pair.behavior(mid) in dark_water:
                return False
            if c == OCEAN and pair.behavior(mid) not in (0x15, 0x12, 0x00):
                return False
            return True
        for table in (self.t8, self.t4):
            for k in list(table):
                cnt = Counter({e: n for e, n in table[k].items() if ok(k[0], e)})
                if sum(cnt.values()) < min_key:
                    del table[k]
                else:
                    table[k] = cnt
        for c in list(self.t0):
            self.t0[c] = Counter({e: n for e, n in self.t0[c].items() if ok(c, e)})

    def pick(self, c, cls, x, y, w, h, rng=None):
        k = self.key8(c, neigh_sig(cls, x, y, w, h, c, 8), x, y)
        for table, key in ((self.t8, k), (self.t4, (c, neigh_sig(cls, x, y, w, h, c, 4))), (self.t0, c)):
            cnt = table.get(key)
            if cnt:
                if rng is not None and len(cnt) > 1 and table is self.t0:
                    items = cnt.most_common(4)
                    tot = sum(n for _, n in items)
                    r = rng.random() * tot
                    for e, n in items:
                        r -= n
                        if r <= 0:
                            return e, (0 if table is self.t8 else 1 if table is self.t4 else 2)
                return cnt.most_common(1)[0][0], (0 if table is self.t8 else 1 if table is self.t4 else 2)
        return None, 3


def train(root, secondary_name, secondary_key, extra_layouts=()):
    """Train on every General+<secondary> outdoor layout plus primary-only cells of all others."""
    root = Path(root)
    L = json.load(open(root / 'data/layouts/layouts.json'))['layouts']
    pair = Pair(root, 'general', secondary_name)
    m = Model()
    for l in L:
        if not l or l['primary_tileset'] != 'gTileset_General':
            continue
        same = l['secondary_tileset'] == secondary_key
        b = (root / l['blockdata_filepath']).read_bytes()
        words = list(struct.unpack('<%dH' % (len(b) // 2), b))
        w, h = l['width'], l['height']
        prim_share = sum(1 for e in words if (e & 0x3ff) < 512) / len(words)
        if not same and prim_share < 0.85:
            continue  # interiors/caves: different visual language
        if same:
            m.learn(pair, words, w, h, lambda mid: True)
        else:
            # other secondaries: learn only primary cells; classify via that layout's own pair
            m.learn(pair, words, w, h, lambda mid: mid < 512, foreign_secondary=True)
    m.finalize(pair)
    return pair, m


def pair_ok(m, a, b, horiz):
    return ((a & 0x3ff), (b & 0x3ff)) in (m.pairs_h if horiz else m.pairs_v)


def repair(m, grid, cls, w, h, sweeps=4, candidates=None, frozen=None):
    """Local constraint repair: replace cells whose neighbour pairs never occur
    in real Emerald maps with same-class tiles that maximise authentic pairs."""
    if candidates is None:
        candidates = {c: [e for e, _ in cnt.most_common(60)] for c, cnt in m.t0.items()}
    freq = {c: {e: n for e, n in cnt.items()} for c, cnt in m.t0.items()}

    def score(i, e):
        x, y = i % w, i // w
        s = 0
        if x > 0: s += pair_ok(m, grid[i - 1], e, True)
        if x + 1 < w: s += pair_ok(m, e, grid[i + 1], True)
        if y > 0: s += pair_ok(m, grid[i - w], e, False)
        if y + 1 < h: s += pair_ok(m, e, grid[i + w], False)
        return s

    def nmax(i):
        x, y = i % w, i // w
        return (x > 0) + (x + 1 < w) + (y > 0) + (y + 1 < h)

    bad_total = []
    for sweep in range(sweeps):
        bad = 0; fixed = 0
        for i in range(w * h):
            if frozen and frozen[i]:
                continue
            cur = score(i, grid[i])
            if cur == nmax(i):
                continue
            bad += 1
            best, bs = grid[i], cur * 1000 + freq.get(cls[i], {}).get(grid[i], 0) % 1000
            for e in candidates.get(cls[i], ()):
                s = score(i, e) * 1000 + min(999, freq[cls[i]].get(e, 0))
                if s > bs:
                    best, bs = e, s
            if best != grid[i]:
                grid[i] = best; fixed += 1
        bad_total.append((bad, fixed))
        if fixed == 0:
            break
    return grid, bad_total


def violations(m, grid, w, h):
    v = 0
    for i in range(w * h):
        x, y = i % w, i // w
        if x + 1 < w and not pair_ok(m, grid[i], grid[i + 1], True): v += 1
        if y + 1 < h and not pair_ok(m, grid[i], grid[i + w], False): v += 1
    return v
