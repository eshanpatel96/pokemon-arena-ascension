// Wildlands V5 live map: fifth pause-menu page (START -> MAP).
//
// Drawn from the SAME ROM terrain table the game uses for collision, so the
// map can never disagree with what blocks movement. One map pixel covers
// `scale` x `scale` metatiles of the world. Overlays use the same world
// coordinates as the actors: player, partner, both enemies (only when visible
// to the player team, i.e. not concealed in tall grass beyond 48px), the
// current safe circle, the announced next circle and remaining pickups.
// Pause policy: the map is a pause page, so the match clock is stopped while
// it is open (consistent with every other pause page).

#include "wildlands_minimap.inc"
#define MAP_X0 8
#define MAP_Y0 8
#define MAP_MAX_W 96
#define MAP_MAX_H 64
#define MAPC_WATER 13
#define MAPC_SOLID 14
#define MAPC_GROUND 15
#define MAPC_GRASS 3
#define MAPC_PLAYER 10
#define MAPC_ALLY 5
#define MAPC_FOE 6
#define MAPC_ZONE 7
#define MAPC_NEXT 4
#define MAPC_LOOT 12
#define MAPC_HOUSE 8

static const u16 sMapColors[3] = {RGB(6, 12, 24), RGB(4, 14, 7), RGB(22, 20, 12)};

static u32 MapScale(void)
{
    return WL_MINIMAP_SCALE;
}

static void MapPlot(s32 wx, s32 wy, u32 size, u8 color)
{
    u32 s = MapScale() * 16;
    s32 mx = (wx - WL_SLICE_BASE_X * 16) / (s32)s;
    s32 my = (wy - WL_SLICE_BASE_Y * 16) / (s32)s;
    if (mx < 0 || my < 0 || mx >= (s32)((WL_SLICE_W + MapScale() - 1) / MapScale())
        || my >= (s32)((WL_OUTDOOR_H + MapScale() - 1) / MapScale()))
        return;
    WindowRect(1, MAP_X0 + mx - size / 2, MAP_Y0 + my - size / 2, size, size, color);
}

static void MapCircle(s32 cx, s32 cy, s32 r, u8 color, bool8 dotted)
{
    u32 a;
    for (a = 0; a < 64; a++)
        if (!dotted || (a & 1))
            MapPlot(cx + Cos(a * 4, r), cy + Sin(a * 4, r), 1, color);
}

