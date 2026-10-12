"""Enterable interiors for the Wildlands world (build time).

Interiors are real Emerald interior layouts (houses, Weather Institute,
Navel Rock, Sky Pillar, Marine Cave) appended as a strip of rooms BELOW the
outdoor world in the same metatile grid. Collision, projectiles, pickups and
AI therefore keep using one coordinate space and one ROM terrain table. Each
room records its own primary+secondary tileset pair; the runtime swaps the
tile atlas and palettes on entry and renders only the active room (every
other cell draws blank), so rooms can sit close together.

Doors are outdoor cells (native door / water door / cliff cave metatiles).
A door takes the player into its room at a legal spot beside the room's
native exit warp; walking back onto that exit returns to the door it was
entered from.
"""
from pathlib import Path
import json, re, struct

from terrain_flags import FlagModel, words

GAP_X, GAP_Y, TOP = 16, 10, 10   # metatiles; >= one screen apart
BODY_R = 6                       # world movement footprint (wildlands_world.c WL_FOOT)
ROOM_R = 6
SOLID, DEEP, BRIDGE = 1, 2, 16


def _snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class PairData:
    def __init__(self, root, primary, secondary):
        self.primary, self.secondary = primary, secondary
        pdir = 'building' if primary == 'Building' else _snake(primary)
        self.pattr = words(Path(root) / f'data/tilesets/primary/{pdir}/metatile_attributes.bin')
        self.sattr = words(Path(root) / f'data/tilesets/secondary/{_snake(secondary)}/metatile_attributes.bin')

    def attr(self, entry):
        mid = entry & 0x3ff
        a = self.pattr if mid < 512 else self.sattr
        i = mid if mid < 512 else mid - 512
        return a[i] if i < len(a) else 0


def _layout(root, name):
    L = json.load(open(Path(root) / 'data/layouts/layouts.json'))['layouts']
    lay = next(l for l in L if l and l['name'] == name + '_Layout')
    return lay, words(Path(root) / lay['blockdata_filepath'])


def _exit_warp(root, layout_id):
    """First warp event of the first map using this layout (its native exit)."""
    for mj in sorted((Path(root) / 'data/maps').glob('*/map.json')):
        j = json.load(open(mj))
        if j.get('layout') == layout_id and j.get('warp_events'):
            w = j['warp_events'][0]
            return w['x'], w['y'], mj.parent.name
    raise SystemExit(f'no warp for {layout_id}')


