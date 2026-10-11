// Wildlands enemy duo brain: picks one team goal each time the enemy lead
// thinks, and the enemy wing follows it.
//
//   FIGHT    a player member is visible and the fight is winnable: focus the
//            weaker / better-matched target with both members.
//   RETREAT  the lead is hurt and the duo is behind (HP, numbers, type
//            matchup): break away to
//            a legal point far from the threat, preferring tall grass and the
//            safe circle; the wing covers with fire but does not chase.
//   LOOT     nothing visible: walk to the nearest useful pickup (supplies when
//            hurt, otherwise stat orbs).
//   RAID     nothing visible and a lair cache is still there: walk to the
//            lair door, go in, take the cache, come back out.
//   ROAM     nothing worth doing: wander near where it is.
// Storm rotation is layered on top by ZoneSteerEnemy (waypoint override).
// Decisions run on the native think timer (every few frames), never per
// projectile step, so the cost stays a few hundred cycles per decision.

enum { BRAIN_ROAM, BRAIN_FIGHT, BRAIN_RETREAT, BRAIN_LOOT, BRAIN_RAID };

static EWRAM_DATA struct {
    u8 mode, focus, door, spot;
    u16 modeClock, roomStart, roamClock, calm;
    u16 modeStart, retreatEnd, offStamp;
    u8 offReady;
    u8 off[4][4];   // cached BrainOffense(attacker, defender), battlers 0..3
} sBrain = {};
// [0] mode [1] focus battler [2] fight decisions [3] retreat decisions
// [4] loot runs started [5] lair raids entered [6] raid exits
// [7] last advantage (x100: >100 = enemy duo ahead)
EWRAM_DATA u32 gWildlandsBrainTelemetry[8] = {};

// Best type effectiveness (x10) of any damaging move `attacker` knows
// against `defender`, with STAB folded in (x15/10).
static u32 BrainOffenseCalc(u8 attacker, u8 defender)
{
    u32 best = 0, i, k;
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        u16 move = gBattleMons[attacker].moves[i];
        u8 type;
        u32 m = 10;
        if (!move || !gBattleMoves[move].power)
            continue;
        type = gBattleMoves[move].type;
        for (k = 0; TYPE_EFFECT_ATK_TYPE(k) != TYPE_ENDTABLE; k += 3)
        {
            if (TYPE_EFFECT_ATK_TYPE(k) != type)
                continue;
            if (TYPE_EFFECT_DEF_TYPE(k) == gBattleMons[defender].types[0])
                m = m * TYPE_EFFECT_MULTIPLIER(k) / 10;
            if (TYPE_EFFECT_DEF_TYPE(k) == gBattleMons[defender].types[1]
                && gBattleMons[defender].types[1] != gBattleMons[defender].types[0])
                m = m * TYPE_EFFECT_MULTIPLIER(k) / 10;
        }
        if (type == gBattleMons[attacker].types[0] || type == gBattleMons[attacker].types[1])
            m = m * 15 / 10;
        if (m > best)
            best = m;
    }
    return best ? best : 5;
}

// The type table walk is ~100 entries per move: cache the 4x4 matrix and
// refresh it every 20s (moves and types are static within an encounter).
static u32 BrainOffense(u8 attacker, u8 defender)
{
    if (!sBrain.offReady || (u16)(sArena.frame - sBrain.offStamp) > 1200)
    {
        u32 a, d;
        for (a = 0; a < 4; a++)
            for (d = 0; d < 4; d++)
                sBrain.off[a][d] = (a & 1) == (d & 1) ? 10 : min(255, BrainOffenseCalc(a, d));
        sBrain.offReady = TRUE;
        sBrain.offStamp = sArena.frame;
    }
    return sBrain.off[attacker][defender];
}

static u32 BrainHpPct(u8 b)
{
    return SquadAlive(b) && gBattleMons[b].maxHP ? gBattleMons[b].hp * 100 / gBattleMons[b].maxHP : 0;
}

// Team strength against the other team: sum of HP% x average offense.
static u32 BrainPower(u8 team)
{
    u32 sum = 0, m, f;
    for (m = 0; m < 2; m++)
    {
        u8 b = team + m * 2;
        u32 off = 0, n = 0;
        if (!SquadAlive(b))
            continue;
        for (f = 0; f < 2; f++)
        {
            u8 foe = (team ^ 1) + f * 2;
            if (!SquadAlive(foe))
                continue;
            off += BrainOffense(b, foe);
            n++;
        }
        sum += BrainHpPct(b) * (n ? off / n : 10);
    }
    return sum;
}

