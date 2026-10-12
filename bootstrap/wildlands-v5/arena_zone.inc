// Wildlands V5 closing safe zone.
//
// One shared, deterministic world-coordinate controller: a circle (center,
// radius) and a phase clock drive the boundary markers, the HUD countdown, AI
// steering and time-based exposure damage for EVERY living actor (player lead,
// partner, enemy lead, enemy wing) whether on- or off-screen. The clock is
// Arena frames while unpaused and not in a result, so pause never leaks time.
//
// Tuning below is the handoff's PROPOSED default, not a locked decision:
// 60s exploration, then per stage 30s warning (next circle known) + 60s
// shrink; exposure 1/2/4/8% max HP per second by stage; then sudden death.

#define ZONE_FPS 60
// Playtest: the storm felt fast; 90s explore, 45s warning, 75s shrink.
// The island opens with a longer quiet phase (2:30) so lairs, loot and
// legendaries are in play before the first circle moves.
#ifdef WL_ISLAND
#define ZONE_EXPLORE (150 * ZONE_FPS)
#else
#define ZONE_EXPLORE (90 * ZONE_FPS)
#endif
#define ZONE_WARN (45 * ZONE_FPS)
#define ZONE_SHRINK (75 * ZONE_FPS)
#define ZONE_STAGES 4
#define ZONE_MARKERS 12
#define ZONE_RAIN 10

enum { ZONE_EXPLORING, ZONE_WARNING, ZONE_SHRINKING, ZONE_SUDDEN_DEATH };

struct ArenaZone
{
    s32 cx, cy, r;        // current circle, pixels (r in Q8 for smooth shrink)
    s32 fromX, fromY, fromR, toX, toY, toR;
    u32 clock, phaseClock, seed;
    u32 frac[4];          // exposure accumulators, 1/65536 HP
    u8 phase, stage, active, markers[ZONE_MARKERS], hudSecond, outside;
    u8 rain[ZONE_RAIN];
};

static EWRAM_DATA struct ArenaZone sZone = {};
// [0] phase [1] stage [2] cx [3] cy [4] r [5] toX [6] toY [7] toR
// [8..11] storm damage dealt to battlers 0..3 [12] clock frames
// [13] exposed-actor frames [14] next-circle legal picks [15] tie-breaks
EWRAM_DATA u32 gWildlandsZoneTelemetry[16] = {};
// TEST HOOK ONLY: extra zone-clock frames per sim step, written by the mGBA
// harness to exercise full storm cycles quickly (0xFFFF holds the storm
// still while UI/interior checks run). Always 0 in normal play.
EWRAM_DATA u16 gWildlandsZoneTestSpeed = 0;

#ifdef WL_ZONE_RADII
static const u16 sZoneRadii[ZONE_STAGES + 1] = WL_ZONE_RADII;
#else
static const u16 sZoneRadii[ZONE_STAGES + 1] = {600, 360, 210, 110, 40};
#endif
static const u8 sZonePctPerSec[ZONE_STAGES + 1] = {1, 1, 2, 4, 8};

static u32 ZoneRand(void)
{
    sZone.seed = sZone.seed * 1103515245 + 12345;
    return sZone.seed >> 16;
}

static bool8 ZoneGround(s32 x, s32 y)
{
    if (!WildlandsWorld_Active())
        return TRUE;
    return !(WildlandsWorld_TerrainAt(x, y) & (WL_TERRAIN_SOLID | WL_TERRAIN_DEEP_WATER));
}

