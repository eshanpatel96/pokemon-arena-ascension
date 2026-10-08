#!/usr/bin/env python3
"""Export a compact, reproducible *source* snapshot from the pinned Emerald
overlay after Ascension bootstrap. For real map/floor inspection and regression
review. Never include the copyrighted original GBA ROM.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha256
import json
import sys

root=Path(sys.argv[1])
out=Path(sys.argv[2])
out.parent.mkdir(parents=True,exist_ok=True)
files=[
    "src/ascension_career.c",
    "src/realtime_arena.c",
    "src/arena_biomes.inc",
    "include/ascension_progress.h",
    "include/constants/vars.h",
    "include/constants/flags.h",
    "data/ascension_guide.inc",
    "data/maps/map_groups.json",
    "data/layouts/layouts.json",
    "data/layouts/AscensionCity/map.bin",
    "data/layouts/AscensionCityEast/map.bin",
    "data/layouts/AscensionCity/border.bin",
    "data/layouts/AscensionCityEast/border.bin",
    "tools/arena/roster.json",
]
for folder in ["AscensionCity", "AscensionCityEast", "AscensionTeamLab",
               "AscensionItemShop", "AscensionMoveStudio", "AscensionStyleHouse",
               "AscensionBronzeBoss"] + [f"AscensionTower{i}" for i in range(1,9)] + [f"AscensionLeader{i}" for i in range(2,9)]:
    files.extend((f"data/maps/{folder}/map.json",f"data/maps/{folder}/scripts.inc"))
for area in ["primary/general", "secondary/battle_frontier_outside_west","secondary/battle_frontier_outside_east"]:
    folder=root/"data/tilesets"/area
    for file in folder.rglob("*"):
        if file.is_file() and (file.suffix in [".bin",".png",".pal",".gbapal",".json"]):
            files.append(str(file.relative_to(root)))
missing=[p for p in files if not (root/p).is_file()]
if missing:
    raise RuntimeError("diagnostic paths missing: "+str(missing[:20]))
manifest={}
with ZipFile(out,"w",ZIP_DEFLATED,compresslevel=6) as archive:
    for path in sorted(set(files)):
        archive.write(root/path,path)
        body=(root/path).read_bytes()
        manifest[path]={"size":len(body),"sha256":sha256(body).hexdigest()}
    archive.writestr("source-manifest.json",json.dumps(manifest,indent=2))
print(f"V9 diagnostics exported: {len(manifest)} source/maps/tile references, {out.stat().st_size} bytes")
