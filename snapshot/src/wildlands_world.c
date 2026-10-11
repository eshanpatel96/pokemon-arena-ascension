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
#include "constants/species.h"
#include "fieldmap.h"

extern const struct Tileset gTileset_General;
extern const struct Tileset gTileset_Fortree;

static const u16 sWorldSlice[] = INCBIN_U16("data/wildlands_world/slice.bin");
// One flag byte per metatile, generated at build time (terrain_flags.py).
static const u8 sWorldTerrain[] = INCBIN_U8("data/wildlands_world/terrain.bin");
static const struct ArenaPoint sNavPoints[] =
{
#include "wildlands_world_nav.inc"
};
#include "wildlands_nav_graph.inc"
#include "wildlands_rooms.inc"
#include "wildlands_biomes.inc"
#include "malloc.h"

#define WL_BLANK_TILE 1023
static EWRAM_DATA bool8 sActive = FALSE;
static EWRAM_DATA s16 sLastTileX = 0x7FFF;
static EWRAM_DATA s16 sLastTileY = 0x7FFF;
static EWRAM_DATA u8 sLastChunkX = 0xFF;
static EWRAM_DATA u8 sLastChunkY = 0xFF;

// Streaming queue: world tile coordinates only (4 bytes/entry); the three
// layer entries are resolved during VBlank. 192 entries cover up to three
// newly exposed rows AND columns (render catch-up can move the camera >1
// tile between draws), so no row is ever dropped.
#define WL_PENDING_TILES 192
static EWRAM_DATA u32 sPending[WL_PENDING_TILES] = {};
static EWRAM_DATA u8 sPendingCount = 0;

EWRAM_DATA u32 gWildlandsWorldTelemetry[16] = {};
// Interiors: room the camera is in (-1 outdoors), door used to enter it,
// door re-trigger guard and frames of forced blank left after a swap.
static EWRAM_DATA s8 sRoom = -1;
static EWRAM_DATA s8 sEntryDoor = -1;
static EWRAM_DATA u8 sWarpCooldown = 0;
static EWRAM_DATA u8 sBlankFrames = 0;
// Biome streaming: index of the secondary tileset currently in VRAM for the
// outdoors, and the camera tile it was last checked at.
static EWRAM_DATA u8 sBiome = 0;
static EWRAM_DATA s16 sBiomeTileX = 0x7FFF, sBiomeTileY = 0x7FFF;
// [0] biome in VRAM + 1 [1] secondary swaps [2] swaps that needed a window
// rebuild [3] windows that saw two secondaries at once (must stay 0)
EWRAM_DATA u32 gWildlandsBiomeTelemetry[4] = {};
// [0] door entries [1] exits [2] current room+1 [3] tileset swaps
// [4] last door [5] slide nudges [6] room of last entry+1
// [7] streaming queue overflows (dropped tiles; must stay 0)
EWRAM_DATA u32 gWildlandsRoomTelemetry[8] = {};
EWRAM_DATA u32 gWildlandsWorldAudit[8] = {};

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

static const struct Tileset *const *CurPair(void)
{
    if (sRoom < 0)
        return sWlOutdoorPairs[sBiome];
    return sWlPairs[sWlRooms[sRoom].pair];
}

static const u16 *MetatileTiles(u16 entry)
{
    u16 id = entry & MAPGRID_METATILE_ID_MASK;
    const struct Tileset *const *pair = CurPair();
    if (id < NUM_METATILES_IN_PRIMARY)
        return pair[0]->metatiles + id * NUM_TILES_PER_METATILE;
    return pair[1]->metatiles + (id - NUM_METATILES_IN_PRIMARY) * NUM_TILES_PER_METATILE;
}

static u16 MetatileAttr(u16 entry)
{
    u16 id = entry & MAPGRID_METATILE_ID_MASK;
    const struct Tileset *const *pair = CurPair();
    if (id < NUM_METATILES_IN_PRIMARY)
        return pair[0]->metatileAttributes[id];
    return pair[1]->metatileAttributes[id - NUM_METATILES_IN_PRIMARY];
}

static s8 RoomAt(s16 x, s16 y)
{
    s16 mx = x >> 4, my = y >> 4;
    u32 i;
    if (my < WL_SLICE_BASE_Y + WL_OUTDOOR_H)
        return -1;
    for (i = 0; i < WL_ROOM_COUNT; i++)
    {
        const struct WlRoom *r = &sWlRooms[i];
        if (mx >= r->x && my >= r->y && mx < r->x + r->w && my < r->y + r->h)
            return i;
    }
    return -1;
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
    const u16 *tiles;
    u16 attr, a, b;
    u8 layer;

    *bottom = WL_BLANK_TILE;
    *middle = WL_BLANK_TILE;
    *top = WL_BLANK_TILE;
    // Only the active region draws: outdoors never shows the room strip, and
    // a room shows nothing outside its own native layout.
    if (sRoom < 0)
    {
        if (my >= WL_SLICE_BASE_Y + WL_OUTDOOR_H)
            entry = WL_VOID_ENTRY;
    }
    else
    {
        const struct WlRoom *r = &sWlRooms[sRoom];
        if (mx < r->x || my < r->y || mx >= r->x + r->w || my >= r->y + r->h)
            return;
    }
    tiles = MetatileTiles(entry);
    attr = MetatileAttr(entry);
    layer = UNPACK_LAYER_TYPE(attr);
    a = ShiftWorldPalette(tiles[sub]);
    b = ShiftWorldPalette(tiles[4 + sub]);
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

static u16 PutWorldTileNow(s16 tx, s16 ty)
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
    {
        gWildlandsWorldTelemetry[7]++;
        gWildlandsWorldAudit[7] = 1;
    }
    return 3;
}

static u16 QueueWorldTile(s16 tx, s16 ty)
{
    if (sPendingCount >= WL_PENDING_TILES)
    {
        gWildlandsRoomTelemetry[7]++;
        return 0;
    }
    sPending[sPendingCount++] = (u16)tx | ((u32)(u16)ty << 16);
    return 3;
}

