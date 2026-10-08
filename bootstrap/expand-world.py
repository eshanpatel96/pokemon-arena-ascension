#!/usr/bin/env python3
"""V7: two connected native city districts and 8 distinct tower lobbies + Summit.

Never changes original Emerald Arena rendering, art, or battle rules.
Requires V6.2 source and dialogue repair before running.
"""
import json
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
maps = root / "data/maps"
layouts = root / "data/layouts"
names = [
    ("Bronze Trials", "MUS_B_TOWER", "OBJ_EVENT_GFX_EXPERT_M",
     "Learn the dodge timing.\nEvery move has an opening.",
     "Boss tip: move away from\nheavy attacks."),
    ("Gale Tower", "MUS_B_ARENA", "OBJ_EVENT_GFX_HIKER",
     "Fast foes change direction.\nWatch their feet.",
     "Boss tip: dodge sideways,\nthen counterattack."),
    ("Verdant Crown", "MUS_B_FRONTIER", "OBJ_EVENT_GFX_BUG_CATCHER",
     "A quick grass attacker can\nclose the gap suddenly.",
     "Boss tip: keep a strong\nanswer to Grass moves."),
    ("Phantom Spire", "MUS_B_PALACE", "OBJ_EVENT_GFX_PSYCHIC_M",
     "Patience beats a ghost.\nAvoid chasing blindly.",
     "Boss tip: save fast moves\nto interrupt attacks."),
    ("Inferno Forge", "MUS_B_PYRAMID", "OBJ_EVENT_GFX_BLACK_BELT",
     "Heavy attacks are risky.\nLearn when to commit.",
     "Boss tip: dodge after\nlanding a strong blow."),
    ("Tidal Bastion", "MUS_B_PIKE", "OBJ_EVENT_GFX_BEAUTY",
     "Your team needs stamina.\nUse a healthy reserve.",
     "Boss tip: switch before\nyour strongest faints."),
    ("Thunder Citadel", "MUS_B_FACTORY", "OBJ_EVENT_GFX_GENTLEMAN",
     "Quick foes can punish a\nslow recovery.",
     "Boss tip: save an attack\nto counter their charge."),
    ("Astral Apex", "MUS_B_DOME", "OBJ_EVENT_GFX_PSYCHIC_M",
     "Every decision matters.\nRead the battle tempo.",
     "Boss tip: use the arena\nedges to your advantage."),
    ("Champion Summit", "MUS_B_TOWER", "OBJ_EVENT_GFX_GENTLEMAN",
     "You stand before the best.\nShow what you have learned.",
     "Boss tip: conserve HP.\nThere are no easy fights.")
]

def dump(p, value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2)+"\n")

def text(label, words):
    words=words.replace("\n", "\\n")
    return label+':\n\t.string "'+words+'$"\n'

def actor(gfx,x,y,script, elevation=3):
    return dict(graphics_id=gfx,x=x,y=y,elevation=elevation,
                movement_type="MOVEMENT_TYPE_FACE_DOWN",
                movement_range_x=0,movement_range_y=0,
                trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
                script=script,flag="0")

west_p=maps/"AscensionCity/map.json"
west=json.loads(west_p.read_text())
assert len(west["warp_events"])==8
assert west["connections"] is None
west["connections"]=[dict(map="MAP_ASCENSION_CITY_EAST",offset=0,direction="right")]

