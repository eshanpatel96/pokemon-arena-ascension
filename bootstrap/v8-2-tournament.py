#!/usr/bin/env python3
"""V8.2: authentic Battle Tower challenger walk-ins and a separate Bronze boss room.
Preserves Emerald Arena combat. Reuses original GBA sprites, scripts and tiles.
"""
from pathlib import Path
import json
import sys

root=Path(sys.argv[1]); maps=root/"data/maps"
def rd(p):return json.loads(p.read_text())
def wr(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+"\n")
def txt(name,value): return name+':\n\t.string "'+value.replace("\n",r"\n")+'$"\n'
def obj(sprite,x,y,script,flag="0",movement="MOVEMENT_TYPE_FACE_DOWN"):
    return dict(graphics_id=sprite,x=x,y=y,elevation=3,
                movement_type=movement,movement_range_x=0,movement_range_y=0,
                trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
                script=script,flag=flag)

# One persistent small variable guarantees a DIFFERENT challenger overworld
# sprite each time a floor starts (including repeats), cycling among six types.
varsfile=root/"include/constants/vars.h";v=varsfile.read_text()
assert v.count("#define VAR_UNUSED_0x40FE")==1
varsfile.write_text(v.replace("#define VAR_UNUSED_0x40FE",
         "#define VAR_ASCENSION_CHALLENGER_ROTATION               0x40FE //\n//#define VAR_UNUSED_0x40FE"))
# V8 party scripts already access VarGet()/VarSet(), gSpecialVar_Result.
career=root/"src/ascension_career.c"; c=career.read_text()
assert '#include "constants/event_objects.h"' not in c
c=c.replace('#include "constants/items.h"','#include "constants/items.h"\n#include "constants/event_objects.h"')
c+="""

// Native visible challenger gfx rotation (no new character assets).
void Ascension_NextChallengerSprite(void)
{
    static const u16 gfx[] = {
        OBJ_EVENT_GFX_COOLTRAINER_M, OBJ_EVENT_GFX_PSYCHIC_M,
        OBJ_EVENT_GFX_BLACK_BELT, OBJ_EVENT_GFX_ACE_TRAINER,
        OBJ_EVENT_GFX_BUG_CATCHER, OBJ_EVENT_GFX_RICH_BOY
    };
    u16 next = (VarGet(VAR_ASCENSION_CHALLENGER_ROTATION) + 1) % ARRAY_COUNT(gfx);
    VarSet(VAR_ASCENSION_CHALLENGER_ROTATION, next);
    VarSet(VAR_OBJ_GFX_ID_0, gfx[next]);
}
"""
# Replace unavailable sprite names early if not part of base Emerald.
gfxdefs=(root/"include/constants/event_objects.h").read_text()
for old,new in [("OBJ_EVENT_GFX_COOLTRAINER_M","OBJ_EVENT_GFX_GENTLEMAN"),("OBJ_EVENT_GFX_ACE_TRAINER","OBJ_EVENT_GFX_HIKER")]:
    if ("#define "+old+" ") not in gfxdefs:
        c=c.replace(old,new)
career.write_text(c)
specials=root/"data/specials.inc";sc=specials.read_text()
key="\tdef_special Ascension_CanChallengeTower"
assert sc.count(key)==1
specials.write_text(sc.replace(key,key+"\n\tdef_special Ascension_NextChallengerSprite"))