static u16 RebuildWindow(s16 tileX, s16 tileY)
{
    s16 x, y;
    u16 writes = 0;
    for (y = tileY - 1; y <= tileY + 30; y++)
        for (x = tileX - 1; x <= tileX + 30; x++)
            writes += PutWorldTileNow(x, y);
    gWildlandsWorldTelemetry[1]++;
    return writes;
}

void WildlandsWorld_RestorePalettes(void)
{
    // Exact Emerald palette ownership of the active tileset pair, shifted one
    // bank so Arena HUD palette 0 remains untouched.
    const struct Tileset *const *pair = CurPair();
    LoadPalette(pair[0]->palettes[0], BG_PLTT_ID(1),
        NUM_PALS_IN_PRIMARY * PLTT_SIZE_4BPP);
    LoadPalette(pair[1]->palettes[NUM_PALS_IN_PRIMARY],
        BG_PLTT_ID(NUM_PALS_IN_PRIMARY + 1),
        (NUM_PALS_TOTAL - NUM_PALS_IN_PRIMARY) * PLTT_SIZE_4BPP);
}

static void LoadPairTiles(void)
{
    const struct Tileset *const *pair = CurPair();
    LZ77UnCompVram(pair[0]->tiles, (void *)BG_CHAR_ADDR(1));
    LZ77UnCompVram(pair[1]->tiles,
        (u8 *)BG_CHAR_ADDR(1) + NUM_TILES_IN_PRIMARY * TILE_SIZE_4BPP);
    // Tile 0 is real Emerald art, so it cannot represent an empty layer.
    // The generator asserts tile 1023 is unused by every pair; zero it for
    // transparent top/middle/bottom layer holes.
    DmaFill16(3, 0, (u8 *)BG_CHAR_ADDR(1) + WL_BLANK_TILE * TILE_SIZE_4BPP,
        TILE_SIZE_4BPP);
}

// Region change (door, ladder, menu re-entry inside a room): swap the tile
// atlas and palettes under forced blank, then rebuild the whole window.
#define WL_LAYER_BITS (DISPCNT_BG1_ON | DISPCNT_BG2_ON | DISPCNT_BG3_ON | DISPCNT_OBJ_ON)
// Hide the terrain layers and sprites (the HUD stays) while VRAM is
// rewritten: the screen shows the dark backdrop for a few frames. Forced
// blank was used before and flashed WHITE on hardware.
static void HideLayers(u8 frames)
{
    REG_DISPCNT &= ~WL_LAYER_BITS;
    ClearGpuRegBits(REG_OFFSET_DISPCNT, WL_LAYER_BITS);
    sBlankFrames = frames;
}

static void EnterRegion(s8 room)
{
    HideLayers(3);
    sRoom = room;
    LoadPairTiles();
    WildlandsWorld_RestorePalettes();
    sPendingCount = 0;
    sLastTileX = sLastTileY = 0x7FFF;
    sBiomeTileX = 0x7FFF;
    gWildlandsRoomTelemetry[2] = room + 1;
    gWildlandsRoomTelemetry[3]++;
}

void WildlandsWorld_LoadGraphics(void)
{
    if (!sActive)
        return;

    // BG1/BG2/BG3 all reference the same unmodified Emerald General+Fortree
    // 4bpp tile atlas. BG0 remains the native Arena HUD. Update the engine's
    // BG control structs as well as the hardware registers: ShowBg() rebuilds
    // BGCNT from these structs and otherwise restores the legacy Arena BG1
    // 8bpp/BG2 charbase-3 settings after this function returns.
    SetBgAttribute(1, BG_ATTR_CHARBASEINDEX, 1);
    SetBgAttribute(1, BG_ATTR_MAPBASEINDEX, 30);
    SetBgAttribute(1, BG_ATTR_PALETTEMODE, 0);
    SetBgAttribute(1, BG_ATTR_PRIORITY, 2);
    SetBgAttribute(2, BG_ATTR_CHARBASEINDEX, 1);
    SetBgAttribute(2, BG_ATTR_MAPBASEINDEX, 29);
    SetBgAttribute(2, BG_ATTR_PALETTEMODE, 0);
    // Top layer (canopies, roofs) at priority 1: actors, shots and pickups
    // (OAM priority 0/1) always draw IN FRONT of foreground scenery, so a
    // fight behind trees stays readable. The HUD (BG0) stays on top.
    SetBgAttribute(2, BG_ATTR_PRIORITY, 1);
    SetBgAttribute(3, BG_ATTR_CHARBASEINDEX, 1);
    SetBgAttribute(3, BG_ATTR_MAPBASEINDEX, 28);
    SetBgAttribute(3, BG_ATTR_PALETTEMODE, 0);
    SetBgAttribute(3, BG_ATTR_PRIORITY, 3);

    SetGpuReg(REG_OFFSET_BG1CNT, BGCNT_PRIORITY(2) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(30) | BGCNT_16COLOR | BGCNT_TXT256x256);
    SetGpuReg(REG_OFFSET_BG2CNT, BGCNT_PRIORITY(1) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(29) | BGCNT_16COLOR | BGCNT_TXT256x256);
    SetGpuReg(REG_OFFSET_BG3CNT, BGCNT_PRIORITY(3) | BGCNT_CHARBASE(1)
        | BGCNT_SCREENBASE(28) | BGCNT_16COLOR | BGCNT_TXT256x256);

    LoadPairTiles();
    WildlandsWorld_RestorePalettes();

    DmaFill16(3, 0, BG_SCREEN_ADDR(28), 0x1800);
    sLastTileX = sLastTileY = 0x7FFF;
    sPendingCount = 0;
}

