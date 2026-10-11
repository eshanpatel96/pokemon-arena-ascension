#include "global.h"
#include "wildlands_world.h"
#include "wildlands_world_data.h"
#include "bg.h"
#include "data.h"
#include "decompress.h"
#include "event_data.h"
#include "gpu_regs.h"
#include "main.h"
#include "metatile_behavior.h"
#include "palette.h"
#include "battle.h"
#include "constants/abilities.h"
#include "constants/pokemon.h"
#include "fieldmap.h"

extern const struct Tileset gTileset_General;
extern const struct Tileset gTileset_Fortree;

static const u16 sWorldSlice[] = INCBIN_U16("data/wildlands_world/slice.bin");
static const struct ArenaPoint sNavPoints[] =
{
#include "data/wildlands_world/nav.inc"
};

static EWRAM_DATA bool8 sActive = FALSE;
static EWRAM_DATA s16 sLastTileX = 0x7FFF;
static EWRAM_DATA s16 sLastTileY = 0x7FFF;
static EWRAM_DATA u8 sLastChunkX = 0xFF;
static EWRAM_DATA u8 sLastChunkY = 0xFF;

EWRAM_DATA u32 gWildlandsWorldTelemetry[16] = {};

static s32 Abs32(s32 n) { return n < 0 ? -n : n; }

bool8 WildlandsWorld_Active(void)
{
    return sActive;
}

static bool8 InSlice(s16 mx, s16 my)
{
    return mx >= WL_SLICE_BASE_X && mx < WL_SLICE_BASE_X + WL_SLICE_W
        && my >= WL_SLICE_BASE_Y && my < WL_SLICE_BASE_Y + WL_SLICE_H;
}

static u16 EntryAtMetatile(s16 mx, s16 my)
{
    if (!InSlice(mx, my))
        return WL_VOID_ENTRY;
    return sWorldSlice[(my - WL_SLICE_BASE_Y) * WL_SLICE_W + (mx - WL_SLICE_BASE_X)];
}

static const u16 *MetatileTiles(u16 entry)
{
    u16 id = entry & MAPGRID_METATILE_ID_MASK;
    if (id < NUM_METATILES_IN_PRIMARY)
        return gTileset_General.metatiles + id * NUM_TILES_PER_METATILE;
    return gTileset_Fortree.metatiles + (id - NUM_METATILES_IN_PRIMARY) * NUM_TILES_PER_METATILE;
}

static u16 MetatileAttr(u16 entry)
{
    u16 id = entry & MAPGRID_METATILE_ID_MASK;
    if (id < NUM_METATILES_IN_PRIMARY)
        return gTileset_General.metatileAttributes[id];
    return gTileset_Fortree.metatileAttributes[id - NUM_METATILES_IN_PRIMARY];
}

static u16 ShiftWorldPalette(u16 tile)
{
    u16 pal = (tile >> 12) & 0xF;
    // Palette 0 is reserved for the Arena HUD. Emerald outdoor maps use 0..12;
    // shift them one slot without changing tile, flip or metatile identity.
    if (pal < 13)
        pal++;
    return (tile & 0x0FFF) | (pal << 12);
}

static void GetWorldTile(s16 worldTx, s16 worldTy, u16 *bottom, u16 *middle, u16 *top)
{
    s16 mx = worldTx >> 1;
    s16 my = worldTy >> 1;
    u8 sub = ((worldTy & 1) << 1) | (worldTx & 1);
    u16 entry = EntryAtMetatile(mx, my);
    const u16 *tiles = MetatileTiles(entry);
    u16 attr = MetatileAttr(entry);
    u8 layer = UNPACK_LAYER_TYPE(attr);
    u16 a = ShiftWorldPalette(tiles[sub]);
    u16 b = ShiftWorldPalette(tiles[4 + sub]);

    *bottom = 0;
    *middle = 0;
    *top = 0;
    switch (layer)
    {
    case METATILE_LAYER_TYPE_COVERED:
        *bottom = a;
        *middle = b;
        break;
    case METATILE_LAYER_TYPE_SPLIT:
        *bottom = a;
        *top = b;
        break;
    case METATILE_LAYER_TYPE_NORMAL:
    default:
        *middle = a;
        *top = b;
        break;
    }
}

