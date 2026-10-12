// Community scenery is separate from the five material palette biomes.
EWRAM_DATA u8 gArenaBiome = 0;

extern const u32 *const gArenaStageTiles[];
extern const u16 *const gArenaStagePalettes[];
#define sStageTiles gArenaStageTiles
#define sStagePalettes gArenaStagePalettes
EWRAM_DATA u8 gArenaStage = 0;
static void LoadArenaBiome(void)
{
    u16 map=gSaveBlock1Ptr->location.mapNum | (gSaveBlock1Ptr->location.mapGroup<<8);
    gArenaBiome=0;gArenaStage=0;
    switch(gBattleEnvironment)
    {
    case BATTLE_ENVIRONMENT_LONG_GRASS:gArenaStage=5;break;
    case BATTLE_ENVIRONMENT_UNDERWATER:
    case BATTLE_ENVIRONMENT_WATER:
    case BATTLE_ENVIRONMENT_POND:gArenaBiome=1;gArenaStage=1;break;
    case BATTLE_ENVIRONMENT_CAVE:
    case BATTLE_ENVIRONMENT_MOUNTAIN:gArenaBiome=2;gArenaStage=2;break;
    case BATTLE_ENVIRONMENT_SAND:gArenaBiome=3;gArenaStage=map==MAP_ROUTE111?3:6;break;
    case BATTLE_ENVIRONMENT_BUILDING:gArenaBiome=4;gArenaStage=4;break;
    case BATTLE_ENVIRONMENT_PLAIN:gArenaBiome=4;gArenaStage=7;break;
    }
    switch(map)
    {
    case MAP_PETALBURG_WOODS:gArenaBiome=0;gArenaStage=0;break;
    case MAP_MT_CHIMNEY:gArenaBiome=2;gArenaStage=16;break;
    case MAP_ROUTE119:
    case MAP_ROUTE120:if(gArenaBiome!=1){gArenaBiome=0;gArenaStage=5;}break;
    case MAP_ROUTE109:if(gArenaBiome!=1){gArenaBiome=3;gArenaStage=6;}break;
    case MAP_RUSTBORO_CITY_GYM:gArenaStage=8;break;
    case MAP_DEWFORD_TOWN_GYM:gArenaStage=9;break;
    case MAP_MAUVILLE_CITY_GYM:gArenaStage=10;break;
    case MAP_LAVARIDGE_TOWN_GYM_1F:
    case MAP_LAVARIDGE_TOWN_GYM_B1F:gArenaStage=11;break;
    case MAP_PETALBURG_CITY_GYM:gArenaStage=12;break;
    case MAP_FORTREE_CITY_GYM:gArenaStage=13;break;
    case MAP_MOSSDEEP_CITY_GYM:gArenaStage=14;break;
    case MAP_SOOTOPOLIS_CITY_GYM_1F:
    case MAP_SOOTOPOLIS_CITY_GYM_B1F:gArenaStage=15;break;
    }
    // Distinct Bronze championship battleground in original Arena engine.
    if(map==MAP_ASCENSION_BRONZE_BOSS){gArenaBiome=4;gArenaStage=8;}
    if(gBattleTypeFlags&BATTLE_TYPE_TRAINER)
    {
        u8 pic=gTrainers[gTrainerBattleOpponent_A].trainerPic;
        if(pic>=TRAINER_PIC_LEADER_ROXANNE&&pic<=TRAINER_PIC_LEADER_JUAN)
            gArenaStage=8+pic-TRAINER_PIC_LEADER_ROXANNE;
    }
    // Tower themes: native game scenery, preserving all original combat art.
    // For trainer battles this must run AFTER the native trainer-pic override.
    switch(map)
    {
    case MAP_ASCENSION_TOWER_1: gArenaBiome=2;gArenaStage=2;break;  // stone
    case MAP_ASCENSION_TOWER_2: gArenaBiome=4;gArenaStage=7;break; // windy sky
    case MAP_ASCENSION_TOWER_3: gArenaBiome=0;gArenaStage=0;break;  // grass
    case MAP_ASCENSION_TOWER_4: gArenaBiome=4;gArenaStage=4;break; // psychic/ghost
    case MAP_ASCENSION_TOWER_5: gArenaBiome=4;gArenaStage=11;break; // volcanic
    case MAP_ASCENSION_TOWER_6: gArenaBiome=1;gArenaStage=1;break;  // water
    case MAP_ASCENSION_TOWER_7: gArenaBiome=4;gArenaStage=4;break; // electric
    case MAP_ASCENSION_TOWER_8: gArenaBiome=4;gArenaStage=7;break; // mystery
    case MAP_ASCENSION_ELITE_1:gArenaBiome=4;gArenaStage=13;break;
        case MAP_ASCENSION_ELITE_2:gArenaBiome=4;gArenaStage=12;break;
        case MAP_ASCENSION_ELITE_3:gArenaBiome=4;gArenaStage=10;break;
        case MAP_ASCENSION_ELITE_4:gArenaBiome=4;gArenaStage=14;break;
        case MAP_ASCENSION_SUMMIT:
        gArenaBiome=4;
        switch(VarGet(VAR_ASCENSION_FLOOR))
        {
        case 0:gArenaStage=13;break; // Arctic / open sky
        case 1:gArenaStage=12;break; // Iron / steel coliseum
        case 2:gArenaStage=10;break; // Lightning / electric gym
        case 3:gArenaStage=14;break; // Crystal / psychic chamber
        default:gArenaStage=7;break;
        }
        break;   // champion
    case MAP_ASCENSION_BRONZE_BOSS:gArenaBiome=4;gArenaStage=8;break;
    case MAP_ASCENSION_LEADER_2:gArenaBiome=4;gArenaStage=13;break;
    case MAP_ASCENSION_LEADER_3:gArenaBiome=0;gArenaStage=5;break;
    case MAP_ASCENSION_LEADER_4:gArenaBiome=4;gArenaStage=14;break;
    case MAP_ASCENSION_LEADER_5:gArenaBiome=2;gArenaStage=16;break;
    case MAP_ASCENSION_LEADER_6:gArenaBiome=4;gArenaStage=15;break;
    case MAP_ASCENSION_LEADER_7:gArenaBiome=4;gArenaStage=10;break;
    case MAP_ASCENSION_LEADER_8:gArenaBiome=4;gArenaStage=12;break;
    case MAP_ASCENSION_LEADER_9:gArenaBiome=4;gArenaStage=7;break;
    }
    if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && FlagGet(FLAG_ARENA_PRACTICE))
    {
        static const u8 sWildlandsGrounds[5]={13,10,14,15,16};
        gArenaStage=sWildlandsGrounds[VarGet(VAR_ASCENSION_FLOOR)%5];
        gArenaBiome=(gArenaStage==15)?1:(gArenaStage==16?2:4);
    }
    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;
    if(WildlandsWorld_Active())
        return;
    LoadPalette(sStagePalettes[gArenaStage],0,512);
    StormBiome(sStageTiles[gArenaStage],sStagePalettes[gArenaStage]);
    LoadBgTiles(1,sStageTiles[gArenaStage],38400,0);
    LoadBgTilemap(1,sForestMap,sizeof(sForestMap),0);
}