east=json.loads((maps/"BattleFrontier_OutsideEast/map.json").read_text())
east.update(id="MAP_ASCENSION_CITY_EAST",name="AscensionCityEast",layout="LAYOUT_ASCENSION_CITY_EAST")
east["connections"]=[dict(map="MAP_ASCENSION_CITY",offset=0,direction="left")]
east["object_events"]=[
    actor("OBJ_EVENT_GFX_WOMAN_5",12,26,"AscensionEast_EventScript_Moves",0),
    actor("OBJ_EVENT_GFX_EXPERT_M",35,32,"AscensionEast_EventScript_Tower",0),
    actor("OBJ_EVENT_GFX_GENTLEMAN",24,42,"AscensionEast_EventScript_Roster",0),
    actor("OBJ_EVENT_GFX_NURSE",8,48,"AscensionEast_EventScript_Heal",0)
]
# Do not lead into unrelated original Emerald Frontier interiors.
east["warp_events"]=[dict(x=35,y=12,elevation=0,dest_map="MAP_ASCENSION_SUMMIT",dest_warp_id="0")]
east["coord_events"]=[]
east["bg_events"]=[]
dump(maps/"AscensionCityEast/map.json",east)
east_scripts="""AscensionCityEast_MapScripts::
 .byte 0
AscensionEast_EventScript_Moves::
 msgbox AscensionEast_Text_Moves, MSGBOX_NPC
 end
AscensionEast_EventScript_Tower::
 msgbox AscensionEast_Text_Tower, MSGBOX_NPC
 end
AscensionEast_EventScript_Roster::
 msgbox AscensionEast_Text_Roster, MSGBOX_NPC
 end
AscensionEast_EventScript_Heal::
 lock
 faceplayer
 msgbox AscensionEast_Text_Heal, MSGBOX_DEFAULT
 special HealPlayerParty
 release
 end
"""
for label,words in [
    ("Moves","MOVE STUDIO: many more\nskills are on the way."),
    ("Tower","The Champion Summit stands\nin the eastern district."),
    ("Roster","POKEMON LAB: every good\nteam needs a strategy."),
    ("Heal","Your team is restored.\nGood luck out there!")]:
    east_scripts+=text("AscensionEast_Text_"+label,words)
(maps/"AscensionCityEast/scripts.inc").write_text(east_scripts)

config=json.loads((layouts/"layouts.json").read_text())
old=next(l for l in config["layouts"] if l["id"]=="LAYOUT_BATTLE_FRONTIER_OUTSIDE_EAST")
copy=dict(old,id="LAYOUT_ASCENSION_CITY_EAST",name="AscensionCityEast_Layout",
          border_filepath="data/layouts/AscensionCityEast/border.bin",
          blockdata_filepath="data/layouts/AscensionCityEast/map.bin")
assert copy["id"] not in [l["id"] for l in config["layouts"]]
config["layouts"].append(copy)
shutil.copytree(layouts/"BattleFrontier_OutsideEast",layouts/"AscensionCityEast",dirs_exist_ok=True)
dump(layouts/"layouts.json",config)

room_template=json.loads((maps/"AscensionTowerHall/map.json").read_text())
new_maps=["AscensionCityEast"]
for index,(title,music,gfx,tip,boss_tip) in enumerate(names):
    summit=index==8
    suffix="Summit" if summit else "Tower"+str(index+1)
    name="Ascension"+suffix
    map_id="MAP_ASCENSION_SUMMIT" if summit else "MAP_ASCENSION_TOWER_"+str(index+1)
    city="MAP_ASCENSION_CITY_EAST" if summit else "MAP_ASCENSION_CITY"
    door=0 if summit else index
    room=json.loads(json.dumps(room_template))
    room.update(id=map_id,name=name,music=music)
    room["object_events"]=[
        actor(gfx,12,5,name+"_EventScript_Master"),
        actor("OBJ_EVENT_GFX_GENTLEMAN",18,5,name+"_EventScript_Advice")
    ]
    room["warp_events"]=[
      dict(x=x,y=9,elevation=3,dest_map=city,dest_warp_id=str(door))
      for x in (12,13)
    ]
    room["bg_events"]=[]
    dump(maps/name/"map.json",room)
    scr=f"""{name}_MapScripts::
 .byte 0
{name}_EventScript_Master::
 lock
 faceplayer
 msgbox {name}_Text_Intro, MSGBOX_DEFAULT
 setvar VAR_0x8004, {index}
 special Ascension_CanChallengeTower
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Locked
 release
 goto AscensionTowerHall_EventScript_Challenge
{name}_EventScript_Locked::
 msgbox {name}_Text_Locked, MSGBOX_DEFAULT
 release
 end
{name}_EventScript_Advice::
 msgbox {name}_Text_Tip, MSGBOX_NPC
 end
"""
    scr+=text(name+"_Text_Intro",title.upper()+" awaits!\n"+tip)
    scr+=text(name+"_Text_Locked","This tier is locked.\nClear the earlier towers.")
    scr+=text(name+"_Text_Tip",boss_tip)
    (maps/name/"scripts.inc").write_text(scr)
    if not summit:
        west["warp_events"][index]["dest_map"]=map_id
        west["warp_events"][index]["dest_warp_id"]="0"
    new_maps.append(name)
