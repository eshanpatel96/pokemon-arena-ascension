#!/usr/bin/env python3
"""V8.1: One actual doorway and one obvious battle path per tower.

Never inject a replacement battle system. Reuses native Tower Battle Room
which has a single visible two-tile SOUTH doorway (x4/5,y8). Master steps aside
from center x5,y5, then player walks up into original Emerald Arena fight.
"""
import json
import sys
from pathlib import Path

root=Path(sys.argv[1]); maps=root/"data/maps"; layouts=root/"data/layouts"
def load(path): return json.loads(path.read_text())
def store(path,obj): path.write_text(json.dumps(obj,indent=2)+"\n")
def npc(gfx,x,y,script):
    return dict(graphics_id=gfx,x=x,y=y,elevation=3,
        movement_type="MOVEMENT_TYPE_FACE_DOWN",movement_range_x=0,movement_range_y=0,
        trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
        script=script,flag="0")
def warp(x,y,target,door):
    return dict(x=x,y=y,elevation=0,dest_map=target,dest_warp_id=str(door))
def text(label,value):
    return label+':\n\t.string "'+value.replace("\n",r"\n")+'$"\n'
# The existing Frontier Battle Room has no maze or desk. Native south exit is
# one 2-tile-wide visible doorway. An internal extra gate is NOT required.
sprite_names=[
  "OBJ_EVENT_GFX_EXPERT_M","OBJ_EVENT_GFX_HIKER","OBJ_EVENT_GFX_BUG_CATCHER",
  "OBJ_EVENT_GFX_PSYCHIC_M","OBJ_EVENT_GFX_BLACK_BELT","OBJ_EVENT_GFX_BEAUTY",
  "OBJ_EVENT_GFX_GENTLEMAN","OBJ_EVENT_GFX_PSYCHIC_M","OBJ_EVENT_GFX_GENTLEMAN"
]
titles=["Bronze Trials","Gale Tower","Verdant Crown","Phantom Spire",
        "Inferno Forge","Tidal Bastion","Thunder Citadel","Astral Apex","Champion Summit"]
advice=[
 "BRONZE: practice dodge timing.\nDefeat every opposing POKEMON.",
 "GALE: avoid straight retreats.\nWatch for quick attackers.",
 "GRASS: balance your team.\nPressure foes between moves.",
 "GHOST: predict their movement.\nSave your fastest attack.",
 "FIRE: use short attack windows.\nNever stand in one place.",
 "WATER: conserve team HP.\nProtect healthy reserves.",
 "THUNDER: anticipate fast foes.\nDodge before contact.",
 "ASTRAL: every move matters.\nPlay for safe openings.",
 "SUMMIT: prepare your six best.\nThe Champions await."
]
for tier in range(9):
    name="AscensionSummit" if tier==8 else f"AscensionTower{tier+1}"
    room_path=maps/name/"map.json"
    room=load(room_path)
    city="MAP_ASCENSION_CITY_EAST" if tier>=4 else "MAP_ASCENSION_CITY"
    entry_warp=0 if tier==8 else (tier-3 if tier>=4 else [0,1,2,7][tier])
    room["layout"]="LAYOUT_BATTLE_FRONTIER_BATTLE_TOWER_BATTLE_ROOM"
    # Only the native 2-tile-wide SOUTH entrance. Remove all fake northern
    # gate warps and spare door hotspots inherited from old lobby maps.
    room["warp_events"]=[warp(x,8,city,entry_warp) for x in (4,5)]
    room["object_events"]=[npc(sprite_names[tier],5,5,name+"_EventScript_Master")]
    room["bg_events"]=[]
    room["coord_events"]=[]
    store(room_path,room)

    # Real physical entrance is at x4/5,y8. Arriving player walks to x5,y6,
    # speaks to Master x5,y5; he moves x5->4, player steps x5,y6->5,y5,
    # then an actual native trainer or wild challenger fight starts.
    s=f"""{name}_MapScripts::
 .byte 0
{name}_EventScript_Master::
 lockall
 faceplayer
 setvar VAR_0x8004, {tier}
 special Ascension_CanChallengeTower
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Locked
 msgbox {name}_Text_Welcome, MSGBOX_DEFAULT
 msgbox {name}_Text_Rules, MSGBOX_DEFAULT
 msgbox {name}_Text_Ready, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_Done
 closemessage
 applymovement 1, {name}_Movement_MasterAside
 waitmovement 1
 applymovement LOCALID_PLAYER, {name}_Movement_PlayerForward
 waitmovement 0
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_NoTeam
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {name}_EventScript_Loss
 special Ascension_RecordVictory
 msgbox {name}_Text_Win, MSGBOX_DEFAULT
 compare VAR_ASCENSION_FLOOR, 2
 goto_if_eq {name}_EventScript_PreBossHeal
 goto {name}_EventScript_Reset
{name}_EventScript_PreBossHeal::
 msgbox {name}_Text_Heal, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_Reset
 special HealPlayerParty
 goto {name}_EventScript_Reset
{name}_EventScript_NoTeam::
 msgbox {name}_Text_NoTeam, MSGBOX_DEFAULT
 goto {name}_EventScript_Reset
{name}_EventScript_Loss::
 msgbox {name}_Text_Loss, MSGBOX_DEFAULT
{name}_EventScript_Reset::
 applymovement LOCALID_PLAYER, {name}_Movement_PlayerBack
 waitmovement 0
 applymovement 1, {name}_Movement_MasterReturn
 waitmovement 1
 goto {name}_EventScript_Done
{name}_EventScript_Locked::
 msgbox {name}_Text_Locked, MSGBOX_DEFAULT
{name}_EventScript_Done::
 releaseall
 end

{name}_Movement_MasterAside:
 walk_left
 step_end

{name}_Movement_PlayerForward:
 walk_up
 step_end

{name}_Movement_PlayerBack:
 walk_down
 step_end

{name}_Movement_MasterReturn:
 walk_right
 step_end
"""
    messages={
      "Welcome":f"{tier+1}. {titles[tier].upper()}!\nI am your Arena Master.",
      "Rules":advice[tier],
      "Ready":"I will step aside. Ready\nto enter the arena?",
      "Win":"Floor cleared! Prepare your\nteam for the next bout.",
      "Heal":"The leader is next!\nHeal before the boss?",
      "NoTeam":"You need a healthy POKEMON\nto challenge this floor.",
      "Loss":"Good effort. Use the city\nfacilities before retrying.",
      "Locked":"Finish the earlier tower\nbefore challenging here."
    }
    for k,v in messages.items(): s+=text(name+"_Text_"+k,v)
    (maps/name/"scripts.inc").write_text(s)