void WildlandsWorld_Init(void)
{
    memset(gWildlandsWorldTelemetry, 0, sizeof(gWildlandsWorldTelemetry));
    memset(gWildlandsWorldAudit, 0, sizeof(gWildlandsWorldAudit));
    sActive = VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE);
    sLastTileX = sLastTileY = 0x7FFF;
    sLastChunkX = sLastChunkY = 0xFF;
    sPendingCount = 0;
    sRoom = -1;
    sWarpCooldown = 0;
    sBlankFrames = 0;
    sBiome = WL_BIOME_START;
    sBiomeTileX = sBiomeTileY = 0x7FFF;
    gWildlandsBiomeTelemetry[0] = sBiome + 1;
    gWildlandsWorldTelemetry[15] = sActive;
    gWildlandsWorldAudit[0] = sActive;
}

extern u16 gWildlandsHitch[8];
static void SwapBiome(u8 biome, bool8 rebuild)
{
    const struct Tileset *sec = sWlOutdoorPairs[biome][1];
    u32 t0 = gMain.vblankCounter1 * 228 + (REG_VCOUNT + 68) % 228, t1;
    if (rebuild)
        HideLayers(2);
    sBiome = biome;
    LZ77UnCompVram(sec->tiles, (u8 *)BG_CHAR_ADDR(1) + NUM_TILES_IN_PRIMARY * TILE_SIZE_4BPP);
    DmaFill16(3, 0, (u8 *)BG_CHAR_ADDR(1) + WL_BLANK_TILE * TILE_SIZE_4BPP, TILE_SIZE_4BPP);
    WildlandsWorld_RestorePalettes();
    if (rebuild)
    {
        sPendingCount = 0;
        sLastTileX = sLastTileY = 0x7FFF;
        gWildlandsBiomeTelemetry[2]++;
    }
    gWildlandsBiomeTelemetry[0] = biome + 1;
    gWildlandsBiomeTelemetry[1]++;
    t1 = gMain.vblankCounter1 * 228 + (REG_VCOUNT + 68) % 228;
    if (t1 - t0 > gWildlandsHitch[4]) gWildlandsHitch[4] = t1 - t0;
}

