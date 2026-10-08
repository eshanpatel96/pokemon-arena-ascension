#!/usr/bin/env python3
"""V9 leader presentation: nine distinct EXISTING-Emerald themed boss interiors.

No extra map assets/tiles; each venue references a native Gym/Frontier/League
layout already compiled into Emerald. Trigger is on-frame; boss stays visible
opposite player's approach, then a real trainer-party Arena fight starts.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);maps=root/"data/maps"
def load(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+"\n")
def say(k,v):return k+':\n\t.string "'+v.replace("\n",r"\n")+'$"\n'
data=[
 ("RustboroCity_Gym","MUS_GYM","OBJ_EVENT_GFX_ROXANNE",5,2,5,7,"STONE TRIALS","The ancient stone arena."),
 ("FortreeCity_Gym","MUS_GYM","OBJ_EVENT_GFX_WINONA",15,2,15,7,"GALE SUMMIT","Feel the rush of the wind!"),
 ("BattleFrontier_BattlePalaceBattleRoom","MUS_B_PALACE","OBJ_EVENT_GFX_EXPERT_F",13,2,5,7,"VERDANT SANCTUARY","May the forest grant strength."),
 ("MtPyre_2F","MUS_MT_PYRE","OBJ_EVENT_GFX_PSYCHIC_M",6,4,6,8,"PHANTOM CRYPT","Face the shadows calmly."),
 ("LavaridgeTown_Gym_1F","MUS_GYM","OBJ_EVENT_GFX_FLANNERY",13,9,13,12,"INFERNO FURNACE","Feel the fire of the forge!"),
 ("SootopolisCity_Gym_1F","MUS_GYM","OBJ_EVENT_GFX_JUAN",8,2,8,7,"TIDAL CITADEL","Conserve strength in the deep."),
 ("MauvilleCity_Gym","MUS_GYM","OBJ_EVENT_GFX_WATTSON",5,2,5,7,"THUNDER CHAMBER","Every lightning strike counts!"),
 ("MossdeepCity_Gym","MUS_GYM","OBJ_EVENT_GFX_STEVEN",23,7,22,11,"ASTRAL SANCTUM","You cannot outrun destiny."),
 ("EverGrandeCity_ChampionsRoom","MUS_VS_CHAMPION","OBJ_EVENT_GFX_WALLACE",6,5,6,9,"CHAMPION THRONE","The world title is at stake!")
]
assert len(data)==9
names=[]
for tier,(template,music,gfx,bx,by,px,py,title,quote) in enumerate(data):
    name="AscensionBronzeBoss" if tier==0 else "AscensionLeader"+str(tier+1)
    target="MAP_ASCENSION_BRONZE_BOSS" if tier==0 else "MAP_ASCENSION_LEADER_"+str(tier+1)
    source=load(maps/template/"map.json")
    source.update(id=target,name=name,music=music,
                  region_map_section="MAPSEC_BATTLE_FRONTIER",connections=None)
    source["object_events"]=[
      dict(graphics_id=gfx,x=bx,y=by,elevation=3,
      movement_type="MOVEMENT_TYPE_FACE_DOWN",movement_range_x=0,movement_range_y=0,
      trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
      script=name+"_EventScript_Leader",flag="0")]
    source["coord_events"]=[]
    source["bg_events"]=[]
    # Independent one-way fallback exit: returning to tower even if the automatic
    # boss script fails/was interrupted. Uses original exit portal art.
    if source["warp_events"]:
        source["warp_events"]=[dict(x=w["x"],y=w["y"],elevation=w.get("elevation",0),
            dest_map="MAP_ASCENSION_TOWER_"+str(tier+1) if tier<8 else "MAP_ASCENSION_SUMMIT",
            dest_warp_id="0") for w in source["warp_events"][:2]]
    save(maps/name/"map.json",source)
    if tier==0:
        # V8.2 already generated the 1st leader map script and include.
        scr=maps/name/"scripts.inc"
        s=scr.read_text()
        s=s.replace("WELCOME TO BRONZE FINALS!","WELCOME TO BRONZE FINALS!")
        s=s.replace("This is the leader's arena.","The stone Master awaits!")
        scr.write_text(s)
        continue
    names.append(name)
    prev="MAP_ASCENSION_SUMMIT" if tier==8 else "MAP_ASCENSION_TOWER_"+str(tier+1)
    sc=f"""{name}_MapScripts::
 map_script MAP_SCRIPT_ON_FRAME_TABLE, {name}_OnFrame
 .byte 0
{name}_OnFrame:
 map_script_2 VAR_TEMP_0, 0, {name}_EventScript_Start
 .2byte 0
{name}_EventScript_Start::
 setvar VAR_TEMP_0, 1
 lockall
 msgbox {name}_Text_Welcome, MSGBOX_DEFAULT
 msgbox {name}_Text_Lead, MSGBOX_DEFAULT
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_Return
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {name}_EventScript_Lost
 special Ascension_RecordVictory
 msgbox {name}_Text_Win, MSGBOX_DEFAULT
 goto {name}_EventScript_Return
{name}_EventScript_Lost::
 special Ascension_RecordDefeat
 msgbox {name}_Text_Lost, MSGBOX_DEFAULT
{name}_EventScript_Return::
 warp {prev}, 5, 6
 waitstate
 end
{name}_EventScript_Leader::
 msgbox {name}_Text_Lead, MSGBOX_NPC
 end
