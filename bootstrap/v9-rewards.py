#!/usr/bin/env python3
"""V9 permanent tower milestone licenses, claimed safely through Professor.

Eight species per tower, original animated roster only. A license is not a
duplicate awarded on every rematch; if PC is full it remains claimable later.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);maps=root/"data/maps"
flags=root/"include/constants/flags.h";f=flags.read_text()
assert f.count("#define FLAG_UNUSED_0x264")==1
flags.write_text(f.replace("#define FLAG_UNUSED_0x264",
                           "#define FLAG_ASCENSION_REWARD_FIRST"))
career=root/"src/ascension_career.c"
s=career.read_text()
s+="""

// First-clear tower prize species from the 187 existing animated set.
// Each individual prize is flagged only AFTER GiveMonToPlayer succeeds.
static const u16 sTowerPrizes[ASCENSION_TOWER_COUNT][8] =
{
    {SPECIES_REGIROCK, SPECIES_AGGRON, SPECIES_ARON, SPECIES_LAIRON, SPECIES_GOLEM, SPECIES_GRAVELER, SPECIES_GEODUDE, SPECIES_RHYDON},
    {SPECIES_LUGIA, SPECIES_DRAGONITE, SPECIES_PIDGEOT, SPECIES_TAILLOW, SPECIES_SWELLOW, SPECIES_WINGULL, SPECIES_PELIPPER, SPECIES_ALTARIA},
    {SPECIES_SUICUNE, SPECIES_SCEPTILE, SPECIES_TREECKO, SPECIES_GROVYLE, SPECIES_ROSELIA, SPECIES_VILEPLUME, SPECIES_ODDISH, SPECIES_GLOOM},
    {SPECIES_MEWTWO, SPECIES_GENGAR, SPECIES_GASTLY, SPECIES_HAUNTER, SPECIES_SHUPPET, SPECIES_BANETTE, SPECIES_DUSKULL, SPECIES_DUSCLOPS},
    {SPECIES_ENTEI, SPECIES_BLAZIKEN, SPECIES_TORCHIC, SPECIES_COMBUSKEN, SPECIES_TORKOAL, SPECIES_NUMEL, SPECIES_CAMERUPT, SPECIES_MAGMAR},
    {SPECIES_KYOGRE, SPECIES_SWAMPERT, SPECIES_MUDKIP, SPECIES_MARSHTOMP, SPECIES_KINGDRA, SPECIES_MILOTIC, SPECIES_SEALEO, SPECIES_WALREIN},
    {SPECIES_ZAPDOS, SPECIES_METAGROSS, SPECIES_PIKACHU, SPECIES_RAICHU, SPECIES_ELECTRIKE, SPECIES_MANECTRIC, SPECIES_PLUSLE, SPECIES_MINUN},
    {SPECIES_RAYQUAZA, SPECIES_SALAMENCE, SPECIES_SHELGON, SPECIES_FLYGON, SPECIES_TRAPINCH, SPECIES_GARDEVOIR, SPECIES_KIRLIA, SPECIES_RALTS},
};
static const u16 sTowerRewardMoveProfiles[ASCENSION_TOWER_COUNT][MAX_MON_MOVES] =
{
    {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT},
    {MOVE_WING_ATTACK, MOVE_GUST, MOVE_DRAGON_BREATH, MOVE_PROTECT},
    {MOVE_LEAF_BLADE, MOVE_GIGA_DRAIN, MOVE_QUICK_ATTACK, MOVE_PROTECT},
    {MOVE_SHADOW_BALL, MOVE_NIGHT_SHADE, MOVE_PSYCHIC, MOVE_PROTECT},
    {MOVE_FLAMETHROWER, MOVE_FIRE_BLAST, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_WATER_GUN, MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_PROTECT},
    {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_QUICK_ATTACK, MOVE_PROTECT},
    {MOVE_DRAGON_BREATH, MOVE_DRAGON_CLAW, MOVE_SWIFT, MOVE_PROTECT},
};

void Ascension_ClaimTowerRewards(void)
{
    struct Pokemon mon;
    u16 completed=VarGet(VAR_ASCENSION_RANK);
    u8 rank,part,slot,granted=0;
    u16 floor=VarGet(VAR_ASCENSION_FLOOR);
    if(completed>ASCENSION_COMPLETE)completed=ASCENSION_COMPLETE;
    for(rank=0;rank<ASCENSION_TOWER_COUNT && rank<=completed;rank++)
    {
        for(part=0;part<8;part++)
        {
            u16 flag=FLAG_ASCENSION_REWARD_FIRST + rank*8 + part;
            // Two themed recruit licenses after each ordinary floor;
            // boss finishes remaining 4 including the legendary + partner.
            if(rank==completed && !(
                 ((part==2 || part==3) && floor>=1)
                 || ((part==4 || part==5) && floor>=2)))
                continue;
            if(FlagGet(flag))continue;
            CreateMon(&mon,sTowerPrizes[rank][part],60,USE_RANDOM_IVS,
                      FALSE,0,OT_ID_PLAYER_ID,0);
            // Curated baseline, original Arena actions; Move Studio will allow
            // specialized learnsets later. Do not force unsupported classics.
            for(slot=0;slot<MAX_MON_MOVES;slot++)
                SetMonMoveSlot(&mon,sTowerRewardMoveProfiles[rank][slot],slot);
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
print("V9: 8 tower progress tracks 64 permanent species licenses (2 per ordinary floor, 4 on boss clear). Professor Birch claims into PC/party; full PC remains claimable.")