static u16 PutWorldTile(s16 tx, s16 ty)
{
    u16 bottom, middle, top;
    u16 slot = ((u16)ty & 31) * 32 + ((u16)tx & 31);
    volatile u16 *bgBottom = (volatile u16 *)BG_SCREEN_ADDR(28);
    volatile u16 *bgMiddle = (volatile u16 *)BG_SCREEN_ADDR(30);
    volatile u16 *bgTop = (volatile u16 *)BG_SCREEN_ADDR(29);

    GetWorldTile(tx, ty, &bottom, &middle, &top);
    bgBottom[slot] = bottom;
    bgMiddle[slot] = middle;
    bgTop[slot] = top;
    if (top)
        gWildlandsWorldTelemetry[7]++;
    return 3;
}

static u16 RebuildWindow(s16 tileX, s16 tileY)
{
    s16 x, y;
    u16 writes = 0;
    for (y = tileY - 1; y <= tileY + 30; y++)
        for (x = tileX - 1; x <= tileX + 30; x++)
            writes += PutWorldTile(x, y);
    gWildlandsWorldTelemetry[1]++;
    return writes;
}

void WildlandsWorld_RestorePalettes(void)
{
    // Exact Emerald outdoor palette ownership, shifted one bank so Arena HUD
    // palette 0 remains untouched.
    LoadPalette(gTileset_General.palettes[0], BG_PLTT_ID(1),
        NUM_PALS_IN_PRIMARY * PLTT_SIZE_4BPP);
    LoadPalette(gTileset_Fortree.palettes[NUM_PALS_IN_PRIMARY],
        BG_PLTT_ID(NUM_PALS_IN_PRIMARY + 1),
        (NUM_PALS_TOTAL - NUM_PALS_IN_PRIMARY) * PLTT_SIZE_4BPP);
}

void WildlandsWorld_LoadGraphics(void)
{
    if (!sActive)
        return;

    // BG1/BG2/BG3 all reference the same unmodified Emerald General+Fortree
    // 4bpp tile atlas. BG0 remains the native Arena HUD.
    SetGpuReg(REG_OFFSET_BG1CNT, BGCNT_PRIORITY(2) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(30) | BGCNT_TXT256x256);
    SetGpuReg(REG_OFFSET_BG2CNT, BGCNT_PRIORITY(0) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(29) | BGCNT_TXT256x256);
    SetGpuReg(REG_OFFSET_BG3CNT, BGCNT_PRIORITY(3) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(28) | BGCNT_TXT256x256);

    LZ77UnCompVram(gTileset_General.tiles, BG_CHAR_ADDR(1));
    LZ77UnCompVram(gTileset_Fortree.tiles,
        (u8 *)BG_CHAR_ADDR(1) + NUM_TILES_IN_PRIMARY * TILE_SIZE_4BPP);
    WildlandsWorld_RestorePalettes();

    DmaFill16(3, 0, BG_SCREEN_ADDR(28), 0x1800);
    sLastTileX = sLastTileY = 0x7FFF;
}

void WildlandsWorld_Init(void)
{
    memset(gWildlandsWorldTelemetry, 0, sizeof(gWildlandsWorldTelemetry));
    sActive = VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE);
    sLastTileX = sLastTileY = 0x7FFF;
    sLastChunkX = sLastChunkY = 0xFF;
    gWildlandsWorldTelemetry[15] = sActive;
}