"""
    for msg,value in [
     ("Welcome",title+"!\nA real Tower Leader awaits."),
     ("Lead",quote+"\nShow me your whole team!"),
     ("Win","Outstanding! Record updated.\nSee the Lab about rewards."),
     ("Lost","Well fought. You can return\nwith another team soon.")]:
        sc+=say(name+"_Text_"+msg,value)
    (maps/name/"scripts.inc").write_text(sc)
    tower="AscensionSummit" if tier==8 else "AscensionTower"+str(tier+1)
    scripts=maps/tower/"scripts.inc"
    s=scripts.read_text()
    search=(f" msgbox {tower}_Text_Next, MSGBOX_DEFAULT\n"
            f" goto {tower}_EventScript_NextOpponent\n")
    assert s.count(search)==1,tower
    replacement=f""" compare VAR_ASCENSION_FLOOR, 2
 goto_if_eq {tower}_EventScript_BossApproach
"""+search+f"""{tower}_EventScript_BossApproach::
 msgbox {tower}_Text_LeaderReady, MSGBOX_DEFAULT
 msgbox {tower}_Text_LeaderHeal, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {tower}_EventScript_BossWarp
 special HealPlayerParty
{tower}_EventScript_BossWarp::
 warp {target}, {px}, {py}
 waitstate
 end
"""
    s=s.replace(search,replacement)
    s+=say(tower+"_Text_LeaderReady","The Tower Master awaits!\nStep into the final arena.")
    s+=say(tower+"_Text_LeaderHeal","Take a FULL team heal\nbefore the final fight?")
    scripts.write_text(s)

# Bronze's native leader room is a genuine stone Gym now; all others are
# existing themed Emerald levels (not recolored clones of the old desk room).
groups=maps/"map_groups.json"
m=load(groups)
key=next(x for x,a in m.items() if "AscensionCity" in a)
for name in names:
    assert name not in m[key]
    m[key].append(name)
save(groups,m)
events=root/"data/event_scripts.s";s=events.read_text()
anchor='\t.include "data/maps/AscensionBronzeBoss/scripts.inc"'
assert s.count(anchor)==1
events.write_text(s.replace(anchor,anchor+"\n"+"\n".join(
 '\t.include "data/maps/'+name+'/scripts.inc"' for name in names)))

# Original Arena engine already owns these environment tiles; select the
# native scene according to the leader map after trainer-pic default styles.
biome=root/"src/arena_biomes.inc";s=biome.read_text()
needle="    case MAP_ASCENSION_BRONZE_BOSS:gArenaBiome=4;gArenaStage=8;break;"
assert s.count(needle)==1
insert="""
    case MAP_ASCENSION_LEADER_2:gArenaBiome=4;gArenaStage=13;break;
    case MAP_ASCENSION_LEADER_3:gArenaBiome=0;gArenaStage=5;break;
    case MAP_ASCENSION_LEADER_4:gArenaBiome=4;gArenaStage=14;break;
    case MAP_ASCENSION_LEADER_5:gArenaBiome=2;gArenaStage=16;break;
    case MAP_ASCENSION_LEADER_6:gArenaBiome=1;gArenaStage=1;break;
    case MAP_ASCENSION_LEADER_7:gArenaBiome=4;gArenaStage=10;break;
    case MAP_ASCENSION_LEADER_8:gArenaBiome=4;gArenaStage=15;break;
    case MAP_ASCENSION_LEADER_9:gArenaBiome=4;gArenaStage=7;break;"""
biome.write_text(s.replace(needle,needle+insert))
for tier in range(9):
    name="AscensionBronzeBoss" if tier==0 else "AscensionLeader"+str(tier+1)
    d=load(maps/name/"map.json")
    assert d["layout"] and d["id"]
print("V9 visual leader upgrade: nine native Emerald-themed maps, own music, opposing boss NPCs, dedicated prep/heal entry and Arena stage.")
