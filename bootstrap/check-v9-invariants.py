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
assert "if(part<2)continue;" in career
assert "if(((milestones>>(rank*2))&3)<1+(part-2)/2" in career
assert "Ascension_RememberClearedFloor(rank,floor+1);" in career
assert "#define VAR_ASCENSION_RECRUIT_MILESTONES" in vars_h
assert "switch(sArena.style)" in (root/"src/realtime_arena.c").read_text()
assert "sBronzeSemiFinalTeams[3][4]" in career
assert "VarSet(VAR_ASCENSION_FLOOR,0); // loss resets this run" in career
assert "u8 level=59+rank+floor/2+(isBoss?2:0)" in career
header=(root/"include/ascension_progress.h").read_text()
assert "Ascension_FloorCount" in header
assert "4,5,5,6,6,7,8,9,5" in header
for rank,total in enumerate([4,5,5,6,6,7,8,9],1):
    script=(maps/f"AscensionTower{rank}"/"scripts.inc").read_text()
    assert f"compare VAR_ASCENSION_FLOOR, {total-1}" in script
    assert f"warp MAP_ASCENSION_CITY" in script, f"tower {rank} missing city defeat return"
assert "AscensionV9City_EventScript_SupplySign" in (maps/"AscensionCity/scripts.inc").read_text()
assert "AscensionV9City_EventScript_MoveSign" in (maps/"AscensionCity/scripts.inc").read_text()
import struct
city_layout=(root/"data/layouts/AscensionCity/map.bin").read_bytes()
assert len(city_layout)==56*72*2
city_metatiles=struct.unpack("<"+str(56*72)+"H",city_layout)
assert city_metatiles[51*56+52]&1023!=0x42
assert city_metatiles[51*56+53]&1023!=0x43
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


# Native exterior identity and door-route regression checks; static, not Delta.
from collections import deque
import struct
def facade(area,side,w,h,x,y,palette):
    v=struct.unpack("<"+str(w*h)+"H",(root/f"data/layouts/{area}/map.bin").read_bytes())
    m=v[y*w+x]&1023
    bank=root/"data/tilesets"
    path=(bank/"primary/general/metatiles.bin" if m<512
          else bank/f"secondary/battle_frontier_outside_{side}/metatiles.bin")
    tiles=struct.unpack_from("<8H",path.read_bytes(),(m if m<512 else m-512)*16)
    assert sum(q>>12==palette for q in tiles)>=2,(area,x,y,palette)
facade("AscensionCity","west",56,72,5,18,6)
facade("AscensionCity","west",56,72,11,33,8)
facade("AscensionCityEast","east",72,72,45,50,5)
facade("AscensionCityEast","east",72,72,39,24,12)
for area,w,h,start in (("AscensionCity",56,72,(40,45)),
                       ("AscensionCityEast",72,72,(0,5))):
    v=struct.unpack("<"+str(w*h)+"H",(root/f"data/layouts/{area}/map.bin").read_bytes())
    def walk(x,y): return 0<=x<w and 0<=y<h and ((v[y*w+x]>>10)&3)==0
    seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for X,Y in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if walk(X,Y) and (X,Y) not in seen:
                seen.add((X,Y));queue.append((X,Y))
    for warp in json.loads((maps/area/"map.json").read_text())["warp_events"]:
        assert (warp["x"],warp["y"]+1) in seen, (area,warp["dest_map"],"unreachable")

for script in maps.glob("Ascension*/scripts.inc"):
    assert r"\\n" not in script.read_text(), f"{script}: double-escaped dialogue"

print("V9 STATIC PREFLIGHT PASSED: 187 unique animation allocation; 4/5/5/6/6/7/8/9 native trainer floors, career/boss routes, Bronze semifinals, gated species, 1,000 loss cap, real middle-campus metatiles and eight contrasting stage settings.")
print("NOT VERIFIED HERE: emulator boot, real-time faint/send-out, Bag/switch, hazards on screen, new city architecture, saving/reloading, frame rate or Delta playthrough.")