def build(root, world, terrain, W, H, base, outdoor_pair, doors, rooms_spec):
    """world/terrain: outdoor grid (W x H). doors: list of dicts
    {cell:(x,y) local, room:key, kind:'door'|'water'|'cave', facing:'up'}.
    rooms_spec: ordered dict key -> {layout, loot:[types]}.
    Returns (world, terrain, total_h, c_source, loot_px, manifest)."""
    fm = FlagModel(root)
    pairs = [outdoor_pair]
    pair_data = {}
    rooms = []
    # Shelf-pack rooms under the outdoor world.
    x, y, shelf_h = 0, H + TOP, 0
    for key, spec in rooms_spec.items():
        lay, blocks = _layout(root, spec['layout'])
        w, h = lay['width'], lay['height']
        if x and x + w > W:
            x, y, shelf_h = 0, y + shelf_h + GAP_Y, 0
        assert w <= W, (key, w, W)
        pr = (lay['primary_tileset'].replace('gTileset_', ''), lay['secondary_tileset'].replace('gTileset_', ''))
        if pr not in pairs:
            pairs.append(pr)
        if pr not in pair_data:
            pair_data[pr] = PairData(root, *pr)
        ex, ey, mapname = _exit_warp(root, lay['id'])
        rooms.append(dict(key=key, x=x, y=y, w=w, h=h, blocks=blocks, pair=pairs.index(pr),
                          pd=pair_data[pr], exit=(ex, ey), map=mapname, loot=spec.get('loot', []),
                          lair=spec.get('lair', False),
                          legend=('SPECIES_' + spec['legend']) if spec.get('legend') else '0'))
        x += w + GAP_X
        shelf_h = max(shelf_h, h)
    total_h = y + shelf_h + 2
    void = world[0]
    grid = list(world) + [void] * (W * (total_h - H))
    terr = bytearray(terrain) + bytearray([SOLID]) * (W * (total_h - H))
    for r in rooms:
        for yy in range(r['h']):
            for xx in range(r['w']):
                e = r['blocks'][yy * r['w'] + xx] & 0x0FFF
                i = (r['y'] + yy) * W + r['x'] + xx
                grid[i] = e
                terr[i] = fm.flags(e, r['pd'].attr(e) & 0xff)

    def solid(gx, gy):
        if not (0 <= gx < W and 0 <= gy < total_h):
            return True
        return bool(terr[gy * W + gx] & SOLID)

    def stand_px(px, py, water_ok=False, rect=None):
        rad = ROOM_R if rect else BODY_R
        for my in range((py - rad) >> 4, ((py + rad) >> 4) + 1):
            for mx in range((px - rad) >> 4, ((px + rad) >> 4) + 1):
                if solid(mx, my):
                    return False
                if rect and not (rect[0] <= mx < rect[0] + rect[2] and rect[1] <= my < rect[1] + rect[3]):
                    return False
        f = terr[(py >> 4) * W + (px >> 4)]
        return water_ok or not (f & DEEP) or bool(f & BRIDGE)

    def near_stand(cx, cy, avoid, min_d, water_ok=False, rect=None, max_r=64):
        best = None
        for r in range(0, max_r, 2):
            for dy in range(-r, r + 1, 2):
                for dx in range(-r, r + 1, 2):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    px, py = cx + dx, cy + dy
                    if abs(px - avoid[0]) + abs(py - avoid[1]) < min_d:
                        continue
                    if stand_px(px, py, water_ok, rect):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]:
                            best = (d, px, py)
            if best:
                return best[1], best[2]
        raise SystemExit(f'no standable spot near {(cx, cy)}')

    room_rows, door_rows, loot_px, man_rooms = [], [], [], {}
    for ri, r in enumerate(rooms):
        rect = (r['x'], r['y'], r['w'], r['h'])
        ex, ey = r['x'] + r['exit'][0], r['y'] + r['exit'][1]
        ecx, ecy = ex * 16 + 8, ey * 16 + 8
        down = r['exit'][1] >= r['h'] - 2
        # Only floor connected to the native exit is floor: Emerald layouts
        # leave unreachable scenery (sky, void, behind-wall art) passable.
        from collections import deque
        seen = {(ex, ey)}
        q = deque([(ex, ey)])
        while q:
            cx_, cy_ = q.popleft()
            for nx, ny in ((cx_ + 1, cy_), (cx_ - 1, cy_), (cx_, cy_ + 1), (cx_, cy_ - 1)):
                if (nx, ny) in seen or not (rect[0] <= nx < rect[0] + rect[2] and rect[1] <= ny < rect[1] + rect[3]):
                    continue
                if terr[ny * W + nx] & SOLID:
                    continue
                seen.add((nx, ny)); q.append((nx, ny))
        pruned = 0
        for yy in range(rect[1], rect[1] + rect[3]):
            for xx in range(rect[0], rect[0] + rect[2]):
                if not (terr[yy * W + xx] & SOLID) and (xx, yy) not in seen:
                    terr[yy * W + xx] |= SOLID
                    pruned += 1
        r['floor'] = len(seen); r['pruned'] = pruned
        # Arrival: legal floor next to the exit, clear of its trigger.
        ax, ay = near_stand(ecx, ecy - (20 if down else 0), (ecx, ecy), 22, rect=rect)
        # Loot: spread over legal floor, far from the exit, deterministic.
        floor = [(xx, yy) for yy in range(r['h']) for xx in range(r['w'])
                 if stand_px((r['x'] + xx) * 16 + 8, (r['y'] + yy) * 16 + 8, rect=rect)]
        floor.sort(key=lambda c: -((c[0] * 16 + 8 + r['x'] * 16 - ecx) ** 2 + (c[1] * 16 + 8 + r['y'] * 16 - ecy) ** 2))
        picked = []
        for (xx, yy) in floor:
            if len(picked) >= len(r['loot']):
                break
            px, py = (r['x'] + xx) * 16 + 8, (r['y'] + yy) * 16 + 8
            if all(abs(px - qx) + abs(py - qy) > 32 for qx, qy in picked):
                picked.append((px, py))
        assert len(picked) == len(r['loot']), (r['key'], 'not enough floor for loot')
        # Boss: legal exit-connected floor beside the farthest cache (never off the floor).
        bx, by = (ax, ay)
        if picked:
            bx, by = near_stand(picked[0][0], picked[0][1] - 24, picked[0], 20, rect=rect)
        # Beta: the boss waits within sight of the arrival (big rooms put the
        # farthest cache 700+ px away, so the legendary never engaged).
        if r['lair'] and abs(bx - ax) + abs(by - ay) > 300:
            cands = []
            for (xx, yy) in floor:
                px, py = (r['x'] + xx) * 16 + 8, (r['y'] + yy) * 16 + 8
                d = abs(px - ax) + abs(py - ay)
                if 150 <= d <= 260:
                    cands.append((d, px, py))
            if cands:
                cands.sort()
                d, cx_, cy_ = cands[-1]
                bx, by = near_stand(cx_, cy_, (ax, ay), 20, rect=rect)
        room_rows.append((r['x'], r['y'], r['w'], r['h'], r['pair'], ex, ey, 1 if down else 0, 1 if r['lair'] else 0, ax, ay, r['legend'], bx, by))
        for (px, py), t in zip(picked, r['loot']):
            loot_px.append(((base[0] * 16) + px, (base[1] * 16) + py, t))
        man_rooms[r['key']] = dict(layout=r['map'], rect=list(rect), pair=list(pairs[r['pair']]),
                                   exit=[ex, ey], exit_faces_down=down, lair=r['lair'], legend=r['legend'], arrival=[ax, ay], boss=[bx, by], loot=r['loot'],
                                   floor_cells=r['floor'], pruned_cells=r['pruned'])
    keys = [r['key'] for r in rooms]
    man_doors = []
    for d in doors:
        dx, dy = d['cell']
        ri = keys.index(d['room'])
        water = d['kind'] == 'water'
        cx, cy = dx * 16 + 8, dy * 16 + 8
        try:
            ox, oy = near_stand(cx, cy + 22, (cx, cy), 20, water_ok=water, max_r=48)
        except SystemExit:
            raise SystemExit(f'door {d} has no legal outside spot')
        door_rows.append((dx, dy, ri, 1 if water else 0, ox, oy))
        man_doors.append(dict(cell=[dx, dy], room=d['room'], kind=d['kind'], outside=[ox, oy]))

    BX, BY = base[0] * 16, base[1] * 16
    BMX, BMY = base
    src = ['// Generated by interiors.py: enterable rooms and their doors.',
           f'#define WL_ROOM_COUNT {len(rooms)}', f'#define WL_DOOR_COUNT {len(door_rows)}',
           f'#define WL_PAIR_COUNT {len(pairs)}']
    for p, s in pairs:
        src.append(f'extern const struct Tileset gTileset_{p};')
        src.append(f'extern const struct Tileset gTileset_{s};')
    src.append('static const struct Tileset *const sWlPairs[WL_PAIR_COUNT][2] = {'
               + ','.join(f'{{&gTileset_{p},&gTileset_{s}}}' for p, s in pairs) + '};')
    src.append('struct WlRoom { u16 x, y, exitX, exitY; u8 w, h, pair, exitDown, lair; s16 arriveX, arriveY; u16 legend; s16 bossX, bossY; };')
    src.append('struct WlDoor { u16 x, y; u8 room, water; s16 outX, outY; };')
    src.append('static const struct WlRoom sWlRooms[WL_ROOM_COUNT] = {' + ','.join(
        f'{{{x + BMX},{y + BMY},{ex + BMX},{ey + BMY},{w},{h},{p},{dn},{lr},{ax + BX},{ay + BY},{lg},{bx + BX},{by + BY}}}'
        for x, y, w, h, p, ex, ey, dn, lr, ax, ay, lg, bx, by in room_rows) + '};')
    src.append('static const struct WlDoor sWlDoors[WL_DOOR_COUNT] = {' + ','.join(
        f'{{{x + BMX},{y + BMY},{ri},{wt},{ox + BX},{oy + BY}}}' for x, y, ri, wt, ox, oy in door_rows) + '};')
    manifest = dict(rooms=man_rooms, doors=man_doors, pairs=[list(p) for p in pairs], total_rows=total_h)
    return grid, bytes(terr), total_h, '\n'.join(src) + '\n', loot_px, manifest
