"""Build-time terrain flag table for the Wildlands world.

Mirrors wildlands_world.c's original TerrainEntry() exactly, using the engine's
own behaviour enum (include/constants/metatile_behaviors.h) and its
sTileBitAttributes surfable table (src/metatile_behavior.c), so the runtime can
replace ~15 out-of-line MetatileBehavior_* ROM calls per sample with one byte
read from a ROM-resident table. Zero EWRAM cost.
"""
from pathlib import Path
import re, struct

SOLID, DEEP_WATER, WET, CONCEAL, BRIDGE = 1, 2, 4, 8, 16


def behaviour_ids(root):
    src = (Path(root) / 'include/constants/metatile_behaviors.h').read_text()
    body = src[src.index('{'):src.index('}')]
    names = re.findall(r'^\s*(MB_\w+)\s*(?:=\s*(\w+))?\s*,', body, re.M)
    ids, n = {}, 0
    for name, val in names:
        if val:
            n = int(val, 0)
        ids[name] = n
        n += 1
    return ids


def surfable_ids(root, ids):
    src = (Path(root) / 'src/metatile_behavior.c').read_text()
    out = set()
    for name, flags in re.findall(r'\[(MB_\w+)\]\s*=\s*([^,\n]+(?:\|[^,\n]+)*),', src):
        if 'TILE_FLAG_SURFABLE' in flags and name in ids:
            out.add(ids[name])
    return out


class FlagModel:
    def __init__(self, root):
        ids = behaviour_ids(root)
        g = lambda *n: {ids[x] for x in n if x in ids}
        self.solid_beh = g('MB_IMPASSABLE_EAST', 'MB_IMPASSABLE_NORTHEAST', 'MB_IMPASSABLE_SOUTHEAST',
                           'MB_IMPASSABLE_WEST_AND_EAST', 'MB_SECRET_BASE_BREAKABLE_DOOR',
                           'MB_IMPASSABLE_WEST', 'MB_IMPASSABLE_NORTHWEST', 'MB_IMPASSABLE_SOUTHWEST',
                           'MB_IMPASSABLE_NORTH', 'MB_IMPASSABLE_SOUTH_AND_NORTH', 'MB_IMPASSABLE_SOUTH',
                           'MB_JUMP_EAST', 'MB_JUMP_WEST', 'MB_JUMP_NORTH', 'MB_JUMP_SOUTH')
        self.bridge = g('MB_BRIDGE_OVER_OCEAN', 'MB_BRIDGE_OVER_POND_LOW', 'MB_BRIDGE_OVER_POND_MED',
                        'MB_BRIDGE_OVER_POND_HIGH', 'MB_BRIDGE_OVER_POND_HIGH_EDGE_1',
                        'MB_BRIDGE_OVER_POND_HIGH_EDGE_2', 'MB_UNUSED_BRIDGE', 'MB_BIKE_BRIDGE_OVER_BARRIER',
                        'MB_FORTREE_BRIDGE')
        self.surf = surfable_ids(root, ids)
        self.wet = g('MB_PUDDLE', 'MB_SHALLOW_WATER', 'MB_STAIRS_OUTSIDE_ABANDONED_SHIP', 'MB_SHOAL_CAVE_ENTRANCE')
        self.conceal = g('MB_TALL_GRASS', 'MB_LONG_GRASS', 'MB_LONG_GRASS_SOUTH_EDGE')
        assert self.surf and self.bridge and self.conceal, 'behaviour parse failed'

    def flags(self, entry, behaviour):
        f = 0
        if (entry >> 10) & 3 or behaviour in self.solid_beh:
            f |= SOLID
        if behaviour in self.bridge:
            f |= BRIDGE
        elif behaviour in self.surf:
            f |= DEEP_WATER | WET
        if behaviour in self.wet:
            f |= WET
        if behaviour in self.conceal:
            f |= CONCEAL
        return f


def words(path):
    b = Path(path).read_bytes()
    return list(struct.unpack('<%dH' % (len(b) // 2), b))


def build_table(root, grid, primary_attr, secondary_attr):
    fm = FlagModel(root)
    out = bytearray()
    for e in grid:
        mid = e & 0x3ff
        attr = primary_attr[mid] if mid < 512 else secondary_attr[mid - 512]
        out.append(fm.flags(e, attr & 0xff))
    return bytes(out)
