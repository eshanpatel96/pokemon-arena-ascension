#!/usr/bin/env python3
"""Apply Pokemon Wildlands V1 vertical-slice changes to the pinned V11.1 assembled source."""
from pathlib import Path
import json, sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent

def once(path, old, new):
    p = root / path
    s = p.read_text()
    if s.count(old) != 1:
        raise SystemExit(f"source drift in {path}: expected exactly one occurrence of {old[:80]!r}, got {s.count(old)}")
    p.write_text(s.replace(old, new, 1))

# Dedicated field-combat module.
(root / 'include/wildlands_v1.h').write_bytes((here / 'wildlands_v1.h').read_bytes())
(root / 'src/wildlands_v1.c').write_bytes((here / 'wildlands_v1.c').read_bytes())

# Tick Wildlands after the native overworld frame. Ascension practice stays present
# in the inherited engine but is never enabled by the Wildlands NEW GAME preset.
p = root / 'src/overworld.c'
s = p.read_text()
marker = '#include "realtime_arena.h"'
if '#include "wildlands_v1.h"' not in s:
    if s.count(marker) != 1:
        raise SystemExit('overworld include anchor drift')
    s = s.replace(marker, marker + '\n#include "wildlands_v1.h"', 1)
old = '    RealtimeArena_PracticeTick();\n#if ARENA_LAB'
new = '    RealtimeArena_PracticeTick();\n    WildlandsV1_Tick();\n#if ARENA_LAB'
if s.count(old) != 1:
    raise SystemExit('overworld tick anchor drift')
p.write_text(s.replace(old, new, 1))

# Grass is concealment, never an encounter transition.
p = root / 'src/wild_encounter.c'
s = p.read_text()
if '#include "wildlands_v1.h"' not in s:
    lines = s.splitlines()
    lines.insert(1, '#include "wildlands_v1.h"')
    s = '\n'.join(lines) + '\n'
old_a = 'bool8 StandardWildEncounter(u16 currMetaTileBehavior, u16 previousMetaTileBehavior)\n{'
old_b = 'bool8 StandardWildEncounter(u16 curMetatileBehavior, u16 prevMetatileBehavior)\n{'
old = old_a if old_a in s else old_b
if old not in s:
    raise SystemExit('wild encounter function anchor drift')
decls = old + '\n    u16 headerId;\n    struct Roamer *roamer;\n'
if decls not in s:
    raise SystemExit('wild encounter declaration anchor drift')
s = s.replace(decls, decls + '\n    if (WildlandsV1_IsActive())\n        return FALSE;', 1)
p.write_text(s)

# Use the already save-safe NEW GAME hook from Ascension, but seed a Wildlands
# two-Pokemon squad on Route 119 instead of activating the Ascension career.
p = root / 'src/realtime_arena.c'
s = p.read_text()
old = '''    SetWarpDestination(MAP_GROUP(MAP_ASCENSION_CITY), MAP_NUM(MAP_ASCENSION_CITY),
                       WARP_ID_NONE, 26, 40);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ASCENSION_CITY);
    VarSet(VAR_ASCENSION_CAREER_ACTIVE, 1);'''
new = '''    SetWarpDestination(MAP_GROUP(MAP_ROUTE119), MAP_NUM(MAP_ROUTE119),
                       WARP_ID_NONE, 19, 133);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_OLDALE_TOWN);
    VarSet(VAR_ASCENSION_CAREER_ACTIVE, 0);
    FlagSet(FLAG_HIDE_ROUTE_119_RIVAL);
    FlagSet(FLAG_HIDE_ROUTE_119_RIVAL_ON_BIKE);
    FlagSet(FLAG_HIDE_ROUTE_119_SCOTT);'''
if s.count(old) != 1:
    raise SystemExit('new game warp anchor drift')
s = s.replace(old, new, 1)
start_anchor = '''#else
    // A native NEW GAME preset, never an imported save or a fixture mailbox.'''
end_anchor = '''#endif
    return TRUE;'''
start = s.find(start_anchor)
end = s.find(end_anchor, start)
if start < 0 or end < 0:
    raise SystemExit('new game party block anchor drift')
new_party = '''#else
    // Pokemon Wildlands V1: fixed two-Pokemon vertical-slice squad.
    // Selection UI comes after the continuous field-combat feel test.
    gPlayerPartyCount = 2;
    CreateMon(&gPlayerParty[0], SPECIES_CHARIZARD, 60, 20, TRUE, 0, OT_ID_PLAYER_ID, 0);
    SetMonMoveSlot(&gPlayerParty[0], MOVE_FLAMETHROWER, 0);
    SetMonMoveSlot(&gPlayerParty[0], MOVE_SLASH, 1);
    SetMonMoveSlot(&gPlayerParty[0], MOVE_WING_ATTACK, 2);
    SetMonMoveSlot(&gPlayerParty[0], MOVE_DIG, 3);
    CreateMon(&gPlayerParty[1], SPECIES_BLASTOISE, 60, 20, TRUE, 2, OT_ID_PLAYER_ID, 0);
    SetMonMoveSlot(&gPlayerParty[1], MOVE_WATER_GUN, 0);
    SetMonMoveSlot(&gPlayerParty[1], MOVE_BITE, 1);
    SetMonMoveSlot(&gPlayerParty[1], MOVE_HYDRO_PUMP, 2);
    SetMonMoveSlot(&gPlayerParty[1], MOVE_SURF, 3);
'''
s = s[:start] + new_party + s[end:]
p.write_text(s)

# Route 119 is the V1 Wildlands island slice. Keep the actual Emerald layout,
# grass/water/bridges and terrain; remove story/NPC/warp interactions.
p = root / 'data/maps/Route119/map.json'
m = json.loads(p.read_text())
# Three hidden object stubs retain assembler-local IDs referenced by dormant
# vanilla Route 119 scripts. Their hide flags are forced at Wildlands startup,
# so no trainer/NPC is rendered while the old script_data still links safely.
m['object_events'] = [
    e for e in m['object_events']
    if e.get('local_id') in (
        'LOCALID_ROUTE119_RIVAL',
        'LOCALID_ROUTE119_RIVAL_ON_BIKE',
        'LOCALID_ROUTE119_SCOTT',
    )
]
m['warp_events'] = []
m['coord_events'] = []
m['bg_events'] = []
m['connections'] = None
p.write_text(json.dumps(m, indent=2) + '\n')

report = {
    'name': 'Pokemon Wildlands V1',
    'scope': 'continuous-overworld vertical slice',
    'map': 'Route 119 Emerald layout, story/NPC events stripped',
    'player': 'Charizard fixed test loadout',
    'partner': 'Blastoise AI partner with Surf traversal',
    'enemy_teams': 2,
    'legendary_boss': 'Rayquaza; defeat then recruit to replace partner',
    'field_systems': ['A attack', 'L/R move cycle', 'B+dpad dodge immunity', 'grass concealment', 'loot', 'Surf mount', 'Dig shortcut'],
    'not_yet_v1': ['30-team remote simulation', 'selection UI', 'five legendary lairs', 'closing field', 'full island sectors', 'building interiors', 'final balancing'],
}
(root / 'wildlands-v1-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
