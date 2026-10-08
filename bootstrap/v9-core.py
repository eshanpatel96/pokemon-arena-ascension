#!/usr/bin/env python3
"""V9 foundation: real trainer parties in all nine venues, native identities,
actual battle-items-only Mart, free Professor squad service and money economy.

Applied AFTER v8-2-rematches.py. Changes do not invent a new battle renderer.
This is an experimental integration until save, faint and Delta tests pass.
"""
from pathlib import Path
import json, re, sys
root=Path(sys.argv[1]); maps=root/"data/maps"
career=root/"src/ascension_career.c"
scripts=root/"data/specials.inc"
def exactly(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f"{label}: expected 1 anchor, found {n}: {old[:120]!r}")
    return src.replace(old,new,1)
s=career.read_text()

# Existing Arena movement sprites and battle trainer photos were previously
# unrelated (Bronze always Brawly). A single deterministic trainer ID now
# controls both and must remain stable until opponent faint transitions finish.
old=re.search(r'void Ascension_NextChallengerSprite\(void\)\n\{.*?\n\}',s,re.S)
assert old, "V8 rotating challenger function missing"
new="""void Ascension_NextChallengerSprite(void)
{
    static const u16 trainers[] = {
        TRAINER_ROXANNE_1, TRAINER_BRAWLY_1, TRAINER_WATTSON_1,
        TRAINER_FLANNERY_1, TRAINER_NORMAN_1, TRAINER_WINONA_1,
        TRAINER_JUAN_1, TRAINER_STEVEN
    };
    static const u16 gfx[] = {
        OBJ_EVENT_GFX_ROXANNE, OBJ_EVENT_GFX_BRAWLY, OBJ_EVENT_GFX_WATTSON,
        OBJ_EVENT_GFX_FLANNERY, OBJ_EVENT_GFX_NORMAN, OBJ_EVENT_GFX_WINONA,
        OBJ_EVENT_GFX_JUAN, OBJ_EVENT_GFX_STEVEN
    };
    u16 rank = VarGet(VAR_ASCENSION_RANK);
    u16 floor = VarGet(VAR_ASCENSION_FLOOR);
    u16 next = (VarGet(VAR_ASCENSION_CHALLENGER_ROTATION)+1)%ARRAY_COUNT(gfx);
    u16 slot = floor==2 ? rank%ARRAY_COUNT(gfx) : next;
    VarSet(VAR_ASCENSION_CHALLENGER_ROTATION,next);
    VarSet(VAR_OBJ_GFX_ID_0,gfx[slot]);
    gTrainerBattleOpponent_A = trainers[slot];
}
"""
s=s[:old.start()]+new+s[old.end():]
s=exactly(s,"     gTrainerBattleOpponent_A = TRAINER_BRAWLY_1;\n",
          "     if (floor == 2) gTrainerBattleOpponent_A = TRAINER_ROXANNE_1;\n","remove static Brawly trainer")

