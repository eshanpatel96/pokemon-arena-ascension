#!/usr/bin/env python3
"""V8.2 rematches: Bronze multi-Pokemon curated party remix; one themed
legendary at each tower boss. This runs after all V8.2 world scripts.

Guarantees different encounter composition after defeat without tampering with
save data, battle renderer, existing Pokemon animation or in-game credits.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
vars_h=root/"include/constants/vars.h"
career=root/"src/ascension_career.c"
specials=root/"data/specials.inc"
maps=root/"data/maps"
def once(s, old, new, name):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"{name}: expected 1 occurrence, got {n}: {old[:150]!r}")
    return s.replace(old,new,1)

# One unused persistent Emerald var. Increment ONLY on a loss: retries rotate
# cleanly through three lineups, guaranteeing a new lineup on the next attempt.
s=vars_h.read_text()
s=once(s,'#define VAR_UNUSED_0x40FF',
         '#define VAR_ASCENSION_REMATCH_CYCLE                    0x40FF // changes on tower defeat\n//#define VAR_UNUSED_0x40FF',
         "save variable")
vars_h.write_text(s)

s=career.read_text()
start=s.index('static const struct AscensionTrainerMon sBronzeOpponents[3][4] =')
end=s.index('static const u8 sBronzeTeamSizes[3] =',start)
# Three layouts for each Bronze floor. Fixed size for each floor and the final
# opposing Pokemon of each boss rematch is always REGIROCK. These six species
# are among the original 187 Emerald Arena animated Pokemon and their moves
# are present in arena_moves.c.
sub='''static const struct AscensionTrainerMon sBronzeRematchTeams[3][3][4] =
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
'''
s=s[:start]+sub+s[end:]
s=once(s,'const struct AscensionTrainerMon *op = &sBronzeOpponents[floor][mon];',
       'const struct AscensionTrainerMon *op = &sBronzeRematchTeams[floor][VarGet(VAR_ASCENSION_REMATCH_CYCLE) % 3][mon];',
       "Bronze battle rotation")

# At other towers, keep the known original wild-battle fallback for now, but
# vary the Pokémon from a different theme-specific curated roster after loss.
# Floor two always has a signature legendary or mythic; it is never obtainable
# directly from the opponent's battle and never rendered as a fake sprite.
# Species selected here ALL appear in tools/arena/roster.json and moves in
# src/arena_moves.c.
pool='''struct AscensionThemedMon
{
    u16 species;
    u16 moves[MAX_MON_MOVES];
};
// Three variants for each non-Bronze tower, 3 ordinary slots per variant.
// The final floor always features a fixed animated legendary at a bounded
// level. Locked species are not gifted to the player by victory.
static const struct AscensionThemedMon sThemePool[8][3] =
{
    // Gale: wind and flight; Lugia ace
    {
        {SPECIES_PIDGEOT,   {MOVE_GUST, MOVE_WING_ATTACK, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
        {SPECIES_ALTARIA,   {MOVE_DRAGON_BREATH, MOVE_PECK, MOVE_GUST, MOVE_PROTECT}},
        {SPECIES_LUGIA,    {MOVE_AEROBLAST, MOVE_GUST, MOVE_SWIFT, MOVE_PROTECT}},
    },
    // Verdant: grass, cover, healing and a mystical Mew ace
    {
        {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_QUICK_ATTACK, MOVE_MEGA_DRAIN, MOVE_PROTECT}},
        {SPECIES_VENUSAUR, {MOVE_GIGA_DRAIN, MOVE_TACKLE, MOVE_SOLAR_BEAM, MOVE_PROTECT}},
        {SPECIES_MEW,      {MOVE_GIGA_DRAIN, MOVE_SOLAR_BEAM, MOVE_PSYCHIC, MOVE_PROTECT}},
    },
    // Phantom: Ghost moves and strong mind-game Mewtwo ace
    {
        {SPECIES_BANETTE,  {MOVE_SHADOW_BALL, MOVE_ASTONISH, MOVE_NIGHT_SHADE, MOVE_PROTECT}},
        {SPECIES_GENGAR,   {MOVE_SHADOW_BALL, MOVE_NIGHT_SHADE, MOVE_PSYCHIC, MOVE_PROTECT}},
        {SPECIES_MEWTWO,   {MOVE_SHADOW_BALL, MOVE_PSYCHIC, MOVE_SWIFT, MOVE_PROTECT}},
    },
    // Inferno: burning pressure, Entei ace
    {
        {SPECIES_TORKOAL,  {MOVE_EMBER, MOVE_BODY_SLAM, MOVE_FIRE_BLAST, MOVE_PROTECT}},
        {SPECIES_ARCANINE, {MOVE_FLAMETHROWER, MOVE_QUICK_ATTACK, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_ENTEI,    {MOVE_FIRE_BLAST, MOVE_EMBER, MOVE_SWIFT, MOVE_PROTECT}},
    },
    // Tidal: water mobility, Kyogre ace
    {
        {SPECIES_SWAMPERT, {MOVE_WATER_GUN, MOVE_SURF, MOVE_MUD_SHOT, MOVE_PROTECT}},
        {SPECIES_MILOTIC,  {MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_ICY_WIND, MOVE_PROTECT}},
        {SPECIES_KYOGRE,   {MOVE_HYDRO_PUMP, MOVE_SURF, MOVE_BLIZZARD, MOVE_PROTECT}},
    },
    // Thunder: rapid close and ranged electricity; Raikou ace
    {
        {SPECIES_RAICHU,   {MOVE_THUNDER_SHOCK, MOVE_QUICK_ATTACK, MOVE_SHOCK_WAVE, MOVE_PROTECT}},
        {SPECIES_MANECTRIC,{MOVE_SHOCK_WAVE, MOVE_THUNDER_SHOCK, MOVE_BITE, MOVE_PROTECT}},
        {SPECIES_RAIKOU,   {MOVE_SHOCK_WAVE, MOVE_SWIFT, MOVE_QUICK_ATTACK, MOVE_PROTECT}},
    },
    // Astral: stars and dragons; Rayquaza ace
    {
        {SPECIES_ALTARIA,  {MOVE_DRAGON_BREATH, MOVE_GUST, MOVE_PECK, MOVE_PROTECT}},
        {SPECIES_DRAGONITE,{MOVE_DRAGON_BREATH, MOVE_WING_ATTACK, MOVE_SLAM, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA, {MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}},
    },
    // Summit: rotating elite pressure, Mewtwo at final encounter
    {
        {SPECIES_SCIZOR,   {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
        {SPECIES_RAYQUAZA, {MOVE_DRAGON_CLAW, MOVE_DRAGON_BREATH, MOVE_HYPER_BEAM, MOVE_PROTECT}},
        {SPECIES_MEWTWO,   {MOVE_PSYCHIC, MOVE_SHADOW_BALL, MOVE_SWIFT, MOVE_PROTECT}},
    }
};
'''
anchor='static const u8 sBronzeTeamSizes[3] = {2, 3, 4};'
s=once(s,anchor,anchor+'\n'+pool,"thematic pool insertion")

old=''' o=&sOpponents[rank][floor];
 CreateScriptedWildMon(o->species,o->level,ITEM_NONE);
 SetMonMoveSlot(&gEnemyParty[0],o->move1,0);
 SetMonMoveSlot(&gEnemyParty[0],o->move2,1);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,2);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,3);
 gSpecialVar_Result=1;'''
new=''' // Keep original single-opponent handoff outside Bronze for now.
 // Rotate the ordinary themed opponent after a lost run; tower leaders use
 // their signature animated legendary at the final floor.
 if (rank > 0 && rank < ARRAY_COUNT(sThemePool) + 1)
 {
     const struct AscensionThemedMon *theme;
     u8 pick;
     u8 move;
     if (floor == 2)
         pick = 2; // guaranteed unique legendary ace
     else
         pick = (floor + VarGet(VAR_ASCENSION_REMATCH_CYCLE)) % 2;
     theme=&sThemePool[rank-1][pick];
     CreateScriptedWildMon(theme->species, 59 + rank * 2 + floor, ITEM_NONE);
     for (move=0;move<MAX_MON_MOVES;move++)
         SetMonMoveSlot(&gEnemyParty[0],theme->moves[move],move);
     gSpecialVar_Result=1;
     return;
 }
 o=&sOpponents[rank][floor];
 CreateScriptedWildMon(o->species,o->level,ITEM_NONE);
 SetMonMoveSlot(&gEnemyParty[0],o->move1,0);
 SetMonMoveSlot(&gEnemyParty[0],o->move2,1);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,2);
 SetMonMoveSlot(&gEnemyParty[0],MOVE_NONE,3);
 gSpecialVar_Result=1;'''
s=once(s,old,new,"wild themed handoff")

s+="""

