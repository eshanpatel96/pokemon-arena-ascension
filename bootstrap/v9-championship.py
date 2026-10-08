#!/usr/bin/env python3
"""V9 Championship Tower: four real six-Pokemon Elite teams plus World Champion.

Reuses the pinned Emerald Arena 0.13.0 renderer, existing Summit foyer and
native Championship leader room. All five battles have six sequential enemy
Pokemon with the signature legendary LAST, varied supported real-time moves,
named trainer sprites, gated permanent Lab rewards and explicit healing after
rounds II and IV. Full map/battlefield acceptance still requires Delta QA.
"""
from pathlib import Path
import json
import re
import sys

root=Path(sys.argv[1]);maps=root/"data/maps"
career=root/"src/ascension_career.c"
header=root/"include/constants/vars.h"
flags=root/"include/constants/flags.h"
specials=root/"data/specials.inc"
lab=maps/"AscensionTeamLab/scripts.inc"

def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: expected one match; found {n}: {old[:100]!r}")
    return s.replace(old,new,1)

# Per-trainer six-member lineups, all existing animated 0.13.0 species.
championship=[
 ("ARCTIC",("WALREIN","DEWGONG","LAPRAS","GLALIE","CLOYSTER","ARTICUNO")),
 ("IRON",("MAGNETON","SKARMORY","METAGROSS","SCIZOR","ARMALDO","REGISTEEL")),
 ("LIGHTNING",("NINJASK","SANDSLASH","ELECTABUZZ","CROBAT","MANECTRIC","RAIKOU")),
 ("CRYSTAL",("CLAYDOL","SLOWBRO","GARDEVOIR","ALAKAZAM","JYNX","REGICE")),
 ("CHAMPION",("MACHAMP","ABSOL","GYARADOS","SLAKING","RAYQUAZA","HO_OH"))
]
# Correct permanent licenses: legendary + four thematic partners per round.
prizes=[
 ("ARTICUNO","GLALIE","SPHEAL","DEWGONG","CLOYSTER"),
 ("REGISTEEL","SKARMORY","SCIZOR","MAGNETON","ARMALDO"),
 ("RAIKOU","ELECTABUZZ","NINJASK","SANDSLASH","CROBAT"),
 ("REGICE","ALAKAZAM","JYNX","SLOWBRO","CLAYDOL"),
 ("HO_OH","SLAKING","ABSOL","GYARADOS","MACHAMP"),
]
# Four real-time-supported native moves for each Championship combatant.
profiles={
 "ARTICUNO":"AURORA_BEAM BLIZZARD GUST PROTECT",
 "REGISTEEL":"METEOR_MASH ROCK_SLIDE BODY_SLAM PROTECT",
 "RAIKOU":"THUNDER_SHOCK SHOCK_WAVE QUICK_ATTACK PROTECT",
 "REGICE":"BLIZZARD AURORA_BEAM BODY_SLAM PROTECT",
 "HO_OH":"SACRED_FIRE AERIAL_ACE FIRE_BLAST PROTECT",
 "WALREIN":"AURORA_BEAM SURF BODY_SLAM PROTECT",
 "DEWGONG":"SURF AURORA_BEAM BODY_SLAM PROTECT",
 "LAPRAS":"SURF AURORA_BEAM BODY_SLAM PROTECT",
 "GLALIE":"BLIZZARD BITE AURORA_BEAM PROTECT",
 "CLOYSTER":"BLIZZARD SURF AURORA_BEAM PROTECT",
 "SPHEAL":"WATER_GUN AURORA_BEAM BODY_SLAM PROTECT",
 "MAGNETON":"SHOCK_WAVE THUNDER_SHOCK SCREECH PROTECT",
 "SKARMORY":"WING_ATTACK AERIAL_ACE SLASH PROTECT",
 "METAGROSS":"METEOR_MASH PSYCHIC BODY_SLAM PROTECT",
 "SCIZOR":"QUICK_ATTACK SLASH DOUBLE_TEAM PROTECT",
 "ARMALDO":"ROCK_SLIDE ROCK_TOMB SLASH PROTECT",
 "NINJASK":"QUICK_ATTACK WING_ATTACK DOUBLE_TEAM PROTECT",
 "SANDSLASH":"SCRATCH SLASH DIG SAND_ATTACK",
 "ELECTABUZZ":"THUNDER_SHOCK SHOCK_WAVE SWIFT PROTECT",
 "CROBAT":"WING_ATTACK AERIAL_ACE BITE PROTECT",
 "MANECTRIC":"THUNDER_SHOCK SHOCK_WAVE BITE PROTECT",
 "CLAYDOL":"PSYCHIC MUD_SHOT REFLECT PROTECT",
 "SLOWBRO":"PSYCHIC SURF WATER_GUN PROTECT",
 "GARDEVOIR":"PSYCHIC SWIFT REFLECT PROTECT",
 "ALAKAZAM":"PSYCHIC SWIFT REFLECT PROTECT",
 "JYNX":"PSYCHIC BLIZZARD AURORA_BEAM PROTECT",
 "MACHAMP":"CROSS_CHOP MACH_PUNCH BODY_SLAM PROTECT",
 "ABSOL":"SLASH FAINT_ATTACK QUICK_ATTACK PROTECT",
 "GYARADOS":"BITE HYDRO_PUMP DRAGON_BREATH PROTECT",
 "SLAKING":"BODY_SLAM SLASH HEADBUTT PROTECT",
 "RAYQUAZA":"DRAGON_CLAW DRAGON_BREATH HYPER_BEAM PROTECT",
}
assert len(championship)==len(prizes)==5
assert all(len(x)==6 for _,x in championship)
assert all(len(x)==5 for x in prizes)
assert len({p for row in prizes for p in row})==25
assert {x[-1] for _,x in championship}=={"ARTICUNO","REGISTEEL","RAIKOU","REGICE","HO_OH"}
animated={entry["species"] for entry in json.loads((root/"tools/arena/roster.json").read_text())}
valid_moves=(root/"src/arena_moves.c").read_text()
for _,members in championship:
    for species in members:
        assert species in animated,species
        assert species in profiles,species
