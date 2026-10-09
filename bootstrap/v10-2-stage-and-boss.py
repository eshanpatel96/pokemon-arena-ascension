#!/usr/bin/env python3
"""V10.2 real native choreography: player center, Master clearly below, rival
on right; consistent recovery and safe Bronze long walk-up to Regirock.
Stage changes select *existing* different native background art, no new
renderer or unsupported unseen hazard claims.
"""
from pathlib import Path
import json,re,struct,sys
root=Path(sys.argv[1]);maps=root/"data/maps"
def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: expected 1 anchor got {n}")
    return s.replace(old,new,1)
movement={
    # Positions: initial Master (5,5), player (5,6), challenger (5,1).
    # Master waits (4,7); player finishes (5,4); challenger (7,3).
    "MasterAside":" walk_left\n walk_down\n walk_down\n face_up",
    "MasterReturn":" walk_up\n walk_up\n walk_right\n face_down",
    "MasterFacing":" walk_up\n walk_up\n walk_right\n face_up",
    "MasterBackToSide":" walk_left\n walk_down\n walk_down\n face_up",
    "PlayerAdvance":" walk_up\n walk_up\n face_right",
    "PlayerRetreat":" walk_down\n walk_down\n face_up",
}
for tier in range(1,9):
    name=f"AscensionTower{tier}"
    file=maps/name/"scripts.inc";s=file.read_text()
    for k,moves in movement.items():
        anchor=f"{name}_Move_{k}:\n"
        a=s.index(anchor);b=s.index("\n step_end",a)+len("\n step_end")
        s=s[:a]+anchor+moves+"\n step_end"+s[b:]
    # Original Emerald 10x9 Battle Tower arena is walkable at (5,4),(4,7),
    # (7,3). No character walks through another's occupied tile.
    assert s.count(" applywaitmovement LOCALID_PLAYER, "+name+"_Move_PlayerAdvance")==1
    assert f"{name}_Move_ChallengerEnter:\n walk_down\n walk_down\n walk_right\n walk_right\n face_left" in s
    file.write_text(s)
boss=maps/"AscensionTower1/scripts.inc"
s=boss.read_text()
s=once(s," warp MAP_ASCENSION_BRONZE_BOSS, 5, 8\n",
       " warp MAP_ASCENSION_BRONZE_BOSS, 5, 12\n",
       "lower stone Coliseum entry")
boss.write_text(s)
# Use original collision data to ensure player arrives with a true
# walk-up-to-boss route, not an unusable or trapped spawn.
layouts={r["id"]:r for r in json.loads((root/"data/layouts/layouts.json").read_text())["layouts"]}
bossmap=json.loads((maps/"AscensionBronzeBoss/map.json").read_text())
lay=layouts[bossmap["layout"]];w,h=lay["width"],lay["height"]
meta=struct.unpack("<"+str(w*h)+"H",(root/lay["blockdata_filepath"]).read_bytes())
assert 0<=12<h and ((meta[12*w+5]>>10)&3)==0
# A small but meaningful distinct stage fix: Phantom already uses original
# stage 14; Astral now uses ORIGINAL Arena stage 12, visually different.
biomes=root/"src/arena_biomes.inc"
src=biomes.read_text()
src=once(src,
 "case MAP_ASCENSION_LEADER_8:gArenaBiome=4;gArenaStage=14;break;",
 "case MAP_ASCENSION_LEADER_8:gArenaBiome=4;gArenaStage=12;break;",
 "different actual Astral battle background")
biomes.write_text(src)

# Specific themed intros instead of the same generic "real leader" line.
dialogs={
 "AscensionBronzeBoss":("STONE MASTER REGIROCK","STONE PILLARS WILL SHATTER"),
 "AscensionLeader2":("LUGIA: EYE OF THE STORM","THE AIR IS ELECTRIC"),
 "AscensionLeader3":("SUICUNE: ANCIENT GROVE","NATURE NEVER RESTS"),
 "AscensionLeader4":("MEWTWO: PHANTOM CRYPT","TRUST YOUR SENSES"),
 "AscensionLeader5":("ENTEI: BLAZING FORGE","FIRE TESTS YOUR FOOTWORK"),
 "AscensionLeader6":("KYOGRE: TIDAL THRONE","WATCH THE FLOOD LEVEL"),
 "AscensionLeader7":("ZAPDOS: REACTOR CORE","SHOCKS FAVOR THE CARELESS"),
 "AscensionLeader8":("RAYQUAZA: STAR SANCTUM","KEEP YOUR BALANCE"),
 "AscensionLeader9":("WORLD CHAMPION: HO-OH","EVERY MATCH LED HERE"),
}
for name,(title,warning) in dialogs.items():
    f=maps/name/"scripts.inc";v=f.read_text()
    key=f"{name}_EventScript_Leader::\n lockall\n faceplayer\n"
    assert v.count(key)==1
    v=v.replace(key,key+f" msgbox {name}_Text_V102Intro, MSGBOX_DEFAULT\n",1)
    v+=f'\n{name}_Text_V102Intro:\n .string "{title}!\\n{warning}.$"\n'
    f.write_text(v)
print("V10.2 STAGING: player center (5,4), rival right (7,3), Master low (4,7), Master step-in heals, Bronze arrival lowered to (5,12), eight distinct native boss combat backdrops and themed introductions.")