# Expand the old three-member theme pool. First five entries are ordinary
# strong foes, final member is the signature legendary. All species already
# exist in the verified 187 animated source roster and moves have original
# Arena move profiles. No special Mega/Groudon/Tyranitar asset introduced.
pools=[
 [("PIDGEOT","GUST","WING_ATTACK","QUICK_ATTACK","PROTECT"),
  ("SWELLOW","WING_ATTACK","QUICK_ATTACK","AERIAL_ACE","DOUBLE_TEAM"),
  ("PELIPPER","WATER_GUN","GUST","WING_ATTACK","PROTECT"),
  ("ALTARIA","DRAGON_BREATH","PECK","GUST","PROTECT"),
  ("DRAGONITE","WING_ATTACK","DRAGON_BREATH","SLAM","AGILITY"),
  ("LUGIA","AEROBLAST","GUST","SWIFT","PROTECT")],
 [("GROVYLE","LEAF_BLADE","QUICK_ATTACK","SLAM","PROTECT"),
  ("SCEPTILE","LEAF_BLADE","QUICK_ATTACK","SLAM","PROTECT"),
  ("VILEPLUME","GIGA_DRAIN","ACID","SOLAR_BEAM","PROTECT"),
  ("SHIFTRY","FAINT_ATTACK","GIGA_DRAIN","GROWTH","PROTECT"),
  ("BRELOOM","MACH_PUNCH","MEGA_DRAIN","HEADBUTT","PROTECT"),
  ("SUICUNE","AURORA_BEAM","GUST","RAIN_DANCE","PROTECT")],
 [("BANETTE","SHADOW_BALL","ASTONISH","NIGHT_SHADE","PROTECT"),
  ("GENGAR","SHADOW_BALL","NIGHT_SHADE","PSYCHIC","PROTECT"),
  ("DUSCLOPS","SHADOW_PUNCH","NIGHT_SHADE","SHADOW_BALL","PROTECT"),
  ("SABLEYE","FAINT_ATTACK","ASTONISH","SHADOW_BALL","PROTECT"),
  ("ABSOL","SLASH","FAINT_ATTACK","QUICK_ATTACK","PROTECT"),
  ("MEWTWO","SHADOW_BALL","PSYCHIC","SWIFT","PROTECT")],
 [("TORKOAL","EMBER","BODY_SLAM","FIRE_BLAST","PROTECT"),
  ("ARCANINE","FLAMETHROWER","QUICK_ATTACK","BITE","PROTECT"),
  ("CAMERUPT","EMBER","ROCK_SLIDE","FIRE_BLAST","PROTECT"),
  ("MAGMAR","FIRE_PUNCH","FLAMETHROWER","SMOKESCREEN","PROTECT"),
  ("BLAZIKEN","BLAZE_KICK","FIRE_PUNCH","MACH_PUNCH","PROTECT"),
  ("ENTEI","FIRE_BLAST","FLAMETHROWER","SWIFT","PROTECT")],
 [("SWAMPERT","WATER_GUN","SURF","MUD_SHOT","PROTECT"),
  ("MILOTIC","SURF","HYDRO_PUMP","ICY_WIND","PROTECT"),
  ("KINGDRA","WATER_GUN","DRAGON_BREATH","SURF","PROTECT"),
  ("WALREIN","AURORA_BEAM","SURF","BODY_SLAM","PROTECT"),
  ("GYARADOS","BITE","HYDRO_PUMP","DRAGON_BREATH","PROTECT"),
  ("KYOGRE","HYDRO_PUMP","SURF","BLIZZARD","PROTECT")],
 [("RAICHU","THUNDER_SHOCK","QUICK_ATTACK","SHOCK_WAVE","PROTECT"),
  ("MANECTRIC","SHOCK_WAVE","THUNDER_SHOCK","BITE","PROTECT"),
  ("ELECTABUZZ","THUNDER_SHOCK","SHOCK_WAVE","SWIFT","PROTECT"),
  ("MAGNETON","SHOCK_WAVE","THUNDER_SHOCK","SCREECH","PROTECT"),
  ("METAGROSS","METEOR_MASH","PSYCHIC","BODY_SLAM","PROTECT"),
  ("ZAPDOS","SHOCK_WAVE","THUNDER_SHOCK","AERIAL_ACE","PROTECT")],
 [("ALTARIA","DRAGON_BREATH","GUST","PECK","PROTECT"),
  ("DRAGONITE","DRAGON_BREATH","WING_ATTACK","SLAM","PROTECT"),
  ("FLYGON","DRAGON_CLAW","DIG","MUD_SHOT","PROTECT"),
  ("SALAMENCE","DRAGON_CLAW","FLAMETHROWER","AERIAL_ACE","PROTECT"),
  ("GARDEVOIR","PSYCHIC","SWIFT","REFLECT","PROTECT"),
  ("RAYQUAZA","DRAGON_CLAW","DRAGON_BREATH","HYPER_BEAM","PROTECT")],
 [("SCIZOR","QUICK_ATTACK","SLASH","DOUBLE_TEAM","PROTECT"),
  ("DRAGONITE","DRAGON_BREATH","WING_ATTACK","SLAM","PROTECT"),
  ("METAGROSS","METEOR_MASH","PSYCHIC","BODY_SLAM","PROTECT"),
  ("REGICE","BLIZZARD","AURORA_BEAM","BODY_SLAM","PROTECT"),
  ("MEWTWO","PSYCHIC","SHADOW_BALL","SWIFT","PROTECT"),
  ("HO_OH","SACRED_FIRE","AERIAL_ACE","FIRE_BLAST","PROTECT")]
]
assert len(pools)==8 and all(len(q)==6 for q in pools)
roster=json.loads((root/"tools/arena/roster.json").read_text())
allow={r["species"] for r in roster}
moves=(root/"src/arena_moves.c").read_text()
for q in pools:
    for species,*attacks in q:
        if species not in allow:raise RuntimeError(f"V9 unanimated opponent: {species}")
        if any("{MOVE_"+a+"," not in moves for a in attacks):
            raise RuntimeError(f"V9 unsupported move for {species}: {attacks}")
