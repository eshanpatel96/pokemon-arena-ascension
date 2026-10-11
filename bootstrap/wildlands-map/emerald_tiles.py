"""Native Emerald tileset/metatile loader and renderer (design + audit tool).

Reads pokeemerald data/tilesets/{primary,secondary}/<name>/ (tiles.png indexed,
palettes/*.pal, metatiles.bin, metatile_attributes.bin) exactly as the game
does: 512 primary + up to 512 secondary metatiles, 8 tiles each (bottom layer
then top layer), 16-bit tile entries with hflip/vflip/palette.
"""
from pathlib import Path
import struct
from PIL import Image

NUM_PRIMARY = 512


def _words(p):
    b = Path(p).read_bytes()
    return list(struct.unpack('<%dH' % (len(b) // 2), b))


def _pal(p):
    lines = Path(p).read_text().split()
    n = int(lines[2])
    vals = list(map(int, lines[3:3 + 3 * n]))
    return [tuple(vals[i * 3:i * 3 + 3]) for i in range(n)]


class Tileset:
    def __init__(self, root, kind, name):
        d = Path(root) / 'data/tilesets' / kind / name
        img = Image.open(d / 'tiles.png')
        assert img.mode == 'P', d
        w, h = img.size
        px = img.load()
        self.tiles = []
        for ty in range(h // 8):
            for tx in range(w // 8):
                self.tiles.append([[px[tx * 8 + x, ty * 8 + y] & 15 for x in range(8)] for y in range(8)])
        self.pals = [_pal(d / 'palettes' / ('%02d.pal' % i)) for i in range(16)]
        self.metatiles = _words(d / 'metatiles.bin')
        self.attrs = _words(d / 'metatile_attributes.bin')
        self.dir = d


class Pair:
    """A primary+secondary pair as loaded in VRAM (tiles 0-511 primary, 512+ secondary;
    palettes 0-5 primary, 6-12 secondary)."""

    def __init__(self, root, primary='general', secondary='fortree'):
        self.p = Tileset(root, 'primary', primary)
        self.s = Tileset(root, 'secondary', secondary)
        self.cache = {}

    def tile(self, idx):
        if idx < 512:
            return self.p.tiles[idx] if idx < len(self.p.tiles) else None
        i = idx - 512
        return self.s.tiles[i] if i < len(self.s.tiles) else None

    def pal(self, n):
        return self.p.pals[n] if n < 6 else self.s.pals[n]

    def meta(self, mid):
        if mid < NUM_PRIMARY:
            m = self.p.metatiles[mid * 8:mid * 8 + 8]
        else:
            j = mid - NUM_PRIMARY
            m = self.s.metatiles[j * 8:j * 8 + 8]
        return m

    def attr(self, mid):
        if mid < NUM_PRIMARY:
            return self.p.attrs[mid] if mid < len(self.p.attrs) else 0
        j = mid - NUM_PRIMARY
        return self.s.attrs[j] if j < len(self.s.attrs) else 0

    def behavior(self, mid):
        return self.attr(mid) & 0xff

    def layer_type(self, mid):
        return (self.attr(mid) >> 12) & 0xf

    def render_meta(self, mid, layers=(0, 1)):
        key = (mid, layers)
        if key in self.cache:
            return self.cache[key]
        im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        px = im.load()
        m = self.meta(mid)
        if len(m) < 8:
            self.cache[key] = im
            return im
        for layer in layers:
            for q in range(4):
                e = m[layer * 4 + q]
                t = self.tile(e & 0x3ff)
                if t is None:
                    continue
                hf, vf, pn = (e >> 10) & 1, (e >> 11) & 1, (e >> 12) & 15
                pal = self.pal(pn)
                ox, oy = (q & 1) * 8, (q >> 1) * 8
                for y in range(8):
                    for x in range(8):
                        c = t[7 - y if vf else y][7 - x if hf else x]
                        if c == 0 and not (layer == 0):
                            continue
                        if c == 0 and layer == 0:
                            col = pal[0]
                        else:
                            col = pal[c]
                        px[ox + x, oy + y] = col + (255,)
        self.cache[key] = im
        return im


def render_map(pair, grid, w, h, scale=1, layers=(0, 1), overlay=None):
    im = Image.new('RGB', (w * 16, h * 16))
    for y in range(h):
        for x in range(w):
            e = grid[y * w + x]
            im.paste(pair.render_meta(e & 0x3ff, layers), (x * 16, y * 16), pair.render_meta(e & 0x3ff, layers))
    if overlay:
        overlay(im)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return im


def load_layout(root, name):
    import json
    L = json.load(open(Path(root) / 'data/layouts/layouts.json'))['layouts']
    for l in L:
        if l and l['name'] == name + '_Layout' or (l and l['name'] == name):
            words = _words(Path(root) / l['blockdata_filepath'])
            return l, words
    raise KeyError(name)
