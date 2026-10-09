#!/usr/bin/env python3
"""V10 Masters Circuit: eight post-Champion six-Pokemon trainer rounds, 18
permanent first-clear licenses, stricter one-checkpoint recovery, and remixes.

Uses original animated 187-species renderer, native trainer-party Arena and
the existing Summit tournament room; no additional oversized sprite pack.
Release certification still needs full emulator/Delta playthrough.
"""
from pathlib import Path
import json,sys

root=Path(sys.argv[1]);maps=root/"data/maps"
career=root/"src/ascension_career.c"
vars_h=root/"include/constants/vars.h"
flags_h=root/"include/constants/flags.h"
specials=root/"data/specials.inc"

def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{label}: expected one anchor, found {n}: {a[:90]!r}")
    return s.replace(a,b,1)

exclusive=("SHEDINJA","NINCADA","WAILORD","WAILMER","SHARPEDO","CARVANHA",
           "CACTURNE","CRADILY","SOLROCK","CRAWDAUNT","CORPHISH",
           "NIDOKING","NIDOQUEEN","EXEGGUTOR","KECLEON","SABLEYE","KINGLER","STARMIE")
assert len(exclusive)==len(set(exclusive))==18
teams=[
 ("PHANTOM TRICKSTERS",("KECLEON","NINCADA","SABLEYE","ABSOL","GENGAR","SHEDINJA")),
 ("TIDAL GIANTS",("WAILMER","CARVANHA","KINGLER","MILOTIC","STARMIE","WAILORD")),
 ("DESERT ROYALTY",("CRADILY","SOLROCK","CACTURNE","SANDSLASH","NIDOQUEEN","NIDOKING")),
 ("ABYSSAL RULERS",("CORPHISH","KINGLER","CARVANHA","GYARADOS","SHARPEDO","CRAWDAUNT")),
 ("WILD EMPRESS",("KECLEON","SABLEYE","SOLROCK","GARDEVOIR","NIDOKING","NIDOQUEEN")),
 ("COSMIC VEIL",("CRADILY","SABLEYE","ALAKAZAM","SLOWBRO","RAYQUAZA","STARMIE")),
 ("STORM PREDATORS",("WAILORD","WAILMER","STARMIE","KINGLER","LUGIA","SHARPEDO")),
 ("ASCENSION FINAL",("NINCADA","SHEDINJA","NIDOKING","NIDOQUEEN","EXEGGUTOR","RAYQUAZA")),
]
assert len(teams)==8 and all(len(a)==6 for _,a in teams)
# Four Original-Arena-supported moves each. No unsupported art/physics.
moves={
 "SHEDINJA":"SHADOW_BALL FAINT_ATTACK QUICK_ATTACK PROTECT",
 "NINCADA":"SCRATCH DIG QUICK_ATTACK PROTECT",
 "WAILORD":"SURF HYDRO_PUMP BODY_SLAM PROTECT",
 "WAILMER":"WATER_GUN SURF BODY_SLAM PROTECT",
 "SHARPEDO":"BITE SURF SLASH PROTECT",
 "CARVANHA":"BITE WATER_GUN SLASH PROTECT",
 "CACTURNE":"FAINT_ATTACK GIGA_DRAIN SOLAR_BEAM PROTECT",
 "CRADILY":"ROCK_SLIDE GIGA_DRAIN ACID PROTECT",
 "SOLROCK":"PSYCHIC ROCK_SLIDE REFLECT PROTECT",
 "CRAWDAUNT":"CRABHAMMER BITE SLASH PROTECT",
 "CORPHISH":"CRABHAMMER WATER_GUN BITE PROTECT",
 "NIDOKING":"DIG ROCK_SLIDE SLASH PROTECT",
 "NIDOQUEEN":"DIG ROCK_SLIDE BODY_SLAM PROTECT",
 "EXEGGUTOR":"PSYCHIC SOLAR_BEAM GIGA_DRAIN PROTECT",
 "KECLEON":"SLASH SHADOW_BALL SWIFT PROTECT",
 "SABLEYE":"SHADOW_BALL FAINT_ATTACK ASTONISH PROTECT",
 "KINGLER":"CRABHAMMER SURF SLASH PROTECT",
 "STARMIE":"PSYCHIC SURF SWIFT PROTECT",
 "ABSOL":"SLASH FAINT_ATTACK QUICK_ATTACK PROTECT",
 "GENGAR":"SHADOW_BALL NIGHT_SHADE PSYCHIC PROTECT",
 "MILOTIC":"SURF HYDRO_PUMP AURORA_BEAM PROTECT",
 "SANDSLASH":"SCRATCH SLASH DIG SAND_ATTACK",
 "GARDEVOIR":"PSYCHIC SWIFT REFLECT PROTECT",
 "ALAKAZAM":"PSYCHIC SWIFT REFLECT PROTECT",
 "SLOWBRO":"PSYCHIC SURF WATER_GUN PROTECT",
 "RAYQUAZA":"DRAGON_CLAW DRAGON_BREATH HYPER_BEAM PROTECT",
 "GYARADOS":"BITE HYDRO_PUMP DRAGON_BREATH PROTECT",
 "LUGIA":"AEROBLAST GUST SWIFT PROTECT",
}
roster={x["species"] for x in json.loads((root/"tools/arena/roster.json").read_text())}
assert set(exclusive)<=roster
used=set(p for _,group in teams for p in group)
assert used<=roster and used<=set(moves)
source_moves=(root/"src/arena_moves.c").read_text()
for species in used:
    four=moves[species].split()
    assert len(four)==4
    for move in four:
        assert "{MOVE_"+move+"," in source_moves,(species,move)