void WildlandsWorld_UpdateCamera(s16 cameraX, s16 cameraY)
{
    s16 tileX, tileY, x, y;
    u16 writes = 0;
    u32 stamp, now;
    u8 chunkX, chunkY;

    if (!sActive)
        return;

    stamp = gMain.vblankCounter1 * 228 + (REG_VCOUNT + 68) % 228;
    tileX = cameraX >> 3;
    tileY = cameraY >> 3;

    if (sLastTileX == 0x7FFF || Abs32(tileX - sLastTileX) > 1 || Abs32(tileY - sLastTileY) > 1)
        writes = RebuildWindow(tileX, tileY);
    else
    {
        if (tileX > sLastTileX)
        {
            x = tileX + 30;
            for (y = tileY - 1; y <= tileY + 30; y++)
                writes += PutWorldTile(x, y);
        }
        else if (tileX < sLastTileX)
        {
            x = tileX - 1;
            for (y = tileY - 1; y <= tileY + 30; y++)
                writes += PutWorldTile(x, y);
        }

        if (tileY > sLastTileY)
        {
            y = tileY + 30;
            for (x = tileX - 1; x <= tileX + 30; x++)
                writes += PutWorldTile(x, y);
        }
        else if (tileY < sLastTileY)
        {
            y = tileY - 1;
            for (x = tileX - 1; x <= tileX + 30; x++)
                writes += PutWorldTile(x, y);
        }
    }

    sLastTileX = tileX;
    sLastTileY = tileY;
    gWildlandsWorldTelemetry[0] += writes;
    if (writes > gWildlandsWorldTelemetry[8])
        gWildlandsWorldTelemetry[8] = writes;

    chunkX = cameraX >> 8;
    chunkY = cameraY >> 8;
    if (sLastChunkX != 0xFF && (chunkX != sLastChunkX || chunkY != sLastChunkY))
        gWildlandsWorldTelemetry[2]++;
    sLastChunkX = chunkX;
    sLastChunkY = chunkY;
    gWildlandsWorldTelemetry[13] = chunkX;
    gWildlandsWorldTelemetry[14] = chunkY;

    SetGpuReg(REG_OFFSET_BG1HOFS, cameraX & 0xFF);
    SetGpuReg(REG_OFFSET_BG1VOFS, cameraY & 0xFF);
    SetGpuReg(REG_OFFSET_BG2HOFS, cameraX & 0xFF);
    SetGpuReg(REG_OFFSET_BG2VOFS, cameraY & 0xFF);
    SetGpuReg(REG_OFFSET_BG3HOFS, cameraX & 0xFF);
    SetGpuReg(REG_OFFSET_BG3VOFS, cameraY & 0xFF);

    now = gMain.vblankCounter1 * 228 + (REG_VCOUNT + 68) % 228;
    if (now - stamp > gWildlandsWorldTelemetry[9])
        gWildlandsWorldTelemetry[9] = now - stamp;
}

static bool8 IsBridgeBehavior(u8 behavior)
{
    return MetatileBehavior_IsBridgeOverWater(behavior)
        || MetatileBehavior_IsBridgeOverWaterNoEdge(behavior)
        || MetatileBehavior_IsFortreeBridge(behavior);
}

static u8 TerrainEntry(s16 mx, s16 my)
{
    u16 entry;
    u16 attr;
    u8 behavior;
    u8 flags = 0;

    if (!InSlice(mx, my))
        return WL_TERRAIN_SOLID | WL_TERRAIN_DEEP_WATER | WL_TERRAIN_WET;

    entry = EntryAtMetatile(mx, my);
    attr = MetatileAttr(entry);
    behavior = UNPACK_BEHAVIOR(attr);

    if (UNPACK_COLLISION(entry)
        || MetatileBehavior_IsEastBlocked(behavior)
        || MetatileBehavior_IsWestBlocked(behavior)
        || MetatileBehavior_IsNorthBlocked(behavior)
        || MetatileBehavior_IsSouthBlocked(behavior)
        || MetatileBehavior_IsJumpEast(behavior)
        || MetatileBehavior_IsJumpWest(behavior)
        || MetatileBehavior_IsJumpNorth(behavior)
        || MetatileBehavior_IsJumpSouth(behavior))
        flags |= WL_TERRAIN_SOLID;

    if (IsBridgeBehavior(behavior))
        flags |= WL_TERRAIN_BRIDGE;
    else if (MetatileBehavior_IsSurfableWaterOrUnderwater(behavior))
        flags |= WL_TERRAIN_DEEP_WATER | WL_TERRAIN_WET;

    if (MetatileBehavior_IsPuddle(behavior)
        || MetatileBehavior_IsShallowFlowingWater(behavior))
        flags |= WL_TERRAIN_WET;

    if (MetatileBehavior_IsTallGrass(behavior)
        || MetatileBehavior_IsLongGrass(behavior)
        || MetatileBehavior_IsLongGrassSouthEdge(behavior))
        flags |= WL_TERRAIN_CONCEAL;

    return flags;
}

u8 WildlandsWorld_TerrainAt(s16 x, s16 y)
{
    if (!sActive)
        return 0;
    return TerrainEntry(x >> 4, y >> 4);
}

