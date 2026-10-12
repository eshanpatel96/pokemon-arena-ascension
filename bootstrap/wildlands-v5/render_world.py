#!/usr/bin/env python3
"""Evidence only: render the outdoor island from its native metatiles
(General primary + each cell's streamed secondary) to PNG for map review.

Writes <out>/world-half.png (2048x1536) and world-quarter.png.
"""
from pathlib import Path
from PIL import Image
import struct, sys

eng = Path(sys.argv[1]); out = Path(sys.argv[2])
wd = eng / 'data/wildlands_world'
W, H = 256, 192
world = struct.unpack('<%dH' % (len(wd.joinpath('slice.bin').read_bytes()) // 2), wd.joinpath('slice.bin').read_bytes())
sec = wd.joinpath('biome.bin').read_bytes()
SEC = {1: 'fortree', 2: 'mauville', 3: 'fallarbor', 4: 'lavaridge', 5: 'slateport'}


def pal_file(p):
    lines = p.read_text().split('\n')[3:19]
    return [tuple(int(v) for v in l.split()[:3]) for l in lines if l.strip()]


def load_set(d):
    tiles = Image.open(d / 'tiles.png')
    tw = tiles.width // 8
    idx = list(tiles.getdata())
    tl = []
    for t in range((tiles.width // 8) * (tiles.height // 8)):
        tx, ty = (t % tw) * 8, (t // tw) * 8
        tl.append([idx[(ty + y) * tiles.width + tx + x] & 15 for y in range(8) for x in range(8)])
    mb = (d / 'metatiles.bin').read_bytes()
    metas = [struct.unpack('<8H', mb[i:i + 16]) for i in range(0, len(mb), 16)]
    pals = [pal_file(d / 'palettes' / ('%02d.pal' % k)) if (d / 'palettes' / ('%02d.pal' % k)).exists() else [(0, 0, 0)] * 16
            for k in range(16)]
    return tl, metas, pals


prim = load_set(eng / 'data/tilesets/primary/general')
secs = {k: load_set(eng / 'data/tilesets/secondary' / v) for k, v in SEC.items()
        if (eng / 'data/tilesets/secondary' / v / 'tiles.png').exists()}
cache = {}


def metatile_img(mid, s):
    key = (mid, s)
    if key in cache:
        return cache[key]
    st = secs.get(s) or secs.get(1)
    ptl, pmeta, ppal = prim
    stl, smeta, spal = st
    pals = ppal[:6] + spal[6:13] + ppal[13:]
    meta = pmeta[mid] if mid < 512 else (smeta[mid - 512] if mid - 512 < len(smeta) else (0,) * 8)
    im = Image.new('RGB', (16, 16), (0, 0, 0))
    px = im.load()
    for layer in (0, 1):
        for q in range(4):
            e = meta[layer * 4 + q]
            t, xf, yf, pal = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12
            data = ptl[t] if t < 512 else (stl[t - 512] if t - 512 < len(stl) else [0] * 64)
            ox, oy = (q & 1) * 8, (q >> 1) * 8
            for y in range(8):
                for x in range(8):
                    c = data[(7 - y if yf else y) * 8 + (7 - x if xf else x)]
                    if c or layer == 0:
                        if c == 0 and layer == 0:
                            c = 0
                        px[ox + x, oy + y] = pals[pal][c] if pal < len(pals) and c < len(pals[pal]) else (255, 0, 255)
    cache[key] = im
    return im


full = Image.new('RGB', (W * 16, H * 16))
for y in range(H):
    for x in range(W):
        i = y * W + x
        full.paste(metatile_img(world[i] & 0x3FF, sec[i] if i < len(sec) else 0), (x * 16, y * 16))
out.mkdir(parents=True, exist_ok=True)
full.resize((W * 8, H * 8), Image.BOX).save(out / 'world-half.png', optimize=True)
full.resize((W * 4, H * 4), Image.BOX).save(out / 'world-quarter.png', optimize=True)
print('world rendered', len(cache), 'distinct metatiles')