for rewards in prizes:
    for species in rewards:
        assert species in animated,species
        assert species in profiles,species
for species,moves in profiles.items():
    assert len(moves.split())==4,species
    for move in moves.split():
        if "{MOVE_"+move+"," not in valid_moves:
            raise RuntimeError(f"Unsupported real-time Arena profile: {species} / {move}")

def cmon(species):
    return "{SPECIES_"+species+", {"+", ".join("MOVE_"+x for x in profiles[species].split())+"}}"
team_rows=",\n".join(
    "    {\n"+",\n".join("        "+cmon(p) for p in members)+"\n    }"
    for _,members in championship)
reward_rows=",\n".join(
    "    {"+", ".join("SPECIES_"+p for p in row)+"}"
    for row in prizes)
reward_move_rows=",\n".join(
    "    {\n"+",\n".join("        {"+", ".join("MOVE_"+x for x in profiles[p].split())+"}"
                      for p in row)+"\n    }"
    for row in prizes)

# Native persistent save VAR 0x40F9: highest completed Championship round,
# independent of current stage (which resets to Elite I on a failed attempt).
h=header.read_text()
h=once(h,"#define VAR_UNUSED_0x40F9",
       "#define VAR_ASCENSION_CHAMPION_WINS                   0x40F9 // earned rounds 0..5\n//#define VAR_UNUSED_0x40F9",
       "champion victory persistence")
header.write_text(h)

# 24 contiguous unused flags + separately verified unused 0x2D9 = 25.
# The 64 prior tower prize flags occupy 0x264..0x2A3 and MUST NOT overlap.
f=flags.read_text()
f=once(f,"#define FLAG_UNUSED_0x2A4",
       "#define FLAG_ASCENSION_CHAMP_PRIZES_FIRST  0x2A4 // 24 native flags\n//#define FLAG_UNUSED_0x2A4",
       "first Championship flag")
f=once(f,"#define FLAG_UNUSED_0x2D9",
       "#define FLAG_ASCENSION_CHAMP_PRIZE_LAST    0x2D9 // final 25th native flag\n//#define FLAG_UNUSED_0x2D9",
       "25th Championship flag")
flags.write_text(f)

s=career.read_text()
p="static const struct AscensionThemedMon sThemePool[8][6] ="
assert p in s
s=s.replace(p,"""// Five mandatory Summit rounds: no extra sprites; native 1v1 send-outs.
static const struct AscensionThemedMon sChampionTeams[5][6]=
{
"""+team_rows+"""
};
static const u16 sChampionRewards[5][5]=
{
"""+reward_rows+"""
};
static const u16 sChampionRewardMoves[5][5][MAX_MON_MOVES]=
{
"""+reward_move_rows+"""
};

"""+p,1)

