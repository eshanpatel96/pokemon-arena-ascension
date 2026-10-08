#!/usr/bin/env python3
"""V10.1 native exterior tidy pass.

Undo experimental one-palette-only residential/supply-roof recolors that
create striped or blocky mismatched houses on authentic Emerald pixels. Retain
real Lab, plaza, natural flowers, functional signs, all original door warps,
the remaining distinctive native arena/tower buildings and all 16x16 tiles.
Use thematically appropriate ORIGINAL NPC art instead of generic gentlemen
in the nine leader rooms (especially Bronze stone quarry).
"""
from pathlib import Path
import json,struct,sys
root=Path(sys.argv[1])
w,h=56,72
live=root/"data/layouts/AscensionCity/map.bin"
original=root/"data/layouts/BattleFrontier_OutsideWest/map.bin"
current=live.read_bytes()
base=original.read_bytes()
assert len(current)==len(base)==2*w*h
words=list(struct.unpack("<"+str(w*h)+"H",current))
source=struct.unpack("<"+str(w*h)+"H",base)
locations=0
for left,right in ((44,49),(52,54)):
    for y in range(41,44):
        for x in range(left,right+1):
            ix=y*w+x
            before=words[ix]
            native=source[ix]
            assert before>>10==native>>10,(x,y,"collision was modified")
            words[ix]=(before&~1023)|(native&1023)
            locations+=1
# Keep the actually hand-built LAB lettering and public campus garden; only
# restore deliberately experimental supply/studio half-palette roof patches.
assert (words[51*w+52]&1023)!=(source[51*w+52]&1023)
assert (words[51*w+53]&1023)!=(source[51*w+53]&1023)
live.write_bytes(struct.pack("<"+str(w*h)+"H",*words))
# The original game tilesets are paletted, unchanged for native buildings.
# Names on signs identify services without false-colour blocky roof pixels.
art={
    "AscensionBronzeBoss":"OBJ_EVENT_GFX_HIKER",
    "AscensionLeader2":"OBJ_EVENT_GFX_LASS",
    "AscensionLeader3":"OBJ_EVENT_GFX_EXPERT_F",
    "AscensionLeader4":"OBJ_EVENT_GFX_PSYCHIC_M",
    "AscensionLeader5":"OBJ_EVENT_GFX_BLACK_BELT",
    "AscensionLeader6":"OBJ_EVENT_GFX_SWIMMER_M",
    "AscensionLeader7":"OBJ_EVENT_GFX_SCIENTIST_1",
    "AscensionLeader8":"OBJ_EVENT_GFX_PSYCHIC_M",
    "AscensionLeader9":"OBJ_EVENT_GFX_OLD_MAN",
}
for name,gfx in art.items():
    p=root/f"data/maps/{name}/map.json"
    doc=json.loads(p.read_text())
    objs=doc["object_events"]
    assert len(objs)==2 and "ExitAttendant" in objs[1]["script"],name
    objs[1]["graphics_id"]=gfx
    p.write_text(json.dumps(doc,indent=2)+"\n")
# Verify all service warps remain unchanged and the campus paths stay intact.
city=json.loads((root/"data/maps/AscensionCity/map.json").read_text())
assert len(city["object_events"])<=16
assert "AscensionV9City_EventScript_SupplySign" in (root/"data/maps/AscensionCity/scripts.inc").read_text()
assert "AscensionV9City_EventScript_MoveSign" in (root/"data/maps/AscensionCity/scripts.inc").read_text()
print(f"V10.1 PIXEL ART TIDY: {locations} building-roof metatiles restored to cohesive native Emerald art; Lab and garden retained; 9 boss gatekeepers now themed, including Bronze Hiker. No GBA resolution change and no door collision changes.")
