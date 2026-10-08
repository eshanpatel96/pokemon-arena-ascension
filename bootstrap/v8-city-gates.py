#!/usr/bin/env python3
"""V8: redistribute themed towers around both real Frontier districts; central shops.

Stages a separate walk-through arena gate for each tower. The battle inside
still uses the previous single-opponent challenge while genuine trainer-party
combat is developed and emulator-tested. No replacement renderer.
"""
import json
import sys
from pathlib import Path

root=Path(sys.argv[1])
maps=root/"data/maps"
events=root/"data/event_scripts.s"
groups_p=maps/"map_groups.json"

def read(p): return json.loads(p.read_text())
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2)+"\n")
def message(label,msg):
    return label+':\n\t.string "'+msg.replace("\n",r"\n")+'$"\n'
def actor(gfx,x,y,script,elevation=3):
    return dict(graphics_id=gfx,x=x,y=y,elevation=elevation,
                movement_type="MOVEMENT_TYPE_FACE_DOWN",
                movement_range_x=0,movement_range_y=0,
                trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
                script=script,flag="0")
def warp(x,y,map_id,warp_id):
    return dict(x=x,y=y,elevation=0,dest_map=map_id,dest_warp_id=str(warp_id))
def sign(x,y,script):
    return dict(type="sign",x=x,y=y,elevation=0,
                player_facing_dir="BG_EVENT_PLAYER_FACING_ANY",script=script)
def add_map(name,original,building_door):
    d=read(maps/(original+"/map.json"))
    d["id"]="MAP_"+name.upper().replace("ASCENSION","ASCENSION_") if False else {
       "AscensionTeamLab":"MAP_ASCENSION_TEAM_LAB",
       "AscensionItemShop":"MAP_ASCENSION_ITEM_SHOP",
       "AscensionMoveStudio":"MAP_ASCENSION_MOVE_STUDIO",
       "AscensionStyleHouse":"MAP_ASCENSION_STYLE_HOUSE"}[name]
    d["name"]=name
    d["warp_events"]=[warp(w["x"],w["y"],"MAP_ASCENSION_CITY",building_door)
                       for w in d["warp_events"] if w["dest_map"]=="MAP_BATTLE_FRONTIER_OUTSIDE_WEST"]
    if not d["warp_events"]: raise ValueError(name+" no usable return doors")
    d["coord_events"]=[]
    d["bg_events"]=[]
    d["connections"]=None
    d["object_events"]=[]
    return d

west_p=maps/"AscensionCity/map.json"
west=read(west_p)
east_p=maps/"AscensionCityEast/map.json"
east=read(east_p)
assert len(west["warp_events"])==8
assert len(east["warp_events"])==1 and east["warp_events"][0]["dest_map"]=="MAP_ASCENSION_SUMMIT"

# Four famous outer western buildings remain towers. Former central lounges
# become real service buildings. Avoid routing users into vanilla Frontier houses.
west_map={0:0,1:1,2:2,7:3}
for ext,tier in west_map.items():
    west["warp_events"][ext]["dest_map"]="MAP_ASCENSION_TOWER_"+str(tier+1)
    west["warp_events"][ext]["dest_warp_id"]="0"
for ext,newid in [(3,"MAP_ASCENSION_TEAM_LAB"),(4,"MAP_ASCENSION_ITEM_SHOP"),
                   (5,"MAP_ASCENSION_STYLE_HOUSE"),(6,"MAP_ASCENSION_MOVE_STUDIO")]:
    west["warp_events"][ext]["dest_map"]=newid
    west["warp_events"][ext]["dest_warp_id"]="0"

