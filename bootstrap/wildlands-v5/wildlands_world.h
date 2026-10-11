#ifndef GUARD_WILDLANDS_WORLD_H
#define GUARD_WILDLANDS_WORLD_H

#include "global.h"
#include "arena_navigation.h"

#define WL_TERRAIN_SOLID      (1 << 0)
#define WL_TERRAIN_DEEP_WATER (1 << 1)
#define WL_TERRAIN_WET        (1 << 2)
#define WL_TERRAIN_CONCEAL    (1 << 3)
#define WL_TERRAIN_BRIDGE     (1 << 4)

bool8 WildlandsWorld_Active(void);
void WildlandsWorld_Init(void);
void WildlandsWorld_LoadGraphics(void);
void WildlandsWorld_UpdateCamera(s16 cameraX, s16 cameraY);
void WildlandsWorld_VBlank(void);
void WildlandsWorld_TickBody(u8 side, s16 x, s16 y);
void WildlandsWorld_RecordProjectileBlock(void);
void WildlandsWorld_RestorePalettes(void);
void WildlandsWorld_ReleaseNav(void);

u8 WildlandsWorld_TerrainAt(s16 x, s16 y);
bool8 WildlandsWorld_LineClear(s16 x1, s16 y1, s16 x2, s16 y2, u8 radius);
bool8 WildlandsWorld_BodyLineClear(u8 side, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius);
bool8 WildlandsWorld_SpeciesLineClear(u16 species, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius);
bool8 WildlandsWorld_CanStandSide(u8 side, s16 x, s16 y, u8 radius);
bool8 WildlandsWorld_CanStandSpecies(u16 species, s16 x, s16 y, u8 radius);
bool8 WildlandsWorld_IsConcealed(s16 x, s16 y);
bool8 WildlandsWorld_IsWater(s16 x, s16 y);
bool8 WildlandsWorld_IsWet(s16 x, s16 y);
u16 WildlandsWorld_ClipRay(s16 x, s16 y, s16 dx, s16 dy, u16 distance, u8 radius);

u8 WildlandsWorld_NextWaypointSide(u8 side, s16 x, s16 y, s16 goalX, s16 goalY, struct ArenaPoint *next);
u8 WildlandsWorld_NextWaypointSpecies(u16 species, s16 x, s16 y, s16 goalX, s16 goalY, struct ArenaPoint *next);

bool8 WildlandsWorld_InRoom(s16 x, s16 y);
void WildlandsWorld_OutdoorPos(s32 *x, s32 *y);
bool8 WildlandsWorld_PollDoor(s16 x, s16 y, bool8 facingUp, bool8 facingDown, s16 *outX, s16 *outY);
void WildlandsWorld_ClampCamera(s32 px, s32 py, s32 *camX, s32 *camY);
s8 WildlandsWorld_SlideNudge(u8 side, s16 x, s16 y, s8 sx, s8 sy);
void WildlandsWorld_DoorArrival(u8 door, s16 *x, s16 *y);
bool8 WildlandsWorld_RoomExitPos(s16 x, s16 y, s16 *ex, s16 *ey);
u8 WildlandsWorld_RoomCount(void);
s8 WildlandsWorld_RoomIndexAt(s16 x, s16 y);
u16 WildlandsWorld_RoomLegend(s8 room);
void WildlandsWorld_NavPoint(u16 index, s16 *x, s16 *y);
u16 WildlandsWorld_NavPointCount(void);
u8 WildlandsWorld_DoorCount(void);
void WildlandsWorld_DoorInfo(u8 i, s16 *x, s16 *y, bool8 *lair);

extern EWRAM_DATA u32 gWildlandsWorldTelemetry[16];
extern EWRAM_DATA u32 gWildlandsRoomTelemetry[8];
extern EWRAM_DATA u32 gWildlandsWorldAudit[8];

#endif
