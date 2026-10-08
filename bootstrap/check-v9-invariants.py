#!/usr/bin/env python3
"""Build-time V9 static invariants (NOT gameplay/emulator tests).

We reject accidental early legendary unlocks, duplicate starter claims,
mismatched reward allocations, identical trial/boss backdrops, and duplicate
defeat penalties before producing a candidate .gba.
"""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
maps = root / "data/maps"
career = (root / "src/ascension_career.c").read_text()
vars_h = (root / "include/constants/vars.h").read_text()
biomes = (root / "src/arena_biomes.inc").read_text()
rom_roster = json.loads((root / "tools/arena/roster.json").read_text())
animated = {entry["species"] for entry in rom_roster}
assert len(animated) == len(rom_roster) == 187, "original animated roster changed"

def section(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]

starters = re.findall(r"\{SPECIES_([A-Z0-9_]+), \d+\}",
                     section(career, "sAscensionStarterPool[]", "sAscensionStarterMoves"))
prizes = re.findall(r"SPECIES_([A-Z0-9_]+)",
                    section(career, "sTowerPrizes[ASCENSION_TOWER_COUNT][8]", "sTowerRewardMoveProfiles"))

assert len(starters) == len(set(starters)) == 80, "starter catalog contains duplicates"
assert len(prizes) == len(set(prizes)) == 64, "tower reward species duplicated"
assert not set(starters) & set(prizes), "starter unlocked as tower reward"
assert (set(starters) | set(prizes)) <= animated, "species without original animation"
assert len(animated - set(starters) - set(prizes)) == 43, "V10-only roster allocation changed"

signature_pairs = [
    ("REGIROCK", "AGGRON"), ("LUGIA", "DRAGONITE"),
    ("SUICUNE", "SCEPTILE"), ("MEWTWO", "GENGAR"),
    ("ENTEI", "BLAZIKEN"), ("KYOGRE", "SWAMPERT"),
    ("ZAPDOS", "METAGROSS"), ("RAYQUAZA", "SALAMENCE"),
]
assert [tuple(prizes[i*8:i*8+2]) for i in range(8)] == signature_pairs

assert "for(i=VarGet(VAR_ASCENSION_STARTER_NEXT_INDEX);" in career
assert "VarSet(VAR_ASCENSION_STARTER_NEXT_INDEX,i+1);" in career
assert "#define VAR_ASCENSION_STARTER_NEXT_INDEX" in vars_h
assert "if(part<2 || part>=6)continue;" in career
assert "if(part<4 && floor<1)continue;" in career
assert "if(part>=4 && floor<2)continue;" in career
assert "if(penalty>1000)penalty=1000;" in career

def stage(map_label):
    pat = re.compile(r"case "+re.escape(map_label)+r":\s*gArenaBiome=(\d+);gArenaStage=(\d+);break;")
    result = pat.findall(biomes)
    assert len(result) == 1, (map_label, result)
    return tuple(map(int,result[0]))

for rank in range(1,9):
    trial = stage(f"MAP_ASCENSION_TOWER_{rank}")
    boss = stage("MAP_ASCENSION_BRONZE_BOSS" if rank == 1 else f"MAP_ASCENSION_LEADER_{rank}")
    assert trial != boss, f"tower {rank} identical native battle backdrops: {trial}"

assert "MAP_ASCENSION_LEADER_6" in (root/"src/realtime_arena.c").read_text()
assert "MAP_ASCENSION_LEADER_7" in (root/"src/realtime_arena.c").read_text()

for rank in range(1,9):
    tower = f"AscensionTower{rank}"
    boss = "AscensionBronzeBoss" if rank==1 else f"AscensionLeader{rank}"
    a = json.loads((maps / tower / "map.json").read_text())
    b = json.loads((maps / boss / "map.json").read_text())
    assert a["warp_events"], f"tower {rank} has no safe return door"
    assert b["layout"], f"boss {rank} lacks a layout"
    script = (maps/tower/"scripts.inc").read_text()
    # Exactly one loss fine per tower challenger; separate boss fine below.
    assert script.count("special Ascension_RecordDefeat") == 1, f"tower {rank}: duplicate/missing loss fine"
    boss_script = (maps/boss/"scripts.inc").read_text()
    assert boss_script.count("special Ascension_RecordDefeat") == 1, f"boss {rank}: duplicate/missing fine"

for area in ("AscensionCity", "AscensionCityEast"):
    info = json.loads((maps/area/"map.json").read_text())
    assert len(info["object_events"]) <= 16, f"{area}: exceeds engine local object budget"
    for ev in info["warp_events"]:
        assert ev["dest_map"].startswith("MAP_ASCENSION_"), f"{area}: unrelated destination"

for script in maps.glob("Ascension*/scripts.inc"):
    assert r"\\n" not in script.read_text(), f"{script}: double-escaped dialogue"

print("V9 STATIC PREFLIGHT PASSED: 187 original animations; 80 starters, 64 uniquely gated tower rewards, 43 deferred, eight contrasting native trial/boss stages, bounded money penalty and unique defeat scripts.")
print("NOT VERIFIED HERE: emulator boot, real-time faint/send-out, Bag/switch, hazards on screen, new city architecture, saving/reloading, frame rate or Delta playthrough.")