static bool8 SolidCircle(s16 x, s16 y, u8 radius)
{
    static const s8 ox[9] = {0, 1,-1, 0, 0, 1, 1,-1,-1};
    static const s8 oy[9] = {0, 0, 0, 1,-1, 1,-1, 1,-1};
    u8 i;
    for (i = 0; i < 9; i++)
        if (WildlandsWorld_TerrainAt(x + ox[i] * radius, y + oy[i] * radius) & WL_TERRAIN_SOLID)
            return TRUE;
    return FALSE;
}

static bool8 WaterCircle(s16 x, s16 y, u8 radius)
{
    static const s8 ox[5] = {0, 1,-1, 0, 0};
    static const s8 oy[5] = {0, 0, 0, 1,-1};
    u8 i;
    for (i = 0; i < 5; i++)
        if (WildlandsWorld_TerrainAt(x + ox[i] * radius, y + oy[i] * radius) & WL_TERRAIN_DEEP_WATER)
            return TRUE;
    return FALSE;
}

bool8 WildlandsWorld_LineClear(s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    s32 dx, dy, steps, i, fx, fy, sx, sy;
    if (!sActive)
        return TRUE;
    dx = x2 - x1;
    dy = y2 - y1;
    steps = max(Abs32(dx), Abs32(dy)) / 4 + 1;
    fx = x1 << 8;
    fy = y1 << 8;
    sx = (dx << 8) / steps;
    sy = (dy << 8) / steps;
    for (i = 0; i <= steps; i++, fx += sx, fy += sy)
        if (SolidCircle(fx >> 8, fy >> 8, radius))
            return FALSE;
    return TRUE;
}

static bool8 SideCanWater(u8 side)
{
    return gBattleMons[side].types[0] == TYPE_WATER
        || gBattleMons[side].types[1] == TYPE_WATER
        || gBattleMons[side].types[0] == TYPE_FLYING
        || gBattleMons[side].types[1] == TYPE_FLYING
        || gBattleMons[side].ability == ABILITY_LEVITATE;
}

static bool8 SpeciesCanWater(u16 species)
{
    return gBaseStats[species].type1 == TYPE_WATER
        || gBaseStats[species].type2 == TYPE_WATER
        || gBaseStats[species].type1 == TYPE_FLYING
        || gBaseStats[species].type2 == TYPE_FLYING;
}

static bool8 TraversalClear(bool8 waterAllowed, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    s32 dx, dy, steps, i, fx, fy, sx, sy;
    u8 terrain;
    if (!sActive)
        return TRUE;
    dx = x2 - x1;
    dy = y2 - y1;
    steps = max(Abs32(dx), Abs32(dy)) / 4 + 1;
    fx = x1 << 8;
    fy = y1 << 8;
    sx = (dx << 8) / steps;
    sy = (dy << 8) / steps;
    for (i = 0; i <= steps; i++, fx += sx, fy += sy)
    {
        if (SolidCircle(fx >> 8, fy >> 8, radius))
            return FALSE;
        terrain = WildlandsWorld_TerrainAt(fx >> 8, fy >> 8);
        if (!waterAllowed && (terrain & WL_TERRAIN_DEEP_WATER)
            && WaterCircle(fx >> 8, fy >> 8, radius))
        {
            gWildlandsWorldTelemetry[4]++;
            return FALSE;
        }
    }
    return TRUE;
}

bool8 WildlandsWorld_BodyLineClear(u8 side, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    return TraversalClear(SideCanWater(side), x1, y1, x2, y2, radius);
}

bool8 WildlandsWorld_SpeciesLineClear(u16 species, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    return TraversalClear(SpeciesCanWater(species), x1, y1, x2, y2, radius);
}

bool8 WildlandsWorld_CanStandSide(u8 side, s16 x, s16 y, u8 radius)
{
    return WildlandsWorld_BodyLineClear(side, x, y, x, y, radius);
}

bool8 WildlandsWorld_CanStandSpecies(u16 species, s16 x, s16 y, u8 radius)
{
    return WildlandsWorld_SpeciesLineClear(species, x, y, x, y, radius);
}

bool8 WildlandsWorld_IsConcealed(s16 x, s16 y)
{
    return sActive && (WildlandsWorld_TerrainAt(x, y) & WL_TERRAIN_CONCEAL);
}

bool8 WildlandsWorld_IsWater(s16 x, s16 y)
{
    return sActive && (WildlandsWorld_TerrainAt(x, y) & WL_TERRAIN_DEEP_WATER);
}

