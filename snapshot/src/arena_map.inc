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

#define MAP_X0 4
#define MAP_Y0 4
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

static const u16 sMapColors[3] = {RGB(6, 12, 24), RGB(4, 14, 7), RGB(22, 20, 12)};

static u32 MapScale(void)
{
    u32 sx = (WL_SLICE_W + MAP_MAX_W - 1) / MAP_MAX_W, sy = (WL_SLICE_H + MAP_MAX_H - 1) / MAP_MAX_H;
    return max(1u, max(sx, sy));
}

static void MapPlot(s32 wx, s32 wy, u32 size, u8 color)
{
    u32 s = MapScale() * 16;
    s32 mx = (wx - WL_SLICE_BASE_X * 16) / (s32)s;
    s32 my = (wy - WL_SLICE_BASE_Y * 16) / (s32)s;
    if (mx < 0 || my < 0 || mx >= (s32)((WL_SLICE_W + MapScale() - 1) / MapScale())
        || my >= (s32)((WL_SLICE_H + MapScale() - 1) / MapScale()))
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
    static const u8 sHelp[] = _("B: BACK");
    u32 scale = MapScale(), x, y, i;
    u32 w = (WL_SLICE_W + scale - 1) / scale, h = (WL_SLICE_H + scale - 1) / scale;
    LoadPalette(sMapColors, BG_PLTT_ID(0) + MAPC_WATER, sizeof(sMapColors));
    FillWindowPixelBuffer(1, PIXEL_FILL(9));
    WindowRect(1, MAP_X0 - 1, MAP_Y0 - 1, w + 2, h + 2, 8);
    for (y = 0; y < h; y++)
        for (x = 0; x < w; x++)
        {
            // Majority-free, collision-first: any solid/water metatile in the
            // cell wins so blocked terrain is never shown as open ground.
            u32 dx, dy;
            u8 flags = 0;
            for (dy = 0; dy < scale; dy++)
                for (dx = 0; dx < scale; dx++)
                    flags |= WildlandsWorld_TerrainAt((WL_SLICE_BASE_X + x * scale + dx) * 16 + 8,
                                                      (WL_SLICE_BASE_Y + y * scale + dy) * 16 + 8);
            WindowRect(1, MAP_X0 + x, MAP_Y0 + y, 1, 1,
                (flags & WL_TERRAIN_BRIDGE) ? MAPC_GROUND
                : (flags & WL_TERRAIN_DEEP_WATER) ? MAPC_WATER
                : (flags & WL_TERRAIN_SOLID) ? MAPC_SOLID
                : (flags & WL_TERRAIN_CONCEAL) ? MAPC_GRASS : MAPC_GROUND);
        }
    // Overlays: zone first so actors draw on top.
    if (sZone.active)
    {
        MapCircle(sZone.cx, sZone.cy, sZone.r >> 8, MAPC_ZONE, FALSE);
        if (sZone.phase == ZONE_WARNING || sZone.phase == ZONE_SHRINKING)
            MapCircle(sZone.toX, sZone.toY, sZone.toR >> 8, MAPC_NEXT, TRUE);
    }
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < 32; i++)
        if (!(sLoot.collected & (1u << i)))
            MapPlot(sLootSpots[i].x, sLootSpots[i].y, 1, MAPC_LOOT);
    for (i = 0; i < 4; i++)
    {
        s32 ax, ay;
        if (!SquadAlive(i))
            continue;
        SquadPos(i, &ax, &ay);
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
    HudTinyWindow(1, x, 60, sHelp, 7, 8);
    PutWindowTilemap(1);
    CopyWindowToVram(1, COPYWIN_FULL);
    gWildlandsMapTelemetry[0]++;
    gWildlandsMapTelemetry[1] = w | (h << 8) | (scale << 16);
}