static bool8 BrainCanGo(s32 x, s32 y)
{
    return WildlandsWorld_CanStandSide(1, x, y, 6);
}

// Flee point: 12 headings at ~110px, scored by distance from the threat,
// concealment and staying inside the circle; must be directly reachable.
static bool8 BrainFleePoint(struct ArenaBody *body, s32 tx, s32 ty, s32 *gx, s32 *gy)
{
    static const s8 dirX[12] = {16, 14, 8, 0, -8, -14, -16, -14, -8, 0, 8, 14};
    static const s8 dirY[12] = {0, 8, 14, 16, 14, 8, 0, -8, -14, -16, -14, -8};
    s32 bx = body->x / Q, by = body->y / Q, best = -0x7FFFFFFF;
    u32 i;
    bool8 found = FALSE;
    for (i = 0; i < 12; i++)
    {
        s32 cx = bx + dirX[i] * 7, cy = by + dirY[i] * 7, score;
        if (!BrainCanGo(cx, cy) || !WildlandsWorld_BodyLineClear(1, bx, by, cx, cy, 6))
            continue;
        score = ArenaNav_Distance(cx, cy, tx, ty) * 2;
        if (WildlandsWorld_IsConcealed(cx, cy)) score += 90;
        if (ZoneOutside(cx, cy, 16)) score -= 220;
        if (!WildlandsWorld_LineClear(cx, cy, tx, ty, 2)) score += 60; // breaks line of sight
        if (score > best) { best = score; *gx = cx; *gy = cy; found = TRUE; }
    }
    return found;
}

// Nearest useful pickup for the enemy team. Room pickups are reached through
// their room's door (RAID); only lair caches and, when hurt, supplies are
// worth a detour indoors.
static bool8 BrainPickLoot(struct ArenaBody *body, bool8 hurt, u8 *spot, u8 *door)
{
    u32 i, bestD = hurt ? 900 : 640;
    bool8 found = FALSE;
    s32 bx = body->x / Q, by = body->y / Q;
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < LOOT_MAX; i++)
    {
        const struct LootSpot *s = &sLootSpots[i];
        s32 lx = s->x, ly = s->y;
        u32 d;
        u8 via = 0xFF;
        if (LootTaken(i) || LootUseless(1, s->type))
            continue;
        if (s->type == LOOT_HEAL && !hurt)
            continue;
        if (WildlandsWorld_InRoom(lx, ly))
        {
            u32 k;
            if (s->type != LOOT_CACHE && s->type != LOOT_HEAL)
                continue;
            WildlandsWorld_OutdoorPos(&lx, &ly);
            for (k = 0; k < WildlandsWorld_DoorCount(); k++)
            {
                s16 ox, oy;
                bool8 lair;
                WildlandsWorld_DoorInfo(k, &ox, &oy, &lair);
                if (ox == lx && oy == ly) { via = k; break; }
            }
            if (via == 0xFF)
                continue;
        }
        d = ArenaNav_Distance(bx, by, lx, ly);
        if (s->type == LOOT_CACHE) d = d * 2 / 3;   // caches are worth the trip
        if (d < bestD) { bestD = d; *spot = i; *door = via; found = TRUE; }
    }
    return found;
}

static void BrainSetMode(u8 mode)
{
    if (sBrain.mode == mode)
        return;
    if (sBrain.mode == BRAIN_RETREAT)
        sBrain.retreatEnd = sArena.frame;
    sBrain.mode = mode;
    sBrain.modeClock = 0;
    sBrain.modeStart = sArena.frame;
    if (mode == BRAIN_LOOT || mode == BRAIN_RAID) gWildlandsBrainTelemetry[4]++;
    gWildlandsBrainTelemetry[0] = mode;
}

