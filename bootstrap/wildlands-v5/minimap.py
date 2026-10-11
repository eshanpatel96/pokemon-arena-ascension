"""Build-time minimap: the live map's base terrain layer as 4bpp tiles.

Same classification the runtime used per pixel (collision-first): bridge ->
ground, deep water -> water, solid -> solid, concealment -> grass, else
ground. One map pixel covers `scale` x `scale` metatiles. Emitted in window
tile order (row-major 8x8 tiles, 4bpp, low nibble = left pixel).
"""
WATER, SOLID, GROUND, GRASS = 13, 14, 15, 3


def emit(terrain, W, H, path, max_w=96, max_h=64):
    scale = max(1, -(-W // max_w), -(-H // max_h))
    mw, mh = -(-W // scale), -(-H // scale)
    tw, th = -(-mw // 8), -(-mh // 8)
    px = [[9] * (tw * 8) for _ in range(th * 8)]
    for y in range(mh):
        for x in range(mw):
            f = 0
            for dy in range(scale):
                for dx in range(scale):
                    X, Y = x * scale + dx, y * scale + dy
                    if X < W and Y < H:
                        f |= terrain[Y * W + X]
            px[y][x] = GROUND if f & 16 else WATER if f & 2 else SOLID if f & 1 else GRASS if f & 8 else GROUND
    data = bytearray()
    for ty in range(th):
        for tx in range(tw):
            for r in range(8):
                row = px[ty * 8 + r][tx * 8:tx * 8 + 8]
                for i in range(0, 8, 2):
                    data.append(row[i] | (row[i + 1] << 4))
    with open(path, 'w') as f:
        f.write(f'#define WL_MINIMAP_SCALE {scale}\n#define WL_MINIMAP_W {mw}\n#define WL_MINIMAP_H {mh}\n'
                f'#define WL_MINIMAP_TW {tw}\n#define WL_MINIMAP_TH {th}\n'
                'static const u8 sMinimapTiles[] = {' + ','.join(map(str, data)) + '};\n')
    return scale, mw, mh
