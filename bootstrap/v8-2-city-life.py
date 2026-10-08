#!/usr/bin/env python3
"""V8.2 city life, working Lab terminals, native signs, and distinct arena biomes.

No new 32MB artwork added; selects already present Emerald Arena backdrops.
"""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);maps=root/"data/maps"
def load(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+"\n")
def text(k,msg):return k+':\n\t.string "'+msg.replace('\n',r'\n')+'$"\n'
def npc(gfx,x,y,script,pattern="MOVEMENT_TYPE_LOOK_AROUND"):
 return dict(graphics_id=gfx,x=x,y=y,elevation=3,
 movement_type=pattern,movement_range_x=1,movement_range_y=1,
 trainer_type="TRAINER_TYPE_NONE",trainer_sight_or_berry_tree_id="0",
 script=script,flag="0")

# Professor Birch's original map ensures these are legit walkable NPC tiles:
# Aide (9,8), Professor (6,4). The earlier new NPC (3,6) could overlap a
# furnishing, so remove it and give terminal interaction to actual computers.
lab=maps/"AscensionTeamLab/map.json"
d=load(lab)
d["object_events"]=[
 npc("OBJ_EVENT_GFX_PROF_BIRCH",6,4,"AscensionTeamLab_EventScript_Professor","MOVEMENT_TYPE_FACE_DOWN"),
 npc("OBJ_EVENT_GFX_SCIENTIST_1",9,8,"AscensionTeamLab_EventScript_Assistant","MOVEMENT_TYPE_LOOK_AROUND")]
d["bg_events"]=[
 dict(type="sign",x=x,y=y,elevation=0,player_facing_dir="BG_EVENT_PLAYER_FACING_ANY",
      script="EventScript_PC")
 for x,y in ((3,1),(4,1),(1,9),(1,10),(11,9),(11,10))
]
dump(lab,d)
labsc="""AscensionTeamLab_MapScripts::
 .byte 0
AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 release
 end
AscensionTeamLab_EventScript_Assistant::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Assistant, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_Done
 special HealPlayerParty
 msgbox AscensionTeamLab_Text_Healed, MSGBOX_DEFAULT
AscensionTeamLab_EventScript_Done::
 release
 end
"""
for key,msg in [
("Professor","Welcome to the Arena Lab!\nPC terminals manage your team."),
("Assistant","Would you like a FREE heal\nbefore the next tower?"),
("Healed","All healthy! Remember to\ncheck your moves and team.")]:
 labsc+=text("AscensionTeamLab_Text_"+key,msg)
(maps/"AscensionTeamLab/scripts.inc").write_text(labsc)

# Populate authentic, originally walkable Battle Frontier street positions.
# Original Frontier map-event NPC coordinates are used, not arbitrary rooftops
# or counter tiles. Keep total scene load small on GBA.
districts=[
 ("AscensionCity",[
   ("OBJ_EVENT_GFX_SCIENTIST_1",38,27,"Laboratory research is\nhelping our Arena Masters."),
   ("OBJ_EVENT_GFX_MANIAC",13,44,"Ghost Tower gets spooky!\nWatch your positioning."),
   ("OBJ_EVENT_GFX_GIRL_1",23,47,"This city trains future\nchampions!"),
   ("OBJ_EVENT_GFX_CAMPER",9,47,"I practice dodging at\nthe dojo every day."),
   ("OBJ_EVENT_GFX_LASS",35,5,"Check START > ARENA GUIDE\nfor the tower order."),
   ("OBJ_EVENT_GFX_SKITTY",11,66,"Skitty: Meow!"),
   ("OBJ_EVENT_GFX_MAN_2",31,31,"Team Lab has a POKEMON PC.\nKeep a balanced roster."),
 ]),
 ("AscensionCityEast",[
   ("OBJ_EVENT_GFX_ZIGZAGOON_2",40,56,"Zigzagoon: Zig-zag!"),
   ("OBJ_EVENT_GFX_WINGULL",59,35,"Wingull: Kwee!"),
   ("OBJ_EVENT_GFX_GIRL_3",51,53,"The Water Tower challenges\nyour entire team."),
   ("OBJ_EVENT_GFX_HIKER",53,6,"The Fire Tower is HOT!\nSave a Water-type!"),
   ("OBJ_EVENT_GFX_NINJA_BOY",20,17,"Astral challenges test\nsmart dodging."),
   ("OBJ_EVENT_GFX_PIKACHU",18,40,"Pikachu: Pika pika!"),
   ("OBJ_EVENT_GFX_PSYCHIC_M",62,18,"The northern Summit is\nfor the top rank only."),
   ("OBJ_EVENT_GFX_WOMAN_5",10,21,"Get your team ready in\nthe western research Lab."),
 ])]
for area,new_npcs in districts:
 p=maps/area/"map.json";m=load(p)
 scriptfile=maps/area/"scripts.inc"
 scripts=scriptfile.read_text()
 used={(o["x"],o["y"]) for o in m["object_events"]}
 for i,(gfx,x,y,line) in enumerate(new_npcs):
  if (x,y) in used:raise RuntimeError("NPC tile occupied "+area+str((x,y)))
  used.add((x,y))
  label="AscensionLife_"+area+"_NPC"+str(i)
  pattern=("MOVEMENT_TYPE_WANDER_AROUND" if gfx not in ("OBJ_EVENT_GFX_SCIENTIST_1","OBJ_EVENT_GFX_PSYCHIC_M") else "MOVEMENT_TYPE_LOOK_AROUND")
  m["object_events"].append(npc(gfx,x,y,label,pattern))
  scripts+=f"\n{label}::\n msgbox {label}_Text, MSGBOX_NPC\n end\n"
  scripts+=text(label+"_Text",line)
 dump(p,m);scriptfile.write_text(scripts)

# Use original Emerald Arena's built-in community scenery (no huge new art).
biomes=root/"src/arena_biomes.inc";s=biomes.read_text()
old='''    if(map==MAP_ASCENSION_BRONZE_BOSS){gArenaBiome=4;gArenaStage=8;}
    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;'''
new='''    // Tower themes: native game scenery, preserving all original combat art.
    // For trainer battles this must run AFTER the native trainer-pic override.
    switch(map)
    {
    case MAP_ASCENSION_TOWER_1: gArenaBiome=4;gArenaStage=8;break;  // stone
    case MAP_ASCENSION_TOWER_2: gArenaBiome=4;gArenaStage=13;break; // windy sky
    case MAP_ASCENSION_TOWER_3: gArenaBiome=0;gArenaStage=5;break;  // grass
    case MAP_ASCENSION_TOWER_4: gArenaBiome=4;gArenaStage=14;break; // psychic/ghost
    case MAP_ASCENSION_TOWER_5: gArenaBiome=2;gArenaStage=16;break; // volcanic
    case MAP_ASCENSION_TOWER_6: gArenaBiome=1;gArenaStage=1;break;  // water
    case MAP_ASCENSION_TOWER_7: gArenaBiome=4;gArenaStage=10;break; // electric
    case MAP_ASCENSION_TOWER_8: gArenaBiome=4;gArenaStage=15;break; // mystery
    case MAP_ASCENSION_SUMMIT: gArenaBiome=4;gArenaStage=7;break;   // champion
    case MAP_ASCENSION_BRONZE_BOSS:gArenaBiome=4;gArenaStage=8;break;
    }
    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;'''
assert s.count(old)==1,"Stage override missing"
biomes.write_text(s.replace(old,new))
print("V8.2 city life: lab uses real PC terminals + free heal; 15 verified outdoor NPC positions, Pokémon wanderers and original biome themes.")