# The existing Move Studio must also recognize these earned Championship
# species, not only the old starter/tower sets. Keep native move data.
needle="    if(profile==NULL)return;"
assert s.count(needle)==1
s=s.replace(needle,"""    if(profile==NULL)
        for(i=0;i<5*5;i++)
            if(sChampionRewards[i/5][i%5]==species)
            {
                profile=sChampionRewardMoves[i/5][i%5];
                break;
            }
"""+needle,1)

# Match the visible challenger graphic, sideline photo and actual name.
needle="    u16 slot = floor+1==Ascension_FloorCount(rank) ? rank%ARRAY_COUNT(gfx) : next;"
assert s.count(needle)==1
s=s.replace(needle,"""    if(rank==ASCENSION_SUMMIT_INDEX)
    {
        static const u16 eliteTrainers[5]={
            TRAINER_WINONA_1,TRAINER_STEVEN,TRAINER_WATTSON_1,
            TRAINER_JUAN_1,TRAINER_WALLACE
        };
        static const u16 eliteGraphics[5]={
            OBJ_EVENT_GFX_WINONA,OBJ_EVENT_GFX_STEVEN,OBJ_EVENT_GFX_WATTSON,
            OBJ_EVENT_GFX_JUAN,OBJ_EVENT_GFX_WALLACE
        };
        u8 round=floor<5?floor:4;
        VarSet(VAR_ASCENSION_CHALLENGER_ROTATION,next);
        VarSet(VAR_OBJ_GFX_ID_0,eliteGraphics[round]);
        gTrainerBattleOpponent_A=eliteTrainers[round];
        return;
    }
"""+needle,1)

# IMPORTANT: this block comes before generic tier lookup and before the old
# Summit sThemePool path, so every Elite and World Champion uses six members.
needle=" if (rank > 0 && rank <= 8)"
assert s.count(needle)==1
new=""" if(rank==ASCENSION_SUMMIT_INDEX)
 {
     static const u16 eliteTrainers[5]={
         TRAINER_WINONA_1,TRAINER_STEVEN,TRAINER_WATTSON_1,
         TRAINER_JUAN_1,TRAINER_WALLACE
     };
     u8 mon,slot;
     u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE)%3;
     if(floor>=5)return;
     gTrainerBattleOpponent_A=eliteTrainers[floor];
     for(mon=0;mon<6;mon++)
     {
         const struct AscensionThemedMon *op;
         u8 pick=mon==5?5:(mon+cycle)%5;
         u8 level=64+floor*2+(mon==5?1:0);
         op=&sChampionTeams[floor][pick];
         if(mon==0)
             CreateScriptedWildMon(op->species,level,ITEM_NONE);
         else
             CreateMon(&gEnemyParty[mon],op->species,level,
                       USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
         for(slot=0;slot<MAX_MON_MOVES;slot++)
             SetMonMoveSlot(&gEnemyParty[mon],op->moves[slot],slot);
     }
     gAscensionTrainerPartyActive=TRUE;
     gSpecialVar_Result=1;
     return;
 }
"""
s=s.replace(needle,new+needle,1)

# Save first-clear eligibility BEFORE rank/floor increments. A loss does not
# delete previously earned licenses, only resets the current Summit attempt.
needle=" Ascension_RememberClearedFloor(rank,floor+1);"
assert s.count(needle)==1
s=s.replace(needle,needle+"""
 if(rank==ASCENSION_SUMMIT_INDEX
    && floor+1>VarGet(VAR_ASCENSION_CHAMPION_WINS))
     VarSet(VAR_ASCENSION_CHAMPION_WINS,floor+1);""",1)