# Recruitment licenses cannot duplicate the 169 in the base career.
pool=(root/"src/ascension_career.c").read_text()
prize_region=pool[pool.index("sTowerPrizes[ASCENSION_TOWER_COUNT][8]"):pool.index("sTowerRewardMoveProfiles")]
starter_region=pool[pool.index("sAscensionStarterPool[]"):pool.index("sAscensionStarterMoves")]
champ_region=pool[pool.index("sChampionRewards[5][5]"):pool.index("sChampionRewardMoves")]
for p in exclusive:
    assert "SPECIES_"+p not in prize_region+starter_region+champ_region,p

def cmon(p):
    return "{SPECIES_"+p+",{"+", ".join("MOVE_"+m for m in moves[p].split())+"}}"
team_data=",\n".join("    {\n"+",\n".join("        "+cmon(p) for p in mons)+"\n    }" for name,mons in teams)
reward_species=", ".join("SPECIES_"+p for p in exclusive)
reward_moves=",\n".join("    {"+", ".join("MOVE_"+m for m in moves[p].split())+"}" for p in exclusive)

v=vars_h.read_text()
v=once(v,"#define VAR_UNUSED_0x40E5",
    "#define VAR_ASCENSION_MASTERS_STAGE              0x40E5 // active 0..8\n//#define VAR_UNUSED_0x40E5",
    "persistent Masters active stage")
v=once(v,"#define VAR_UNUSED_0x40DB",
    "#define VAR_ASCENSION_MASTERS_BEST               0x40DB // highest floor won\n//#define VAR_UNUSED_0x40DB",
    "persistent Masters reward ceiling")
vars_h.write_text(v)
f=flags_h.read_text()
f=once(f,"#define FLAG_UNUSED_0x4C0",
    "#define FLAG_ASCENSION_MASTERS_PRIZE_FIRST    0x4C0 // 18 separate one-time claims\n//#define FLAG_UNUSED_0x4C0",
    "18 Masters one-time reward flags")
flags_h.write_text(f)