# Four peripheral eastern Battle Frontier buildings get Fire/Water/Thunder/
# Astral. The north-central ranking hall becomes the Champion Summit.
# Exact positions refer to *existing* Emerald building doorway tiles.
east["warp_events"]=[
    warp(35,12,"MAP_ASCENSION_SUMMIT",0),
    warp(58,14,"MAP_ASCENSION_TOWER_5",0),
    warp(45,56,"MAP_ASCENSION_TOWER_6",0),
    warp(39,29,"MAP_ASCENSION_TOWER_7",0),
    warp(16,14,"MAP_ASCENSION_TOWER_8",0),
]
# Use the ORIGINAL tile-backed Frontier sign locations, with actual interactable
# event scripts. They're not fake floating icons in the middle of the street.
west_signs=[
    (45,30,"BRONZE TRIALS - TOWER 1\nFirst Arena, EAST side."),
    (15,18,"GALE TOWER - TOWER 2\nFind the NORTHWEST dome."),
    (16,43,"VERDANT CROWN - TOWER 3\nFind the SOUTHWEST hall."),
    (52,51,"ITEM SHOP\nUse the middle district MART."),
    (53,51,"ASCENSION CITY\nSTART > ARENA GUIDE."),
]
east_signs=[
    (13,17,"ASTRAL APEX - TOWER 8\nNORTHWEST tower."),
    (43,56,"TIDAL BASTION - TOWER 6\nSOUTH palace."),
    (36,34,"THUNDER CITADEL - TOWER 7\nCENTRAL arena."),
    (62,15,"INFERNO FORGE - TOWER 5\nNORTHEAST pyramid."),
    (32,13,"CHAMPION SUMMIT\nNORTH central great hall."),
    (7,29,"WELCOME TO EAST CITY\nTowers 5 through 8."),
]
ws=west["bg_events"]
ws[:]=[sign(x,y,"AscensionV8West_EventScript_Sign"+str(i)) for i,(x,y,_) in enumerate(west_signs)]
east["bg_events"]=[sign(x,y,"AscensionV8East_EventScript_Sign"+str(i))
                    for i,(x,y,_) in enumerate(east_signs)]

for t in range(8):
    p=maps/("AscensionTower"+str(t+1))/"map.json"
    room=read(p)
    if t in (0,1,2,3):
        ext=[0,1,2,7][t]
        back="MAP_ASCENSION_CITY"
    else:
        ext=[1,2,3,4][t-4]
        back="MAP_ASCENSION_CITY_EAST"
    room["warp_events"]=[warp(w["x"],w["y"],back,ext)
                         for w in room["warp_events"]]
    # A real step-through transition to a separate native battle-room map.
    # Each rank uses the same GBA-authentic room layout as a memory-safe
    # proof of routing, not its final themed battlefield.
    room["warp_events"].append(warp(12,2,"MAP_ASCENSION_ARENA_GATE_"+str(t+1),0))
    dump(p,room)

# The Summit uses the east hall warp, unlike V7's west-only exits.
summit=maps/"AscensionSummit/map.json"
d=read(summit)
d["warp_events"]=[warp(w["x"],w["y"],"MAP_ASCENSION_CITY_EAST",0)
                 for w in d["warp_events"]]
d["warp_events"].append(warp(12,2,"MAP_ASCENSION_ARENA_GATE_9",0))
dump(summit,d)

# Make every Arena Master a guide: the *gate* and only the gate starts fights.
for t in range(9):
    name="AscensionSummit" if t==8 else "AscensionTower"+str(t+1)
    p=maps/name/"scripts.inc"
    text=p.read_text()
    a=(" release\n goto AscensionTowerHall_EventScript_Challenge\n"
       +name+"_EventScript_Locked::")
    b=(" msgbox "+name+"_Text_Gate, MSGBOX_DEFAULT\n release\n end\n"
       +name+"_EventScript_Locked::")
    assert text.count(a)==1,name
    text=text.replace(a,b)
    text+=message(name+"_Text_Gate","Meet the challengers ahead.\nUse the NORTH arena gate.")
    p.write_text(text)