# Actual per-species grants are safe across retries/full PC and saved only on
# GiveMonToPlayer success. Their native flag identities cannot overlap tower
# prizes or original game flags.
s+="""

// Claim 25 earned Championship POKEMON from the native Lab, five per round.
// All five are unique from the 80 starters, 64 ordinary tower rewards and the
// 18 reserved Masters species. A full box never erases a reward license.
void Ascension_ClaimChampionRewards(void)
{
    struct Pokemon mon;
    u8 r,p,slot,granted=0;
    u16 eligible=VarGet(VAR_ASCENSION_CHAMPION_WINS);
    if(eligible>5)eligible=5;
    for(r=0;r<eligible;r++)
    {
        for(p=0;p<5;p++)
        {
            u16 number=r*5+p;
            u16 flag=number==24 ? FLAG_ASCENSION_CHAMP_PRIZE_LAST
                                : FLAG_ASCENSION_CHAMP_PRIZES_FIRST+number;
            if(FlagGet(flag))continue;
            CreateMon(&mon,sChampionRewards[r][p],65,
                      USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
            for(slot=0;slot<MAX_MON_MOVES;slot++)
                SetMonMoveSlot(&mon,sChampionRewardMoves[r][p][slot],slot);
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
career.write_text(s)

sp=specials.read_text()
sp=once(sp,"\tdef_special Ascension_ClaimTowerRewards",
        "\tdef_special Ascension_ClaimTowerRewards\n\tdef_special Ascension_ClaimChampionRewards",
        "native Champion reward special")
specials.write_text(sp)

lab_script=lab.read_text()
needle=" special Ascension_ClaimTowerRewards\n goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoNewRewards\n msgbox AscensionTeamLab_Text_TowerRewards, MSGBOX_DEFAULT"
assert lab_script.count(needle)==1
lab_script=lab_script.replace(needle,needle+"""
AscensionTeamLab_EventScript_ChampionClaim::
 special Ascension_ClaimChampionRewards
 goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoChampionRewards
 msgbox AscensionTeamLab_Text_ChampionPrizes, MSGBOX_DEFAULT
AscensionTeamLab_EventScript_NoChampionRewards::""",1)
lab_script=once(lab_script,
    "goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoNewRewards",
    "goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_ChampionClaim",
    "Champion rewards still offered if no ordinary tower rewards pending")
lab_script+="\nAscensionTeamLab_Text_ChampionPrizes:\n\t.string \"ELITE rewards added to BOXES!\\nYour licenses are permanent.$\"\n"
lab.write_text(lab_script)

# Five announced stages, full healing after Elite II, and reset to beginning
# on any loss. The existing pre-final-full-heal in v9-leader-rooms.py provides
# the Elite IV -> Champion break.
summit=maps/"AscensionSummit/scripts.inc"
sc=summit.read_text()
needle=" msgbox AscensionSummit_Text_Next, MSGBOX_DEFAULT\n goto AscensionSummit_EventScript_NextOpponent\n"
assert sc.count(needle)==1,"Summit next-round choreography is missing"
sc=sc.replace(needle,""" compare VAR_ASCENSION_FLOOR, 2
 goto_if_eq AscensionSummit_EventScript_Elite2Heal
"""+needle+"""AscensionSummit_EventScript_Elite2Heal::
 msgbox AscensionSummit_Text_Elite2Heal, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionSummit_EventScript_NextOpponent
 special HealPlayerParty
 goto AscensionSummit_EventScript_NextOpponent
""",1)
sc+="\nAscensionSummit_Text_Elite2Heal:\n\t.string \"ELITE II CLEAR! FULL TEAM\\nrecovery before ELITE III?$\"\n"
needle="AscensionSummit_EventScript_Loss::\n special Ascension_RecordDefeat\n"
assert sc.count(needle)==1
sc=sc.replace(needle,needle+""" msgbox AscensionSummit_Text_Restart, MSGBOX_DEFAULT
 special HealPlayerParty
 warp MAP_ASCENSION_CITY_EAST, 35, 13
 waitstate
 end
""",1)
sc+="\nAscensionSummit_Text_Restart:\n\t.string \"CHAMPIONSHIP run ended.\\nNext attempt starts at ELITE I.$\"\n"
sc+="\nAscensionSummit_Text_Series:\n\t.string \"FIVE CHAMPIONSHIP BATTLES!\\nSix POKEMON per opponent.$\"\n"
sc=once(sc," msgbox AscensionSummit_Text_Ready, MSGBOX_YESNO",
        " msgbox AscensionSummit_Text_Series, MSGBOX_DEFAULT\n msgbox AscensionSummit_Text_Ready, MSGBOX_YESNO",
        "Championship foyer briefing")
sc=once(sc,"The Tower Master awaits!\\nStep into the final arena.",
        "WORLD CHAMPION HO-OH awaits!\\nYour final six-on-six fight.",
        "Champion warning")
# Introduce the Elite stages and World Champion during the native foyer flow.
sc=once(sc," msgbox AscensionSummit_Text_ChallengerIntro, MSGBOX_DEFAULT",
        " call AscensionSummit_EventScript_NamedRound",
        "five named Elite/Champion round briefings")
sc+="""
AscensionSummit_EventScript_NamedRound::
 compare VAR_ASCENSION_FLOOR, 0
 goto_if_eq AscensionSummit_EventScript_Arctic
 compare VAR_ASCENSION_FLOOR, 1
 goto_if_eq AscensionSummit_EventScript_Iron
 compare VAR_ASCENSION_FLOOR, 2
 goto_if_eq AscensionSummit_EventScript_Lightning
 compare VAR_ASCENSION_FLOOR, 3
 goto_if_eq AscensionSummit_EventScript_Crystal
 msgbox AscensionSummit_Text_ChampionIntro, MSGBOX_DEFAULT
 return