s=career.read_text()
s+="""

// Post-World-Champion circuit: original Arena engine and 1 active per side.
static const struct AscensionThemedMon sMastersTrainerTeams[8][6]=
{
"""+team_data+"""
};
static const u16 sMastersRewards[18]={"""+reward_species+"""};
static const u16 sMastersRewardMoves[18][MAX_MON_MOVES]={
"""+reward_moves+"""
};

void Ascension_MastersStart(void)
{
    if(VarGet(VAR_ASCENSION_RANK)!=ASCENSION_COMPLETE)
    {
        gSpecialVar_Result=0;return;
    }
    if(VarGet(VAR_ASCENSION_MASTERS_STAGE)>=8)
        VarSet(VAR_ASCENSION_MASTERS_STAGE,0); // replay after first clear
    gSpecialVar_Result=1;
}
void Ascension_MastersNextChallengerSprite(void)
{
    static const u16 ids[8]={
        TRAINER_NORMAN_1,TRAINER_JUAN_1,TRAINER_STEVEN,
        TRAINER_BRAWLY_1,TRAINER_WINONA_1,TRAINER_WALLACE,
        TRAINER_WATTSON_1,TRAINER_STEVEN
    };
    static const u16 gfx[8]={
        OBJ_EVENT_GFX_NORMAN,OBJ_EVENT_GFX_JUAN,OBJ_EVENT_GFX_STEVEN,
        OBJ_EVENT_GFX_BRAWLY,OBJ_EVENT_GFX_WINONA,OBJ_EVENT_GFX_WALLACE,
        OBJ_EVENT_GFX_WATTSON,OBJ_EVENT_GFX_STEVEN
    };
    u16 stage=VarGet(VAR_ASCENSION_MASTERS_STAGE);
    if(stage>7)stage=7;
    VarSet(VAR_OBJ_GFX_ID_0,gfx[stage]);
    gTrainerBattleOpponent_A=ids[stage];
}
void Ascension_PrepareMastersChallenge(void)
{
    u16 stage=VarGet(VAR_ASCENSION_MASTERS_STAGE);
    u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
    u8 mon,slot;
    if(VarGet(VAR_ASCENSION_RANK)!=ASCENSION_COMPLETE||stage>=8)
    {
        gSpecialVar_Result=0;return;
    }
    for(mon=0;mon<6;mon++)
    {
        const struct AscensionThemedMon *op;
        u8 pick=mon==5?5:(mon+cycle+stage)%5;
        u8 level=68+stage+(mon==5?1:0);
        op=&sMastersTrainerTeams[stage][pick];
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
}
void Ascension_RecordMastersVictory(void)
{
    u16 stage=VarGet(VAR_ASCENSION_MASTERS_STAGE);
    if(VarGet(VAR_ASCENSION_RANK)!=ASCENSION_COMPLETE || stage>=8)
    {
        gSpecialVar_Result=0;return;
    }
    AddMoney(&gSaveBlock1Ptr->money,800+stage*180);
    stage++;
    VarSet(VAR_ASCENSION_MASTERS_STAGE,stage);
    if(stage>VarGet(VAR_ASCENSION_MASTERS_BEST))
        VarSet(VAR_ASCENSION_MASTERS_BEST,stage);
    gSpecialVar_Result=(stage==8)?3:1;
}
void Ascension_RecordMastersDefeat(void)
{
    Ascension_RecordDefeat(); // exactly one capped 10% fine
    VarSet(VAR_ASCENSION_MASTERS_STAGE,0);
}
void Ascension_ClaimMastersRewards(void)
{
    struct Pokemon mon;
    u8 i,slot,given=0;
    u16 best=VarGet(VAR_ASCENSION_MASTERS_BEST);
    if(best>8)best=8;
    for(i=0;i<18;i++)
    {
        u8 req=i<14 ? i/2+1 : 8;
        u16 flag=FLAG_ASCENSION_MASTERS_PRIZE_FIRST+i;
        if(best<req || FlagGet(flag))continue;
        CreateMon(&mon,sMastersRewards[i],67,
                  USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
        for(slot=0;slot<MAX_MON_MOVES;slot++)
            SetMonMoveSlot(&mon,sMastersRewardMoves[i][slot],slot);
        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)
        {
            gSpecialVar_Result=given;return;
        }
        FlagSet(flag);
        given++;
    }
    gSpecialVar_Result=given;
}
"""
career.write_text(s)
specials_file=specials.read_text()
specials_file=once(specials_file,"\tdef_special Ascension_ClaimChampionRewards",
    "\tdef_special Ascension_ClaimChampionRewards\n"
    "\tdef_special Ascension_MastersStart\n"
    "\tdef_special Ascension_MastersNextChallengerSprite\n"
    "\tdef_special Ascension_PrepareMastersChallenge\n"
    "\tdef_special Ascension_RecordMastersVictory\n"
    "\tdef_special Ascension_RecordMastersDefeat\n"
    "\tdef_special Ascension_ClaimMastersRewards", "seven new native Masters specials")
specials.write_text(specials_file)

lab=maps/"AscensionTeamLab/scripts.inc"
p=lab.read_text()
p=once(p,"AscensionTeamLab_EventScript_NoChampionRewards::",
  """AscensionTeamLab_EventScript_NoChampionRewards::
 special Ascension_ClaimMastersRewards
 goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoMastersRewards
 msgbox AscensionTeamLab_Text_MastersPrizes, MSGBOX_DEFAULT
AscensionTeamLab_EventScript_NoMastersRewards::""",
  "Lab grants Masters after Champion")
p+="\nAscensionTeamLab_Text_MastersPrizes:\n\t.string \"MASTERS licenses earned!\\nClaimed to your party or BOX.$\"\n"
lab.write_text(p)