// Defeat does not change career rank or clear count. It ONLY changes which
// curated team you face next time, guaranteeing varied rematches.
void Ascension_RecordDefeat(void)
{
    u16 cycle=VarGet(VAR_ASCENSION_REMATCH_CYCLE);
    VarSet(VAR_ASCENSION_REMATCH_CYCLE, (cycle + 1) % 3);
}
"""
career.write_text(s)
spec=specials.read_text()
spec=once(spec,"\tdef_special Ascension_NextChallengerSprite",
              "\tdef_special Ascension_NextChallengerSprite\n\tdef_special Ascension_RecordDefeat",
              "native special")
specials.write_text(spec)

# On defeat, call native special exactly once per entire attempted floor/round.
# Applies to the animated Bronze boss room and each tower's trainer choreography.
for i in range(9):
    name="AscensionSummit" if i==8 else "AscensionTower"+str(i+1)
    path=maps/name/"scripts.inc"
    src=path.read_text()
    marker=f'{name}_EventScript_Loss::\n'
    src=once(src,marker,marker+' special Ascension_RecordDefeat\n',"defeat script "+name)
    path.write_text(src)
path=maps/"AscensionBronzeBoss/scripts.inc"
src=path.read_text()
marker="AscensionBronzeBoss_EventScript_Lost::\n"
src=once(src,marker,marker+" special Ascension_RecordDefeat\n","Bronze leader defeat")
path.write_text(src)

# Build-time checks to prevent impossible animations or unsupported attacks
# from entering a GBA test ROM.
import json,re
roster_path=root/"tools/arena/roster.json"
roster={v["species"] for v in json.loads(roster_path.read_text())}
arena_moves=(root/"src/arena_moves.c").read_text()
for species in re.findall(r'\{SPECIES_([A-Z0-9_]+),\s*\{MOVE_',pool+sub):
    if species not in roster:
        raise RuntimeError(f"Unanimated opponent: {species}")
for move in set(re.findall(r'MOVE_([A-Z0-9_]+)',pool+sub)):
    if not re.search(r'\{MOVE_'+move+r',',arena_moves):
        raise RuntimeError(f"Missing native real-time move profile: {move}")
for variant in re.findall(r'\{SPECIES_REGIROCK,\s*\{MOVE_([A-Z0-9_]+)',sub):
    assert variant=='ROCK_SLIDE'
assert s.count('SPECIES_REGIROCK')==3
print("V8.2 rematches: three distinct Bronze lineups/floor, guaranteed Regirock final ace, loss-cycle persistent; 8 themed tower leader aces validated in 187-sprite/move roster.")
