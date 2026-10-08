#!/usr/bin/env python3
"""V9 permanent tower milestone licenses, claimed safely through Professor.

Two species per tower, original animated roster only. A license is not a
duplicate awarded on every rematch; if PC is full it remains claimable later.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);maps=root/"data/maps"
flags=root/"include/constants/flags.h";f=flags.read_text()
assert f.count("#define FLAG_UNUSED_0x022")==1
flags.write_text(f.replace("#define FLAG_UNUSED_0x022",
                           "#define FLAG_ASCENSION_REWARD_FIRST"))
career=root/"src/ascension_career.c"
s=career.read_text()
s+="""

// First-clear tower prize species from the 187 existing animated set.
// Each individual prize is flagged only AFTER GiveMonToPlayer succeeds.
static const u16 sTowerPrizes[ASCENSION_TOWER_COUNT][2] =
{
    {SPECIES_REGIROCK, SPECIES_AGGRON},
    {SPECIES_LUGIA, SPECIES_DRAGONITE},
    {SPECIES_SUICUNE, SPECIES_SCEPTILE},
    {SPECIES_MEWTWO, SPECIES_GENGAR},
    {SPECIES_ENTEI, SPECIES_BLAZIKEN},
    {SPECIES_KYOGRE, SPECIES_SWAMPERT},
    {SPECIES_ZAPDOS, SPECIES_METAGROSS},
    {SPECIES_RAYQUAZA, SPECIES_SALAMENCE},
};

void Ascension_ClaimTowerRewards(void)
{
    struct Pokemon mon;
    u16 completed=VarGet(VAR_ASCENSION_RANK);
    u8 rank,part,granted=0;
    if(completed>ASCENSION_COMPLETE)completed=ASCENSION_COMPLETE;
    for(rank=0;rank<ASCENSION_TOWER_COUNT && rank<completed;rank++)
    {
        for(part=0;part<2;part++)
        {
            u16 flag=FLAG_ASCENSION_REWARD_FIRST + rank*2 + part;
            if(FlagGet(flag))continue;
            CreateMon(&mon,sTowerPrizes[rank][part],60,USE_RANDOM_IVS,
                      FALSE,0,OT_ID_PLAYER_ID,0);
            // Curated baseline, original Arena actions; Move Studio will allow
            // specialized learnsets later. Do not force unsupported classics.
            SetMonMoveSlot(&mon,MOVE_TACKLE,0);
            SetMonMoveSlot(&mon,MOVE_SWIFT,1);
            SetMonMoveSlot(&mon,MOVE_PROTECT,2);
            SetMonMoveSlot(&mon,MOVE_QUICK_ATTACK,3);
            if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)
            {
                gSpecialVar_Result=granted;
                return;
            }
            FlagSet(flag);
            granted++;
        }
    }
    gSpecialVar_Result=granted;
}
"""
# Some species can't learn generic moves naturally; all four profiles exist in
# native Emerald Arena. We'll replace these as we build 187 legal loadouts.
career.write_text(s)
specials=root/"data/specials.inc"
v=specials.read_text()
needle="\tdef_special Ascension_RegisterStarterRoster"
assert v.count(needle)==1
specials.write_text(v.replace(needle,needle+"\n\tdef_special Ascension_ClaimTowerRewards"))
prof=maps/"AscensionTeamLab/scripts.inc"
v=prof.read_text()
needle=" msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT\n"
assert v.count(needle)==1
v=v.replace(needle,needle+""" special Ascension_ClaimTowerRewards
 goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoNewRewards
 msgbox AscensionTeamLab_Text_TowerRewards, MSGBOX_DEFAULT
AscensionTeamLab_EventScript_NoNewRewards::
""")
v+="\nAscensionTeamLab_Text_TowerRewards:\n\t.string \"Your earned tower POKEMON are\\nregistered in your BOXES!$\"\n"
prof.write_text(v)
print("V9: 8 boss first-clears grant 16 permanent individual species licenses. Professor Birch claims into PC/party; full PC remains claimable.")
