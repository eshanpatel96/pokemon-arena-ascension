#include "global.h"
#include "overworld.h"
#include "global.h"
#include "ascension_progress.h"
#include "battle.h"
#include "battle_setup.h"
#include "event_data.h"
#include "pokemon.h"
#include "random.h"
#include "script_pokemon_util.h"
#include "string_util.h"
#include "constants/vars.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/items.h"
#include "money.h"
#include "constants/flags.h"
#include "constants/event_objects.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "constants/opponents.h"

static void Ascension_V111LegalizeEnemyParty(void);

// Persistent for a single native trainer fight; cleared on returning to field.
EWRAM_DATA bool8 gAscensionTrainerPartyActive = FALSE;

struct AscensionTrainerMon
{
    u16 species;
    u16 moves[MAX_MON_MOVES];
};
static const struct AscensionTrainerMon sBronzeRematchTeams[3][3][4] =
{
    // Floor 1: 2 foes, all rock/ground/steel.
    {
        {
            {SPECIES_GOLEM,     {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_DEFENSE_CURL}},
            {SPECIES_SCIZOR,    {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        },
        {
            {SPECIES_SANDSLASH, {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
        },
        {
            {SPECIES_RHYDON,    {MOVE_ROCK_THROW, MOVE_ROCK_TOMB, MOVE_BODY_SLAM, MOVE_SUPERPOWER}},
            {SPECIES_SCIZOR,    {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        },
    },
    // Floor 2: 3 foes with different mobility and defensive roles.
    {
        {
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
            {SPECIES_GOLEM,     {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_DEFENSE_CURL}},
            {SPECIES_SANDSLASH, {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
        },
        {
            {SPECIES_RHYDON,    {MOVE_ROCK_THROW, MOVE_ROCK_TOMB, MOVE_BODY_SLAM, MOVE_SUPERPOWER}},
            {SPECIES_SCIZOR,    {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
        },
        {
            {SPECIES_SANDSLASH, {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
            {SPECIES_GOLEM,     {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_DEFENSE_CURL}},
            {SPECIES_RHYDON,    {MOVE_ROCK_THROW, MOVE_ROCK_TOMB, MOVE_BODY_SLAM, MOVE_SUPERPOWER}},
        },
    },
    // Bronze Tower Master: 4 foes. Regirock always arrives LAST and acts as
    // a real-time, animated final ace, not a single-Pokemon "leader".
    {
        {
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
            {SPECIES_RHYDON,    {MOVE_ROCK_THROW, MOVE_ROCK_TOMB, MOVE_BODY_SLAM, MOVE_SUPERPOWER}},
            {SPECIES_GOLEM,     {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_DEFENSE_CURL}},
            {SPECIES_REGIROCK,  {MOVE_ROCK_SLIDE, MOVE_SUPERPOWER, MOVE_ROCK_TOMB, MOVE_PROTECT}},
        },
        {
            {SPECIES_SCIZOR,    {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
            {SPECIES_SANDSLASH, {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
            {SPECIES_REGIROCK,  {MOVE_ROCK_SLIDE, MOVE_SUPERPOWER, MOVE_ROCK_TOMB, MOVE_PROTECT}},
        },
        {
            {SPECIES_GOLEM,     {MOVE_ROCK_THROW, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_DEFENSE_CURL}},
            {SPECIES_AGGRON,    {MOVE_ROCK_TOMB, MOVE_HEADBUTT, MOVE_ROCK_SLIDE, MOVE_PROTECT}},
            {SPECIES_RHYDON,    {MOVE_ROCK_THROW, MOVE_ROCK_TOMB, MOVE_BODY_SLAM, MOVE_SUPERPOWER}},
            {SPECIES_REGIROCK,  {MOVE_ROCK_SLIDE, MOVE_SUPERPOWER, MOVE_ROCK_TOMB, MOVE_PROTECT}},
        },
    }
};
static const u8 sBronzeTeamSizes[3] = {2, 3, 4};
static const struct AscensionTrainerMon sBronzeSemiFinalTeams[3][4]={
    {
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_SCIZOR,{MOVE_QUICK_ATTACK,MOVE_SLASH,MOVE_DOUBLE_TEAM,MOVE_PROTECT}},
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
    },
    {
        {SPECIES_SANDSLASH,{MOVE_SCRATCH,MOVE_SLASH,MOVE_DIG,MOVE_SAND_ATTACK}},
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
    },
    {
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
        {SPECIES_SCIZOR,{MOVE_QUICK_ATTACK,MOVE_SLASH,MOVE_DOUBLE_TEAM,MOVE_PROTECT}},
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
    },
};

struct AscensionThemedMon
{
    u16 species;
    u16 moves[MAX_MON_MOVES];
};
// Three variants for each non-Bronze tower, 3 ordinary slots per variant.
// The final floor always features a fixed animated legendary at a bounded
// level. Locked species are not gifted to the player by victory.
// Five mandatory Summit rounds: no extra sprites; native 1v1 send-outs.
static const struct AscensionThemedMon sChampionTeams[5][6]=
{
    {
        {SPECIES_WALREIN, {MOVE_AURORA_BEAM, MOVE_SURF, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_DEWGONG, {MOVE_SURF, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_LAPRAS, {MOVE_SURF, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_GLALIE, {MOVE_BLIZZARD, MOVE_BITE, MOVE_AURORA_BEAM, MOVE_PROTECT}},
        {SPECIES_CLOYSTER, {MOVE_BLIZZARD, MOVE_SURF, MOVE_AURORA_BEAM, MOVE_PROTECT}},
        {SPECIES_ARTICUNO, {MOVE_AURORA_BEAM, MOVE_BLIZZARD, MOVE_GUST, MOVE_PROTECT}}
    },
    {
        {SPECIES_MAGNETON, {MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_SCREECH, MOVE_PROTECT}},
        {SPECIES_SKARMORY, {MOVE_WING_ATTACK, MOVE_AERIAL_ACE, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_METAGROSS, {MOVE_METEOR_MASH, MOVE_PSYCHIC, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        {SPECIES_ARMALDO, {MOVE_ROCK_SLIDE, MOVE_ROCK_TOMB, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_REGISTEEL, {MOVE_METEOR_MASH, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT}}
    },
    {
        {SPECIES_NINJASK, {MOVE_QUICK_ATTACK, MOVE_WING_ATTACK, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        {SPECIES_SANDSLASH, {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
        {SPECIES_ELECTABUZZ, {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_CROBAT, {MOVE_WING_ATTACK, MOVE_AERIAL_ACE, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_MANECTRIC, {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_RAIKOU, {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_QUICK_ATTACK, MOVE_PROTECT}}
    },
    {
        {SPECIES_CLAYDOL, {MOVE_PSYCHIC, MOVE_MUD_SHOT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_SLOWBRO, {MOVE_PSYCHIC, MOVE_SURF, MOVE_WATER_GUN, MOVE_PROTECT}},
        {SPECIES_GARDEVOIR, {MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_ALAKAZAM, {MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_JYNX, {MOVE_PSYCHIC, MOVE_BLIZZARD, MOVE_AURORA_BEAM, MOVE_PROTECT}},
        {SPECIES_REGICE, {MOVE_BLIZZARD, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT}}
    },
    {
        {SPECIES_MACHAMP, {MOVE_CROSS_CHOP, MOVE_MACH_PUNCH, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_ABSOL, {MOVE_SLASH, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_GYARADOS, {MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_DRAGON_BREATH, MOVE_PROTECT}},
        {SPECIES_SLAKING, {MOVE_BODY_SLAM, MOVE_SLASH, MOVE_HEADBUTT, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA, {MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}},
        {SPECIES_HO_OH, {MOVE_SACRED_FIRE, MOVE_AERIAL_ACE, MOVE_FIRE_BLAST, MOVE_PROTECT}}
    }
};
static const u16 sChampionRewards[5][5]=
{
    {SPECIES_ARTICUNO, SPECIES_GLALIE, SPECIES_SPHEAL, SPECIES_DEWGONG, SPECIES_CLOYSTER},
    {SPECIES_REGISTEEL, SPECIES_SKARMORY, SPECIES_SCIZOR, SPECIES_MAGNETON, SPECIES_ARMALDO},
    {SPECIES_RAIKOU, SPECIES_ELECTABUZZ, SPECIES_NINJASK, SPECIES_SANDSLASH, SPECIES_CROBAT},
    {SPECIES_REGICE, SPECIES_ALAKAZAM, SPECIES_JYNX, SPECIES_SLOWBRO, SPECIES_CLAYDOL},
    {SPECIES_HO_OH, SPECIES_SLAKING, SPECIES_ABSOL, SPECIES_GYARADOS, SPECIES_MACHAMP}
};
static const u16 sChampionRewardMoves[5][5][MAX_MON_MOVES]=
{
    {
        {MOVE_AURORA_BEAM, MOVE_BLIZZARD, MOVE_GUST, MOVE_PROTECT},
        {MOVE_BLIZZARD, MOVE_BITE, MOVE_AURORA_BEAM, MOVE_PROTECT},
        {MOVE_WATER_GUN, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT},
        {MOVE_SURF, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT},
        {MOVE_BLIZZARD, MOVE_SURF, MOVE_AURORA_BEAM, MOVE_PROTECT}
    },
    {
        {MOVE_METEOR_MASH, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT},
        {MOVE_WING_ATTACK, MOVE_AERIAL_ACE, MOVE_SLASH, MOVE_PROTECT},
        {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT},
        {MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_SCREECH, MOVE_PROTECT},
        {MOVE_ROCK_SLIDE, MOVE_ROCK_TOMB, MOVE_SLASH, MOVE_PROTECT}
    },
    {
        {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_QUICK_ATTACK, MOVE_PROTECT},
        {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_SWIFT, MOVE_PROTECT},
        {MOVE_QUICK_ATTACK, MOVE_WING_ATTACK, MOVE_DOUBLE_TEAM, MOVE_PROTECT},
        {MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK},
        {MOVE_WING_ATTACK, MOVE_AERIAL_ACE, MOVE_BITE, MOVE_PROTECT}
    },
    {
        {MOVE_BLIZZARD, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT},
        {MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT},
        {MOVE_PSYCHIC, MOVE_BLIZZARD, MOVE_AURORA_BEAM, MOVE_PROTECT},
        {MOVE_PSYCHIC, MOVE_SURF, MOVE_WATER_GUN, MOVE_PROTECT},
        {MOVE_PSYCHIC, MOVE_MUD_SHOT, MOVE_REFLECT, MOVE_PROTECT}
    },
    {
        {MOVE_SACRED_FIRE, MOVE_AERIAL_ACE, MOVE_FIRE_BLAST, MOVE_PROTECT},
        {MOVE_BODY_SLAM, MOVE_SLASH, MOVE_HEADBUTT, MOVE_PROTECT},
        {MOVE_SLASH, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT},
        {MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_DRAGON_BREATH, MOVE_PROTECT},
        {MOVE_CROSS_CHOP, MOVE_MACH_PUNCH, MOVE_BODY_SLAM, MOVE_PROTECT}
    }
};

static const struct AscensionThemedMon sThemePool[8][6] =
{
    {
        {SPECIES_PIDGEOT, {MOVE_GUST, MOVE_WING_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_SWELLOW, {MOVE_WING_ATTACK, MOVE_QUICK_ATTACK, MOVE_AERIAL_ACE, MOVE_DOUBLE_TEAM}},
        {SPECIES_PELIPPER, {MOVE_WATER_GUN, MOVE_GUST, MOVE_WING_ATTACK, MOVE_PROTECT}},
        {SPECIES_ALTARIA, {MOVE_DRAGON_BREATH, MOVE_PECK, MOVE_GUST, MOVE_PROTECT}},
        {SPECIES_DRAGONITE, {MOVE_WING_ATTACK, MOVE_DRAGON_BREATH, MOVE_SLAM, MOVE_AGILITY}},
        {SPECIES_LUGIA, {MOVE_AEROBLAST, MOVE_GUST, MOVE_SWIFT, MOVE_PROTECT}}
    },
    {
        {SPECIES_GROVYLE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_VILEPLUME, {MOVE_GIGA_DRAIN, MOVE_ACID, MOVE_SOLAR_BEAM, MOVE_PROTECT}},
        {SPECIES_SHIFTRY, {MOVE_FAINT_ATTACK, MOVE_GIGA_DRAIN, MOVE_GROWTH, MOVE_PROTECT}},
        {SPECIES_BRELOOM, {MOVE_MACH_PUNCH, MOVE_MEGA_DRAIN, MOVE_HEADBUTT, MOVE_PROTECT}},
        {SPECIES_SUICUNE, {MOVE_AURORA_BEAM, MOVE_GUST, MOVE_RAIN_DANCE, MOVE_PROTECT}}
    },
    {
        {SPECIES_BANETTE, {MOVE_SHADOW_BALL, MOVE_ASTONISH, MOVE_NIGHT_SHADE, MOVE_PROTECT}},
        {SPECIES_GENGAR, {MOVE_SHADOW_BALL, MOVE_NIGHT_SHADE, MOVE_PSYCHIC, MOVE_PROTECT}},
        {SPECIES_DUSCLOPS, {MOVE_SHADOW_PUNCH, MOVE_NIGHT_SHADE, MOVE_SHADOW_BALL, MOVE_PROTECT}},
        {SPECIES_SABLEYE, {MOVE_FAINT_ATTACK, MOVE_ASTONISH, MOVE_SHADOW_BALL, MOVE_PROTECT}},
        {SPECIES_ABSOL, {MOVE_SLASH, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_MEWTWO, {MOVE_SHADOW_BALL, MOVE_PSYCHIC, MOVE_SWIFT, MOVE_PROTECT}}
    },
    {
        {SPECIES_TORKOAL, {MOVE_EMBER, MOVE_BODY_SLAM, MOVE_FIRE_BLAST, MOVE_PROTECT}},
        {SPECIES_ARCANINE, {MOVE_FLAMETHROWER, MOVE_QUICK_ATTACK, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_CAMERUPT, {MOVE_EMBER, MOVE_ROCK_SLIDE, MOVE_FIRE_BLAST, MOVE_PROTECT}},
        {SPECIES_MAGMAR, {MOVE_FIRE_PUNCH, MOVE_FLAMETHROWER, MOVE_SMOKESCREEN, MOVE_PROTECT}},
        {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_FIRE_PUNCH, MOVE_MACH_PUNCH, MOVE_PROTECT}},
        {SPECIES_ENTEI, {MOVE_FIRE_BLAST, MOVE_FLAMETHROWER, MOVE_SWIFT, MOVE_PROTECT}}
    },
    {
        {SPECIES_SWAMPERT, {MOVE_WATER_GUN, MOVE_SURF, MOVE_MUD_SHOT, MOVE_PROTECT}},
        {SPECIES_MILOTIC, {MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_ICY_WIND, MOVE_PROTECT}},
        {SPECIES_KINGDRA, {MOVE_WATER_GUN, MOVE_DRAGON_BREATH, MOVE_SURF, MOVE_PROTECT}},
        {SPECIES_WALREIN, {MOVE_AURORA_BEAM, MOVE_SURF, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_GYARADOS, {MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_DRAGON_BREATH, MOVE_PROTECT}},
        {SPECIES_KYOGRE, {MOVE_HYDRO_PUMP, MOVE_SURF, MOVE_BLIZZARD, MOVE_PROTECT}}
    },
    {
        {SPECIES_RAICHU, {MOVE_THUNDER_SHOCK, MOVE_QUICK_ATTACK, MOVE_SHOCK_WAVE, MOVE_PROTECT}},
        {SPECIES_MANECTRIC, {MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_ELECTABUZZ, {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_MAGNETON, {MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_SCREECH, MOVE_PROTECT}},
        {SPECIES_METAGROSS, {MOVE_METEOR_MASH, MOVE_PSYCHIC, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_ZAPDOS, {MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_AERIAL_ACE, MOVE_PROTECT}}
    },
    {
        {SPECIES_ALTARIA, {MOVE_DRAGON_BREATH, MOVE_GUST, MOVE_PECK, MOVE_PROTECT}},
        {SPECIES_DRAGONITE, {MOVE_DRAGON_BREATH, MOVE_WING_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_FLYGON, {MOVE_DRAGON_CLAW, MOVE_DIG, MOVE_MUD_SHOT, MOVE_PROTECT}},
        {SPECIES_SALAMENCE, {MOVE_DRAGON_CLAW, MOVE_FLAMETHROWER, MOVE_AERIAL_ACE, MOVE_PROTECT}},
        {SPECIES_GARDEVOIR, {MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA, {MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}}
    },
    {
        {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        {SPECIES_DRAGONITE, {MOVE_DRAGON_BREATH, MOVE_WING_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_METAGROSS, {MOVE_METEOR_MASH, MOVE_PSYCHIC, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_REGICE, {MOVE_BLIZZARD, MOVE_AURORA_BEAM, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_MEWTWO, {MOVE_PSYCHIC, MOVE_SHADOW_BALL, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_HO_OH, {MOVE_SACRED_FIRE, MOVE_AERIAL_ACE, MOVE_FIRE_BLAST, MOVE_PROTECT}}
    },
};


struct AscensionOpponent {u16 species, move1, move2; u8 level;};
// Eight three-floor towers + three final summit battles. Curated arena-supported moves only.
// No new battle renderer or damage formula: this uses Emerald Arena's native battle handoff.
static const struct AscensionOpponent sOpponents[9][3] = {
 {{SPECIES_SCIZOR,MOVE_QUICK_ATTACK,MOVE_SLASH,45},{SPECIES_SCEPTILE,MOVE_LEAF_BLADE,MOVE_QUICK_ATTACK,48},{SPECIES_BLAZIKEN,MOVE_BLAZE_KICK,MOVE_EMBER,50}},
 {{SPECIES_BLASTOISE,MOVE_WATER_GUN,MOVE_BITE,50},{SPECIES_CHARIZARD,MOVE_FLAMETHROWER,MOVE_SLASH,52},{SPECIES_DRAGONITE,MOVE_SLAM,MOVE_WING_ATTACK,53}},
 {{SPECIES_SCEPTILE,MOVE_LEAF_BLADE,MOVE_QUICK_ATTACK,54},{SPECIES_SCIZOR,MOVE_QUICK_ATTACK,MOVE_SLASH,55},{SPECIES_BLASTOISE,MOVE_HYDRO_PUMP,MOVE_WATER_GUN,56}},
 {{SPECIES_BLAZIKEN,MOVE_BLAZE_KICK,MOVE_EMBER,56},{SPECIES_CHARIZARD,MOVE_FLAMETHROWER,MOVE_WING_ATTACK,58},{SPECIES_DRAGONITE,MOVE_SLAM,MOVE_HYPER_BEAM,59}},
 {{SPECIES_BLASTOISE,MOVE_HYDRO_PUMP,MOVE_WATER_GUN,60},{SPECIES_SCEPTILE,MOVE_LEAF_BLADE,MOVE_QUICK_ATTACK,61},{SPECIES_CHARIZARD,MOVE_FLAMETHROWER,MOVE_SLASH,62}},
 {{SPECIES_SCIZOR,MOVE_QUICK_ATTACK,MOVE_SLASH,63},{SPECIES_DRAGONITE,MOVE_WING_ATTACK,MOVE_HYPER_BEAM,64},{SPECIES_BLAZIKEN,MOVE_BLAZE_KICK,MOVE_EMBER,65}},
 {{SPECIES_CHARIZARD,MOVE_FLAMETHROWER,MOVE_SLASH,66},{SPECIES_BLASTOISE,MOVE_HYDRO_PUMP,MOVE_WATER_GUN,67},{SPECIES_RAYQUAZA,MOVE_DRAGON_CLAW,MOVE_HYPER_BEAM,68}},
 {{SPECIES_DRAGONITE,MOVE_DRAGON_BREATH,MOVE_HYPER_BEAM,68},{SPECIES_SCIZOR,MOVE_QUICK_ATTACK,MOVE_SLASH,70},{SPECIES_MEWTWO,MOVE_PSYCHIC,MOVE_SWIFT,71}},
 {{SPECIES_BLAZIKEN,MOVE_BLAZE_KICK,MOVE_FIRE_PUNCH,72},{SPECIES_RAYQUAZA,MOVE_DRAGON_CLAW,MOVE_HYPER_BEAM,74},{SPECIES_MEWTWO,MOVE_PSYCHIC,MOVE_SWIFT,76}}
};

void Ascension_GetProgress(void)
{
 u16 rank=VarGet(VAR_ASCENSION_RANK), floor=VarGet(VAR_ASCENSION_FLOOR);
 if(rank>ASCENSION_COMPLETE)rank=ASCENSION_COMPLETE;
 if(floor>=Ascension_FloorCount(rank))floor=0;
 ConvertIntToDecimalStringN(gStringVar1,rank+1,STR_CONV_MODE_LEFT_ALIGN,2);
 ConvertIntToDecimalStringN(gStringVar2,floor+1,STR_CONV_MODE_LEFT_ALIGN,1);
 gSpecialVar_Result=rank==ASCENSION_COMPLETE?0:1;
}

void Ascension_PrepareChallenge(void)
{
 u16 i,rank=VarGet(VAR_ASCENSION_RANK),floor=VarGet(VAR_ASCENSION_FLOOR);
 const struct AscensionOpponent *o;
 gSpecialVar_Result=0;
 if(!Ascension_CanEnter(rank,floor))return;
 for(i=0;i<gPlayerPartyCount;i++)
  if(GetMonData(&gPlayerParty[i],MON_DATA_HP) && !GetMonData(&gPlayerParty[i],MON_DATA_IS_EGG))break;
 if(i==gPlayerPartyCount)return;
 gAscensionTrainerPartyActive = FALSE;
 if (rank == 0 && floor < Ascension_FloorCount(rank))
 {
     u8 mon, slot, bronzePhase=(floor+1==Ascension_FloorCount(rank)) ? 2 : (floor==0 ? 0 : 1);
     u8 count = floor==2 ? 4 : sBronzeTeamSizes[bronzePhase];
     for (mon = 0; mon < count; mon++)
     {
         const struct AscensionTrainerMon *op = floor==2 ? &sBronzeSemiFinalTeams[VarGet(VAR_ASCENSION_REMATCH_CYCLE)%3][mon] : &sBronzeRematchTeams[bronzePhase][VarGet(VAR_ASCENSION_REMATCH_CYCLE)%3][mon];
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
     if (floor+1 == Ascension_FloorCount(rank)) gTrainerBattleOpponent_A = TRAINER_ROXANNE_1;
     Ascension_V111LegalizeEnemyParty();
     gAscensionTrainerPartyActive=TRUE;
     gSpecialVar_Result = 1;
     return;
 }
 // All eight towers and the Summit now use the native trainer-party
 // battle flag and a populated opposing party, not a wild 1-Pokemon fight.
 if(rank==ASCENSION_SUMMIT_INDEX)
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
         u8 pick=floor==4 ? mon : (mon==5?5:(mon+cycle)%5);
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
     Ascension_V111LegalizeEnemyParty();
     gAscensionTrainerPartyActive=TRUE;
     gSpecialVar_Result=1;
     return;
 }
 if (rank > 0 && rank <= 8)
 {
     u8 mon, slot, count;
     u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
     bool8 isBoss=floor+1==Ascension_FloorCount(rank);
     u8 level=59+rank+floor/2+(isBoss?2:0);
     count=isBoss ? (rank>=6?6:5) : floor==0?2 : floor==1?3 : floor>=4?5:4;
     for (mon=0;mon<count;mon++)
     {
         const struct AscensionThemedMon *op;
         u8 pick = (floor+1==Ascension_FloorCount(rank) && mon==count-1)
             ? 5 : (mon + cycle + floor + rank) % 5;
         op=&sThemePool[rank-1][pick];
         if(mon==0)
             CreateScriptedWildMon(op->species,level,ITEM_NONE);
         else
             CreateMon(&gEnemyParty[mon], op->species,level,
                       USE_RANDOM_IVS, FALSE, 0, OT_ID_PLAYER_ID, 0);
         for(slot=0;slot<MAX_MON_MOVES;slot++)
             SetMonMoveSlot(&gEnemyParty[mon],op->moves[slot],slot);
     }
     // Floor 3 boss receives a different native trainer identity.
     if(floor+1==Ascension_FloorCount(rank))
     {
         static const u16 leaders[9]={
             TRAINER_ROXANNE_1,TRAINER_WINONA_1,TRAINER_MOLLIE,
             TRAINER_EDWARD,TRAINER_FLANNERY_1,TRAINER_JUAN_1,
             TRAINER_WATTSON_1,TRAINER_STEVEN,TRAINER_WALLACE
         };
         gTrainerBattleOpponent_A=leaders[rank];
     }
     Ascension_V111LegalizeEnemyParty();
     gAscensionTrainerPartyActive=TRUE;
     gSpecialVar_Result=1;
     return;
 }
 o=&sOpponents[rank][floor];
 CreateScriptedWildMon(o->species,o->level,ITEM_NONE);
 SetMonMoveSlot(&gEnemyParty[0],o->move1,0);
 SetMonMoveSlot(&gEnemyParty[0],o->move2,1);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,2);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,3);
 gSpecialVar_Result=1;
}

// Completed ordinary-floor unlock eligibility is independent of today's run.
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

void Ascension_RecordVictory(void)
{
 u16 rank=VarGet(VAR_ASCENSION_RANK),floor=VarGet(VAR_ASCENSION_FLOOR);
 gSpecialVar_Result=0;
 if(!Ascension_CanEnter(rank,floor))return;
 AddMoney(&gSaveBlock1Ptr->money,
          floor+1==Ascension_FloorCount(rank) ? (1500 + rank*200) : (350 + rank*55 + floor*80));
 Ascension_RememberClearedFloor(rank,floor+1);
 if(rank==ASCENSION_SUMMIT_INDEX
    && floor+1>VarGet(VAR_ASCENSION_CHAMPION_WINS))
     VarSet(VAR_ASCENSION_CHAMPION_WINS,floor+1);
 VarSet(VAR_ASCENSION_RANK,Ascension_NextRank(rank,floor));
 VarSet(VAR_ASCENSION_FLOOR,Ascension_NextFloor(rank,floor));
 // Result 1=next floor, 2=next tower, 3=Champion Summit completed.
 rank=VarGet(VAR_ASCENSION_RANK);
 gSpecialVar_Result=rank==ASCENSION_COMPLETE?3:(VarGet(VAR_ASCENSION_FLOOR)==0?2:1);
}

// Intro training bout is replayable from the Arena City dojo guide.
// This deliberately uses Emerald Arena's existing wild-battle dispatch,
// not a duplicate combat renderer or a special title-screen launcher.
void Ascension_PrepareTutorial(void)
{
    u16 i;
    gSpecialVar_Result = 0;
    for (i = 0; i < gPlayerPartyCount; i++)
        if (GetMonData(&gPlayerParty[i], MON_DATA_HP)
            && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
            break;
    if (i == gPlayerPartyCount)
        return;

    {
        static const struct {
            u16 species;
            u16 moves[4];
        } practice[6] = {
            {SPECIES_SCIZOR, {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
            {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_EMBER, MOVE_SLASH, MOVE_PROTECT}},
            {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
            {SPECIES_BLASTOISE, {MOVE_WATER_GUN, MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_PROTECT}},
            {SPECIES_DRAGONITE, {MOVE_WING_ATTACK, MOVE_SLAM, MOVE_DRAGON_BREATH, MOVE_AGILITY}},
            {SPECIES_CHARIZARD, {MOVE_FLAMETHROWER, MOVE_WING_ATTACK, MOVE_SLASH, MOVE_PROTECT}}
        };
        u16 pick = Random() % 6;
        u8 slot;
        CreateScriptedWildMon(practice[pick].species, 54, ITEM_NONE);
        for (slot = 0; slot < 4; slot++)
            SetMonMoveSlot(&gEnemyParty[0], practice[pick].moves[slot], slot);
    }
    gSpecialVar_Result = 1;
}


// Only the tower matching your saved rank can launch a ranking fight.
void Ascension_CanChallengeTower(void)
{
    gSpecialVar_Result = (VarGet(VAR_ASCENSION_RANK) == gSpecialVar_0x8004);
}


// Native visible challenger gfx rotation (no new character assets).
void Ascension_NextChallengerSprite(void)
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
    u16 slot = floor+1==Ascension_FloorCount(rank) ? rank%ARRAY_COUNT(gfx) : next;
    if(rank==ASCENSION_SUMMIT_INDEX)
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

    VarSet(VAR_ASCENSION_CHALLENGER_ROTATION,next);
    VarSet(VAR_OBJ_GFX_ID_0,gfx[slot]);
    gTrainerBattleOpponent_A = trainers[slot];
}



// Defeat does not change career rank or clear count. It ONLY changes which
// curated team you face next time, guaranteeing varied rematches.
void Ascension_RecordDefeat(void)
{
    u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
    u32 balance=GetMoney(&gSaveBlock1Ptr->money);
    u32 penalty=balance/10;
    if(penalty>1000)penalty=1000;
    RemoveMoney(&gSaveBlock1Ptr->money,penalty);
    VarSet(VAR_ASCENSION_REMATCH_CYCLE,(cycle+1)%3);
    Ascension_RememberClearedFloor(VarGet(VAR_ASCENSION_RANK),VarGet(VAR_ASCENSION_FLOOR));
    VarSet(VAR_ASCENSION_FLOOR,0); // loss resets this run, not rank/unlocks
}


struct AscensionStarterSpecies {u16 species;u8 style;};
static const struct AscensionStarterSpecies sAscensionStarterPool[] =
{
    {SPECIES_BULBASAUR, 0},
    {SPECIES_IVYSAUR, 0},
    {SPECIES_VENUSAUR, 0},
    {SPECIES_VICTREEBEL, 0},
    {SPECIES_BELLOSSOM, 0},
    {SPECIES_LOTAD, 0},
    {SPECIES_LOMBRE, 0},
    {SPECIES_LUDICOLO, 0},
    {SPECIES_SEEDOT, 0},
    {SPECIES_NUZLEAF, 0},
    {SPECIES_SHIFTRY, 0},
    {SPECIES_SHROOMISH, 0},
    {SPECIES_BRELOOM, 0},
    {SPECIES_CHARMANDER, 1},
    {SPECIES_CHARMELEON, 1},
    {SPECIES_CHARIZARD, 1},
    {SPECIES_NINETALES, 1},
    {SPECIES_ARCANINE, 1},
    {SPECIES_RAPIDASH, 1},
    {SPECIES_FLAREON, 1},
    {SPECIES_SLUGMA, 1},
    {SPECIES_SQUIRTLE, 2},
    {SPECIES_WARTORTLE, 2},
    {SPECIES_BLASTOISE, 2},
    {SPECIES_GOLDUCK, 2},
    {SPECIES_POLIWRATH, 2},
    {SPECIES_TENTACOOL, 2},
    {SPECIES_TENTACRUEL, 2},
    {SPECIES_GOLDEEN, 2},
    {SPECIES_SEAKING, 2},
    {SPECIES_STARYU, 2},
    {SPECIES_LAPRAS, 2},
    {SPECIES_MARILL, 2},
    {SPECIES_AZUMARILL, 2},
    {SPECIES_BARBOACH, 2},
    {SPECIES_WHISCASH, 2},
    {SPECIES_ABRA, 3},
    {SPECIES_KADABRA, 3},
    {SPECIES_PRIMEAPE, 4},
    {SPECIES_MACHOP, 4},
    {SPECIES_MACHOKE, 4},
    {SPECIES_MAKUHITA, 4},
    {SPECIES_HARIYAMA, 4},
    {SPECIES_MEDITITE, 4},
    {SPECIES_MEDICHAM, 4},
    {SPECIES_SANDSHREW, 5},
    {SPECIES_DUGTRIO, 5},
    {SPECIES_MAROWAK, 5},
    {SPECIES_ARBOK, 6},
    {SPECIES_KOFFING, 6},
    {SPECIES_GULPIN, 6},
    {SPECIES_SWALOT, 6},
    {SPECIES_BUTTERFREE, 7},
    {SPECIES_BEEDRILL, 7},
    {SPECIES_VENOMOTH, 7},
    {SPECIES_WURMPLE, 7},
    {SPECIES_SILCOON, 7},
    {SPECIES_BEAUTIFLY, 7},
    {SPECIES_CASCOON, 7},
    {SPECIES_DUSTOX, 7},
    {SPECIES_ZUBAT, 8},
    {SPECIES_GOLBAT, 8},
    {SPECIES_SCYTHER, 8},
    {SPECIES_CLEFABLE, 9},
    {SPECIES_PERSIAN, 9},
    {SPECIES_EEVEE, 9},
    {SPECIES_POOCHYENA, 9},
    {SPECIES_MIGHTYENA, 9},
    {SPECIES_ZIGZAGOON, 9},
    {SPECIES_LINOONE, 9},
    {SPECIES_SLAKOTH, 9},
    {SPECIES_VIGOROTH, 9},
    {SPECIES_WHISMUR, 9},
    {SPECIES_LOUDRED, 9},
    {SPECIES_EXPLOUD, 9},
    {SPECIES_NOSEPASS, 9},
    {SPECIES_SKITTY, 9},
    {SPECIES_DELCATTY, 9},
    {SPECIES_MAGIKARP, 9},
    {SPECIES_MAGNEMITE, 10}
};
static const u16 sAscensionStarterMoves[][MAX_MON_MOVES] =
{
    {MOVE_ABSORB, MOVE_GIGA_DRAIN, MOVE_PROTECT, MOVE_GROWTH},
    {MOVE_EMBER, MOVE_FLAMETHROWER, MOVE_PROTECT, MOVE_QUICK_ATTACK},
    {MOVE_WATER_GUN, MOVE_SURF, MOVE_PROTECT, MOVE_BITE},
    {MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT},
    {MOVE_MACH_PUNCH, MOVE_SLAM, MOVE_CROSS_CHOP, MOVE_PROTECT},
    {MOVE_MUD_SHOT, MOVE_DIG, MOVE_SLAM, MOVE_PROTECT},
    {MOVE_ACID, MOVE_BITE, MOVE_GROWL, MOVE_PROTECT},
    {MOVE_LEECH_LIFE, MOVE_AERIAL_ACE, MOVE_SCRATCH, MOVE_PROTECT},
    {MOVE_WING_ATTACK, MOVE_GUST, MOVE_QUICK_ATTACK, MOVE_PROTECT},
    {MOVE_TACKLE, MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_THUNDER_SHOCK, MOVE_SHOCK_WAVE, MOVE_QUICK_ATTACK, MOVE_PROTECT}
};

// Professor Birch hands out a native PC catalog exactly once. A full PC does
// not destroy an existing Pokemon or fake a successful grant.
void Ascension_RegisterStarterRoster(void)
{
    struct Pokemon mon;
    u16 i;
    u8 slot;
    gSpecialVar_Result=0;
    if(FlagGet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED))
    {
        gSpecialVar_Result=2;
        return;
    }
    for(i=VarGet(VAR_ASCENSION_STARTER_NEXT_INDEX);i<ARRAY_COUNT(sAscensionStarterPool);i++)
    {
        const struct AscensionStarterSpecies *candidate=&sAscensionStarterPool[i];
        CreateMon(&mon,candidate->species,60,USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
        for(slot=0;slot<MAX_MON_MOVES;slot++)
            SetMonMoveSlot(&mon,sAscensionStarterMoves[candidate->style][slot],slot);
        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)
            return; // no index advance: next attempt retries this grant
        VarSet(VAR_ASCENSION_STARTER_NEXT_INDEX,i+1);
    }
    FlagSet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED);
    gSpecialVar_Result=1;
}


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
    u16 milestones=VarGet(VAR_ASCENSION_RECRUIT_MILESTONES);
    if(completed>ASCENSION_COMPLETE)completed=ASCENSION_COMPLETE;
    for(rank=0;rank<ASCENSION_TOWER_COUNT && rank<=completed;rank++)
    {
        for(part=0;part<8;part++)
        {
            u16 flag=FLAG_ASCENSION_REWARD_FIRST + rank*8 + part;
            // Two themed recruit licenses after each ordinary floor;
            // boss finishes remaining 4 including the legendary + partner.
            if(rank==completed)
            {
                // A tower in progress never grants its boss ace or end prizes.
                if(part<2)continue; // boss legendary + partner AFTER clear
                if(((milestones>>(rank*2))&3)<1+(part-2)/2
                   && floor<1+(part-2)/2)continue;
            }
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


// Restore known native real-time moves for starter/tower-reward recruits.
// Other species are never silently assigned an invalid shared profile.
void Ascension_ResetArenaMoves(void)
{
    u16 species,i,slot;
    const u16 *profile=NULL;
    gSpecialVar_Result=0;
    if(gSpecialVar_0x8004>=PARTY_SIZE)return;
    if(GetMonData(&gPlayerParty[gSpecialVar_0x8004],MON_DATA_IS_EGG))return;
    species=GetMonData(&gPlayerParty[gSpecialVar_0x8004],MON_DATA_SPECIES);
    for(i=0;i<ARRAY_COUNT(sAscensionStarterPool);i++)
        if(sAscensionStarterPool[i].species==species)
        {
            profile=sAscensionStarterMoves[sAscensionStarterPool[i].style];
            break;
        }
    if(profile==NULL)
        for(i=0;i<ASCENSION_TOWER_COUNT*8;i++)
            if(sTowerPrizes[i/8][i%8]==species)
            {
                profile=sTowerRewardMoveProfiles[i/8];
                break;
            }
    if(profile==NULL)
        for(i=0;i<5*5;i++)
            if(sChampionRewards[i/5][i%5]==species)
            {
                profile=sChampionRewardMoves[i/5][i%5];
                break;
            }
    if(profile==NULL)return;
    for(slot=0;slot<MAX_MON_MOVES;slot++)
        SetMonMoveSlot(&gPlayerParty[gSpecialVar_0x8004],profile[slot],slot);
    gSpecialVar_Result=1;
}


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


// Post-World-Champion circuit: original Arena engine and 1 active per side.
static const struct AscensionThemedMon sMastersTrainerTeams[8][6]=
{
    {
        {SPECIES_KECLEON,{MOVE_SLASH, MOVE_SHADOW_BALL, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_NINCADA,{MOVE_SCRATCH, MOVE_DIG, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_SABLEYE,{MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_ASTONISH, MOVE_PROTECT}},
        {SPECIES_ABSOL,{MOVE_SLASH, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_GENGAR,{MOVE_SHADOW_BALL, MOVE_NIGHT_SHADE, MOVE_PSYCHIC, MOVE_PROTECT}},
        {SPECIES_SHEDINJA,{MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}}
    },
    {
        {SPECIES_WAILMER,{MOVE_WATER_GUN, MOVE_SURF, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_CARVANHA,{MOVE_BITE, MOVE_WATER_GUN, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_KINGLER,{MOVE_CRABHAMMER, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_MILOTIC,{MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_AURORA_BEAM, MOVE_PROTECT}},
        {SPECIES_STARMIE,{MOVE_PSYCHIC, MOVE_SURF, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_WAILORD,{MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_BODY_SLAM, MOVE_PROTECT}}
    },
    {
        {SPECIES_CRADILY,{MOVE_ROCK_SLIDE, MOVE_GIGA_DRAIN, MOVE_ACID, MOVE_PROTECT}},
        {SPECIES_SOLROCK,{MOVE_PSYCHIC, MOVE_ROCK_SLIDE, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_CACTURNE,{MOVE_FAINT_ATTACK, MOVE_GIGA_DRAIN, MOVE_SOLAR_BEAM, MOVE_PROTECT}},
        {SPECIES_SANDSLASH,{MOVE_SCRATCH, MOVE_SLASH, MOVE_DIG, MOVE_SAND_ATTACK}},
        {SPECIES_NIDOQUEEN,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_NIDOKING,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_SLASH, MOVE_PROTECT}}
    },
    {
        {SPECIES_CORPHISH,{MOVE_CRABHAMMER, MOVE_WATER_GUN, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_KINGLER,{MOVE_CRABHAMMER, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_CARVANHA,{MOVE_BITE, MOVE_WATER_GUN, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_GYARADOS,{MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_DRAGON_BREATH, MOVE_PROTECT}},
        {SPECIES_SHARPEDO,{MOVE_BITE, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_CRAWDAUNT,{MOVE_CRABHAMMER, MOVE_BITE, MOVE_SLASH, MOVE_PROTECT}}
    },
    {
        {SPECIES_KECLEON,{MOVE_SLASH, MOVE_SHADOW_BALL, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_SABLEYE,{MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_ASTONISH, MOVE_PROTECT}},
        {SPECIES_SOLROCK,{MOVE_PSYCHIC, MOVE_ROCK_SLIDE, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_GARDEVOIR,{MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_NIDOKING,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_NIDOQUEEN,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT}}
    },
    {
        {SPECIES_CRADILY,{MOVE_ROCK_SLIDE, MOVE_GIGA_DRAIN, MOVE_ACID, MOVE_PROTECT}},
        {SPECIES_SABLEYE,{MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_ASTONISH, MOVE_PROTECT}},
        {SPECIES_ALAKAZAM,{MOVE_PSYCHIC, MOVE_SWIFT, MOVE_REFLECT, MOVE_PROTECT}},
        {SPECIES_SLOWBRO,{MOVE_PSYCHIC, MOVE_SURF, MOVE_WATER_GUN, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA,{MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}},
        {SPECIES_STARMIE,{MOVE_PSYCHIC, MOVE_SURF, MOVE_SWIFT, MOVE_PROTECT}}
    },
    {
        {SPECIES_WAILORD,{MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_WAILMER,{MOVE_WATER_GUN, MOVE_SURF, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_STARMIE,{MOVE_PSYCHIC, MOVE_SURF, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_KINGLER,{MOVE_CRABHAMMER, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_LUGIA,{MOVE_AEROBLAST, MOVE_GUST, MOVE_SWIFT, MOVE_PROTECT}},
        {SPECIES_SHARPEDO,{MOVE_BITE, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT}}
    },
    {
        {SPECIES_NINCADA,{MOVE_SCRATCH, MOVE_DIG, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_SHEDINJA,{MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_NIDOKING,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_SLASH, MOVE_PROTECT}},
        {SPECIES_NIDOQUEEN,{MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT}},
        {SPECIES_EXEGGUTOR,{MOVE_PSYCHIC, MOVE_SOLAR_BEAM, MOVE_GIGA_DRAIN, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA,{MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}}
    }
};
static const u16 sMastersRewards[18]={SPECIES_SHEDINJA, SPECIES_NINCADA, SPECIES_WAILORD, SPECIES_WAILMER, SPECIES_SHARPEDO, SPECIES_CARVANHA, SPECIES_CACTURNE, SPECIES_CRADILY, SPECIES_SOLROCK, SPECIES_CRAWDAUNT, SPECIES_CORPHISH, SPECIES_NIDOKING, SPECIES_NIDOQUEEN, SPECIES_EXEGGUTOR, SPECIES_KECLEON, SPECIES_SABLEYE, SPECIES_KINGLER, SPECIES_STARMIE};
static const u16 sMastersRewardMoves[18][MAX_MON_MOVES]={
    {MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT},
    {MOVE_SCRATCH, MOVE_DIG, MOVE_QUICK_ATTACK, MOVE_PROTECT},
    {MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_BODY_SLAM, MOVE_PROTECT},
    {MOVE_WATER_GUN, MOVE_SURF, MOVE_BODY_SLAM, MOVE_PROTECT},
    {MOVE_BITE, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_BITE, MOVE_WATER_GUN, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_FAINT_ATTACK, MOVE_GIGA_DRAIN, MOVE_SOLAR_BEAM, MOVE_PROTECT},
    {MOVE_ROCK_SLIDE, MOVE_GIGA_DRAIN, MOVE_ACID, MOVE_PROTECT},
    {MOVE_PSYCHIC, MOVE_ROCK_SLIDE, MOVE_REFLECT, MOVE_PROTECT},
    {MOVE_CRABHAMMER, MOVE_BITE, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_CRABHAMMER, MOVE_WATER_GUN, MOVE_BITE, MOVE_PROTECT},
    {MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_DIG, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_PROTECT},
    {MOVE_PSYCHIC, MOVE_SOLAR_BEAM, MOVE_GIGA_DRAIN, MOVE_PROTECT},
    {MOVE_SLASH, MOVE_SHADOW_BALL, MOVE_SWIFT, MOVE_PROTECT},
    {MOVE_SHADOW_BALL, MOVE_FAINT_ATTACK, MOVE_ASTONISH, MOVE_PROTECT},
    {MOVE_CRABHAMMER, MOVE_SURF, MOVE_SLASH, MOVE_PROTECT},
    {MOVE_PSYCHIC, MOVE_SURF, MOVE_SWIFT, MOVE_PROTECT}
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
    Ascension_V111LegalizeEnemyParty();
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


// Free reversible build practice has real native Emerald EV/stat effects.
// Training caps each stat at 252 and full EV budget at 510; never changes
// the user's Pokemon species, moves, OT, nickname, IVs or personality.
void Ascension_TrainChosenStat(void)
{
    static const u8 fields[6]={
        MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV,
        MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV
    };
    struct Pokemon *mon;
    u16 total=0,left;
    u8 stat,part,val;
    gSpecialVar_Result=0;
    part=gSpecialVar_0x8004;
    if(part>=PARTY_SIZE||gSpecialVar_0x8005>=6)return;
    mon=&gPlayerParty[part];
    if(GetMonData(mon,MON_DATA_IS_EGG))return;
    if(GetMonData(mon,MON_DATA_SPECIES)==SPECIES_NONE)return;
    stat=gSpecialVar_0x8005;
    for(part=0;part<6;part++)
        total+=GetMonData(mon,fields[part]);
    val=GetMonData(mon,fields[stat]);
    if(val>=252||total>=510)
    {
        gSpecialVar_Result=2;
        return;
    }
    left=510-total;
    if(left>252-val)left=252-val;
    if(left>16)left=16;
    val+=left;
    SetMonData(mon,fields[stat],&val);
    CalculateMonStats(mon);
    gSpecialVar_Result=1;
}
// Deliberate Move Studio choices actually change active native Arena move
// slots. All three drills are supported Arena engine moves, no fake menus.
void Ascension_TrainChosenArenaMove(void)
{
    struct Pokemon *mon;
    u16 move;
    u8 slot;
    gSpecialVar_Result=0;
    if(gSpecialVar_0x8004>=PARTY_SIZE)return;
    mon=&gPlayerParty[gSpecialVar_0x8004];
    if(GetMonData(mon,MON_DATA_IS_EGG))return;
    if(GetMonData(mon,MON_DATA_SPECIES)==SPECIES_NONE)return;
    switch(gSpecialVar_0x8005)
    {
    case 1:move=MOVE_PROTECT;slot=3;break;
    case 2:move=MOVE_DOUBLE_TEAM;slot=2;break;
    case 3:move=MOVE_SWIFT;slot=1;break;
    default:return;
    }
    SetMonMoveSlot(mon,move,slot);
    gSpecialVar_Result=1;
}


// Original Emerald four-move learner UI bridge; no fake scripted move drills.
#include "ascension_studio_legal.inc"
EWRAM_DATA u8 gAscensionStudioMode=0;
void Ascension_StudioOn(void) {gAscensionStudioMode=TRUE;}
void Ascension_StudioOff(void) {gAscensionStudioMode=FALSE;}
u8 Ascension_GetStudioMoves(struct Pokemon *mon,u16 *output)
{
    u16 species,i,j,known[4];
    u8 count=0;
    if(!mon||GetMonData(mon,MON_DATA_IS_EGG))return 0;
    species=GetMonData(mon,MON_DATA_SPECIES);
    for(j=0;j<4;j++) known[j]=GetMonData(mon,MON_DATA_MOVE1+j);
    for(i=0;i<ARRAY_COUNT(sAscensionStudioIndex);i++)
    {
        const struct AscensionStudioEntry *entry=&sAscensionStudioIndex[i];
        if(entry->species!=species)continue;
        for(j=0;j<entry->count;j++)
        {
            u16 move=sAscensionStudioMoveBank[entry->start+j];
            u8 k;
            for(k=0;k<4;k++)if(known[k]==move)break;
            if(k==4)output[count++]=move;
        }
        return count;
    }
    return 0;
}


// Persistent GBA-native wardrobe, original player and rival sprite sheets.
void Ascension_ChooseWardrobeOutfit(void)
{
    u8 choice=gSpecialVar_0x8005;
    if(choice>4) {gSpecialVar_Result=0;return;}
    VarSet(VAR_ASCENSION_WARDROBE,choice);
    ObjectEventSetGraphicsId(&gObjectEvents[gPlayerAvatar.objectEventId],
        GetPlayerAvatarGraphicsIdByStateId(PLAYER_AVATAR_STATE_NORMAL));
    gSpecialVar_Result=1;
}

void Ascension_V11EnsureSafeEntry(void)
{
    const struct MapLayout *layout = gMapHeader.mapLayout;
    s16 x = gSaveBlock1Ptr->pos.x;
    s16 y = gSaveBlock1Ptr->pos.y;
    if (layout == NULL) return;
    if (x < 0 || y < 0 || x >= layout->width || y >= layout->height
        || ((layout->map[y * layout->width + x] >> 10) & 3) != 0)
    {
        gSaveBlock1Ptr->pos.x = 9;
        gSaveBlock1Ptr->pos.y = 18;
    }
}

#include "ascension_v111_services.inc"

#include "arena_moves.h"
// Beta: a Wildlands match is a duo. Anything beyond the first two party
// slots goes back to the PC before the match (the PC's move mode could
// place a third).
#include "pokemon_storage_system.h"
void Wildlands_TrimParty(void)
{
    u32 k, box;
    for (k = 2; k < PARTY_SIZE; k++)
    {
        if (!GetMonData(&gPlayerParty[k], MON_DATA_SPECIES))
            continue;
        for (box = 0; box < TOTAL_BOXES_COUNT; box++)
        {
            s16 pos = GetFirstFreeBoxSpot(box);
            if (pos >= 0)
            {
                SetBoxMonAt(box, pos, &gPlayerParty[k].box);
                break;
            }
        }
        ZeroMonData(&gPlayerParty[k]);
    }
    CompactPartySlots();
    CalculatePlayerPartyCount();
}
// Wildlands loadout: species-legal moves (Ascension studio bank) that the
// real-time Arena can actually perform. Keeps the current moves that qualify
// (player choices survive), then fills by power + STAB + type coverage.
static bool8 WildlandsRealtimeMove(u16 move)
{
    return move && ArenaMoves_Get(move) != NULL;
}
void Wildlands_ArenaLoadout(struct Pokemon *mon)
{
    u16 species = GetMonData(mon, MON_DATA_SPECIES), chosen[4] = {0}, i, j, n = 0;
    const struct AscensionStudioEntry *e = V111LegalEntry(species);
    bool8 damaging = FALSE;
    if (!e || GetMonData(mon, MON_DATA_IS_EGG))
    {
        V111Loadout(mon, NULL);
        return;
    }
    for (i = 0; i < 4; i++)
    {
        u16 move = GetMonData(mon, MON_DATA_MOVE1 + i);
        if (!V111LegalMove(e, move) || !WildlandsRealtimeMove(move))
            continue;
        for (j = 0; j < n; j++) if (chosen[j] == move) break;
        if (j == n) chosen[n++] = move;
    }
    while (n < 4)
    {
        s16 best = -32767;
        u16 pick = MOVE_NONE;
        for (i = 0; i < e->count; i++)
        {
            u16 move = sAscensionStudioMoveBank[e->start + i];
            u8 type = gBattleMoves[move].type;
            s16 score = gBattleMoves[move].power;
            if (!WildlandsRealtimeMove(move))
                continue;
            for (j = 0; j < n; j++) if (chosen[j] == move) break;
            if (j < n) continue;
            if (score > 120) score = 120;
            if (score)
            {
                if (type == gSpeciesInfo[species].types[0] || type == gSpeciesInfo[species].types[1]) score += 35;
                for (j = 0; j < n; j++) if (gBattleMoves[chosen[j]].power && gBattleMoves[chosen[j]].type == type) break;
                if (j == n) score += 25;
            }
            else if (move == MOVE_PROTECT) score = 25;
            if (score > best) { best = score; pick = move; }
        }
        if (!pick) break;
        chosen[n++] = pick;
    }
    for (i = 0; i < n; i++)
        if (gBattleMoves[chosen[i]].power) damaging = TRUE;
    if (!damaging)
    {
        V111Loadout(mon, NULL);   // no real-time attack in the bank: legacy pick
        return;
    }
    for (i = 0; i < 4; i++)
    {
        u16 cur = GetMonData(mon, MON_DATA_MOVE1 + i);
        if (cur != chosen[i])
            SetMonMoveSlot(mon, chosen[i], i);
    }
}

// Beta: party (and optionally every PC box) to arena-supported moves only.
static void Wildlands_SweepParty(void)
{
    u32 k;
    for (k = 0; k < PARTY_SIZE; k++)
        if (GetMonData(&gPlayerParty[k], MON_DATA_SPECIES) && !GetMonData(&gPlayerParty[k], MON_DATA_IS_EGG))
            Wildlands_ArenaLoadout(&gPlayerParty[k]);
}
void Wildlands_SweepAllMoves(void)
{
    struct Pokemon mon;
    u32 box, pos;
    Wildlands_SweepParty();
    for (box = 0; box < TOTAL_BOXES_COUNT; box++)
        for (pos = 0; pos < IN_BOX_COUNT; pos++)
        {
            struct BoxPokemon *bm = GetBoxedMonPtr(box, pos);
            if (!GetBoxMonData(bm, MON_DATA_SPECIES) || GetBoxMonData(bm, MON_DATA_IS_EGG))
                continue;
            BoxMonToMon(bm, &mon);
            Wildlands_ArenaLoadout(&mon);
            SetBoxMonAt(box, pos, &mon.box);
        }
}
// Script special: after the coach's PICK DUO the new duo is swept.
void Wildlands_SweepMoves(void)
{
    Wildlands_SweepParty();
}