ctype="\n".join("    {\n"+",\n".join("        {SPECIES_"+m[0]+", {"+", ".join("MOVE_"+a for a in m[1:])+"}}" for m in tier)+"\n    }," for tier in pools)
newpool="""static const struct AscensionThemedMon sThemePool[8][6] =
{
"""+ctype+"""
};"""
s,n=re.subn(r'static const struct AscensionThemedMon sThemePool\[8\]\[3\] =\n\{.*?\n\};',lambda _:newpool,s,flags=re.S)
assert n==1,f"theme pool: {n}"

# First two floor encounters field 2 and 3 enemies; leaders field 4 to 6,
# with the theme's legendary ALWAYS in the very last enemy slot. Repeat losses
# rotate the earlier opponents so rematches aren't identical.
start=s.index(' // Keep original single-opponent handoff outside Bronze for now.')
end=s.index('\n o=&sOpponents[rank][floor];',start)
fresh=""" // All eight towers and the Summit now use the native trainer-party
 // battle flag and a populated opposing party, not a wild 1-Pokemon fight.
 if (rank > 0 && rank <= 8)
 {
     u8 mon, slot, count;
     u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
     count=floor==0 ? 2 : floor==1 ? 3 : rank==8 ? 6 : rank>=5 ? 5 : 4;
     for (mon=0;mon<count;mon++)
     {
         const struct AscensionThemedMon *op;
         u8 pick = (floor==2 && mon==count-1)
             ? 5 : (mon + cycle + floor + rank) % 5;
         op=&sThemePool[rank-1][pick];
         if(mon==0)
             CreateScriptedWildMon(op->species, 59+2*rank+floor, ITEM_NONE);
         else
             CreateMon(&gEnemyParty[mon], op->species,59+2*rank+floor,
                       USE_RANDOM_IVS, FALSE, 0, OT_ID_PLAYER_ID, 0);
         for(slot=0;slot<MAX_MON_MOVES;slot++)
             SetMonMoveSlot(&gEnemyParty[mon],op->moves[slot],slot);
     }
     // Floor 3 boss receives a different native trainer identity.
     if(floor==2)
     {
         static const u16 leaders[9]={
             TRAINER_ROXANNE_1,TRAINER_WINONA_1,TRAINER_JUAN_1,
             TRAINER_NORMAN_1,TRAINER_FLANNERY_1,TRAINER_JUAN_1,
             TRAINER_WATTSON_1,TRAINER_STEVEN,TRAINER_WALLACE
         };
         gTrainerBattleOpponent_A=leaders[rank];
     }
     gAscensionTrainerPartyActive=TRUE;
     gSpecialVar_Result=1;
     return;
 }"""
s=s[:start]+fresh+s[end:]

