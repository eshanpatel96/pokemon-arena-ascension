#!/usr/bin/env python3
"""V8 experimental: native sequential trainer parties in Bronze Tower.

The native Emerald Arena real-time engine supports BATTLE_TYPE_TRAINER and
normal party replacement. This bridge is intentionally used ONLY for Bronze,
with other towers retaining the proven wild battle path until phone-tested.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
career=root/"src/ascension_career.c"
main=root/"src/battle_main.c"
setup=root/"src/battle_setup.c"
def one(path,before,after):
    s=path.read_text()
    count=s.count(before)
    if count!=1: raise SystemExit(f"V8 Bronze: {path.name} anchor {before[:65]!r} matched {count} times")
    path.write_text(s.replace(before,after,1))

one(career,'#include "constants/items.h"',
           '#include "constants/items.h"\n#include "constants/opponents.h"')
one(career,'struct AscensionOpponent {u16 species, move1, move2; u8 level;};',
'''// Persistent for a single native trainer fight; cleared on returning to field.
EWRAM_DATA bool8 gAscensionTrainerPartyActive = FALSE;

struct AscensionTrainerMon
{
    u16 species;
    u16 moves[MAX_MON_MOVES];
};
static const struct AscensionTrainerMon sBronzeOpponents[3][4] =
{
    {
        {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_EMBER, MOVE_SLASH, MOVE_PROTECT}},
    },
    {
        {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_BLASTOISE, {MOVE_WATER_GUN, MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_PROTECT}},
        {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
    },
    {
        {SPECIES_CHARIZARD, {MOVE_FLAMETHROWER, MOVE_WING_ATTACK, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_BLASTOISE, {MOVE_WATER_GUN, MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_PROTECT}},
        {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_EMBER, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_DRAGONITE, {MOVE_WING_ATTACK, MOVE_SLAM, MOVE_DRAGON_BREATH, MOVE_AGILITY}},
    },
};
static const u8 sBronzeTeamSizes[3] = {2, 3, 4};

struct AscensionOpponent {u16 species, move1, move2; u8 level;};''')
old=''' if(i==gPlayerPartyCount)return;
 o=&sOpponents[rank][floor];'''
new=''' if(i==gPlayerPartyCount)return;
 gAscensionTrainerPartyActive = FALSE;
 if (rank == 0 && floor < ARRAY_COUNT(sBronzeTeamSizes))
 {
     u8 mon, slot, count = sBronzeTeamSizes[floor];
     for (mon = 0; mon < count; mon++)
     {
         const struct AscensionTrainerMon *op = &sBronzeOpponents[floor][mon];
         u8 level = 59 + floor + (mon == count - 1);
         if (mon == 0)
             CreateScriptedWildMon(op->species, level, ITEM_NONE);
         else
             CreateMon(&gEnemyParty[mon], op->species, level, USE_RANDOM_IVS,
                       FALSE, 0, OT_ID_PLAYER_ID, 0);
         for (slot = 0; slot < MAX_MON_MOVES; slot++)
             SetMonMoveSlot(&gEnemyParty[mon], op->moves[slot], slot);
     }
     // Native trainer intro, sendout and faint replacement state, using the
     // existing Brawly trainer artwork temporarily (not a new battle engine).
     gTrainerBattleOpponent_A = TRAINER_BRAWLY_1;
     gAscensionTrainerPartyActive = TRUE;
     gSpecialVar_Result = 1;
     return;
 }
 o=&sOpponents[rank][floor];'''
one(career,old,new)

# Start a standard scripted battle whose TYPE is trainer for the curated Bronze
# party. The native state machine then sends out all remaining enemy members.
one(setup,'void BattleSetup_StartScriptedWildBattle(void)\n{\n    LockPlayerFieldControls();\n    gMain.savedCallback = CB2_EndScriptedWildBattle;\n    gBattleTypeFlags = 0;',
'''extern bool8 gAscensionTrainerPartyActive;
void BattleSetup_StartScriptedWildBattle(void)
{
    LockPlayerFieldControls();
    gMain.savedCallback = CB2_EndScriptedWildBattle;
    gBattleTypeFlags = gAscensionTrainerPartyActive ? BATTLE_TYPE_TRAINER : 0;''')
one(setup,'static void CB2_EndScriptedWildBattle(void)\n{\n    CpuFill16',
          'static void CB2_EndScriptedWildBattle(void)\n{\n    gAscensionTrainerPartyActive = FALSE;\n    CpuFill16')
# battle_main.c originally replaces EVERY normal opponent trainer party with
# the static gTrainers table. Bronze provides its battle party dynamically;
# keep its Pokémon and avoid that replacement only for Bronze.
# Safe insertion of extern before the function definition, not its prototype.
old='''        CreateNPCTrainerParty(&gEnemyParty[0], gTrainerBattleOpponent_A, TRUE);
        if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)'''
new='''        if (!gAscensionTrainerPartyActive)
            CreateNPCTrainerParty(&gEnemyParty[0], gTrainerBattleOpponent_A, TRUE);
        if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)'''
one(main,old,new)
one(main,'#include "realtime_arena.h"',
         '#include "realtime_arena.h"\nextern bool8 gAscensionTrainerPartyActive;')
print("V8 Bronze: native 2/3/4-Pokemon opponent teams, intact real-time renderer, trainer-type switching enabled.")