# Distinct central laboratory, reusing Birch's native research tiles and
# professor sprites, rather than the bland Pokemon Center counter.
lab_path=maps/"AscensionTeamLab/map.json"
lab=load(maps/"LittlerootTown_ProfessorBirchsLab/map.json")
lab.update(id="MAP_ASCENSION_TEAM_LAB",name="AscensionTeamLab",
           music="MUS_BIRCH_LAB",
           region_map_section="MAPSEC_BATTLE_FRONTIER")
lab["object_events"]=[
 npc("OBJ_EVENT_GFX_PROF_BIRCH",6,4,"AscensionTeamLab_EventScript_Professor"),
 npc("OBJ_EVENT_GFX_SCIENTIST_1",9,8,"AscensionTeamLab_EventScript_PC"),
 npc("OBJ_EVENT_GFX_SCIENTIST_1",3,6,"AscensionTeamLab_EventScript_Training")
]
lab["warp_events"]=[warp(x,12,"MAP_ASCENSION_CITY",4) for x in (6,7)]
lab["bg_events"]=[]
lab["coord_events"]=[]
lab["connections"]=None
store(lab_path,lab)
lab_script="""AscensionTeamLab_MapScripts::
 .byte 0
AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 release
 end
AscensionTeamLab_EventScript_PC::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_PC, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_Done
 special ShowPokemonStorageSystemPC
AscensionTeamLab_EventScript_Done::
 release
 end
AscensionTeamLab_EventScript_Training::
 msgbox AscensionTeamLab_Text_Training, MSGBOX_NPC
 end
"""
lab_script+=text("AscensionTeamLab_Text_Professor","WELCOME TO ASCENSION LAB!\nPlan your tower strategy.")
lab_script+=text("AscensionTeamLab_Text_PC","Open the POKEMON BOXES\nto arrange your roster?")
lab_script+=text("AscensionTeamLab_Text_Training","Team research and training\nwill expand next season.")
(maps/"AscensionTeamLab/scripts.inc").write_text(lab_script)

# Replace surplus duplicate doors with a centrally positioned facility sign.
# Keep signs only on native sign metatiles (the exact original Battle Frontier
# placement), not arbitrary floor tiles that cannot be interacted with.
west=maps/"AscensionCity/map.json"
w=load(west)
assert len(w["warp_events"])==8
# Original West Mart's building now houses the Lab; more clearly a hub.
w["warp_events"][3]["dest_map"]="MAP_ASCENSION_ITEM_SHOP"
w["warp_events"][4]["dest_map"]="MAP_ASCENSION_TEAM_LAB"
# Item Shop formerly returned to old Mart slot 4; after swapping buildings its
# actual return must be slot 3 in the city map.
shop_path=maps/"AscensionItemShop/map.json"
shop=load(shop_path)
for doorway in shop["warp_events"]:
    doorway["dest_map"]="MAP_ASCENSION_CITY"
    doorway["dest_warp_id"]="3"
store(shop_path,shop)

# The original shop's two physical sign tiles are a single facility.
w["bg_events"]=[
    dict(type="sign",x=x,y=y,elevation=0,
         player_facing_dir="BG_EVENT_PLAYER_FACING_ANY",script=label)
    for x,y,label in [
      (15,18,"AscensionV8West_EventScript_Sign1"),
      (45,30,"AscensionV8West_EventScript_Sign0"),
      (16,43,"AscensionV8West_EventScript_Sign2"),
      (52,51,"AscensionLab_EventScript_Sign"),
      (53,51,"AscensionLab_EventScript_Sign")
    ]]
store(west,w)
# Correct service location, no fake shop sign over the lab.
wc=maps/"AscensionCity/scripts.inc"
old=wc.read_text()
old+="""
AscensionLab_EventScript_Sign::
 msgbox AscensionLab_Text_Sign, MSGBOX_SIGN
 end
"""
old+=text("AscensionLab_Text_Sign","ASCENSION POKEMON LAB\nParty research and BOXES.")
wc.write_text(old)
# Return to the *actual* lab doorway in West (warp index 4).
assert {x["dest_warp_id"] for x in lab["warp_events"]}=={"4"}
for t in range(9):
    z=load(maps/("AscensionSummit" if t==8 else f"AscensionTower{t+1}")/"map.json")
    assert len(z["warp_events"])==2
    assert {tuple((w["x"],w["y"])) for w in z["warp_events"]}=={(4,8),(5,8)}
    assert len(z["object_events"])==1 and z["object_events"][0]["x"]==5
print("V8.1: nine clear single-entrance arena rooms; guides step aside, player enters fights automatically; real Birch-style Lab with PC.")