bool8 WildlandsWorld_IsWet(s16 x, s16 y)
{
    return sActive && (WildlandsWorld_TerrainAt(x, y) & WL_TERRAIN_WET);
}

u16 WildlandsWorld_ClipRay(s16 x, s16 y, s16 dx, s16 dy, u16 distance, u8 radius)
{
    u16 d;
    if (!sActive)
        return distance;
    for (d = 4; d <= distance; d += 4)
    {
        s16 nx = x + dx * d / 256;
        s16 ny = y + dy * d / 256;
        if (!WildlandsWorld_LineClear(x, y, nx, ny, radius))
            return d > 4 ? d - 4 : 0;
    }
    return distance;
}

static u16 PointDistance(s16 x1, s16 y1, s16 x2, s16 y2)
{
    s32 dx = Abs32(x1 - x2);
    s32 dy = Abs32(y1 - y2);
    return dx > dy ? dx + dy / 2 : dy + dx / 2;
}

static bool8 MoverLine(bool8 speciesMode, u16 mover, s16 x1, s16 y1, s16 x2, s16 y2)
{
    if (speciesMode)
        return WildlandsWorld_SpeciesLineClear(mover, x1, y1, x2, y2, 10);
    return WildlandsWorld_BodyLineClear((u8)mover, x1, y1, x2, y2, 10);
}

static bool8 MoverStand(bool8 speciesMode, u16 mover, s16 x, s16 y)
{
    if (speciesMode)
        return WildlandsWorld_CanStandSpecies(mover, x, y, 10);
    return WildlandsWorld_CanStandSide((u8)mover, x, y, 10);
}

static u8 NextWaypoint(bool8 speciesMode, u16 mover, s16 x, s16 y,
    s16 goalX, s16 goalY, struct ArenaPoint *next)
{
    u32 i, j;
    s32 best = 0x7FFFFFFF;
    s32 score, second;
    u16 d1, d2;

    next->x = x;
    next->y = y;
    gWildlandsWorldTelemetry[10]++;

    if (MoverLine(speciesMode, mover, x, y, goalX, goalY))
    {
        next->x = goalX;
        next->y = goalY;
        return TRUE;
    }

    for (i = 0; i < WL_NAV_POINT_COUNT; i++)
    {
        const struct ArenaPoint *p = &sNavPoints[i];
        if (!MoverStand(speciesMode, mover, p->x, p->y)
            || !MoverLine(speciesMode, mover, x, y, p->x, p->y))
            continue;

        d1 = PointDistance(x, y, p->x, p->y);
        if (MoverLine(speciesMode, mover, p->x, p->y, goalX, goalY))
            score = d1 + PointDistance(p->x, p->y, goalX, goalY) - 4000;
        else
        {
            second = 0x7FFFFFFF;
            for (j = 0; j < WL_NAV_POINT_COUNT; j++)
            {
                const struct ArenaPoint *q = &sNavPoints[j];
                if (i == j
                    || !MoverStand(speciesMode, mover, q->x, q->y)
                    || !MoverLine(speciesMode, mover, p->x, p->y, q->x, q->y))
                    continue;
                d2 = PointDistance(p->x, p->y, q->x, q->y);
                score = d1 + d2 + PointDistance(q->x, q->y, goalX, goalY);
                if (MoverLine(speciesMode, mover, q->x, q->y, goalX, goalY))
                    score -= 2000;
                if (score < second)
                    second = score;
            }
            score = second;
        }

        if (score < best)
        {
            best = score;
            *next = *p;
        }
    }

    if (best == 0x7FFFFFFF)
    {
        gWildlandsWorldTelemetry[11]++;
        return FALSE;
    }
    return TRUE;
}

u8 WildlandsWorld_NextWaypointSide(u8 side, s16 x, s16 y,
    s16 goalX, s16 goalY, struct ArenaPoint *next)
{
    if (!sActive)
        return FALSE;
    return NextWaypoint(FALSE, side, x, y, goalX, goalY, next);
}

u8 WildlandsWorld_NextWaypointSpecies(u16 species, s16 x, s16 y,
    s16 goalX, s16 goalY, struct ArenaPoint *next)
{
    if (!sActive)
        return FALSE;
    return NextWaypoint(TRUE, species, x, y, goalX, goalY, next);
}
