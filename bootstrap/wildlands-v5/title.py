#!/usr/bin/env python3
"""Install the approved Pokemon Wildlands title (Charizard + Blastoise facing
the island, Rayquaza above, PRESS START) as the native 240x160 mode-4 title.

Source: docs/art/wildlands-title-240x160.png, a 256-colour, undithered
downscale of the approved concept (docs/art/wildlands-title-concept.png) with
its "title screen concept" caption removed. Replaces the V4 placeholder.
"""
from pathlib import Path
from PIL import Image
import sys

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[2]
img = Image.open(repo / 'docs/art/wildlands-title-240x160.png')
assert img.size == (240, 160) and img.mode == 'P', (img.size, img.mode)
out = root / 'graphics/title_screen/wildlands_v4'
out.mkdir(parents=True, exist_ok=True)
(out / 'title.raw').write_bytes(img.tobytes())
pal = (img.getpalette() + [0] * 768)[:768]
data = bytearray()
for i in range(256):
    r, g, b = pal[i * 3:i * 3 + 3]
    c = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)
    data += bytes((c & 255, c >> 8))
(out / 'title.gbapal').write_bytes(data)
print('Wildlands approved title installed: 240x160, %d colours' % len(img.getcolors(256)))
