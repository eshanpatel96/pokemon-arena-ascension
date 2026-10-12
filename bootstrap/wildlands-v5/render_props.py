#!/usr/bin/env python3
"""Evidence only: render the arena's prop sheets (5 biome sets x 7 props x
intact/damaged/broken) to a PNG, with the terrain palette, for art review."""
from pathlib import Path
from PIL import Image
import sys
eng = Path(sys.argv[1]); out = Path(sys.argv[2])
pal = [(0,0,0),(6,9,7),(11,14,10),(15,18,15),(21,24,18),(28,30,24),(13,8,5),(21,13,7),(13,20,7),(30,23,11),
       (22,27,10),(5,20,27),(22,31,31),(17,10,25),(31,10,4),(31,30,19)]
pal = [(r*8, g*8, b*8) for r, g, b in pal]
names = ['props', 'coast-props', 'cave-props', 'desert-props', 'gym-props']
im = Image.new('RGB', (7 * 3 * 34, len(names) * 34), (255, 0, 255))
for row, n in enumerate(names):
    p = eng / '.arena-dev/art' / (n + '.4bpp')
    if not p.exists():
        continue
    b = p.read_bytes()
    for f in range(min(21, len(b) // 512)):
        fr = b[f * 512:(f + 1) * 512]
        for t in range(16):
            tx, ty = (t % 4) * 8, (t // 4) * 8
            for y in range(8):
                for x in range(8):
                    byte = fr[t * 32 + y * 4 + x // 2]
                    c = (byte >> 4) if x & 1 else (byte & 15)
                    if c:
                        im.putpixel((f * 34 + tx + x, row * 34 + ty + y), pal[c])
im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(out)
print('rendered', out)