gate_template=read(maps/"BattleFrontier_BattleTowerBattleRoom/map.json")
new_maps=[]
for t in range(9):
    name="AscensionArenaGate"+str(t+1)
    d=json.loads(json.dumps(gate_template))
    d["id"]="MAP_ASCENSION_ARENA_GATE_"+str(t+1)
    d["name"]=name
    d["object_events"]=[
        actor("OBJ_EVENT_GFX_EXPERT_M",5,1,name+"_EventScript_Official")]
    previous="MAP_ASCENSION_SUMMIT" if t==8 else "MAP_ASCENSION_TOWER_"+str(t+1)
    d["warp_events"]=[warp(5,8,previous,2),warp(6,8,previous,2)]
    d["bg_events"]=[]
    # Walk forward into combat. Trigger on a step rather than talking to
    # someone. The battle *currently* follows V7 single-opponent logic.
    d["coord_events"]=[dict(type="trigger",x=x,y=4,elevation=3,
        var="VAR_ASCENSION_CAREER_ACTIVE",var_value="1",
        script=name+"_EventScript_Enter") for x in (5,6)]
    dump(maps/name/"map.json",d)
    info=f"""{name}_MapScripts::
 .byte 0
{name}_EventScript_Official::
 msgbox {name}_Text_Info, MSGBOX_NPC
 end
{name}_EventScript_Enter::
 lockall
 setvar VAR_0x8004, {t}
 special Ascension_CanChallengeTower
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Locked
 special Ascension_GetProgress
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Locked
 msgbox {name}_Text_Ready, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_End
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_NoTeam
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {name}_EventScript_Loss
 special Ascension_RecordVictory
 msgbox {name}_Text_Win, MSGBOX_DEFAULT
 goto {name}_EventScript_End
{name}_EventScript_Locked::
 msgbox {name}_Text_Locked, MSGBOX_DEFAULT
 goto {name}_EventScript_End
{name}_EventScript_NoTeam::
 msgbox {name}_Text_NoTeam, MSGBOX_DEFAULT
 goto {name}_EventScript_End
{name}_EventScript_Loss::
 msgbox {name}_Text_Loss, MSGBOX_DEFAULT
{name}_EventScript_End::
 releaseall
 end
"""
    for label,value in [
      ("Info","CROSS THE ARENA LINE\nwhen you are ready to fight."),
      ("Ready","ENTER THE REAL-TIME ARENA?\nYour next challenger awaits."),
      ("Win","Victory! Your rank record\nhas been updated."),
      ("Locked","Complete the earlier towers\nbefore challenging this one."),
      ("NoTeam","Please heal your team\nbefore entering."),
      ("Loss","The challenger prevailed.\nTry again when prepared.")]:
        info+=message(name+"_Text_"+label,value)
    (maps/name/"scripts.inc").write_text(info)
    new_maps.append(name)

# A functional native party/PC lab (reused Pokemon Center interior) and
# genuinely functional native PokeMart, not fake shops.
lab=add_map("AscensionTeamLab","BattleFrontier_PokemonCenter_1F",3)
lab["object_events"]=[
 actor("OBJ_EVENT_GFX_NURSE",7,2,"BattleFrontier_PokemonCenter_1F_EventScript_Nurse"),
 actor("OBJ_EVENT_GFX_EXPERT_M",4,5,"AscensionTeamLab_EventScript_Guide")
]
dump(maps/"AscensionTeamLab/map.json",lab)
labsc="""AscensionTeamLab_MapScripts::
 .byte 0
AscensionTeamLab_EventScript_Guide::
 msgbox AscensionTeamLab_Text_Welcome, MSGBOX_NPC
 end
"""
labsc+=message("AscensionTeamLab_Text_Welcome","TEAM LAB: use the PC to\nmanage your roster.")
(maps/"AscensionTeamLab/scripts.inc").write_text(labsc)

mart=add_map("AscensionItemShop","BattleFrontier_Mart",4)
mart["object_events"]=[
 actor("OBJ_EVENT_GFX_MART_EMPLOYEE",1,3,"BattleFrontier_Mart_EventScript_Clerk",0),
 actor("OBJ_EVENT_GFX_GENTLEMAN",5,4,"AscensionItemShop_EventScript_Visitor",0)]
