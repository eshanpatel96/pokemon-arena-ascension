#include "global.h"
#include "event_data.h"
#include "fieldmap.h"
#include "field_player_avatar.h"
#include "overworld.h"
#include "script_movement.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"
#include "constants/maps.h"
#include "constants/layouts.h"
#include "constants/vars.h"

// Temporary movement only; no changes to persistent save structures.
static EWRAM_DATA u8 sV11Walk[64] = {0};
static u8 StepTo(u8 n, s16 *p, s16 goal, u8 negative, u8 positive)
{
    while (*p != goal && n < sizeof(sV11Walk)-2)
    {
        sV11Walk[n++] = *p < goal ? positive : negative;
        *p += *p < goal ? 1 : -1;
    }
    return n;
}
static void WalkToMark(bool8 returning)
{
    s16 x,y;
    u8 n=0;
    bool8 summit = gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ASCENSION_SUMMIT)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ASCENSION_SUMMIT);
    PlayerGetDestCoords(&x,&y); x-=MAP_OFFSET; y-=MAP_OFFSET;
    if (summit)
    {
        // The central corridor is clear after the Master steps to (5,16).
        n=StepTo(n,&x,9,MOVEMENT_ACTION_WALK_NORMAL_LEFT,MOVEMENT_ACTION_WALK_NORMAL_RIGHT);
        n=StepTo(n,&y,returning?17:8,MOVEMENT_ACTION_WALK_NORMAL_UP,MOVEMENT_ACTION_WALK_NORMAL_DOWN);
        if (!returning) n=StepTo(n,&x,6,MOVEMENT_ACTION_WALK_NORMAL_LEFT,MOVEMENT_ACTION_WALK_NORMAL_RIGHT);
    }
    else
    {
        // Route below the inner rectangle, never across the Master at (4,7).
        n=StepTo(n,&y,6,MOVEMENT_ACTION_WALK_NORMAL_UP,MOVEMENT_ACTION_WALK_NORMAL_DOWN);
        n=StepTo(n,&x,returning?5:2,MOVEMENT_ACTION_WALK_NORMAL_LEFT,MOVEMENT_ACTION_WALK_NORMAL_RIGHT);
        if (!returning) n=StepTo(n,&y,4,MOVEMENT_ACTION_WALK_NORMAL_UP,MOVEMENT_ACTION_WALK_NORMAL_DOWN);
    }
    sV11Walk[n++]= returning ? MOVEMENT_ACTION_FACE_UP : MOVEMENT_ACTION_FACE_RIGHT;
    sV11Walk[n]=MOVEMENT_ACTION_STEP_END;
    ScriptMovement_StartObjectMovementScript(LOCALID_PLAYER,gSaveBlock1Ptr->location.mapNum,
                                             gSaveBlock1Ptr->location.mapGroup,sV11Walk);
}
void AscensionV11_CourtLineUp(void) { WalkToMark(FALSE); }
void AscensionV11_CourtReturn(void) { WalkToMark(TRUE); }

bool8 AscensionV11_RepairRoomLayout(void)
{
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    u16 desired=0;
    bool8 repaired=FALSE;
    s16 x=gSaveBlock1Ptr->pos.x,y=gSaveBlock1Ptr->pos.y;
    switch(map)
    {
    case MAP_ASCENSION_BRONZE_BOSS: desired=LAYOUT_ASCENSION_V11_BRONZE; break;
    case MAP_ASCENSION_LEADER_2: desired=LAYOUT_ASCENSION_V11_GALE; break;
    case MAP_ASCENSION_LEADER_3: desired=LAYOUT_ASCENSION_V11_VERDANT; break;
    case MAP_ASCENSION_LEADER_4: desired=LAYOUT_ASCENSION_V11_PHANTOM; break;
    case MAP_ASCENSION_LEADER_5: desired=LAYOUT_ASCENSION_V11_INFERNO; break;
    case MAP_ASCENSION_LEADER_6: desired=LAYOUT_ASCENSION_V11_TIDAL; break;
    case MAP_ASCENSION_LEADER_7: desired=LAYOUT_ASCENSION_V11_THUNDER; break;
    case MAP_ASCENSION_LEADER_8: desired=LAYOUT_ASCENSION_V11_ASTRAL; break;
    case MAP_ASCENSION_LEADER_9: desired=LAYOUT_ASCENSION_V11_CHAMPION; break;
    case MAP_ASCENSION_SUMMIT:
        switch(VarGet(VAR_ASCENSION_FLOOR))
        {
        case 0: desired=LAYOUT_ASCENSION_V11_ELITEARCTIC; break;
        case 1: desired=LAYOUT_ASCENSION_V11_ELITEIRON; break;
        case 2: desired=LAYOUT_ASCENSION_V11_ELITELIGHTNING; break;
        default: desired=LAYOUT_ASCENSION_V11_ELITECRYSTAL; break;
        }
        break;
    default: return FALSE;
    }
    if(gSaveBlock1Ptr->mapLayoutId != desired)
    {
        SetCurrentMapLayout(desired);
        repaired=TRUE;
    }
    // Old-room coordinates cannot strand a returning save behind new pillars.
    if (repaired || x<0 || y<0 || x>=gMapHeader.mapLayout->width || y>=gMapHeader.mapLayout->height
        || (gMapHeader.mapLayout->map[y*gMapHeader.mapLayout->width+x]&0xC00)
        || (x==12&&y==18) || (x==9&&(y==5||y==16)))
    {
        gSaveBlock1Ptr->pos.x=9; gSaveBlock1Ptr->pos.y=18;
        repaired=TRUE;
    }
    if (repaired) LoadObjEventTemplatesFromHeader();
    return repaired;
}
