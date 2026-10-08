#!/usr/bin/env python3
"""Persist earned floor rewards through defeat, retries and reloads.

Each of eight towers owns two bits (0..3 floors credited) in an unused native
Emerald save var. Boss legendary/partner remain locked until rank advances.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
header=root/"include/constants/vars.h"
career=root/"src/ascension_career.c"
s=header.read_text()
anchor="#define VAR_UNUSED_0x40F8"
assert s.count(anchor)==1
header.write_text(s.replace(anchor,
    "#define VAR_ASCENSION_RECRUIT_MILESTONES                0x40F8 // 2 saved bits per tower\n//"+anchor,1))
s=career.read_text()
anchor="void Ascension_RecordVictory(void)\n{"
assert s.count(anchor)==1
s=s.replace(anchor,"""// Completed ordinary-floor unlock eligibility is independent of today's run.
static void Ascension_RememberClearedFloor(u16 rank,u16 cleared)
{
    u16 mask,bits,old;
    if(rank>=ASCENSION_TOWER_COUNT||!cleared)return;
    if(cleared>3)cleared=3;
    bits=VarGet(VAR_ASCENSION_RECRUIT_MILESTONES);
    old=(bits>>(rank*2))&3;
    if(cleared<=old)return;
    mask=3<<(rank*2);
    VarSet(VAR_ASCENSION_RECRUIT_MILESTONES,(bits&~mask)|(cleared<<(rank*2)));
}

"""+anchor,1)
anchor=" AddMoney(&gSaveBlock1Ptr->money,\n          floor+1==Ascension_FloorCount(rank) ? (1500 + rank*200) : (350 + rank*55 + floor*80));"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n Ascension_RememberClearedFloor(rank,floor+1);",1)
anchor="    VarSet(VAR_ASCENSION_FLOOR,0); // loss resets this run, not rank/unlocks"
assert s.count(anchor)==1
s=s.replace(anchor,
    "    Ascension_RememberClearedFloor(VarGet(VAR_ASCENSION_RANK),VarGet(VAR_ASCENSION_FLOOR));\n"+anchor,1)
anchor="    u16 floor=VarGet(VAR_ASCENSION_FLOOR);\n    if(completed>ASCENSION_COMPLETE)"
assert s.count(anchor)==1
s=s.replace(anchor,
    "    u16 floor=VarGet(VAR_ASCENSION_FLOOR);\n    u16 milestones=VarGet(VAR_ASCENSION_RECRUIT_MILESTONES);\n    if(completed>ASCENSION_COMPLETE)",1)
anchor="if(floor < 1+(part-2)/2)continue;"
assert s.count(anchor)==1
s=s.replace(anchor,
    "if(((milestones>>(rank*2))&3)<1+(part-2)/2\n                   && floor<1+(part-2)/2)continue;",1)
career.write_text(s)
assert "Ascension_RememberClearedFloor(rank,floor+1);" in s
assert "VAR_ASCENSION_RECRUIT_MILESTONES" in header.read_text()
print("V9 preserved earned milestone rewards: eight saved unlock counters survive loss; legendary pairs require full boss clear.")