AscensionSummit_EventScript_Arctic::
 msgbox AscensionSummit_Text_ArcticIntro, MSGBOX_DEFAULT
 return
AscensionSummit_EventScript_Iron::
 msgbox AscensionSummit_Text_IronIntro, MSGBOX_DEFAULT
 return
AscensionSummit_EventScript_Lightning::
 msgbox AscensionSummit_Text_LightningIntro, MSGBOX_DEFAULT
 return
AscensionSummit_EventScript_Crystal::
 msgbox AscensionSummit_Text_CrystalIntro, MSGBOX_DEFAULT
 return
AscensionSummit_Text_ArcticIntro:
 .string "ELITE I: ARCTIC TEMPEST!\\nARTICUNO enters last.$"
AscensionSummit_Text_IronIntro:
 .string "ELITE II: IRON ARCHITECT!\\nREGISTEEL enters last.$"
AscensionSummit_Text_LightningIntro:
 .string "ELITE III: LIGHTNING!\\nRAIKOU enters last.$"
AscensionSummit_Text_CrystalIntro:
 .string "ELITE IV: CRYSTAL ORACLE!\\nREGICE enters last.$"
AscensionSummit_Text_ChampionIntro:
 .string "WORLD CHAMPION FINAL!\\nHO-OH enters last.$"
"""

summit.write_text(sc)

leader=maps/"AscensionLeader9/scripts.inc"
s=leader.read_text()
needle="AscensionLeader9_EventScript_Lost::\n special Ascension_RecordDefeat\n"
assert s.count(needle)==1
s=s.replace(needle,needle+""" msgbox AscensionLeader9_Text_Eliminated, MSGBOX_DEFAULT
 special HealPlayerParty
 warp MAP_ASCENSION_CITY_EAST, 35, 13
 waitstate
 end
""",1)
s+="\nAscensionLeader9_Text_Eliminated:\n\t.string \"HO-OH prevailed. Your next\\nrun restarts at ELITE I.$\"\n"
s=once(s,"AscensionLeader9_Text_Win:\n\t.string \"Outstanding! Record updated.\\nSee the Lab about rewards.$\"",
       "AscensionLeader9_Text_Win:\n\t.string \"WORLD CHAMPION! HO-OH won!\\nClaim your LAB licenses.$\"",
       "World Champion postgame recognition")
leader.write_text(s)

# Original native battle backgrounds provide five visually different existing
# stages without creating a second 32-MiB sprite/art pack.
biome=root/"src/arena_biomes.inc"
b=biome.read_text()
needle="case MAP_ASCENSION_SUMMIT: gArenaBiome=4;gArenaStage=7;break;"
assert b.count(needle)==1,"Summit native scene mapping absent"
b=b.replace(needle,"""case MAP_ASCENSION_SUMMIT:
        gArenaBiome=4;
        switch(VarGet(VAR_ASCENSION_FLOOR))
        {
        case 0:gArenaStage=13;break; // Arctic / open sky
        case 1:gArenaStage=12;break; // Iron / steel coliseum
        case 2:gArenaStage=10;break; // Lightning / electric gym
        case 3:gArenaStage=14;break; // Crystal / psychic chamber
        default:gArenaStage=7;break;
        }
        break;""",1)
biome.write_text(b)

guide=root/"data/ascension_guide.inc"
g=guide.read_text()
g=once(g,"9 CHAMPION SUMMIT - EAST","9 CHAMPION SUMMIT - EAST",
       "Summit guide anchor") if False else g
g=g.replace("9 CHAMPION SUMMIT - EAST\\nUse building signs and guides.",
            "9 ELITE + CHAMPION - EAST\\nFive rounds, no mid-run exit.")
guide.write_text(g)

print("V9 CHAMPIONSHIP SOURCE: Elite I Articuno, II Registeel, III Raikou, IV Regice, World Champion Ho-Oh; 5x6 animated native trainer parties, last-ace guarantees, native battle stages, II/IV heals, loss resets, 25 persistent Lab prizes.")
