#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
def rep(old,new):
 global s
 n=s.count(old)
 if n != 1: raise SystemExit("Upstream source mismatch: expected one occurrence, got "+str(n)+" for "+repr(old[:90]))
 s=s.replace(old,new,1)
rep('static const u8 sDemoName[] = _("ARENA");','static const u8 sDemoName[] = _("ASCEND");')
rep('    {SPECIES_EEVEE,36}, {SPECIES_BLASTOISE,36}, {SPECIES_SCIZOR,15},\n    {SPECIES_BLAZIKEN,20}, {SPECIES_DRAGONITE,30}, {SPECIES_CHARIZARD,36},','    {SPECIES_SCIZOR,15}, {SPECIES_BLAZIKEN,20}, {SPECIES_DRAGONITE,30},\n    {SPECIES_EEVEE,36}, {SPECIES_BLASTOISE,36}, {SPECIES_CHARIZARD,36},')
rep('static u16 MonVisualScale(u8 side)\n{\n    (void)side;\n    return 256;\n}\n', '''static u16 MonVisualScale(u8 side)
{
    switch (gBattleMons[side].species)
    {
    case SPECIES_EEVEE:
    case SPECIES_PIKACHU:
    case SPECIES_TREECKO:
    case SPECIES_SQUIRTLE:
    case SPECIES_BULBASAUR:
    case SPECIES_POOCHYENA: return 232;
    case SPECIES_DRAGONITE:
    case SPECIES_RAYQUAZA:
    case SPECIES_SNORLAX:
    case SPECIES_BLASTOISE:
    case SPECIES_CHARIZARD: return 244;
    default: return 240;
    }
}
static u16 MonMassSpeedFactor(u8 side)
{
    switch (gBattleMons[side].species)
    {
    case SPECIES_RAYQUAZA:
    case SPECIES_DRAGONITE:
    case SPECIES_BLASTOISE:
    case SPECIES_SNORLAX: return 232;
    case SPECIES_CHARIZARD:
    case SPECIES_BLAZIKEN: return 244;
    default: return 256;
    }
}
''')
rep('    speed=StormSpeed(side,256 + Clamp(speed, 1, 120) * 2);\n    return (gBattleMons[side].status1&STATUS1_PARALYSIS)', '    speed=StormSpeed(side,256 + Clamp(speed, 1, 120) * 2);\n    speed=speed*MonMassSpeedFactor(side)/256;\n    return (gBattleMons[side].status1&STATUS1_PARALYSIS)')
rep('''        {SPECIES_CHARIZARD,36}, {SPECIES_BLASTOISE,36}, {SPECIES_EEVEE,25},
        {SPECIES_DRAGONITE,30}, {SPECIES_SCIZOR,15}, {SPECIES_BLAZIKEN,20}''','''        {SPECIES_CHARIZARD,60}, {SPECIES_BLASTOISE,60}, {SPECIES_EEVEE,60},
        {SPECIES_DRAGONITE,60}, {SPECIES_SCIZOR,60}, {SPECIES_BLAZIKEN,60}''')
rep('''        {SPECIES_TREECKO,11}, {SPECIES_POOCHYENA,12}, {SPECIES_BULBASAUR,12},
        {SPECIES_SQUIRTLE,15}, {SPECIES_GROVYLE,16}, {SPECIES_SCEPTILE,43}''','''        {SPECIES_TREECKO,60}, {SPECIES_POOCHYENA,60}, {SPECIES_BULBASAUR,60},
        {SPECIES_SQUIRTLE,60}, {SPECIES_GROVYLE,60}, {SPECIES_SCEPTILE,60}''')
rep('''    u32 i;
#endif
    if (!sDemoRequested) return FALSE;''','''    static const u16 sDemoMoves[6][MAX_MON_MOVES] =
    {
        {MOVE_FLAMETHROWER, MOVE_WING_ATTACK, MOVE_SLASH, MOVE_PROTECT},
        {MOVE_WATER_GUN, MOVE_HYDRO_PUMP, MOVE_BITE, MOVE_PROTECT},
        {MOVE_QUICK_ATTACK, MOVE_BITE, MOVE_TAIL_WHIP, MOVE_PROTECT},
        {MOVE_WING_ATTACK, MOVE_SLAM, MOVE_AGILITY, MOVE_HYPER_BEAM},
        {MOVE_QUICK_ATTACK, MOVE_SLASH, MOVE_DOUBLE_TEAM, MOVE_PROTECT},
        {MOVE_BLAZE_KICK, MOVE_SLASH, MOVE_EMBER, MOVE_PROTECT}
    };
    u32 i, j;
#endif
    if (!sDemoRequested) return FALSE;''')
rep('''    gSaveBlock1Ptr->location.mapGroup = MAP_GROUP(MAP_OLDALE_TOWN);
    gSaveBlock1Ptr->location.mapNum = MAP_NUM(MAP_OLDALE_TOWN);
    gSaveBlock1Ptr->location.warpId = -1;
    gSaveBlock1Ptr->location.x = 10;
    gSaveBlock1Ptr->location.y = 17;
    gSaveBlock1Ptr->pos.x = 10;
    gSaveBlock1Ptr->pos.y = 17;
    SetLastHealLocationWarp(HEAL_LOCATION_OLDALE_TOWN);''','''    SetWarpDestination(MAP_GROUP(MAP_ASCENSION_CITY), MAP_NUM(MAP_ASCENSION_CITY),
                       WARP_ID_NONE, 26, 40);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ASCENSION_CITY);
    VarSet(VAR_ASCENSION_TUTORIAL, 0);''')
rep('''    for (i = 0; i < ARRAY_COUNT(team); i++)
        CreateMon(&gPlayerParty[i], team[i].species, team[i].level,
                  20, TRUE, i * 2, OT_ID_PLAYER_ID, 0);
    for (i = 0; i < ARRAY_COUNT(box); i++)''','''    for (i = 0; i < ARRAY_COUNT(team); i++)
    {
        CreateMon(&gPlayerParty[i], team[i].species, team[i].level,
                  20, TRUE, i * 2, OT_ID_PLAYER_ID, 0);
        for (j = 0; j < MAX_MON_MOVES; j++)
            SetMonMoveSlot(&gPlayerParty[i], sDemoMoves[i][j], j);
    }
    for (i = 0; i < ARRAY_COUNT(box); i++)''')
p.write_text(s)
print("Clean upstream Emerald Arena patched for Ascension V6.1")