static u32 ZoneIsqrt(u32 n)
{
    u32 r = 0, b = 1 << 30;
    while (b > n) b >>= 2;
    while (b) { if (n >= r + b) { n -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; }
    return r;
}

// Next circle: fully inside the current one, centred on legal dry ground.
static void ZonePickNext(void)
{
    s32 maxOff, i;
    s32 r = sZone.r >> 8;
    sZone.fromX = sZone.cx; sZone.fromY = sZone.cy; sZone.fromR = sZone.r;
    sZone.toR = sZoneRadii[min(sZone.stage + 1, ZONE_STAGES)] << 8;
    maxOff = r - (sZone.toR >> 8);
    if (maxOff < 0) maxOff = 0;
    sZone.toX = sZone.cx; sZone.toY = sZone.cy;
    // Hot zone: about one circle in three drifts toward a lair whose
    // legendary is still home, so boss fights stay reachable and contested.
    {
        s32 ax, ay;
        if (ZoneRand() % 100 < 35 && maxOff > 0 && DirectorLairAnchor(&ax, &ay))
        {
            s32 ox = ax - sZone.cx, oy = ay - sZone.cy;
            s32 len = ZoneIsqrt(ox * ox + oy * oy), lim = maxOff * 4 / 5;
            if (len > lim && len) { ox = ox * lim / len; oy = oy * lim / len; }
            if (ZoneGround(sZone.cx + ox, sZone.cy + oy))
            {
                sZone.toX = sZone.cx + ox; sZone.toY = sZone.cy + oy;
                gWildlandsZoneTelemetry[14]++;
                return;
            }
        }
    }
    for (i = 0; i < 12; i++)
    {
        s32 ox = (s32)(ZoneRand() % (2 * maxOff + 1)) - maxOff;
        s32 oy = (s32)(ZoneRand() % (2 * maxOff + 1)) - maxOff;
        if (ox * ox + oy * oy > maxOff * maxOff)
            continue;
        // The first circle always lands well off centre (a different side
        // of the island each match) so openings never feel the same.
        if (sZone.stage == 0 && i < 10 && ox * ox + oy * oy < maxOff * maxOff / 4)
            continue;
        if (ZoneGround(sZone.cx + ox, sZone.cy + oy))
        {
            sZone.toX = sZone.cx + ox; sZone.toY = sZone.cy + oy;
            gWildlandsZoneTelemetry[14]++;
            break;
        }
    }
}

// Storm rain: translucent streaks drawn only over the part of the screen the
// storm covers, so the safe edge reads at a glance (no free BG layer is left
// for fog; all four carry the HUD and the three terrain layers).
// The streak tile lives in the loot sheet (one extra tile after the gems):
// that allocation is proven safe from the Arena's frame uploads.
EWRAM_DATA u8 gWildlandsRainVisible = 0;
// diagnostics: [0] rain tile [1] rain[0] sprite id [2] its oam tileNum [3] priority | palette << 4 | objMode << 8 | affine << 12
EWRAM_DATA u16 gWildlandsRainDiag[4] = {};

static void ZoneCreateRain(void)
{
    struct SpriteTemplate t = sShotTemplate;
    u16 start = GetSpriteTileStartByTag(LOOT_TAG);
    u32 i;
    if (start == 0xFFFF)
        return;
    t.tileTag = LOOT_TAG;
    for (i = 0; i < ZONE_RAIN; i++)
    {
        sZone.rain[i] = CreateSprite(&t, 0, 0, 1);
        if (sZone.rain[i] != MAX_SPRITES)
        {
            struct Sprite *r = &gSprites[sZone.rain[i]];
            r->invisible = TRUE;
            r->animPaused = TRUE;
            r->oam.tileNum = start + LOOT_TYPES * 4;
            r->oam.paletteNum = LootPaletteNum();
        }
    }
}

// Biome weather inside the circle: 1 = sandstorm (desert: Rock/Ground/Steel
// moves +20%), 2 = ashfall (volcano: Fire +20%). Outside the circle the storm
// rain replaces it (Water +20%, Fire -20%).
EWRAM_DATA u8 gWildlandsWeather = 0;   // 0 none, 1 sand, 2 ash, 3 storm rain (at the camera)
static EWRAM_DATA u8 sShownWeather = 0;
static void DirPopup(const u8 *a, const u8 *b, u8 color);
static u8 ZoneBiomeWeather(void)
{
    u32 b = gWildlandsBiomeTelemetry[0];
    return b == 2 ? 1 : b == 4 ? 2 : 0;
}
u16 Wildlands_WeatherPercent(u8 type)
{
    if (!WildlandsWorld_Active())
        return 100;
    switch (gWildlandsWeather)
    {
    case 1: return (type == TYPE_ROCK || type == TYPE_GROUND || type == TYPE_STEEL) ? 120 : 100;
    case 2: return type == TYPE_FIRE ? 120 : 100;
    case 3: return type == TYPE_WATER ? 120 : type == TYPE_FIRE ? 80 : 100;
    }
    return 100;
}
static void ZoneDrawRain(void)
{
    static const u8 sSandName[] = _("SANDSTORM");
    static const u8 sAshName[] = _("ASHFALL");
    static const u8 sRockUp[] = _(" ROCK UP");
    static const u8 sFireUp[] = _(" FIRE UP");
    u32 i, n = 0;
    s32 camX = sArenaXLCameraX, camY = sArenaXLCameraY;
    s32 r = sZone.r >> 8;
    bool8 show = sZone.active && !sArena.paused && WildlandsWorld_Active()
        && !WildlandsWorld_InRoom(camX + 120, camY + 80);
    u8 biome = show ? ZoneBiomeWeather() : 0;
    u16 start = GetSpriteTileStartByTag(LOOT_TAG);
    {
        s32 cdx = camX + 120 - sZone.cx, cdy = camY + 80 - sZone.cy;
        gWildlandsWeather = !show ? 0 : (r > 0 && cdx * cdx + cdy * cdy > r * r) ? 3 : biome;
    }
    if (gWildlandsWeather != sShownWeather && (gWildlandsWeather == 1 || gWildlandsWeather == 2))
        DirPopup(gWildlandsWeather == 1 ? sSandName : sAshName, gWildlandsWeather == 1 ? sRockUp : sFireUp, 7);
    sShownWeather = gWildlandsWeather;
    {
        // Streak sprites exist only while something can show: the storm edge
        // in view or biome weather. Otherwise they are freed (FPS: 10 fewer
        // sprites to animate and sort every frame).
        s32 cdx = camX + 120 - sZone.cx, cdy = camY + 80 - sZone.cy;
        s32 d2 = cdx * cdx + cdy * cdy, rin = r > 170 ? r - 170 : 0;
        bool8 needed = show && (biome || r <= 0 || d2 >= rin * rin);
        if (sZone.rain[0] == MAX_SPRITES && needed && !(sArena.frame & 31))
            ZoneCreateRain();
        else if (sZone.rain[0] != MAX_SPRITES && !needed && !(sArena.frame & 63))
            ZoneFreeRain();
    }
    for (i = 0; i < ZONE_RAIN; i++)
    {
        struct Sprite *spr;
        s32 sx, sy, wx, wy, dx, dy;
        if (sZone.rain[i] == MAX_SPRITES)
            continue;
        spr = &gSprites[sZone.rain[i]];
        // Each streak falls down-left at its own phase; positions come from
        // the game clock, so nothing is stored per drop.
        sy = (s32)((i * 53 + sArena.frame * (5 + (i & 1))) % 176) - 8;
        sx = (s32)((i * 101 + 40 - (sArena.frame + i * 29) / 2) & 255) - 8;
        wx = camX + sx; wy = camY + sy;
        dx = wx - sZone.cx; dy = wy - sZone.cy;
        if (show && biome && sx <= 244 && !(r > 0 && dx * dx + dy * dy > r * r))
        {
            // Inside the circle: the biome's own weather.
            if (biome == 1)
            {
                sx = (s32)((i * 101 + sArena.frame * (6 + (i & 1))) & 255) - 8;
                sy = (s32)((i * 53 + sArena.frame / 3) % 176) - 8;
            }
            else
            {
                sy = (s32)((i * 53 + sArena.frame / (2 + (i & 1))) % 176) - 8;
                sx = (s32)((i * 101 + ((sArena.frame >> 3) + i) % 6) & 255) - 8;
            }
            wx = camX + sx; wy = camY + sy;
            dx = wx - sZone.cx; dy = wy - sZone.cy;
            if (sx > 244 || (r > 0 && dx * dx + dy * dy > r * r))
            { spr->invisible = TRUE; continue; }
            if (start != 0xFFFF) spr->oam.tileNum = start + LOOT_TYPES * 4 + biome;
            spr->x = wx; spr->y = wy;
            spr->invisible = FALSE;
            continue;
        }
        if (start != 0xFFFF) spr->oam.tileNum = start + LOOT_TYPES * 4;
        if (!show || sx > 244 || (r > 0 && dx * dx + dy * dy <= r * r))
        { spr->invisible = TRUE; continue; }
        spr->x = wx; spr->y = wy;
        spr->invisible = FALSE;
        n++;
    }
    gWildlandsRainVisible = n;
    gWildlandsRainDiag[0] = GetSpriteTileStartByTag(LOOT_TAG);
    gWildlandsRainDiag[1] = sZone.rain[0];
    if (sZone.rain[0] != MAX_SPRITES)
    {
        struct Sprite *r0 = &gSprites[sZone.rain[0]];
        gWildlandsRainDiag[2] = r0->oam.tileNum;
        gWildlandsRainDiag[3] = r0->oam.priority | (r0->oam.paletteNum << 4) | (r0->oam.objMode << 8) | (r0->oam.affineMode << 12);
    }
}

static void ZoneCreateMarkers(void)
{
    u32 i;
    for (i = 0; i < ZONE_MARKERS; i++)
    {
        sZone.markers[i] = CreateSprite(&sShotTemplate, 0, 0, 2);
        if (sZone.markers[i] != MAX_SPRITES)
        {
            gSprites[sZone.markers[i]].oam.paletteNum = IndexOfSpritePaletteTag(SHOT_TAG + 1);
            gSprites[sZone.markers[i]].invisible = TRUE;
        }
    }
}

static void ZoneInit(void)
{
    u32 i;
    if (sWildlandsEncounterLive && sZone.active)
    {
        // Re-entry after a native menu: the clock and circles continue.
        ZoneCreateMarkers();
        return;
    }
    memset(&sZone, 0, sizeof(sZone));
    memset(gWildlandsZoneTelemetry, 0, sizeof(gWildlandsZoneTelemetry));
    for (i = 0; i < ZONE_MARKERS; i++) sZone.markers[i] = MAX_SPRITES;
    for (i = 0; i < ZONE_RAIN; i++) sZone.rain[i] = MAX_SPRITES;
    if (!WildlandsWorld_Active())
        return;
    // Same seed -> same circles: derive from the encounter, not the frame.
    sZone.seed = gBattleMons[1].personality ^ (gBattleMons[0].personality << 1) ^ 0x57494C44;
    sZone.cx = (WL_SLICE_BASE_X + WL_SLICE_W / 2) * 16;
    sZone.cy = (WL_SLICE_BASE_Y + WL_OUTDOOR_H / 2) * 16;
    sZone.r = sZoneRadii[0] << 8;
    sZone.toX = sZone.cx; sZone.toY = sZone.cy; sZone.toR = sZone.r;
    sZone.active = TRUE;
    ZoneCreateMarkers();
}

static void ZoneFreeRain(void)
{
    u32 i;
    for (i = 0; i < ZONE_RAIN; i++)
        if (sZone.rain[i] != MAX_SPRITES)
        { DestroySprite(&gSprites[sZone.rain[i]]); sZone.rain[i] = MAX_SPRITES; }
}

static void ZoneDestroy(void)
{
    u32 i;
    for (i = 0; i < ZONE_MARKERS; i++)
        if (sZone.markers[i] != MAX_SPRITES)
        { DestroySprite(&gSprites[sZone.markers[i]]); sZone.markers[i] = MAX_SPRITES; }
    for (i = 0; i < ZONE_RAIN; i++)
        if (sZone.rain[i] != MAX_SPRITES)
        { DestroySprite(&gSprites[sZone.rain[i]]); sZone.rain[i] = MAX_SPRITES; }
}

// Squared distance from the circle edge test, pixels.
static bool8 ZoneOutside(s32 x, s32 y, s32 margin)
{
    s32 dx, dy, r = (sZone.r >> 8) - margin;
    if (!sZone.active)
        return FALSE;
    WildlandsWorld_OutdoorPos(&x, &y);   // inside a house = at its door
    dx = x - sZone.cx; dy = y - sZone.cy;
    if (r <= 0)
        return TRUE;
    return dx * dx + dy * dy > r * r;
}

static u16 ZoneSecondsLeft(void)
{
    u32 left;
    switch (sZone.phase)
    {
    case ZONE_EXPLORING: left = ZONE_EXPLORE - sZone.phaseClock; break;
    case ZONE_WARNING: left = ZONE_WARN - sZone.phaseClock; break;
    case ZONE_SHRINKING: left = ZONE_SHRINK - sZone.phaseClock; break;
    default: left = 0; break;
    }
    return (left + ZONE_FPS - 1) / ZONE_FPS;
}

static void ZoneDamage(void)
{
    u32 b, pct = sZonePctPerSec[min(sZone.stage, ZONE_STAGES)];
    u16 before[4], after[4];
    bool8 alive[4], exposed[4];
    s32 x, y;
    u32 dmg[4];
    if (sZone.phase == ZONE_SUDDEN_DEATH) pct = 8;
    for (b = 0; b < 4; b++)
    {
        alive[b] = SquadAlive(b);
        exposed[b] = FALSE;
        dmg[b] = 0;
        before[b] = after[b] = alive[b] ? gBattleMons[b].hp : 0;
        if (!alive[b])
            continue;
        SquadPos(b, &x, &y);
        if (!ZoneOutside(x / Q, y / Q, 0))
        { sZone.frac[b] = 0; continue; } // re-entry resets the fraction: no banking
        exposed[b] = TRUE;
        gWildlandsZoneTelemetry[13]++;
        // Elapsed-time exposure: maxHP * pct% per second, accumulated per frame.
        sZone.frac[b] += (u32)gBattleMons[b].maxHP * pct * 65536 / (100 * ZONE_FPS);
        dmg[b] = sZone.frac[b] >> 16;
        sZone.frac[b] &= 0xFFFF;
        after[b] = dmg[b] >= before[b] ? 0 : before[b] - dmg[b];
    }
    // Deterministic simultaneous elimination: if this tick would remove BOTH
    // teams' last members, the team with more total HP left before the tick
    // survives at 1 HP (player team on an exact tie).
    if ((alive[0] || alive[2]) && (alive[1] || alive[3])
        && !after[0] && !after[2] && !after[1] && !after[3])
    {
        u32 t0 = before[0] + before[2], t1 = before[1] + before[3];
        u8 keep = t1 > t0 ? 1 : 0;
        u8 who = alive[keep] ? keep : keep + 2;
        after[who] = 1;
        gWildlandsZoneTelemetry[15]++;
    }
    for (b = 0; b < 4; b++)
    {
        u16 hp;
        if (!exposed[b] || after[b] == before[b])
            continue;
        hp = after[b];
        gBattleMons[b].hp = hp;
        SetMonData(SquadPartyMon(b), MON_DATA_HP, &hp);
        gWildlandsZoneTelemetry[8 + b] += before[b] - hp;
        SquadPos(b, &x, &y);
        ArenaFeedback_Impact(b & 1, x / Q, y / Q, before[b] - hp, ARENA_FEEDBACK_DAMAGE);
        if (b < 2) sArena.bodies[b].flash = 4; else sSquadWings[b - 2].flash = 4;
        sArena.hudDirty = TRUE;
        if (!hp)
            SquadKO(b, b ^ 1);
    }
}

// Storm edge: markers every 20px along the stretch of the circle nearest
// the camera (straight-line tangent approximation; exact enough on screen),
// so the wall reads as a line instead of a few dots.
static void ZoneDrawMarkers(void)
{
    u32 i, n = 0;
    s32 r = sZone.r >> 8, ccx = sArenaXLCameraX + 120, ccy = sArenaXLCameraY + 80;
    s32 dx = ccx - sZone.cx, dy = ccy - sZone.cy;
    s32 d = ZoneIsqrt(dx * dx + dy * dy);
    bool8 blink = sZone.phase == ZONE_WARNING && (sZone.clock & 16);
    bool8 hide = WildlandsWorld_InRoom(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q) || !d || r <= 0;
    if (!hide)
    {
        s32 px = sZone.cx + dx * r / d, py = sZone.cy + dy * r / d;   // nearest edge point
        s32 tx = -dy * 20 / d, ty = dx * 20 / d;                      // 20px along the edge
        s32 k;
        for (k = -(ZONE_MARKERS / 2); k < ZONE_MARKERS / 2 && n < ZONE_MARKERS; k++)
        {
            s32 x = px + tx * k, y = py + ty * k;
            if (x < sArenaXLCameraX - 8 || x > sArenaXLCameraX + 248
                || y < sArenaXLCameraY - 8 || y > sArenaXLCameraY + 168)
                continue;
            if (sZone.markers[n] != MAX_SPRITES)
            {
                struct Sprite *s = &gSprites[sZone.markers[n]];
                s->x = x; s->y = y;
                s->invisible = sArena.paused || blink;
            }
            n++;
        }
    }
    for (i = n; i < ZONE_MARKERS; i++)
        if (sZone.markers[i] != MAX_SPRITES)
            gSprites[sZone.markers[i]].invisible = TRUE;
}

// Storm tint: while the player stands in the storm the terrain palettes are
// blended toward violet (BG palettes only; HUD palette 0 untouched).
static EWRAM_DATA bool8 sZoneTinted = FALSE;
static void ZoneTint(void)
{
    bool8 out = sZone.active && !sArena.paused
        && ZoneOutside(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q, 0);
    // Re-apply periodically while out: a door or menu reloads the palettes.
    if (out == sZoneTinted && (!out || (sArena.frame & 31)))
        return;
    sZoneTinted = out;
    gWildlandsZoneTelemetry[11] = out;
    WildlandsWorld_RestorePalettes();
    if (out)
    {
        BlendPalette(BG_PLTT_ID(1), 13 * 16, 6, RGB(14, 4, 20));
        // The arena re-blends BG palettes from the unfaded buffer each frame;
        // commit the tint there so it persists. RestorePalettes undoes it.
        CpuCopy16(&gPlttBufferFaded[BG_PLTT_ID(1)], &gPlttBufferUnfaded[BG_PLTT_ID(1)], 13 * 16 * 2);
    }
}

// Simulation step (runs once per fixed 60Hz step, possibly twice per render).
static void ZoneSim(void)
{
    if (!sZone.active)
        return;
    if (gWildlandsZoneTestSpeed == 0xFFFE)
    {
        // TEST HOOK ONLY: restore the opening circle, then hold it.
        sZone.phase = ZONE_EXPLORING; sZone.stage = 0;
        sZone.clock = sZone.phaseClock = 0;
        sZone.cx = (WL_SLICE_BASE_X + WL_SLICE_W / 2) * 16;
        sZone.cy = (WL_SLICE_BASE_Y + WL_OUTDOOR_H / 2) * 16;
        sZone.r = sZoneRadii[0] << 8;
        sZone.toX = sZone.cx; sZone.toY = sZone.cy; sZone.toR = sZone.r;
        memset(sZone.frac, 0, sizeof(sZone.frac));
        gWildlandsZoneTestSpeed = 0xFFFF;
    }
    if (!sArena.paused && !sArena.resultTimer && gWildlandsZoneTestSpeed != 0xFFFF)
    {
        sZone.clock += 1 + gWildlandsZoneTestSpeed;
        sZone.phaseClock += 1 + gWildlandsZoneTestSpeed;
        switch (sZone.phase)
        {
        case ZONE_EXPLORING:
            if (sZone.phaseClock >= ZONE_EXPLORE)
            {
                static const u8 sWarn[] = _("STORM INCOMING");
                sZone.phase = ZONE_WARNING; sZone.phaseClock = 0; ZonePickNext();
                DirectorLog(sWarn);
            }
            break;
        case ZONE_WARNING:
            if (sZone.phaseClock >= ZONE_WARN)
            {
                static const u8 sShrink[] = _("STORM CLOSING IN");
                sZone.phase = ZONE_SHRINKING; sZone.phaseClock = 0;
                DirectorLog(sShrink);
            }
            break;
        case ZONE_SHRINKING:
        {
            s32 t = sZone.phaseClock;
            sZone.cx = sZone.fromX + (sZone.toX - sZone.fromX) * t / ZONE_SHRINK;
            sZone.cy = sZone.fromY + (sZone.toY - sZone.fromY) * t / ZONE_SHRINK;
            sZone.r = sZone.fromR + (sZone.toR - sZone.fromR) * t / ZONE_SHRINK;
            if (sZone.phaseClock >= ZONE_SHRINK)
            {
                sZone.cx = sZone.toX; sZone.cy = sZone.toY; sZone.r = sZone.toR;
                sZone.stage++;
                sZone.phaseClock = 0;
                if (sZone.stage >= ZONE_STAGES) sZone.phase = ZONE_SUDDEN_DEATH;
                else { sZone.phase = ZONE_WARNING; ZonePickNext(); }
            }
            break;
        }
        }
        ZoneDamage();
        if (ZoneSecondsLeft() != sZone.hudSecond)
        { sZone.hudSecond = ZoneSecondsLeft(); sArena.hudDirty = TRUE; }
    }
}

// Render step: markers + telemetry once per drawn frame.
static void ZoneTick(void)
{
    if (!sZone.active)
        return;
    ZoneDrawMarkers();
    ZoneDrawRain();
    if (WildlandsWorld_Active())
        ZoneTint();
    gWildlandsZoneTelemetry[0] = sZone.phase;
    gWildlandsZoneTelemetry[1] = sZone.stage;
    gWildlandsZoneTelemetry[2] = sZone.cx;
    gWildlandsZoneTelemetry[3] = sZone.cy;
    gWildlandsZoneTelemetry[4] = sZone.r >> 8;
    gWildlandsZoneTelemetry[5] = sZone.toX;
    gWildlandsZoneTelemetry[6] = sZone.toY;
    gWildlandsZoneTelemetry[7] = sZone.toR >> 8;
    gWildlandsZoneTelemetry[12] = sZone.clock;
}

// AI: an actor outside (or about to be outside) the safe circle heads for it.
static bool8 ZoneSteer(s32 x, s32 y, s32 *goalX, s32 *goalY)
{
    s32 margin = sZone.phase == ZONE_SHRINKING || sZone.phase == ZONE_SUDDEN_DEATH ? 24 : 8;
    if (!sZone.active || sZone.phase == ZONE_EXPLORING)
        return FALSE;
    if (sZone.phase == ZONE_WARNING)
    {
        // Pre-rotate toward the announced next circle.
        s32 dx = x - sZone.toX, dy = y - sZone.toY, r = (sZone.toR >> 8) - 8;
        if (dx * dx + dy * dy <= r * r)
            return FALSE;
        *goalX = sZone.toX; *goalY = sZone.toY;
        return TRUE;
    }
    if (!ZoneOutside(x, y, margin))
        return FALSE;
    *goalX = sZone.cx; *goalY = sZone.cy;
    return TRUE;
}

static void ZoneSteerEnemy(struct ArenaBody *body)
{
    s32 gx, gy;
    struct ArenaPoint wp;
    if (!ZoneSteer(body->x / Q, body->y / Q, &gx, &gy))
        return;
    if (WildlandsWorld_Active() && !((sArena.frame + 2) & 7))
    {
        if (WildlandsWorld_NextWaypointSide(1, body->x / Q, body->y / Q, gx, gy, &wp))
        { sArena.waypoint.x = wp.x; sArena.waypoint.y = wp.y; }
    }
}

// Bottom HUD line (Wildlands replaces the capture-ball help).
static u32 ZoneHudKey(void)
{
    u32 key = (u32)(sLoot.boost[0][0] * 7 + sLoot.boost[0][1] * 3 + sLoot.boost[0][2]) * 0x9E3779B1u;
    key ^= (u32)(sLoot.popupTimer != 0) << 31;
    key ^= (u32)(sLoot.boost[1][0] * 5 + sLoot.boost[1][1] * 11 + sLoot.boost[1][2] * 13) << 24;
    key ^= sZone.hudSecond;
    key ^= (u32)sZone.phase << 8;
    key ^= (u32)ZoneOutside(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q, 0) << 11;
    key ^= (u32)(SquadAlive(2) ? gBattleMons[2].hp : 0) << 12;
    key ^= (u32)(SquadAlive(3) ? gBattleMons[3].hp : 0) << 22;
    key ^= (u32)DirectorLeft() << 26;
    key ^= (u32)DirectorPopupActive() << 30;
    return key;
}

static void ZoneHudLine(void)
{
    static const u8 sSafe[] = _("ZONE ");
    static const u8 sNext[] = _("NEXT ");
    static const u8 sClose[] = _("STRM ");
    static const u8 sOut[] = _("OUT! ");
    static const u8 sFinal[] = _("FINAL");
    static const u8 sAlly[] = _("AL");
    static const u8 sFoe[] = _("F2 ");
    static const u8 sDown[] = _("--");
    u8 text[24];
    u8 *end;
    u16 s;
    bool8 out;
    if (!sZone.active)
        return;
    out = ZoneOutside(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q, 0);
    s = ZoneSecondsLeft();
    if (sZone.phase == ZONE_SUDDEN_DEATH)
        StringCopy(text, sFinal);
    else
    {
        end = StringCopy(text, out ? sOut : sZone.phase == ZONE_EXPLORING ? sSafe
            : sZone.phase == ZONE_WARNING ? sNext : sClose);
        end = ConvertIntToDecimalStringN(end, s / 60, STR_CONV_MODE_LEFT_ALIGN, 1);
        *end++ = CHAR_COLON;
        ConvertIntToDecimalStringN(end, s % 60, STR_CONV_MODE_LEADING_ZEROS, 2);
    }
    {
        u8 color;
        if (DirectorPopupText(text, &color))
        {
            // Kill feed / legendary news take the zone slot like pickups.
            // Kill feed / legendary news: full width up to the LEFT counter.
            HudTinyWindow(2, 104, 10, text, color, 20);
            goto left;
        }
    }
    if (LootPopupText(text))
    {
        // Pickup feedback takes the zone slot for ~2.5s, in highlight colour.
        HudTinyWindow(2, 104, 10, text, sLoot.popupTeam ? 6 : 5, 20);
        goto left;
    }
    else
        HudTinyWindow(2, 104, 10, text, out ? 6 : 4, 9);
    end = StringCopy(text, sAlly);
    *end++ = CHAR_SPACE;
    if (SquadAlive(2)) ConvertIntToDecimalStringN(end, gBattleMons[2].hp, STR_CONV_MODE_LEFT_ALIGN, 3);
    else StringCopy(end, sDown);
    HudTinyWindow(2, 144, 10, text, 4, 6);
    end = StringCopy(text, sFoe);
    if (SquadAlive(3)) ConvertIntToDecimalStringN(end, gBattleMons[3].hp, STR_CONV_MODE_LEFT_ALIGN, 3);
    else StringCopy(end, sDown);
    HudTinyWindow(2, 172, 10, text, 6, 6);
left:
    if (DirectorLeft() || DirectorRunning())
    {
        static const u8 sLeftTag[] = _("LEFT");
        end = ConvertIntToDecimalStringN(text, DirectorLeft(), STR_CONV_MODE_LEFT_ALIGN, 2);
        StringCopy(end, sLeftTag);
    }
    else
        LootHudText(text);
    HudTinyWindow(2, 204, 10, text, 5, 6);
}

// Pause screen: running team boost totals (yours and the enemy duo's).
static void WildlandsPauseBoosts(void)
{
    static const u8 sMine[] = _("TEAM BOOSTS");
    static const u8 sFoe[] = _("FOE BOOSTS");
    u8 text[12];
    if (!sLoot.live)
        return;
    HudTinyWindow(1, 120, 6, sMine, 5, 11);
    text[0] = CHAR_A; text[1] = CHAR_PLUS; text[2] = CHAR_0 + sLoot.boost[0][0];
    text[3] = CHAR_SPACE; text[4] = CHAR_D; text[5] = CHAR_PLUS; text[6] = CHAR_0 + sLoot.boost[0][1];
    text[7] = CHAR_SPACE; text[8] = CHAR_S; text[9] = CHAR_PLUS; text[10] = CHAR_0 + sLoot.boost[0][2]; text[11] = EOS;
    HudTinyWindow(1, 120, 14, text, 4, 11);
    HudTinyWindow(1, 120, 26, sFoe, 6, 10);
    text[2] = CHAR_0 + sLoot.boost[1][0]; text[6] = CHAR_0 + sLoot.boost[1][1]; text[10] = CHAR_0 + sLoot.boost[1][2];
    HudTinyWindow(1, 120, 34, text, 4, 11);
    DirectorPauseLine();
}