dump(west_p,west)

group_p=maps/"map_groups.json"
groups=json.loads(group_p.read_text())
group=next(k for k,v in groups.items() if "AscensionCity" in v)
assert all(name not in groups[group] for name in new_maps)
groups[group].extend(new_maps)
dump(group_p,groups)

events=root/"data/event_scripts.s"
s=events.read_text()
marker='\t.include "data/maps/AscensionTowerHall/scripts.inc"'
assert s.count(marker)==1
events.write_text(s.replace(marker,marker+"\n"+"\n".join(
   '\t.include "data/maps/'+m+'/scripts.inc"' for m in new_maps)))

special=root/"data/specials.inc"
s=special.read_text()
marker="\tdef_special Ascension_GetProgress"
assert s.count(marker)==1
special.write_text(s.replace(marker,"\tdef_special Ascension_CanChallengeTower\n"+marker))

career=root/"src/ascension_career.c"
s=career.read_text()
s+="""

// Only the tower matching your saved rank can launch a ranking fight.
void Ascension_CanChallengeTower(void)
{
    gSpecialVar_Result = (VarGet(VAR_ASCENSION_RANK) == gSpecialVar_0x8004);
}
"""
# The practice dojo now chooses a different Arena-supported opponent each run.
# Four curated moves reduce the old turn-based fallback on exhausted/unsupported attacks.
assert '#include "random.h"' not in s
s=s.replace('#include "pokemon.h"', '#include "pokemon.h"\n#include "random.h"')
fixed="""    CreateScriptedWildMon(SPECIES_SCIZOR, 52, ITEM_NONE);
    SetMonMoveSlot(&gEnemyParty[0], MOVE_QUICK_ATTACK, 0);
    SetMonMoveSlot(&gEnemyParty[0], MOVE_SLASH, 1);
    SetMonMoveSlot(&gEnemyParty[0], MOVE_NONE, 2);
    SetMonMoveSlot(&gEnemyParty[0], MOVE_NONE, 3);"""
rotating="""    {
        static const struct {
            u16 species;
            u16 moves[4];
        } practice[6] = {
            {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
            {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_EMBER, MOVE_SLASH, MOVE_PROTECT}},
            {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
            {SPECIES_BLASTOISE, {MOVE_WATER_GUN, MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_PROTECT}},
            {SPECIES_DRAGONITE, {MOVE_WING_ATTACK, MOVE_SLAM, MOVE_DRAGON_BREATH, MOVE_AGILITY}},
            {SPECIES_CHARIZARD, {MOVE_FLAMETHROWER, MOVE_WING_ATTACK, MOVE_SLASH, MOVE_PROTECT}}
        };
        u16 pick = Random() % 6;
        u8 slot;
        CreateScriptedWildMon(practice[pick].species, 54, ITEM_NONE);
        for (slot = 0; slot < 4; slot++)
            SetMonMoveSlot(&gEnemyParty[0], practice[pick].moves[slot], slot);
    }"""
assert s.count(fixed)==1
s=s.replace(fixed,rotating)
career.write_text(s)

# Gameplay invariant checks: unique entries and return destinations.
assert len({w["dest_map"] for w in west["warp_events"]})==8
for i in range(8):
    tower=json.loads((maps/("AscensionTower"+str(i+1))/"map.json").read_text())
    assert all(w["dest_warp_id"]==str(i) for w in tower["warp_events"])
    assert all(w["dest_map"]=="MAP_ASCENSION_CITY" for w in tower["warp_events"])
for m in new_maps:
    src=(maps/m/"scripts.inc").read_text()
    assert all(not (".string" in line and not line.lstrip().startswith(".string"))
               for line in src.splitlines())
print("V7 world: western/eastern city link, eight individual tower rooms, Summit, correct exits and ranked gates.")