for t in range(9):
    name="AscensionSummit" if t==8 else f"AscensionTower{t+1}"
    p=maps/name/"map.json";m=rd(p)
    # Same exact local IDs as original Emerald Frontier Battle Tower:
    # 1 = challenger, 2 = attendant/master. That code has proven animations.
    m["object_events"]=[
        dict(obj("OBJ_EVENT_GFX_VAR_0",5,1,name+"_EventScript_Opponent",
                 "FLAG_HIDE_BATTLE_TOWER_OPPONENT"),local_id="LOCALID_TOWER_BATTLE_OPPONENT"),
        dict(obj(m["object_events"][0]["graphics_id"],5,5,name+"_EventScript_Master"),
             local_id="LOCALID_TOWER_BATTLE_ATTENDANT_1")
    ]
    m["coord_events"]=[]
    wr(p,m)
    is_bronze=t==0
    # Every floor: player accepts, Master exits, trainer enters from the far
    # end, one trainer-vs-trainer fight, defeated trainer speaks and exits,
    # next trainer walks in without returning to the outer lobby.
    s=f"""{name}_MapScripts::
 map_script MAP_SCRIPT_ON_TRANSITION, {name}_EventScript_Initialize
 .byte 0
{name}_EventScript_Initialize::
 setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 end
{name}_EventScript_Master::
 lockall
 faceplayer
 setvar VAR_0x8004, {t}
 special Ascension_CanChallengeTower
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Locked
 msgbox {name}_Text_Intro, MSGBOX_DEFAULT
 msgbox {name}_Text_Ready, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_End
 closemessage
 applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterAside
 removeobject LOCALID_TOWER_BATTLE_ATTENDANT_1
 applywaitmovement LOCALID_PLAYER, {name}_Move_PlayerAdvance
{name}_EventScript_NextOpponent::
 special Ascension_NextChallengerSprite
 clearflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 addobject LOCALID_TOWER_BATTLE_OPPONENT
 applywaitmovement LOCALID_TOWER_BATTLE_OPPONENT, {name}_Move_ChallengerEnter
 msgbox {name}_Text_ChallengerIntro, MSGBOX_DEFAULT
 closemessage
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_NoTeam
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {name}_EventScript_Loss
 msgbox {name}_Text_ChallengerLost, MSGBOX_DEFAULT
 applywaitmovement LOCALID_TOWER_BATTLE_OPPONENT, {name}_Move_ChallengerExit
 removeobject LOCALID_TOWER_BATTLE_OPPONENT
 setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 special Ascension_RecordVictory
 goto_if_ne VAR_RESULT, 1, {name}_EventScript_Finish
"""
    if is_bronze:
        s+=f""" compare VAR_ASCENSION_FLOOR, 2
 goto_if_eq {name}_EventScript_BossApproach
"""
    s+=f""" msgbox {name}_Text_Next, MSGBOX_DEFAULT
 goto {name}_EventScript_NextOpponent
"""
    if is_bronze:
        s+=f"""{name}_EventScript_BossApproach::
 msgbox {name}_Text_PreBoss, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_BossWarp
 special HealPlayerParty
{name}_EventScript_BossWarp::
 msgbox {name}_Text_BossEntry, MSGBOX_DEFAULT
 warp MAP_ASCENSION_BRONZE_BOSS, 0, 11, 9
 waitstate
 end
"""
    s+=f"""{name}_EventScript_Finish::
 msgbox {name}_Text_Cleared, MSGBOX_DEFAULT
 goto {name}_EventScript_Reset
{name}_EventScript_Loss::
 msgbox {name}_Text_ChallengerWon, MSGBOX_DEFAULT
 applywaitmovement LOCALID_TOWER_BATTLE_OPPONENT, {name}_Move_ChallengerExit
 removeobject LOCALID_TOWER_BATTLE_OPPONENT
 setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 goto {name}_EventScript_Reset
{name}_EventScript_NoTeam::
 msgbox {name}_Text_NoTeam, MSGBOX_DEFAULT
 removeobject LOCALID_TOWER_BATTLE_OPPONENT
 setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
{name}_EventScript_Reset::
 applywaitmovement LOCALID_PLAYER, {name}_Move_PlayerRetreat
 addobject LOCALID_TOWER_BATTLE_ATTENDANT_1
 goto {name}_EventScript_End
{name}_EventScript_Locked::
 msgbox {name}_Text_Locked, MSGBOX_DEFAULT
{name}_EventScript_End::
 releaseall
 end
{name}_EventScript_Opponent::
 msgbox {name}_Text_ChallengerIntro, MSGBOX_NPC
 end

{name}_Move_MasterAside:
 walk_left
 step_end
{name}_Move_PlayerAdvance:
 walk_up
 step_end
{name}_Move_PlayerRetreat:
 walk_down
 step_end
{name}_Move_ChallengerEnter:
 walk_down
 walk_down
 face_down
 step_end
{name}_Move_ChallengerExit:
 walk_up
 walk_up
 step_end
"""
    strings=[
      ("Intro",f"{t+1}. {name.upper()}!\nI'll clear the battle lane."),
      ("Ready","My challenger will enter.\nReady to compete?"),
      ("ChallengerIntro","Let's see your teamwork!\nPrepare to battle!"),
      ("ChallengerLost","A good fight! You earned\nthat win. Well played!"),
      ("ChallengerWon","That was a challenge!\nTrain and come back."),
      ("Next","Next challenger is coming!\nKeep your team ready."),
      ("Cleared","Well done! The next tower\nawaits your team."),
      ("NoTeam","Please restore your team\nbefore fighting again."),
      ("Locked","Win the earlier towers\nto unlock this challenge."),
    ]
    if is_bronze:
        strings.extend([
          ("PreBoss","Your Bronze leader awaits!\nRestore your team first?"),
          ("BossEntry","The grand arena is ready.\nShow your best team!")
        ])
    for key,value in strings:s+=txt(name+"_Text_"+key,value)
    (maps/name/"scripts.inc").write_text(s)