dump(maps/"AscensionItemShop/map.json",mart)
martsc="""AscensionItemShop_MapScripts::
 .byte 0
AscensionItemShop_EventScript_Visitor::
 msgbox AscensionItemShop_Text_Visitor, MSGBOX_NPC
 end
"""
martsc+=message("AscensionItemShop_Text_Visitor","This MART sells basic items.\nSpend wisely between floors.")
(maps/"AscensionItemShop/scripts.inc").write_text(martsc)

# These two districts are meaningful navigational destinations, but true
# EV/Nature edits and move teaching are explicitly V9 and not falsely enabled.
for nm,original,door,msg in [
 ("AscensionMoveStudio","BattleFrontier_Lounge4",6,
  "MOVE STUDIO: test attacks\nat the practice dojo."),
 ("AscensionStyleHouse","BattleFrontier_Lounge2",5,
  "STYLE HOUSE: this studio\nwill offer more options soon.")]:
    d=add_map(nm,original,door)
    d["object_events"]=[actor("OBJ_EVENT_GFX_EXPERT_M",4,4,nm+"_EventScript_Host",0)]
    dump(maps/nm/"map.json",d)
    sc=nm+"""_MapScripts::
 .byte 0
"""+nm+"""_EventScript_Host::
 msgbox """+nm+"""_Text_Host, MSGBOX_NPC
 end
"""+message(nm+"_Text_Host",msg)
    (maps/nm/"scripts.inc").write_text(sc)

# Native old sign tile coords; provide name and order on both sides of city.
wscript=maps/"AscensionCity/scripts.inc"
escript=maps/"AscensionCityEast/scripts.inc"
w=wscript.read_text()
e=escript.read_text()
for i,(_,_,msg) in enumerate(west_signs):
    label="AscensionV8West"
    w+=f"\n{label}_EventScript_Sign{i}::\n msgbox {label}_Text_Sign{i}, MSGBOX_SIGN\n end\n"
    w+=message(label+"_Text_Sign"+str(i),msg)
for i,(_,_,msg) in enumerate(east_signs):
    label="AscensionV8East"
    e+=f"\n{label}_EventScript_Sign{i}::\n msgbox {label}_Text_Sign{i}, MSGBOX_SIGN\n end\n"
    e+=message(label+"_Text_Sign"+str(i),msg)
wscript.write_text(w)
escript.write_text(e)
dump(maps/"AscensionCity/map.json",west)
dump(maps/"AscensionCityEast/map.json",east)

extra_maps=new_maps+["AscensionTeamLab","AscensionItemShop","AscensionMoveStudio","AscensionStyleHouse"]
groups=read(groups_p)
group=next(k for k,v in groups.items() if "AscensionCity" in v)
assert not any(m in groups[group] for m in extra_maps)
groups[group].extend(extra_maps)
dump(groups_p,groups)
sc=events.read_text()
anchor='\t.include "data/maps/AscensionSummit/scripts.inc"'
assert sc.count(anchor)==1
sc=sc.replace(anchor,anchor+"\n"+"\n".join('\t.include "data/maps/'+m+'/scripts.inc"' for m in extra_maps))
events.write_text(sc)

# Compile/build validation complements these structural checks.
assert [west["warp_events"][i]["dest_map"] for i in [3,4,5,6]]==[
  "MAP_ASCENSION_TEAM_LAB","MAP_ASCENSION_ITEM_SHOP",
  "MAP_ASCENSION_STYLE_HOUSE","MAP_ASCENSION_MOVE_STUDIO"]
assert {w["dest_map"] for w in east["warp_events"]}=={
    "MAP_ASCENSION_SUMMIT","MAP_ASCENSION_TOWER_5","MAP_ASCENSION_TOWER_6",
    "MAP_ASCENSION_TOWER_7","MAP_ASCENSION_TOWER_8"}
assert all(len(read(maps/name/"map.json")["warp_events"])==2 for name in extra_maps[-4:])
print("V8: four west towers, four east towers, Summit, native shops/lab, original tile signs, nine separate walk-through gates.")
print("NOTE: gates use V7 single-Pokemon challenger loop until V8 trainer-party system is implemented and tested.")
