#!/usr/bin/env python3
"""V9 eight-tower career depth: per-rank floor counts and boss routing.

Applies after bootstrap/v9-release-safety.py and before static preflight.
No new battle renderer, new art, or extra simultaneous battlers. Final
Championship floor count is a staging placeholder pending V10 Elite Four.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
maps=root/"data/maps"
header=root/"include/ascension_progress.h"
career=root/"src/ascension_career.c"
def one(s,old,new,what):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{what}: expected one source anchor, found {n}: {old[:110]!r}")
    return s.replace(old,new,1)
counts=[4,5,5,6,6,7,8,9,5]
h=header.read_text()
h=one(h,"#define ASCENSION_FLOORS_PER_TOWER 3",
"""#define ASCENSION_FLOORS_PER_TOWER 9 // bound, not a uniform progression
// Normal ranks 0..7: Bronze/Gale/Grass/Ghost/Fire/Water/Thunder/Astral.
// Rank 8 is a provisional five-stage Summit; V10 replaces its opponents
// with the full Elite Four / Champion tournament.
static inline unsigned Ascension_FloorCount(unsigned rank)
{
    static const unsigned char counts[9] = {4,5,5,6,6,7,8,9,5};
    return rank < 9 ? counts[rank] : 0;
}""","career count")
h=one(h,
"""static inline unsigned Ascension_NextRank(unsigned rank,unsigned floor)
{return floor+1 >= ASCENSION_FLOORS_PER_TOWER && rank<ASCENSION_COMPLETE ? rank+1 : rank;}
static inline unsigned Ascension_NextFloor(unsigned floor)
{return floor+1 >= ASCENSION_FLOORS_PER_TOWER ? 0 : floor+1;}
static inline unsigned Ascension_CanEnter(unsigned rank,unsigned floor)
{return rank<ASCENSION_COMPLETE && floor<ASCENSION_FLOORS_PER_TOWER;}""",
"""static inline unsigned Ascension_NextRank(unsigned rank,unsigned floor)
{return rank<ASCENSION_COMPLETE && floor+1 >= Ascension_FloorCount(rank) ? rank+1 : rank;}
static inline unsigned Ascension_NextFloor(unsigned rank,unsigned floor)
{return floor+1 >= Ascension_FloorCount(rank) ? 0 : floor+1;}
static inline unsigned Ascension_CanEnter(unsigned rank,unsigned floor)
{return rank<ASCENSION_COMPLETE && floor<Ascension_FloorCount(rank);}""","rank progression")
header.write_text(h)
c=career.read_text()
c=one(c,"if(floor>=ASCENSION_FLOORS_PER_TOWER)floor=0;",
      "if(floor>=Ascension_FloorCount(rank))floor=0;","HUD floor bounds")
c=one(c,"Ascension_NextFloor(floor)","Ascension_NextFloor(rank,floor)","victory floor progress")
c=one(c,"if (rank == 0 && floor < ARRAY_COUNT(sBronzeTeamSizes))",
      "if (rank == 0 && floor < Ascension_FloorCount(rank))","bronze floor expansion")
c=one(c,"u8 mon, slot, count = sBronzeTeamSizes[floor];",
"""u8 mon, slot, bronzePhase=(floor+1==Ascension_FloorCount(rank)) ? 2 : (floor==0 ? 0 : 1);
     u8 count = sBronzeTeamSizes[bronzePhase];""","bronze team size / final ace")
c=one(c,"&sBronzeRematchTeams[floor][VarGet(VAR_ASCENSION_REMATCH_CYCLE) % 3][mon]",
       "&sBronzeRematchTeams[bronzePhase][VarGet(VAR_ASCENSION_REMATCH_CYCLE) % 3][mon]",
       "bronze pool phase")
c=one(c,"if (floor == 2) gTrainerBattleOpponent_A = TRAINER_ROXANNE_1;",
      "if (floor+1 == Ascension_FloorCount(rank)) gTrainerBattleOpponent_A = TRAINER_ROXANNE_1;",
      "bronze leader actual sprite")
c=one(c,"u16 slot = floor==2 ? rank%ARRAY_COUNT(gfx) : next;",
      "u16 slot = floor+1==Ascension_FloorCount(rank) ? rank%ARRAY_COUNT(gfx) : next;",
      "tier-specific challenger preview")
c=one(c,
"count=floor==0 ? 2 : floor==1 ? 3 : rank==8 ? 6 : rank>=5 ? 5 : 4;",
"""count=floor==0 ? 2 : floor==1 ? 3
         : floor+1==Ascension_FloorCount(rank) ? (rank==8 ? 6 : rank>=5 ? 5 : 4)
         : (floor>=4 && rank>=5 ? 5 : 4);""",
"expanded arena trainer team counts")
c=one(c,"(floor==2 && mon==count-1)",
      "(floor+1==Ascension_FloorCount(rank) && mon==count-1)",
      "signature boss ace only on last floor")
c=one(c,"if(floor==2)\n     {",
      "if(floor+1==Ascension_FloorCount(rank))\n     {",
      "last-floor trainer leader selection")
c=one(c,"floor==2 ? (1500 + rank*200) : (350 + rank*55 + floor*125)",
      "floor+1==Ascension_FloorCount(rank) ? (1500 + rank*200) : (350 + rank*55 + floor*125)",
      "economy boss bonus")
career.write_text(c)
for idx,count in enumerate(counts):
    name="AscensionSummit" if idx==8 else f"AscensionTower{idx+1}"
    path=maps/name/"scripts.inc"
    s=path.read_text()
    # Advancing a floor counts ONLY after defeating an entire trainer team.
    # The final fight starts in its own boss room after N-1 victories.
    s=one(s," compare VAR_ASCENSION_FLOOR, 2\n",
          f" compare VAR_ASCENSION_FLOOR, {count-1}\n",
          f"{name} gate to boss")
    if idx>=4 and idx<8:
        # Later towers get a full voluntary mid-run recovery in addition to
        # the existing offered full boss preparation heal.
        floor_check=max(2,count//2)
        loop=f" msgbox {name}_Text_Next, MSGBOX_DEFAULT\n goto {name}_EventScript_NextOpponent\n"
        insert=f""" compare VAR_ASCENSION_FLOOR, {floor_check}
 goto_if_eq {name}_EventScript_MidRecovery
"""
        insert+=loop
        insert+=f"""{name}_EventScript_MidRecovery::
 msgbox {name}_Text_Recovery, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_NextOpponent
 special HealPlayerParty
 goto {name}_EventScript_NextOpponent
"""
        s=one(s,loop,insert,f"{name} mid-run recovery")
        s+=f'\n{name}_Text_Recovery:\n\t.string "Tower recovery point!\\nFully heal your party?$"\n'
    path.write_text(s)
# V9's reward milestones remain 2 after first floor, 2 after second,
# and final 4 on boss clear; the expanded floors award money and medals,
# never double a permanent species prize.
s=career.read_text()
assert 'Ascension_FloorCount(rank)' in s
assert "floor==2 ? (1500" not in s
assert 'sBronzeRematchTeams[bronzePhase]' in s
for idx,count in enumerate(counts):
    nm="AscensionSummit" if idx==8 else f"AscensionTower{idx+1}"
    assert f"compare VAR_ASCENSION_FLOOR, {count-1}" in (maps/nm/"scripts.inc").read_text()
print("V9 EXPANDED CAREER SOURCE PASS: Bronze 4, Gale 5, Verdant 5, Phantom 6, Inferno 6, Tidal 7, Thunder 8, Astral 9; 5 provisional Summit. Original real-time trainer parties preserved.")
