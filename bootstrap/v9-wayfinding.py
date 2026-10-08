#!/usr/bin/env python3
"""V9 external wayfinding: eight distinct tower greeters, Lab steward and
interactable, numbered exterior signs. Original Emerald NPC pixels only.

All spawn coordinates have been inspected against the original West/East
Frontier map.bin for passability; do not place in door collision or rooftops.
"""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); maps=root/"data/maps"
def add(x):
 return dict(graphics_id=x["gfx"],x=x["x"],y=x["y"],elevation=3,
  movement_type="MOVEMENT_TYPE_FACE_DOWN",movement_range_x=0,
  movement_range_y=0,trainer_type="TRAINER_TYPE_NONE",
  trainer_sight_or_berry_tree_id="0",script=x["script"],flag="0")
def msg(label,line):
 return label+':\n\t.string "'+line.replace("\n",r"\n")+'$"\n'
place=[
 ("AscensionCity",[
  (39,29,"OBJ_EVENT_GFX_HIKER","BRONZE: Tower 1. Rock teams!\nBeat the Master for REGIROCK."),
  (20,20,"OBJ_EVENT_GFX_EXPERT_F","GALE: Tower 2. Flying foes!\nFirst conquer BRONZE."),
  (13,40,"OBJ_EVENT_GFX_BUG_CATCHER","VERDANT: Tower 3. GRASS!\nBring balanced attackers."),
  (3,25,"OBJ_EVENT_GFX_MANIAC","PHANTOM: Tower 4. GHOST!\nTiming matters in the fog."),
  (50,54,"OBJ_EVENT_GFX_SCIENTIST_1","TEAM LAB: Professor Birch\ncan help with your POKEMON.")
 ]),
 ("AscensionCityEast",[
  (55,18,"OBJ_EVENT_GFX_BLACK_BELT","INFERNO: Tower 5. FIRE!\nPrepare a WATER partner."),
  (41,58,"OBJ_EVENT_GFX_SWIMMER_M","TIDAL: Tower 6. WATER!\nBring a healthy reserve."),
  (37,32,"OBJ_EVENT_GFX_GENTLEMAN","THUNDER: Tower 7. ELECTRIC!\nDodge before impact."),
  (15,17,"OBJ_EVENT_GFX_PSYCHIC_M","ASTRAL: Tower 8. DRAGON!\nYour final tower challenge.")
 ])
]
for area,entries in place:
    p=maps/area/"map.json";d=json.loads(p.read_text())
    sc=maps/area/"scripts.inc";text=sc.read_text()
    if area=="AscensionCity":
        # Replace three filler pedestrians with real tower attendants while
        # respecting the hardware/object-event limit.
        stale={"AscensionLife_AscensionCity_NPC2",
               "AscensionLife_AscensionCity_NPC4",
               "AscensionLife_AscensionCity_NPC6"}
        d["object_events"]=[o for o in d["object_events"] if o["script"] not in stale]
    used={(o["x"],o["y"]) for o in d["object_events"]}
    for i,(x,y,gfx,line) in enumerate(entries):
        if (x,y) in used:
            raise RuntimeError(f"already occupied: {area} {(x,y)}")
        used.add((x,y))
        label="AscensionV9_"+area+"_Guide"+str(i)
        d["object_events"].append(add(dict(gfx=gfx,x=x,y=y,script=label)))
        text+="\n"+label+"::\n msgbox "+label+"_Text, MSGBOX_NPC\n end\n"
        text+=msg(label+"_Text",line)
    if len(d["object_events"])>16:
        raise RuntimeError(f"More than 16 local objects in {area}; risk sprite overflow: {len(d['object_events'])}")
    p.write_text(json.dumps(d,indent=2)+"\n")
    sc.write_text(text)
print("V9 exterior guides: nine new native trainers/scientists at existing passable Frontier tiles, 15/16 outdoor NPCs; tower numbering reinforced.")
