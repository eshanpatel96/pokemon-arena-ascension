"""Native cover props mined from real Hoenn routes.

A prop is a small solid metatile group (1-6 cells, rectangular) that Game
Freak placed with open ground all around it: boulders, rock outcrops, bushes,
hedges, sea rocks. Their collision bits come with them, so in Wildlands they
block movement AND projectiles exactly like the art suggests (no invisible
walls). Signs are excluded (any metatile that sits under a sign bg_event).
Each prop is tagged by which secondary tileset it needs ('general' = primary
only, usable anywhere) and whether it stands on land or water, and by look
('green' bush/hedge vs 'rock').
"""
from collections import Counter
from pathlib import Path
import json, re

from emerald_tiles import Pair, load_layout


def _snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def sign_tiles(root):
    out = set()
    for mj in (Path(root) / 'data/maps').glob('Route*/map.json'):
        j = json.load(open(mj))
        try:
            l, g = load_layout(root, j['layout'].replace('LAYOUT_', '').title().replace('_', ''))
        except Exception:
            continue
        for b in j.get('bg_events', []):
            if b.get('type') == 'sign':
                x, y = b['x'], b['y']
                if 0 <= x < l['width'] and 0 <= y < l['height']:
                    out.add(g[y * l['width'] + x] & 0x3ff)
    return out


def mine(root, flag_model, min_uses=2, max_cells=6):
    L = json.load(open(Path(root) / 'data/layouts/layouts.json'))['layouts']
    wild = re.compile(r'^(Route\d+)_Layout$')
    signs = sign_tiles(root)
    props = Counter()
    pairs = {}
    for l in L:
        if not l or not wild.match(l['name']) or l['primary_tileset'] != 'gTileset_General':
            continue
        sn = _snake(l['secondary_tileset'][9:])
        if sn not in pairs:
            pairs[sn] = Pair(root, 'general', sn)
        p = pairs[sn]
        _, g = load_layout(root, l['name'])
        W, H = l['width'], l['height']
        F = [flag_model.flags(e, p.behavior(e & 0x3ff)) for e in g]
        seen = set()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if (x, y) in seen or not F[y * W + x] & 1:
                    continue
                comp = [(x, y)]; seen.add((x, y)); i = 0; ok = True
                while i < len(comp) and len(comp) <= max_cells:
                    cx, cy = comp[i]; i += 1
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if not (0 < nx < W - 1 and 0 < ny < H - 1):
                            ok = False; continue
                        if (nx, ny) in seen:
                            continue
                        if F[ny * W + nx] & 1:
                            comp.append((nx, ny)); seen.add((nx, ny))
                if len(comp) > max_cells or not ok:
                    continue
                xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
                if (x1 - x0 + 1) * (y1 - y0 + 1) != len(comp):
                    continue
                if any((g[cy * W + cx] & 0x3ff) in signs for cx, cy in comp):
                    continue
                ring = [(xx, yy) for yy in range(y0 - 1, y1 + 2) for xx in range(x0 - 1, x1 + 2)
                        if not (x0 <= xx <= x1 and y0 <= yy <= y1)]
                water = sum(1 for xx, yy in ring if F[yy * W + xx] & 2)
                kind = 'water' if water * 2 > len(ring) else 'land' if water == 0 else None
                if kind is None:
                    continue
                need = sn if any((g[cy * W + cx] & 0x3ff) >= 512 for cx, cy in comp) else 'general'
                rows = tuple(tuple(g[(y0 + j) * W + x0 + i] & 0x0FFF for i in range(x1 - x0 + 1)) for j in range(y1 - y0 + 1))
                props[(need, kind, rows)] += 1
    out = []
    for (need, kind, rows), n in props.most_common():
        if n < min_uses:
            continue
        p = pairs.get(need, pairs.get('fortree'))
        r = g_ = b = 0; cnt = 0
        for row in rows:
            for e in row:
                im = p.render_meta(e & 0x3ff).convert('RGB')
                for px in im.getdata():
                    r += px[0]; g_ += px[1]; b += px[2]; cnt += 1
        r, g_, b = r / cnt, g_ / cnt, b / cnt
        look = 'green' if g_ > r + 10 and g_ > b else 'rock'
        out.append(dict(need=need, kind=kind, rows=[list(row) for row in rows], uses=n, look=look,
                        w=len(rows[0]), h=len(rows)))
    return out
