#!/usr/bin/env python3
"""V10.2 real native boss-cover variation, no extra sprites/assets.

Each boss uses existing Arena props and ArenaPhysics collision/breaking.
Differences are physical and persist when the next enemy Pokemon enters:
stone with high HP, airy open lanes, natural cover, psychic crystals,
basalt-open inferno, flood-compatible water lanes, conductive pod chain
reactions and high-health observatory crystals. The native effects remain
counterable and no new per-frame RAM allocation is created.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);path=root/"src/realtime_arena.c"
s=path.read_text()
old="""        ArenaPhysics_Init();
        sEnvironmentInitialized=TRUE;"""
assert s.count(old)==1
new="""        ArenaPhysics_Init();
        // V10.2: thematic physical terrain for actual tower boss fights.
        // This is not a new rendering engine, scripted damage, or fake floor.
        if(VarGet(VAR_ASCENSION_CAREER_ACTIVE))
        {
            u16 map=gSaveBlock1Ptr->location.mapNum |
                    (gSaveBlock1Ptr->location.mapGroup<<8);
            u8 mode=0;
            switch(map)
            {
            case MAP_ASCENSION_BRONZE_BOSS:mode=1;break;
            case MAP_ASCENSION_LEADER_2:mode=2;break;
            case MAP_ASCENSION_LEADER_3:mode=3;break;
            case MAP_ASCENSION_LEADER_4:mode=4;break;
            case MAP_ASCENSION_LEADER_5:mode=5;break;
            case MAP_ASCENSION_LEADER_6:mode=6;break;
            case MAP_ASCENSION_LEADER_7:mode=7;break;
            case MAP_ASCENSION_LEADER_8:mode=8;break;
            }
            if(mode)
            {
                u8 j;
                for(j=0;j<ARENA_OBSTACLES;j++)
                {
                    bool8 remove=FALSE;
                    u8 hp=gArenaProps[j].hp;
                    switch(mode)
                    {
                    case 1:hp=5;break; // quarry pillars endure several hits
                    case 2:hp=1;remove=(j>=4);break; // Gale: broad open lanes
                    case 3:hp=4;break; // Verdant: thick persistent tree cover
                    case 4:hp=2;remove=(j<2);break; // crypt decoy/corner routes
                    case 5:remove=TRUE;break; // original open basalt furnace
                    case 6:hp=2;remove=(j==2 || j==3);break; // flood channels
                    case 7:
                        hp=1;
                        remove=(j==1 || j==2);
                        if(j>=4)gArenaProps[j].kind=ARENA_PROP_POD;
                        break; // conductive reactor pods can chain-explode
                    case 8:
                        hp=4;
                        if(j>=3)gArenaProps[j].kind=ARENA_PROP_CRYSTAL;
                        break; // heavy observatory crystals
                    }
                    if(remove)
                    {
                        gArenaProps[j].broken=TRUE;
                        gArenaProps[j].hp=0;
                        gArenaPhysicsTelemetry.hp[j]=0;
                        gArenaPhysicsTelemetry.solidMask &= ~(1<<j);
                        ArenaNav_SetObstacle(j,FALSE);
                    }
                    else
                    {
                        gArenaProps[j].hp=gArenaProps[j].maxHp=hp;
                        gArenaPhysicsTelemetry.hp[j]=hp;
                    }
                }
            }
        }
        sEnvironmentInitialized=TRUE;"""
path.write_text(s.replace(old,new,1))
assert "mode=7" in path.read_text()
print("V10.2 physical boss arenas: eight distinct native Arena obstacle/cover behaviors, no added sheets or EWRAM globals.")