# Bronze Leader gets a SEPARATE native large Battle Dome chamber with crowd
# art (not an imaginary custom tileset). New map is only 1 extra layout ref,
# keeping ROM and EWRAM use within strict GBA headroom.
boss_name="AscensionBronzeBoss"; boss=rd(maps/"BattleFrontier_BattleDomeBattleRoom/map.json")
boss.update(id="MAP_ASCENSION_BRONZE_BOSS",name=boss_name,
            music="MUS_B_DOME",region_map_section="MAPSEC_BATTLE_FRONTIER",
            layout="LAYOUT_BATTLE_FRONTIER_BATTLE_DOME_BATTLE_ROOM",
            connections=None,coord_events=[],bg_events=[])
boss["object_events"]=[obj("OBJ_EVENT_GFX_ROXANNE",11,6,boss_name+"_EventScript_Leader")]
boss["warp_events"]=[]
wr(maps/boss_name/"map.json",boss)
boss_script=f"""{boss_name}_MapScripts::
 map_script MAP_SCRIPT_ON_FRAME_TABLE, {boss_name}_OnFrame
 .byte 0
{boss_name}_OnFrame:
 map_script_2 VAR_TEMP_0, 0, {boss_name}_EventScript_Start
 .2byte 0
{boss_name}_EventScript_Start::
 setvar VAR_TEMP_0, 1
 lockall
 msgbox {boss_name}_Text_Intro, MSGBOX_DEFAULT
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {boss_name}_EventScript_Leave
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {boss_name}_EventScript_Lost
 special Ascension_RecordVictory
 msgbox {boss_name}_Text_Win, MSGBOX_DEFAULT
 goto {boss_name}_EventScript_Leave
{boss_name}_EventScript_Lost::
 msgbox {boss_name}_Text_Lost, MSGBOX_DEFAULT
{boss_name}_EventScript_Leave::
 warp MAP_ASCENSION_TOWER_1, 0, 5, 6
 waitstate
 end
{boss_name}_EventScript_Leader::
 msgbox {boss_name}_Text_Intro, MSGBOX_NPC
 end
"""
for k,v in [
 ("Intro","WELCOME TO BRONZE FINALS!\nThis is the leader's arena."),
 ("Win","You are the BRONZE CHAMP!\nThe Gale Tower opens next."),
 ("Lost","Return when you're ready.\nThe Bronze leader awaits.")]:
    boss_script+=txt(boss_name+"_Text_"+k,v)
(maps/boss_name/"scripts.inc").write_text(boss_script)

# Arena fight background: stage 8 is Emerald Arena's authentic Roxanne stone
# gym arena, NOT a hand-drawn low-res substitute or duplicate battle engine.
biome=root/"src/arena_biomes.inc"; b=biome.read_text()
needle="    if(gBattleTypeFlags&BATTLE_TYPE_TRAINER)"
assert b.count(needle)==1
b=b.replace(needle,'''    // Distinct Bronze championship battleground in original Arena engine.
    if(map==MAP_ASCENSION_BRONZE_BOSS){gArenaBiome=4;gArenaStage=8;}
'''+needle)
# Original trainer-pic override can overwrite stage 8; reassert afterward.
needle2="    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;"
assert b.count(needle2)==1
b=b.replace(needle2,'''    if(map==MAP_ASCENSION_BRONZE_BOSS){gArenaBiome=4;gArenaStage=8;}
'''+needle2)
biome.write_text(b)

gr=root/"data/maps/map_groups.json"; g=rd(gr)
key=next(k for k,v in g.items() if "AscensionCity" in v)
assert boss_name not in g[key]
g[key].append(boss_name);wr(gr,g)
events=root/"data/event_scripts.s";ev=events.read_text()
anchor='\t.include "data/maps/AscensionSummit/scripts.inc"'
assert ev.count(anchor)==1
events.write_text(ev.replace(anchor,anchor+'\n\t.include "data/maps/'+boss_name+'/scripts.inc"'))
print("V8.2 choreography: master clears lane, six rotating trainer sprites, loser departs, new challenger enters; Bronze has Dome boss chamber and distinct Arena stage 8.")