# Reward economy uses the ORIGINAL Gen III money counter. Rewards are additive;
# lost battles charge a bounded fraction only. No debt and no money lockout.
s=exactly(s,'#include "constants/items.h"','#include "constants/items.h"\n#include "money.h"',"money include")
start=s.index('void Ascension_RecordVictory(void)')
end=s.index('void Ascension_PrepareTutorial(void)',start)
part=s[start:end]
part=exactly(part,
             " if(!Ascension_CanEnter(rank,floor))return;",
             " if(!Ascension_CanEnter(rank,floor))return;\n AddMoney(&gSaveBlock1Ptr->money, 650 + rank*160 + floor*125);",
             "victory reward")
s=s[:start]+part+s[end:]
old="""void Ascension_RecordDefeat(void)
{
    u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
    VarSet(VAR_ASCENSION_REMATCH_CYCLE, (cycle + 1) % 3);
}"""
new="""void Ascension_RecordDefeat(void)
{
    u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
    u32 balance=GetMoney(&gSaveBlock1Ptr->money);
    u32 penalty=balance/10;
    if(penalty>1200)penalty=1200;
    RemoveMoney(&gSaveBlock1Ptr->money,penalty);
    VarSet(VAR_ASCENSION_REMATCH_CYCLE,(cycle+1)%3);
}"""
s=exactly(s,old,new,"loss penalty")
career.write_text(s)

# Functional battle-items-only PokeMart (vanilla Frontiers sells Ultra Ball).
shop=maps/"AscensionItemShop/map.json"
m=json.loads(shop.read_text())
merchant=[o for o in m["object_events"] if o["graphics_id"]=="OBJ_EVENT_GFX_MART_EMPLOYEE"]
assert len(merchant)==1
merchant[0]["script"]="AscensionItemShop_EventScript_Clerk"
shop.write_text(json.dumps(m,indent=2)+"\n")
shopsc=maps/"AscensionItemShop/scripts.inc"
v=shopsc.read_text()
v+="""
AscensionItemShop_EventScript_Clerk::
 lock
 faceplayer
 msgbox AscensionItemShop_Text_Clerk, MSGBOX_DEFAULT
 pokemart AscensionItemShop_BattleItems
 msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
 release
 end
AscensionItemShop_Text_Clerk:
 .string "ARENA SUPPLY SHOP!\\nUse your battle winnings.$"
 .align 2
AscensionItemShop_BattleItems:
 .2byte ITEM_POTION
 .2byte ITEM_SUPER_POTION
 .2byte ITEM_HYPER_POTION
 .2byte ITEM_MAX_POTION
 .2byte ITEM_FULL_RESTORE
 .2byte ITEM_FULL_HEAL
 .2byte ITEM_REVIVE
 .2byte ITEM_MAX_REVIVE
 .2byte ITEM_ETHER
 .2byte ITEM_ELIXIR
 .2byte ITEM_X_ATTACK
 .2byte ITEM_X_DEFEND
 .2byte ITEM_X_SPEED
 .2byte ITEM_GUARD_SPEC
 pokemartlistend
"""
# Normalize deliberately constructed newline to exact GBA charmap escape.
v=v.replace('"ARENA SUPPLY SHOP!\\nUse your battle winnings.$"','"ARENA SUPPLY SHOP!\\\\nUse your battle winnings.$"')
shopsc.write_text(v)

# Professor gives clear Team/PC directions AND opens the real native storage
# UI; no fake choice saying "team changed" without interacting with the party.
prof=maps/"AscensionTeamLab/scripts.inc"
p=prof.read_text()
old="""AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 release
 end"""
new="""AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 msgbox AscensionTeamLab_Text_OpenBoxes, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_ProfessorDone
 special ShowPokemonStorageSystemPC
AscensionTeamLab_EventScript_ProfessorDone::
 release
 end"""
p=exactly(p,old,new,"Professor storage UI")
p+="\nAscensionTeamLab_Text_OpenBoxes:\n\t.string \"Open your POKEMON BOXES?\\\\nUse PARTY to reorder your team.$\"\n"
prof.write_text(p)
print("V9 foundation: nine native trainer-team arenas; trainer graphics match intro; winning money and losing 10%; battle-only shop; Professor native PC.")
