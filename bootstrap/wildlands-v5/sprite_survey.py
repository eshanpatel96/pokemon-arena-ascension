#!/usr/bin/env python3
"""Read-only audit of Arena (PMD) sprite sizes: opaque bounding box of the
idle animation's first frame (south facing) for every species set.
Usage: sprite_survey.py ENGINE_ROOT"""
import re, struct, sys
from pathlib import Path
root = Path(sys.argv[1])
pmd = root / '.arena-dev/pmd'
inc = (pmd / 'sprites.inc').read_text(errors='ignore') if (pmd / 'sprites.inc').exists() else ''
print('files', len(list(pmd.glob('*'))) if pmd.exists() else 'MISSING')
print(inc[:1500])
print('----')
def bbox(path, frames_hint=None):
    b = path.read_bytes()
    if len(b) < 16:
        return None
    dict_off, dict_n = struct.unpack_from('<II', b, 0)
    m = struct.unpack_from('<64H', b, 8)          # direction 0, frame 0
    xs, ys = [], []
    for t, idx in enumerate(m):
        if idx >= dict_n:
            return None
        tile = b[dict_off + idx * 32: dict_off + idx * 32 + 32]
        tx, ty = (t % 8) * 8, (t // 8) * 8
        for y in range(8):
            row = struct.unpack_from('<I', tile, y * 4)[0]
            for x in range(8):
                if (row >> (x * 4)) & 15:
                    xs.append(tx + x); ys.append(ty + y)
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
rows = []
for f in sorted(pmd.glob('*.4bpp')) if pmd.exists() else []:
    try:
        bb = bbox(f)
    except Exception as e:
        bb = repr(e)
    rows.append((f.name, bb))
for name, bb in rows:
    print(name, bb)