static void BrainRoam(struct ArenaBody *body)
{
    if (!sBrain.roamClock-- || ArenaNav_Distance(body->x / Q, body->y / Q,
            sArena.observed.x, sArena.observed.y) < 12)
    {
        u32 k;
        sBrain.roamClock = 12;
        for (k = 0; k < 6; k++)
        {
            s32 nx = body->x / Q + (s32)(Random() % 241) - 120;
            s32 ny = body->y / Q + (s32)(Random() % 241) - 120;
            if (BrainCanGo(nx, ny))
            { sArena.observed.x = nx; sArena.observed.y = ny; break; }
        }
    }
}

// Enemy lead (and wing via regroup) moves between a door and its room.
static void BrainTeleportLead(struct ArenaBody *body, s16 x, s16 y)
{
    body->x = x * Q;
    body->y = y * Q;
    sArena.observed.x = sArena.goal.x = sArena.waypoint.x = x;
    sArena.observed.y = sArena.goal.y = sArena.waypoint.y = y;
    if (sSquadWings[1].active && sSquadWings[1].alive)
        SquadRegroup(&sSquadWings[1], body);
}

static void BrainRaid(struct ArenaBody *body)
{
    s32 bx = body->x / Q, by = body->y / Q;
    s16 ox, oy, ex, ey;
    bool8 lair;
    WildlandsWorld_DoorInfo(sBrain.door, &ox, &oy, &lair);
    if (!WildlandsWorld_InRoom(bx, by))
    {
        if (LootTaken(sBrain.spot))
        { BrainSetMode(BRAIN_ROAM); return; }
        if (ArenaNav_Distance(bx, by, ox, oy) < 14)
        {
            s16 ax, ay;
            WildlandsWorld_DoorArrival(sBrain.door, &ax, &ay);
            BrainTeleportLead(body, ax, ay);
            sBrain.roomStart = sArena.frame;
            gWildlandsBrainTelemetry[5]++;
            return;
        }
        sArena.observed.x = ox; sArena.observed.y = oy;
        return;
    }
    // Inside: take the pickup (up to 10s), then leave by the room's exit
    // (forced after 15s if the layout traps the native router).
    WildlandsWorld_RoomExitPos(bx, by, &ex, &ey);
    if (!LootTaken(sBrain.spot) && (u16)(sArena.frame - sBrain.roomStart) < 600)
    {
        sArena.observed.x = sLootSpots[sBrain.spot].x;
        sArena.observed.y = sLootSpots[sBrain.spot].y;
        return;
    }
    if (ArenaNav_Distance(bx, by, ex, ey) < 14 || (u16)(sArena.frame - sBrain.roomStart) > 900)
    {
        BrainTeleportLead(body, ox, oy);
        gWildlandsBrainTelemetry[6]++;
        BrainSetMode(BRAIN_ROAM);
        return;
    }
    sArena.observed.x = ex; sArena.observed.y = ey;
}