summit=maps/"AscensionSummit/scripts.inc"
p=summit.read_text()
p=once(p,
  "AscensionSummit_EventScript_Master::\n lockall\n faceplayer\n",
  "AscensionSummit_EventScript_Master::\n lockall\n faceplayer\n"
  " compare VAR_ASCENSION_RANK, 9\n"
  " goto_if_eq AscensionSummit_EventScript_MastersOffer\n",
  "unlock post-Champion Circuit through existing Summit Master")
p+="""

// A separate post-Champion tournament, not fake repeat Champion matches.
AscensionSummit_EventScript_MastersOffer::
 msgbox AscensionSummit_Text_MastersIntro, MSGBOX_DEFAULT
 msgbox AscensionSummit_Text_MastersReady, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionSummit_EventScript_End
 special Ascension_MastersStart
 goto_if_eq VAR_RESULT, 0, AscensionSummit_EventScript_End
 closemessage
 applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, AscensionSummit_Move_MasterAside
 removeobject LOCALID_TOWER_BATTLE_ATTENDANT_1
 applywaitmovement LOCALID_PLAYER, AscensionSummit_Move_PlayerAdvance
AscensionSummit_EventScript_MastersNext::
 special Ascension_MastersNextChallengerSprite
 clearflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 addobject LOCALID_TOWER_BATTLE_OPPONENT
 applywaitmovement LOCALID_TOWER_BATTLE_OPPONENT, AscensionSummit_Move_ChallengerEnter
 msgbox AscensionSummit_Text_MastersChallenger, MSGBOX_DEFAULT
 closemessage
 special Ascension_PrepareMastersChallenge
 goto_if_eq VAR_RESULT, 0, AscensionSummit_EventScript_MastersComplete
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, AscensionSummit_EventScript_MastersLost
 msgbox AscensionSummit_Text_MastersWin, MSGBOX_DEFAULT
 applywaitmovement LOCALID_TOWER_BATTLE_OPPONENT, AscensionSummit_Move_ChallengerExit
 removeobject LOCALID_TOWER_BATTLE_OPPONENT
 setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 special Ascension_RecordMastersVictory
 goto_if_ne VAR_RESULT, 1, AscensionSummit_EventScript_MastersComplete
 compare VAR_ASCENSION_MASTERS_STAGE, 4
 goto_if_eq AscensionSummit_EventScript_MastersHeal
 goto AscensionSummit_EventScript_MastersNext
AscensionSummit_EventScript_MastersHeal::
 msgbox AscensionSummit_Text_MastersHeal, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionSummit_EventScript_MastersNext
 special HealPlayerParty
 goto AscensionSummit_EventScript_MastersNext
AscensionSummit_EventScript_MastersLost::
 special Ascension_RecordMastersDefeat
 msgbox AscensionSummit_Text_MastersLost, MSGBOX_DEFAULT
 special HealPlayerParty
 warp MAP_ASCENSION_CITY_EAST, 35, 13
 waitstate
 end
AscensionSummit_EventScript_MastersComplete::
 msgbox AscensionSummit_Text_MastersComplete, MSGBOX_DEFAULT
 warp MAP_ASCENSION_CITY_EAST, 35, 13
 waitstate
 end
AscensionSummit_Text_MastersIntro:
 .string "MASTERS CIRCUIT!\\nEight elite six-POKEMON bouts.$"
AscensionSummit_Text_MastersReady:
 .string "Recovery only after ROUND 4.\\nChallenge the Masters?$"
AscensionSummit_Text_MastersChallenger:
 .string "A MASTER approaches!\\nExpect remixed strategies.$"
AscensionSummit_Text_MastersWin:
 .string "MASTER defeated!\\nYou earned new licenses.$"
AscensionSummit_Text_MastersHeal:
 .string "MID-CIRCUIT RECOVERY!\\nFully heal your team now?$"
AscensionSummit_Text_MastersLost:
 .string "The MASTERS stopped you.\\nRetry from round one.$"
AscensionSummit_Text_MastersComplete:
 .string "MASTERS CIRCUIT CLEARED!\\nClaim 18 licenses at the LAB.$"
"""
summit.write_text(p)
assert len(exclusive)==18
print("V10 MASTERS SOURCE: 8 original Arena native six-Pokemon rounds, stricter midpoint heal, capped loss fees, best-clear persistence, 18 unique permanent Pokemon, replay unlocked after World Champion.")
