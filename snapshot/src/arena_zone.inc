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
#define ZONE_EXPLORE (60 * ZONE_FPS)
#define ZONE_WARN (30 * ZONE_FPS)
#define ZONE_SHRINK (60 * ZONE_FPS)
#define ZONE_STAGES 4
#define ZONE_MARKERS 6

enum { ZONE_EXPLORING, ZONE_WARNING, ZONE_SHRINKING, ZONE_SUDDEN_DEATH };

struct ArenaZone
{
    s32 cx, cy, r;        // current circle, pixels (r in Q8 for smooth shrink)
    s32 fromX, fromY, fromR, toX, toY, toR;
    u32 clock, phaseClock, seed;
    u32 frac[4];          // exposure accumulators, 1/65536 HP
    u8 phase, stage, active, markers[ZONE_MARKERS], hudSecond, outside;
};

static EWRAM_DATA struct ArenaZone sZone = {};
// [0] phase [1] stage [2] cx [3] cy [4] r [5] toX [6] toY [7] toR
// [8..11] storm damage dealt to battlers 0..3 [12] clock frames
// [13] exposed-actor frames [14] next-circle legal picks [15] tie-breaks
EWRAM_DATA u32 gWildlandsZoneTelemetry[16] = {};
// TEST HOOK ONLY: extra zone-clock frames per sim step, written by the mGBA
// harness to exercise full storm cycles quickly. Always 0 in normal play.
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
    for (i = 0; i < 12; i++)
    {
        s32 ox = (s32)(ZoneRand() % (2 * maxOff + 1)) - maxOff;
        s32 oy = (s32)(ZoneRand() % (2 * maxOff + 1)) - maxOff;
        if (ox * ox + oy * oy > maxOff * maxOff)
            continue;
        if (ZoneGround(sZone.cx + ox, sZone.cy + oy))
        {
            sZone.toX = sZone.cx + ox; sZone.toY = sZone.cy + oy;
            gWildlandsZoneTelemetry[14]++;
            break;
        }
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
    if (!WildlandsWorld_Active())
        return;
    // Same seed -> same circles: derive from the encounter, not the frame.
    sZone.seed = gBattleMons[1].personality ^ (gBattleMons[0].personality << 1) ^ 0x57494C44;
    sZone.cx = (WL_SLICE_BASE_X + WL_SLICE_W / 2) * 16;
    sZone.cy = (WL_SLICE_BASE_Y + WL_SLICE_H / 2) * 16;
    sZone.r = sZoneRadii[0] << 8;
    sZone.toX = sZone.cx; sZone.toY = sZone.cy; sZone.toR = sZone.r;
    sZone.active = TRUE;
    ZoneCreateMarkers();
}

static void ZoneDestroy(void)
{
    u32 i;
    for (i = 0; i < ZONE_MARKERS; i++)
        if (sZone.markers[i] != MAX_SPRITES)
        { DestroySprite(&gSprites[sZone.markers[i]]); sZone.markers[i] = MAX_SPRITES; }
}

// Squared distance from the circle edge test, pixels.
static bool8 ZoneOutside(s32 x, s32 y, s32 margin)
{
    s32 dx = x - sZone.cx, dy = y - sZone.cy, r = (sZone.r >> 8) - margin;
    if (!sZone.active)
        return FALSE;
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

static void ZoneDrawMarkers(void)
{
    u32 i, n = 0, a;
    s32 r = sZone.r >> 8;
    bool8 blink = sZone.phase == ZONE_WARNING && (sZone.clock & 16);
    for (a = 0; a < 32 && n < ZONE_MARKERS; a++)
    {
        s32 x = sZone.cx + Cos(a * 8, r);
        s32 y = sZone.cy + Sin(a * 8, r);
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
    for (i = n; i < ZONE_MARKERS; i++)
        if (sZone.markers[i] != MAX_SPRITES)
            gSprites[sZone.markers[i]].invisible = TRUE;
}

// Simulation step (runs once per fixed 60Hz step, possibly twice per render).
static void ZoneSim(void)
{
    if (!sZone.active)
        return;
    if (!sArena.paused && !sArena.resultTimer)
    {
        sZone.clock += 1 + gWildlandsZoneTestSpeed;
        sZone.phaseClock += 1 + gWildlandsZoneTestSpeed;
        switch (sZone.phase)
        {
        case ZONE_EXPLORING:
            if (sZone.phaseClock >= ZONE_EXPLORE)
            { sZone.phase = ZONE_WARNING; sZone.phaseClock = 0; ZonePickNext(); }
            break;
        case ZONE_WARNING:
            if (sZone.phaseClock >= ZONE_WARN)
            { sZone.phase = ZONE_SHRINKING; sZone.phaseClock = 0; }
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
    if (LootPopupText(text))
    {
        // Pickup feedback takes the zone slot for ~2.5s, in highlight colour.
        HudTinyWindow(2, 104, 10, text, sLoot.popupTeam ? 6 : 5, 11);
        StringCopy(text, sZone.phase == ZONE_SUDDEN_DEATH ? sFinal : sSafe);
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
}