// seenMask: bit0 = player lead visible, bit1 = player partner visible.
static void BrainDecide(struct ArenaBody *body, u8 seenMask)
{
    u32 ours, theirs, adv;
    u8 b, focus = 0xFF;
    bool8 hurt;
    if (!WildlandsWorld_Active())
        return;
    sBrain.modeClock++;
    ours = BrainPower(1);
    theirs = BrainPower(0);
    adv = ours * 100 / max(1, theirs);
    gWildlandsBrainTelemetry[7] = adv;
    hurt = BrainHpPct(1) < 60 || (SquadAlive(3) && BrainHpPct(3) < 45);

    // Mid-raid inside a room: finish it (nobody can be seen from in there
    // unless the player followed, in which case fight).
    if (sBrain.mode == BRAIN_RAID && WildlandsWorld_InRoom(body->x / Q, body->y / Q) && !seenMask)
    { BrainRaid(body); return; }

    if (seenMask)
    {
        // Disengage on damage, not on paper: a fresh duo fights even an
        // overlevelled team; it breaks off when hurt (and then goes for
        // supplies), sooner when the matchup is bad.
        bool8 losing = (BrainHpPct(1) < 35 && adv < 140) || (adv < 60 && BrainHpPct(1) < 60);
        u16 inMode = sArena.frame - sBrain.modeStart;
        u16 sinceRetreat = sArena.frame - sBrain.retreatEnd;
        bool8 cornered = FALSE;
        for (b = 0; b < 2; b++)
            if (seenMask & (1 << b))
            {
                s32 x, y;
                SquadPos(b ? 2 : 0, &x, &y);
                if (ArenaNav_Distance(body->x / Q, body->y / Q, x / Q, y / Q) < 64)
                    cornered = TRUE;
            }
        sBrain.calm = 0;
        // Retreat in bursts (<= 2.5s), never twice within 4s, and turn to
        // fight when caught up with: a weak duo still has to fight sometimes.
        if (losing && !cornered
            && (sBrain.mode == BRAIN_RETREAT ? inMode < 150 : (sinceRetreat > 240 || !sBrain.retreatEnd)))
        {
            s32 tx = 0, ty = 0, gx, gy;
            u8 n = 0;
            for (b = 0; b < 2; b++)
                if (seenMask & (1 << b))
                {
                    s32 x, y;
                    SquadPos(b ? 2 : 0, &x, &y);
                    tx += x / Q; ty += y / Q; n++;
                }
            tx /= n; ty /= n;
            if (sBrain.mode != BRAIN_RETREAT) gWildlandsBrainTelemetry[3]++;
            BrainSetMode(BRAIN_RETREAT);
            if (BrainFleePoint(body, tx, ty, &gx, &gy))
            { sArena.observed.x = gx; sArena.observed.y = gy; }
            return;
        }
        // Focus: lowest HP% weighted by how hard we hit them.
        {
            u32 bestScore = 0xFFFFFFFF;
            for (b = 0; b < 2; b++)
            {
                u8 t = b ? 2 : 0;
                u32 score, off;
                if (!(seenMask & (1 << b)))
                    continue;
                off = BrainOffense(1, t) + (SquadAlive(3) ? BrainOffense(3, t) : 0);
                score = (BrainHpPct(t) + 10) * 100 / max(1, off);
                if (score < bestScore) { bestScore = score; focus = t; }
            }
        }
        if (sBrain.mode != BRAIN_FIGHT) gWildlandsBrainTelemetry[2]++;
        BrainSetMode(BRAIN_FIGHT);
        sBrain.focus = focus;
        gWildlandsBrainTelemetry[1] = focus;
        {
            s32 x, y;
            SquadPos(focus, &x, &y);
            sArena.observed.x = x / Q;
            sArena.observed.y = y / Q;
        }
        return;
    }

    // Nothing visible. Keep running for a moment after a retreat, then look
    // for something useful to do.
    if (sBrain.calm < 0xFFFF) sBrain.calm++;
    if (sBrain.mode == BRAIN_RETREAT && sBrain.calm < 12)
        return;
    if (sBrain.mode == BRAIN_RAID)
    { BrainRaid(body); return; }
    if (sBrain.mode == BRAIN_LOOT && !LootTaken(sBrain.spot))
    {
        sArena.observed.x = sLootSpots[sBrain.spot].x;
        sArena.observed.y = sLootSpots[sBrain.spot].y;
        return;
    }
    {
        u8 spot, door;
        if (BrainPickLoot(body, hurt, &spot, &door))
        {
            sBrain.spot = spot;
            if (door != 0xFF)
            {
                sBrain.door = door;
                BrainSetMode(BRAIN_RAID);
                BrainRaid(body);
            }
            else
            {
                BrainSetMode(BRAIN_LOOT);
                sArena.observed.x = sLootSpots[spot].x;
                sArena.observed.y = sLootSpots[spot].y;
            }
            return;
        }
    }
    BrainSetMode(BRAIN_ROAM);
    BrainRoam(body);
}

// Native enemy aim gate: only fire at a visible target while fighting.
static bool8 BrainAllowsFire(void)
{
    return sBrain.mode == BRAIN_FIGHT;
}

// Enemy wing: focus the brain's target; hold formation unless fighting.
static u8 BrainWingTarget(u8 picked)
{
    if (sBrain.mode == BRAIN_FIGHT && sBrain.focus != 0xFF && SquadAlive(sBrain.focus))
        return sBrain.focus;
    return picked;
}

static bool8 BrainWingFollows(void)
{
    return sBrain.mode == BRAIN_RETREAT || sBrain.mode == BRAIN_LOOT || sBrain.mode == BRAIN_RAID;
}

static void BrainInit(void)
{
    if (sWildlandsEncounterLive)
        return;
    memset(&sBrain, 0, sizeof(sBrain));
    sBrain.focus = 0xFF;
    memset(gWildlandsBrainTelemetry, 0, sizeof(gWildlandsBrainTelemetry));
}
