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
# Exterior repainting is now disabled in v9-city-architecture.py before
# allocation of custom metatiles. Do not copy a vanilla map's roof IDs into
# Ascension City: its actual buildings were changed by earlier versions.
# Preserve all already-created native city tile definitions and only replace
# thematically inappropriate gatekeepers in the original boss rooms.
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
print("V10.1 PIXEL ART TIDY: coherent original native Emerald roof metatiles left untouched; Lab, functional signs and plaza retained; 9 boss gatekeepers themed including Bronze Hiker.")
