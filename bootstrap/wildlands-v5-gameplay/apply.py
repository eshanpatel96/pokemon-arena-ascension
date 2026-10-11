#!/usr/bin/env python3
"""Wildlands V5 gameplay integration. Fail rather than silently omit features."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
arena=root/"src/realtime_arena.c"
source=arena.read_text()
anchor="    sArena.frame = 0;\n    sArena.active = TRUE;"
assert anchor in source, "V5 gameplay anchor drift"
# Lightweight match timer: independent of Emerald overworld time.
# This is intentionally the first gameplay feature, not a claim of 2v2.
source=source.replace(anchor,anchor+"\n    gWildlandsV5MatchFrames = 0;",1)
anchor2="    ArenaXL_UpdateCamera();\n    AnimateSprites();\n    BuildOamBuffer();"
assert anchor2 in source, "V5 frame hook anchor drift"
source=source.replace(anchor2,"    if (sArena.active && !sArena.paused) gWildlandsV5MatchFrames++;\n"+anchor2,1)
anchor3="#define ARENA_XL_WORLD_W 4096"
assert anchor3 in source, "V5 world anchor drift"
source=source.replace(anchor3,"EWRAM_DATA u32 gWildlandsV5MatchFrames = 0;\n"+anchor3,1)
arena.write_text(source)
print("Wildlands V5 match timer installed; true 2v2, storm and loot still pending")