// The streamed window (17x17 metatiles) may only ever hold secondary tiles of
// the biome whose tileset is in VRAM. Biomes are generated >= 18 metatiles
// apart with primary-only belts between them, so the swap normally happens
// unseen while the window is all-primary (prefetching the nearest biome);
// a teleport into another biome swaps behind hidden layers instead.
static void BiomeCheck(s16 tileX, s16 tileY)
{
    s16 mx0, my0, mx, my;
    u32 seen = 0;
    if (WL_BIOME_COUNT < 2 || (tileX == sBiomeTileX && tileY == sBiomeTileY))
        return;
    sBiomeTileX = tileX; sBiomeTileY = tileY;
    mx0 = ((tileX - 1) >> 1) - WL_SLICE_BASE_X;
    my0 = ((tileY - 1) >> 1) - WL_SLICE_BASE_Y;
    for (my = my0 < 0 ? 0 : my0; my <= my0 + 16 && my < WL_OUTDOOR_H; my++)
    {
        const u8 *row = &sWlBiomeCells[my * WL_SLICE_W];
        for (mx = mx0 < 0 ? 0 : mx0; mx <= mx0 + 16 && mx < WL_SLICE_W; mx++)
            if (row[mx])
                seen |= 1u << (row[mx] - 1);
    }
    if (seen & ~(1u << sBiome))
    {
        u8 k;
        if ((seen & (seen - 1)))
            gWildlandsBiomeTelemetry[3]++;   // two secondaries in one window
        for (k = 0; k < WL_BIOME_COUNT; k++)
            if ((seen >> k) & 1 && k != sBiome)
                break;
        if (k < WL_BIOME_COUNT)
            SwapBiome(k, TRUE);
        return;
    }
    if (!seen)
    {
        // All-primary window: prefetch the nearest biome core block.
        s16 bx = ((tileX >> 1) + 8 - WL_SLICE_BASE_X) / WL_BIOME_BLOCK;
        s16 by = ((tileY >> 1) + 5 - WL_SLICE_BASE_Y) / WL_BIOME_BLOCK;
        s16 r, dx, dy;
        for (r = 0; r <= 3; r++)
            for (dy = -r; dy <= r; dy++)
                for (dx = -r; dx <= r; dx++)
                {
                    s16 x = bx + dx, y = by + dy;
                    u8 v;
                    if ((dx > -r && dx < r && dy > -r && dy < r) || x < 0 || y < 0
                        || x >= WL_BIOME_GW || y >= WL_BIOME_GH)
                        continue;
                    v = sWlBiomeBlocks[y * WL_BIOME_GW + x];
                    if (v && v - 1 != sBiome)
                    {
                        SwapBiome(v - 1, FALSE);
                        return;
                    }
                    if (v)
                        return;   // nearest core is the one already loaded
                }
    }
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
    {
        // The camera centre always lies in the player's region (rooms clamp
        // the camera onto themselves), so this also restores the right
        // tileset after a native menu returns to an encounter inside a room.
        s8 room = RoomAt(cameraX + 120, cameraY + 80);
        if (room != sRoom)
            EnterRegion(room);
        else if (sBlankFrames && !--sBlankFrames)
            SetGpuRegBits(REG_OFFSET_DISPCNT, WL_LAYER_BITS);
        if (sRoom < 0)
            BiomeCheck(cameraX >> 3, cameraY >> 3);
    }
    tileX = cameraX >> 3;
    tileY = cameraY >> 3;

    if (sLastTileX == 0x7FFF)
        writes = RebuildWindow(tileX, tileY);
    else if (Abs32(tileX - sLastTileX) > 3 || Abs32(tileY - sLastTileY) > 3)
    {
        // Teleports/camera jumps are not part of normal continuous movement.
        // Rebuild immediately only for recovery; ordinary streaming is queued
        // and committed entirely during VBlank below.
        writes = RebuildWindow(tileX, tileY);
        gWildlandsWorldTelemetry[3]++;
    }
    else
    {
        // Up to three newly exposed columns and rows per update. Queue is
        // only cleared once VBlank has committed it (see WildlandsWorld_VBlank).
        s16 c;
        for (c = sLastTileX + 1; c <= tileX; c++)
            for (y = tileY - 1; y <= tileY + 30; y++)
                writes += QueueWorldTile(c + 30, y);
        for (c = sLastTileX - 1; c >= tileX; c--)
            for (y = tileY - 1; y <= tileY + 30; y++)
                writes += QueueWorldTile(c - 1, y);
        for (c = sLastTileY + 1; c <= tileY; c++)
            for (x = tileX - 1; x <= tileX + 30; x++)
                writes += QueueWorldTile(x, c + 30);
        for (c = sLastTileY - 1; c >= tileY; c--)
            for (x = tileX - 1; x <= tileX + 30; x++)
                writes += QueueWorldTile(x, c - 1);
    }

    sLastTileX = tileX;
    sLastTileY = tileY;
    if (sPendingCount == 0)
    {
        gWildlandsWorldTelemetry[0] += writes;
        if (writes > gWildlandsWorldTelemetry[8])
            gWildlandsWorldTelemetry[8] = writes;
    }

    chunkX = cameraX >> 8;
    chunkY = cameraY >> 8;
    if (sLastChunkX != 0xFF && (chunkX != sLastChunkX || chunkY != sLastChunkY))
    {
        gWildlandsWorldTelemetry[2]++;
        gWildlandsWorldAudit[1] = 1;
    }
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

void WildlandsWorld_VBlank(void)
{
    u32 i;
    volatile u16 *bgBottom;
    volatile u16 *bgMiddle;
    volatile u16 *bgTop;
    if (!sActive || !sPendingCount)
        return;

    bgBottom = (volatile u16 *)BG_SCREEN_ADDR(28);
    bgMiddle = (volatile u16 *)BG_SCREEN_ADDR(30);
    bgTop = (volatile u16 *)BG_SCREEN_ADDR(29);
    for (i = 0; i < sPendingCount; i++)
    {
        u16 bottom, middle, top;
        s16 tx = (s16)(sPending[i] & 0xFFFF), ty = (s16)(sPending[i] >> 16);
        u16 slot = ((u16)ty & 31) * 32 + ((u16)tx & 31);
        GetWorldTile(tx, ty, &bottom, &middle, &top);
        bgBottom[slot] = bottom;
        bgMiddle[slot] = middle;
        bgTop[slot] = top;
        if (top) gWildlandsWorldAudit[7] = 1;
    }
    gWildlandsWorldTelemetry[0] += sPendingCount * 3;
    gWildlandsWorldAudit[2] = 1;
    if (sPendingCount > gWildlandsWorldTelemetry[8])
        gWildlandsWorldTelemetry[8] = sPendingCount;
    sPendingCount = 0;
}

void WildlandsWorld_TickBody(u8 side, s16 x, s16 y)
{
    u8 terrain;
    if (!sActive)
        return;
    terrain = WildlandsWorld_TerrainAt(x, y);
    if (side == 0 && (terrain & WL_TERRAIN_CONCEAL))
    {
        gWildlandsWorldTelemetry[5]++;
        gWildlandsWorldAudit[3] = 1;
    }
    if (side == 0 && (terrain & WL_TERRAIN_DEEP_WATER))
    {
        gWildlandsWorldTelemetry[6]++;
        gWildlandsWorldAudit[4] = 1;
    }
}

void WildlandsWorld_RecordProjectileBlock(void)
{
    if (sActive)
        gWildlandsWorldAudit[6] = 1;
}

static const struct WlDoor *RoomDoor(s8 room)
{
    u32 i;
    if (sEntryDoor >= 0 && sWlDoors[sEntryDoor].room == room)
        return &sWlDoors[sEntryDoor];
    for (i = 0; i < WL_DOOR_COUNT; i++)
        if (sWlDoors[i].room == room)
            return &sWlDoors[i];
    return NULL;
}

bool8 WildlandsWorld_InRoom(s16 x, s16 y)
{
    return sActive && RoomAt(x, y) >= 0;
}

// Positions inside a room count as standing at that room's door outside:
// the storm, the map and pursuers all treat a house as where its door is.
void WildlandsWorld_OutdoorPos(s32 *x, s32 *y)
{
    s8 room;
    const struct WlDoor *d;
    if (!sActive)
        return;
    room = RoomAt(*x, *y);
    if (room < 0 || !(d = RoomDoor(room)))
        return;
    *x = d->outX;
    *y = d->outY;
}

// Doors: walking UP into an outdoor door enters its room; stepping onto the
// room's native exit (facing down for door mats, any way for ladders/stairs)
// returns to the door the player came in through.
bool8 WildlandsWorld_PollDoor(s16 x, s16 y, bool8 facingUp, bool8 facingDown, s16 *outX, s16 *outY)
{
    s8 room;
    u32 i;
    if (!sActive)
        return FALSE;
    if (sWarpCooldown)
    {
        sWarpCooldown--;
        return FALSE;
    }
    room = RoomAt(x, y);
    if (room < 0)
    {
        if (!facingUp)
            return FALSE;
        for (i = 0; i < WL_DOOR_COUNT; i++)
        {
            const struct WlDoor *d = &sWlDoors[i];
            s16 cx = d->x * 16 + 8, top = d->y * 16;
            if (Abs32(x - cx) <= 8 && y >= top && y <= top + 30)
            {
                sEntryDoor = i;
                *outX = sWlRooms[d->room].arriveX;
                *outY = sWlRooms[d->room].arriveY;
                sWarpCooldown = 30;
                gWildlandsRoomTelemetry[0]++;
                gWildlandsRoomTelemetry[4] = i + 1;
                gWildlandsRoomTelemetry[6] = d->room + 1;
                return TRUE;
            }
        }
        return FALSE;
    }
    {
        const struct WlRoom *r = &sWlRooms[room];
        const struct WlDoor *d;
        s16 cx = r->exitX * 16 + 8, cy = r->exitY * 16 + 8;
        if (Abs32(x - cx) > 8 || Abs32(y - cy) > 10 || (r->exitDown && !facingDown))
            return FALSE;
        if (!(d = RoomDoor(room)))
            return FALSE;
        *outX = d->outX;
        *outY = d->outY;
        sWarpCooldown = 30;
        gWildlandsRoomTelemetry[1]++;
        return TRUE;
    }
}

// Rooms smaller than the screen are centred; larger ones scroll within
// their own bounds.
void WildlandsWorld_ClampCamera(s32 px, s32 py, s32 *camX, s32 *camY)
{
    s8 room;
    s32 rx, ry, rw, rh;
    if (!sActive || (room = RoomAt(px, py)) < 0)
        return;
    rx = sWlRooms[room].x * 16; ry = sWlRooms[room].y * 16;
    rw = sWlRooms[room].w * 16; rh = sWlRooms[room].h * 16;
    if (rw <= 240) *camX = rx - (240 - rw) / 2;
    else *camX = px - 120 < rx ? rx : px - 120 > rx + rw - 240 ? rx + rw - 240 : px - 120;
    if (rh <= 160) *camY = ry - (160 - rh) / 2;
    else *camY = py - 80 < ry ? ry : py - 80 > ry + rh - 160 ? ry + rh - 160 : py - 80;
}

void WildlandsWorld_DoorArrival(u8 door, s16 *x, s16 *y)
{
    *x = sWlRooms[sWlDoors[door].room].arriveX;
    *y = sWlRooms[sWlDoors[door].room].arriveY;
}

bool8 WildlandsWorld_RoomExitPos(s16 x, s16 y, s16 *ex, s16 *ey)
{
    s8 room = sActive ? RoomAt(x, y) : -1;
    if (room < 0)
        return FALSE;
    *ex = sWlRooms[room].exitX * 16 + 8;
    *ey = sWlRooms[room].exitY * 16 + 8;
    return TRUE;
}

u8 WildlandsWorld_RoomCount(void) { return WL_ROOM_COUNT; }
u8 WildlandsWorld_LandmarkCount(void) { return WL_LANDMARK_COUNT; }
void WildlandsWorld_Landmark(u8 i, s16 *x, s16 *y)
{
    i %= WL_LANDMARK_COUNT;
    *x = sWlLandmarks[i][0];
    *y = sWlLandmarks[i][1];
}
s8 WildlandsWorld_RoomIndexAt(s16 x, s16 y) { return sActive ? RoomAt(x, y) : -1; }
u16 WildlandsWorld_RoomLegend(s8 room) { return room < 0 ? 0 : sWlRooms[room].legend; }
void WildlandsWorld_RoomBoss(u8 room, s32 *x, s32 *y) { *x = sWlRooms[room].bossX; *y = sWlRooms[room].bossY; }

// A legal outdoor point from the build-time navigation anchors.
void WildlandsWorld_NavPoint(u16 index, s16 *x, s16 *y)
{
    index %= ARRAY_COUNT(sNavPoints);
    *x = sNavPoints[index].x;
    *y = sNavPoints[index].y;
}
u16 WildlandsWorld_NavPointCount(void) { return ARRAY_COUNT(sNavPoints); }
u8 WildlandsWorld_DoorCount(void) { return WL_DOOR_COUNT; }
void WildlandsWorld_DoorInfo(u8 i, s16 *x, s16 *y, bool8 *lair)
{
    *x = sWlDoors[i].outX;
    *y = sWlDoors[i].outY;
    *lair = sWlRooms[sWlDoors[i].room].lair;
}

static u8 TerrainEntry(s16 mx, s16 my)
{
    // Hot path: a single ROM byte read. The former per-sample chain of ~15
    // out-of-line MetatileBehavior_* calls (x9 footprint samples x every 4px of
    // every swept line) consumed several frames per Arena update.
    if (!InSlice(mx, my))
        return WL_TERRAIN_SOLID | WL_TERRAIN_DEEP_WATER | WL_TERRAIN_WET;
    return sWorldTerrain[(my - WL_SLICE_BASE_Y) * WL_SLICE_W + (mx - WL_SLICE_BASE_X)];
}

u8 WildlandsWorld_TerrainAt(s16 x, s16 y)
{
    if (!sActive)
        return 0;
    return TerrainEntry(x >> 4, y >> 4);
}

// Inlined ROM flag read; out-of-world reads as solid deep water.
#define WL_TERR(mx, my) \
    ((u16)((mx) - WL_SLICE_BASE_X) < WL_SLICE_W && (u16)((my) - WL_SLICE_BASE_Y) < WL_SLICE_H \
        ? sWorldTerrain[((my) - WL_SLICE_BASE_Y) * WL_SLICE_W + ((mx) - WL_SLICE_BASE_X)] \
        : (WL_TERRAIN_SOLID | WL_TERRAIN_DEEP_WATER | WL_TERRAIN_WET))

static bool8 SolidCircle(s16 x, s16 y, u8 radius)
{
    // Exact square footprint: every metatile the 2r x 2r box touches. This
    // covers every point the former 9-point probe sampled (a superset).
    s16 mx, my;
    s16 x0 = (x - radius) >> 4, x1 = (x + radius) >> 4;
    s16 y0 = (y - radius) >> 4, y1 = (y + radius) >> 4;
    for (my = y0; my <= y1; my++)
        for (mx = x0; mx <= x1; mx++)
            if (WL_TERR(mx, my) & WL_TERRAIN_SOLID)
                return TRUE;
    return FALSE;
}

// Thin rays (LOS, projectiles, radius <= 2): grid traversal visiting each
// metatile the segment crosses exactly once.
static bool8 RayClear(s32 x1, s32 y1, s32 x2, s32 y2)
{
    // Fuzz-verified against dense sampling (40k random rays: 0 unsafe).
    s32 mx = x1 >> 4, my = y1 >> 4, ex = x2 >> 4, ey = y2 >> 4;
    s32 dx = x2 - x1, dy = y2 - y1;
    s32 adx = Abs32(dx), ady = Abs32(dy);
    s32 sx = dx > 0 ? 1 : -1, sy = dy > 0 ? 1 : -1;
    s32 bx = dx > 0 ? 16 - (x1 & 15) : (x1 & 15);
    s32 by = dy > 0 ? 16 - (y1 & 15) : (y1 & 15);
    s32 n = 1 + Abs32(ex - mx) + Abs32(ey - my);
    while (n > 0)
    {
        s32 a, b;
        n--;
        if (WL_TERR(mx, my) & WL_TERRAIN_SOLID)
            return FALSE;
        if (n <= 0)
            break;
        a = bx * ady; b = by * adx;
        if (!ady || (adx && a < b)) { mx += sx; bx += 16; }
        else if (!adx || a > b) { my += sy; by += 16; }
        else
        {
            // Exact corner: be conservative and test both side cells.
            if ((WL_TERR(mx + sx, my) & WL_TERRAIN_SOLID) || (WL_TERR(mx, my + sy) & WL_TERRAIN_SOLID))
                return FALSE;
            mx += sx; my += sy; bx += 16; by += 16; n--;
        }
    }
    return TRUE;
}

// Sample spacing for a swept footprint: consecutive footprint squares of
// half-size r overlap whenever spacing <= 2r, so the sweep stays continuous.
static s32 SweepStep(u8 radius)
{
    return radius >= 3 ? min(radius * 2 - 2, 16) : 4;
}

bool8 WildlandsWorld_LineClear(s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    s32 dx, dy, steps, i, fx, fy, sx, sy;
    if (!sActive)
        return TRUE;
    if (radius <= 2)
        return RayClear(x1, y1, x2, y2);
    dx = x2 - x1;
    dy = y2 - y1;
    steps = max(Abs32(dx), Abs32(dy)) / SweepStep(radius) + 1;
    fx = x1 << 8;
    fy = y1 << 8;
    sx = (dx << 8) / steps;
    sy = (dy << 8) / steps;
    for (i = 0; i <= steps; i++, fx += sx, fy += sy)
        if (SolidCircle(fx >> 8, fy >> 8, radius))
            return FALSE;
    return TRUE;
}

// Deep water: only Water types swim. Nobody flies or hovers over it (a
// Charizard or Gengar "walking" on the sea read as a bug); every water body
// that separates land has a bridge, so no land Pokemon is ever cut off.
static bool8 SideCanWater(u8 side)
{
    return gBattleMons[side].types[0] == TYPE_WATER
        || gBattleMons[side].types[1] == TYPE_WATER;
}

static bool8 SpeciesCanWater(u16 species)
{
    return gSpeciesInfo[species].types[0] == TYPE_WATER
        || gSpeciesInfo[species].types[1] == TYPE_WATER;
}

#define WL_WORLD_BODY_RADIUS 6


static bool8 TraversalClear(bool8 waterAllowed, s16 x1, s16 y1, s16 x2, s16 y2, u8 radius)
{
    s32 dx, dy, steps, i, fx, fy, sx, sy;
    u8 terrain;
    if (!sActive)
        return TRUE;
    // Arena's 10px combat body is intentionally wider than a one-metatile
    // Emerald bridge/path. Keep combat hitboxes unchanged, but use a 6px field
    // footprint so legal 16px paths and bridges remain traversable.
    if (radius > WL_WORLD_BODY_RADIUS)
        radius = WL_WORLD_BODY_RADIUS;
    // A land mover that somehow stands in deep water (knock-back into a
    // shoreline corner, a spawn) may always move: it can only walk out.
    if (!waterAllowed)
    {
        u8 start = TerrainEntry(x1 >> 4, y1 >> 4);
        if ((start & WL_TERRAIN_DEEP_WATER) && !(start & WL_TERRAIN_BRIDGE))
            waterAllowed = TRUE;
    }
    dx = x2 - x1;
    dy = y2 - y1;
    // Footing (water) is checked at the centre, so keep centre samples <=8px
    // apart: no 16px metatile can be skipped.
    steps = max(Abs32(dx), Abs32(dy)) / min(8, SweepStep(radius)) + 1;
    fx = x1 << 8;
    fy = y1 << 8;
    sx = (dx << 8) / steps;
    sy = (dy << 8) / steps;
    for (i = 0; i <= steps; i++, fx += sx, fy += sy)
    {
        if (SolidCircle(fx >> 8, fy >> 8, radius))
            return FALSE;
        terrain = TerrainEntry((fx >> 8) >> 4, (fy >> 8) >> 4);
        // Water is a footing/traversal rule, not a solid body-radius wall.
        // A land Pokemon may stand at a shoreline or on a one-metatile-wide
        // bridge even if its collision circle visually overlaps nearby water.
        // Solid scenery still uses the full collision circle above.
        if (!waterAllowed && (terrain & WL_TERRAIN_DEEP_WATER)
            && !(terrain & WL_TERRAIN_BRIDGE))
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

// Corner assist: when a straight move is blocked, report which way (-1/+1)
// a perpendicular nudge of up to 6px would line the body up with an opening
// (one-metatile doorways, decks, bridges and ladders). 0 = no opening.
s8 WildlandsWorld_SlideNudge(u8 side, s16 x, s16 y, s8 sx, s8 sy)
{
    s16 k;
    bool8 water;
    if (!sActive)
        return 0;
    water = SideCanWater(side);
    // Point tests only: a <=5px shift is smaller than the footprint, so the
    // start and end squares overlap and no sweep is needed.
    for (k = 1; k <= 5; k++)
    {
        s8 dir;
        for (dir = -1; dir <= 1; dir += 2)
        {
            s16 nx = x + (sx ? 0 : dir * k), ny = y + (sx ? dir * k : 0);
            s16 fx = nx + sx * 3, fy = ny + sy * 3;
            u8 t;
            if (SolidCircle(nx, ny, WL_WORLD_BODY_RADIUS) || SolidCircle(fx, fy, WL_WORLD_BODY_RADIUS))
                continue;
            t = TerrainEntry(fx >> 4, fy >> 4);
            if (!water && (t & WL_TERRAIN_DEEP_WATER) && !(t & WL_TERRAIN_BRIDGE))
                continue;
            gWildlandsRoomTelemetry[5]++;
            return dir;
        }
    }
    return 0;
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
    // Linear march. The previous version re-swept the whole segment from the
    // origin at every 4px step (quadratic in range).
    u16 d;
    if (!sActive)
        return distance;
    if (SolidCircle(x, y, radius))
        return 0;
    for (d = 4; d <= distance; d += 4)
    {
        if (SolidCircle(x + dx * d / 256, y + dy * d / 256, radius))
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

#if WL_NAV_GRAPH
// ---- Island navigation: bounded A* over the build-time validated lattice ----
// Edges were accepted at build time only if the straight segment passes the
// same land footprint/footing test used here, so following node to node is
// legal for every land mover. Scratch lives on the heap during a match.
#define WL_NAV_HEAP 640
#define WL_NAV_EXPANSIONS 700
struct WildlandsNavScratch
{
    u16 stamp[WL_NAV_NODES];
    u16 g[WL_NAV_NODES];
    u16 parent[WL_NAV_NODES];
    u16 heap[WL_NAV_HEAP];
    u16 key[WL_NAV_HEAP];
    u16 gen;
};
static EWRAM_DATA struct WildlandsNavScratch *sNav = NULL;
static const s8 sNavDx[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const s8 sNavDy[8] = {0, 1, 1, 1, 0, -1, -1, -1};

void WildlandsWorld_ReleaseNav(void)
{
    if (sNav) { Free(sNav); sNav = NULL; }
}

static u16 NavNeighbor(u16 u, u8 d)
{
    u16 cell = sNavCell[u];
    s16 gx = cell % WL_NAV_GRID_W + sNavDx[d], gy = cell / WL_NAV_GRID_W + sNavDy[d];
    if (gx < 0 || gy < 0 || gx >= WL_NAV_GRID_W || gy >= WL_NAV_GRID_H)
        return 0xFFFF;
    return sNavGrid[gy * WL_NAV_GRID_W + gx];
}

static u16 NavHeuristic(u16 a, u16 b)
{
    s16 dx = Abs32(sNavPoints[a].x - sNavPoints[b].x) >> 4, dy = Abs32(sNavPoints[a].y - sNavPoints[b].y) >> 4;
    return (dx > dy ? dx * 10 + dy * 4 : dy * 10 + dx * 4) * 10 / WL_NAV_STEP;
}

// First node after `start` on a cheapest path toward `goal` (or toward the
// closest expanded node if the bounded search does not reach it).
static u16 NavSearch(u16 start, u16 goal)
{
    u16 n = 0, best = start, bestH = 0xFFFF, expansions = 0, u, v, i;
    if (!sNav)
        return 0xFFFF;
    if (++sNav->gen == 0) { memset(sNav->stamp, 0, sizeof(sNav->stamp)); sNav->gen = 1; }
    sNav->stamp[start] = sNav->gen; sNav->g[start] = 0; sNav->parent[start] = start;
    sNav->heap[n] = start; sNav->key[n++] = NavHeuristic(start, goal);
    while (n && expansions < WL_NAV_EXPANSIONS)
    {
        u16 h;
        u8 d;
        // pop min (binary heap)
        u = sNav->heap[0];
        n--;
        if (n)
        {
            u16 lastNode = sNav->heap[n], lastKey = sNav->key[n], pos = 0;
            for (;;)
            {
                u16 child = pos * 2 + 1;
                if (child >= n) break;
                if (child + 1 < n && sNav->key[child + 1] < sNav->key[child]) child++;
                if (sNav->key[child] >= lastKey) break;
                sNav->heap[pos] = sNav->heap[child]; sNav->key[pos] = sNav->key[child]; pos = child;
            }
            sNav->heap[pos] = lastNode; sNav->key[pos] = lastKey;
        }
        expansions++;
        h = NavHeuristic(u, goal);
        if (h < bestH) { bestH = h; best = u; }
        if (u == goal) { best = u; break; }
        for (d = 0; d < 8; d++)
        {
            u16 cost;
            if (!(sNavEdges[u] & (1 << d))) continue;
            v = NavNeighbor(u, d);
            if (v == 0xFFFF) continue;
            cost = sNav->g[u] + ((d & 1) ? 14 : 10);
            if (sNav->stamp[v] == sNav->gen && sNav->g[v] <= cost) continue;
            sNav->stamp[v] = sNav->gen; sNav->g[v] = cost; sNav->parent[v] = u;
            if (n < WL_NAV_HEAP)
            {
                u16 pos = n++, key = cost + NavHeuristic(v, goal);
                while (pos)
                {
                    u16 par = (pos - 1) / 2;
                    if (sNav->key[par] <= key) break;
                    sNav->heap[pos] = sNav->heap[par]; sNav->key[pos] = sNav->key[par]; pos = par;
                }
                sNav->heap[pos] = v; sNav->key[pos] = key;
            }
        }
    }
    gWildlandsWorldTelemetry[12] = expansions;
    if (best == start)
        return 0xFFFF;
    for (i = 0; i < WL_NAV_NODES && sNav->parent[best] != start; i++)
        best = sNav->parent[best];
    return best;
}

static bool8 MoverLine(bool8 speciesMode, u16 mover, s16 x1, s16 y1, s16 x2, s16 y2);

// Nearest graph node to (x,y); with requireLine, only nodes reachable by a
// straight legal segment count.
static u16 NavNodeNear(bool8 speciesMode, u16 mover, s16 x, s16 y, bool8 requireLine)
{
    s16 cx = (x >> 4) / WL_NAV_STEP, cy = (y >> 4) / WL_NAV_STEP, dx, dy;
    u16 best = 0xFFFF;
    u32 bestD = 0xFFFFFFFF;
    for (dy = -1; dy <= 1; dy++)
        for (dx = -1; dx <= 1; dx++)
        {
            s16 gx = cx + dx, gy = cy + dy;
            u16 node;
            s32 ddx, ddy;
            u32 d;
            if (gx < 0 || gy < 0 || gx >= WL_NAV_GRID_W || gy >= WL_NAV_GRID_H) continue;
            node = sNavGrid[gy * WL_NAV_GRID_W + gx];
            if (node == 0xFFFF) continue;
            ddx = sNavPoints[node].x - x; ddy = sNavPoints[node].y - y;
            d = ddx * ddx + ddy * ddy;
            if (d >= bestD) continue;
            if (requireLine && !MoverLine(speciesMode, mover, x, y, sNavPoints[node].x, sNavPoints[node].y)) continue;
            bestD = d; best = node;
        }
    return best;
}
#else
void WildlandsWorld_ReleaseNav(void) {}
#endif

static u8 NextWaypoint(bool8 speciesMode, u16 mover, s16 x, s16 y,
    s16 goalX, s16 goalY, struct ArenaPoint *next)
{
    u32 i;
    s32 best = 0x7FFFFFFF;
    s32 score;
    u16 d1, dg, directDistance;

    next->x = x;
    next->y = y;
    gWildlandsWorldTelemetry[10]++;
    // A target inside a room is pursued to that room's door.
    if (RoomAt(goalX, goalY) >= 0 && RoomAt(x, y) < 0)
    {
        s32 gx = goalX, gy = goalY;
        WildlandsWorld_OutdoorPos(&gx, &gy);
        goalX = gx; goalY = gy;
    }
    // Audit is monotonic: 1 means a route query occurred; 2 means at least
    // one real terrain-valid route succeeded. Later failed replans must not
    // erase proof that the AI already navigated the world successfully.
    if (gWildlandsWorldAudit[5] < 1)
        gWildlandsWorldAudit[5] = 1;

    // Most movement is open-terrain movement. Preserve the exact traversal
    // test and skip graph work entirely when the target is directly reachable.
    if (MoverLine(speciesMode, mover, x, y, goalX, goalY))
    {
        next->x = goalX;
        next->y = goalY;
        gWildlandsWorldAudit[5] = 2;
        return TRUE;
    }

    // V5 validation uses a deliberately small, hand-curated anchor set.
    // The previous implementation nested every anchor against every other
    // anchor and repeated long collision sweeps (O(N^2 * line length)). On
    // real GBA timing that could occupy the CPU across hundreds of VBlanks.
    // Choose one legal visible anchor per call instead; repeated calls advance
    // through the route. This keeps pathing bounded while preserving native
    // body/water legality and never teleports an actor through cover.
#if WL_NAV_GRAPH
    if (sActive && !sNav)
        sNav = AllocZeroed(sizeof(*sNav));
    if (sNav)
    {
        u16 s = NavNodeNear(speciesMode, mover, x, y, TRUE);
        u16 t = NavNodeNear(speciesMode, mover, goalX, goalY, FALSE);
        if (s != 0xFFFF && t != 0xFFFF)
        {
            u16 n = s == t ? t : NavSearch(s, t);
            if (n != 0xFFFF && MoverLine(speciesMode, mover, x, y, sNavPoints[n].x, sNavPoints[n].y))
                *next = sNavPoints[n];
            else
                *next = sNavPoints[s];
            gWildlandsWorldAudit[5] = 2;
            return TRUE;
        }
    }
#endif
    directDistance = PointDistance(x, y, goalX, goalY);
    {
        // Bounded work per call: rank anchors by cheap geometry, then pay for
        // swept terrain tests on at most WL_NAV_SWEEPS of them.
        #define WL_NAV_SWEEPS 4
        u8 cand[WL_NAV_SWEEPS];
        s32 candScore[WL_NAV_SWEEPS];
        u8 n = 0, k, j;
        for (i = 0; i < WL_NAV_POINT_COUNT; i++)
        {
            const struct ArenaPoint *p = &sNavPoints[i];
            d1 = PointDistance(x, y, p->x, p->y);
            dg = PointDistance(p->x, p->y, goalX, goalY);
            score = d1 + dg;
            if (d1 < 4 || (dg >= directDistance && d1 > 160))
                continue;
            if (n < WL_NAV_SWEEPS) { cand[n] = i; candScore[n] = score; n++; }
            else
            {
                for (k = 0, j = 0; k < WL_NAV_SWEEPS; k++) if (candScore[k] > candScore[j]) j = k;
                if (score < candScore[j]) { cand[j] = i; candScore[j] = score; }
            }
        }
        for (k = 0; k < n; k++)
        {
            const struct ArenaPoint *p = &sNavPoints[cand[k]];
            score = candScore[k];
            if (!MoverStand(speciesMode, mover, p->x, p->y))
                continue;
            if (!MoverLine(speciesMode, mover, x, y, p->x, p->y))
                continue;
            dg = PointDistance(p->x, p->y, goalX, goalY);
            d1 = PointDistance(x, y, p->x, p->y);
            if (MoverLine(speciesMode, mover, p->x, p->y, goalX, goalY))
                score -= 4096;
            else if (dg >= directDistance && d1 > 64)
                score += 1024;
            if (score < best)
            {
                best = score;
                *next = *p;
            }
        }
    }

    if (best == 0x7FFFFFFF)
    {
        gWildlandsWorldTelemetry[11]++;
        return FALSE;
    }

    gWildlandsWorldAudit[5] = 2;
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