static void MapDraw(void)
{
    static const u8 sTitle[] = _("MAP");
    static const u8 sKeyYou[] = _("YOU");
    static const u8 sKeyAlly[] = _("ALLY");
    static const u8 sKeyFoe[] = _("FOE");
    static const u8 sKeyZone[] = _("ZONE");
    static const u8 sKeyNext[] = _("NEXT");
    static const u8 sKeyLoot[] = _("LOOT");
    static const u8 sKeyLair[] = _("LAIR");
    static const u8 sKeyHouse[] = _("HOME");
    static const u8 sHelp[] = _("B: BACK");
    u32 scale = MapScale(), x, i;
    u32 w = WL_MINIMAP_W, h = WL_MINIMAP_H;
    LoadPalette(sMapColors, BG_PLTT_ID(0) + MAPC_WATER, sizeof(sMapColors));
    FillWindowPixelBuffer(1, PIXEL_FILL(9));
    // Base terrain: prerendered at build time from the collision table.
    {
        u32 tx, ty, winW = 28;
        u8 *dst = gWindows[1].tileData;
        for (ty = 0; ty < WL_MINIMAP_TH && ty + MAP_Y0 / 8 < 9; ty++)
            for (tx = 0; tx < WL_MINIMAP_TW; tx++)
                CpuCopy32(&sMinimapTiles[(ty * WL_MINIMAP_TW + tx) * 32],
                    dst + ((ty + MAP_Y0 / 8) * winW + tx + MAP_X0 / 8) * 32, 32);
    }
    // Overlays: zone first so actors draw on top.
    if (sZone.active)
    {
        MapCircle(sZone.cx, sZone.cy, sZone.r >> 8, MAPC_ZONE, FALSE);
        if (sZone.phase == ZONE_WARNING || sZone.phase == ZONE_SHRINKING)
            MapCircle(sZone.toX, sZone.toY, sZone.toR >> 8, MAPC_NEXT, TRUE);
    }
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < LOOT_MAX; i++)
        if (!LootTaken(i) && !WildlandsWorld_InRoom(sLootSpots[i].x, sLootSpots[i].y))
            MapPlot(sLootSpots[i].x, sLootSpots[i].y, 1, MAPC_LOOT);
    // Doors: houses as grey dots, legendary lairs as white rings.
    for (i = 0; i < WildlandsWorld_DoorCount(); i++)
    {
        s16 dx, dy;
        bool8 lair;
        WildlandsWorld_DoorInfo(i, &dx, &dy, &lair);
        if (lair)
        {
            MapPlot(dx, dy, 5, MAPC_PLAYER);
            MapPlot(dx, dy, 3, MAPC_GROUND);
        }
        else
            MapPlot(dx, dy, 2, MAPC_HOUSE);
    }
    for (i = 0; i < 4; i++)
    {
        s32 ax, ay;
        if (!SquadAlive(i))
            continue;
        SquadPos(i, &ax, &ay);
        { s32 ox = ax / Q, oy = ay / Q; WildlandsWorld_OutdoorPos(&ox, &oy); ax = ox * Q; ay = oy * Q; }
        if ((i & 1) && WildlandsWorld_IsConcealed(ax / Q, ay / Q)
            && ArenaNav_Distance(ax / Q, ay / Q, sArena.bodies[0].x / Q, sArena.bodies[0].y / Q) > 48)
            continue; // the map does not reveal hidden enemies
        MapPlot(ax / Q, ay / Q, i == 0 ? 3 : 2, i == 0 ? MAPC_PLAYER : (i & 1) ? MAPC_FOE : MAPC_ALLY);
    }
    // Legend
    x = MAP_X0 + w + 10;
    PrintPopup(x, 2, sTitle, 5);
    WindowRect(1, x, 21, 3, 3, MAPC_PLAYER); HudTinyWindow(1, x + 6, 20, sKeyYou, 4, 4);
    WindowRect(1, x, 29, 2, 2, MAPC_ALLY); HudTinyWindow(1, x + 6, 28, sKeyAlly, 4, 4);
    WindowRect(1, x, 37, 2, 2, MAPC_FOE); HudTinyWindow(1, x + 6, 36, sKeyFoe, 4, 4);
    WindowRect(1, x + 36, 22, 3, 1, MAPC_ZONE); HudTinyWindow(1, x + 42, 20, sKeyZone, 4, 4);
    WindowRect(1, x + 36, 30, 1, 1, MAPC_NEXT); WindowRect(1, x + 38, 30, 1, 1, MAPC_NEXT);
    HudTinyWindow(1, x + 42, 28, sKeyNext, 4, 4);
    WindowRect(1, x + 37, 37, 1, 1, MAPC_LOOT); HudTinyWindow(1, x + 42, 36, sKeyLoot, 4, 4);
    WindowRect(1, x, 44, 5, 5, MAPC_PLAYER); WindowRect(1, x + 1, 45, 3, 3, MAPC_GROUND);
    HudTinyWindow(1, x + 8, 44, sKeyLair, 4, 4);
    WindowRect(1, x + 37, 45, 2, 2, MAPC_HOUSE); HudTinyWindow(1, x + 42, 44, sKeyHouse, 4, 4);
    HudTinyWindow(1, x, 60, sHelp, 7, 8);
    PutWindowTilemap(1);
    CopyWindowToVram(1, COPYWIN_FULL);
    gWildlandsMapTelemetry[0]++;
    gWildlandsMapTelemetry[1] = w | (h << 8) | (scale << 16);
}
