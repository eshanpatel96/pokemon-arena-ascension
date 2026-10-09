#!/usr/bin/env python3
"""Decode the reviewable V11 source/approved title, apply, and check invariants.
The compressed transport follows this repository's original overlay convention;
the fully decoded Python source is included in each source/build artifact.
These checks are STATIC source checks, never a claim of emulator/Delta passes.
"""
from pathlib import Path
from collections import deque
import base64, hashlib, json, re, struct, subprocess, sys, zlib

root = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent
payload = here / 'v11-payload'
def decode_parts(prefix, count):
    return zlib.decompress(base64.b64decode(''.join((payload / f'{prefix}-{i}.b64').read_text().strip() for i in range(count))))
source = decode_parts('source', 3)
title = decode_parts('title', 6)
assert hashlib.sha256(source).hexdigest() == '6bcddc3c7f0b89a87cd039b293906326cf610713640cd5812246f5c6acfd56e1', 'V11 source transport mismatch'
assert hashlib.sha256(title).hexdigest() == 'd57f1e25f21869c9c2afae78f1e106ebe6ae052dce727e67034644af51425207', 'Approved title transport mismatch'
(here / 'v11-native-build.py').write_bytes(source)
(here / 'v11-title-data.b64').write_text(base64.b64encode(zlib.compress(title, 9)).decode())
protected = ['src/save.c', 'src/load_save.c', 'src/new_game.c', 'src/arena_moves.c', 'src/battle_main.c', 'src/pokemon.c', 'include/global.h', 'include/constants/flags.h', 'include/constants/vars.h', 'v10-2-move-coverage.json']
protected = [p for p in protected if (root / p).exists()]
digests = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in protected}
groups_before = json.loads((root / 'data/maps/map_groups.json').read_text())
layouts_before = json.loads((root / 'data/layouts/layouts.json').read_text())['layouts']
shared = {x['blockdata_filepath']: hashlib.sha256((root / x['blockdata_filepath']).read_bytes()).hexdigest() for x in layouts_before}
subprocess.run([sys.executable, str(here / 'v11-native-build.py'), str(root)], check=True)
for path, expected in digests.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, f'Protected native file changed: {path}'
for path, expected in shared.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, f'Existing shared map changed: {path}'
groups_after = json.loads((root / 'data/maps/map_groups.json').read_text())
for key, value in groups_before.items():
    if isinstance(value, list):
        assert groups_after[key][:len(value)] == value, f'Existing map IDs shifted in {key}'
manifest = json.loads((root / 'v11-room-manifest.json').read_text())
assert len(manifest) == 13
layouts = {x['id']: x for x in json.loads((root / 'data/layouts/layouts.json').read_text())['layouts']}
report = {'classification': 'STATIC SOURCE CHECKS ONLY', 'protected_hashes': digests, 'map_ids_preserved': True, 'save_struct_and_flags_preserved': True, 'rooms': []}
for room in manifest:
    layout = layouts[room['layout']]
    raw = (root / layout['blockdata_filepath']).read_bytes()
    assert len(raw) == 798 and layout['width'] == 19 and layout['height'] == 21
    words = struct.unpack('<399H', raw)
    def walkable(p):
        return 0 <= p[0] < 19 and 0 <= p[1] < 21 and not (words[p[1] * 19 + p[0]] & 0xc00)
    for p in ((9,18),(9,4),(12,18),(9,5),(5,10),(13,10)):
        assert walkable(p), (room['name'], 'blocked critical tile', p)
    seen = {(9,18)}; todo = deque(seen)
    while todo:
        x,y = todo.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            p=x+dx,y+dy
            if walkable(p) and p not in seen and p not in ((9,4),(12,18)):
                seen.add(p); todo.append(p)
    assert (9,5) in seen and (11,18) in seen, (room['name'], 'unreachable boss or exit')
    player = [(9,y) for y in range(5,9)] + [(x,8) for x in range(5,10)] + [(5,y) for y in range(8,11)]
    opponent = [(9,y) for y in range(4,11)] + [(x,10) for x in range(9,14)]
    assert all(walkable(p) for p in player + opponent), (room['name'], 'blocked choreography')
    script = (root / 'data/maps' / room['name'] / 'scripts.inc').read_text()
    assert 'MAP_SCRIPT_ON_FRAME_TABLE' not in script
    assert 'MSGBOX_YESNO' in script and 'Move_PlayerStage' in script and 'Move_BossStage' in script
    assert 'Ascension_RecordVictory' in script and 'Ascension_RecordDefeat' in script
    report['rooms'].append({'map':room['name'], 'reachable_tiles':len(seen), 'raw_bytes':len(raw), 'approach_exit_staging':'pass'})
menu = (root / 'src/main_menu.c').read_text()
rt = (root / 'src/realtime_arena.c').read_text()
assert 'JOY_NEW(SELECT_BUTTON) && RealtimeArena_RequestDemo()' not in menu
assert 'SetMainCallback2(CB2_ContinueSavedGame);' in menu
assert 'gSaveFileStatus != SAVE_STATUS_EMPTY' in rt
assert 'Task_AscensionNewGameDecision' in menu and 'RealtimeArena_RequestConfirmedCareer' in rt
assert 'CB2_NewGame' not in (root / 'src/title_screen.c').read_text()
report['native_menu_paths'] = 'visible NEW GAME, separate CONTINUE, empty guard and confirmed restart present'
report['total_new_raw_map_bytes'] = sum(r['raw_bytes'] for r in report['rooms'])
report['not_verified'] = ['mGBA runtime until separate test execution', 'iPhone Delta', 'entire 63-encounter campaign', 'all legal move behavior coverage', 'full visual acceptance and hazard counterplay', 'user save compatibility without supplied backup']
(root / 'v11-static-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
