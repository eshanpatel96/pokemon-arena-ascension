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

extern EWRAM_DATA u32 gWildlandsWorldTelemetry[16];
extern EWRAM_DATA u32 gWildlandsWorldAudit[8];

#endif
