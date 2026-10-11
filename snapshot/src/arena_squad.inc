// Wildlands V5: true duo combat inside the native realtime Arena.
//
// Battlers follow Emerald's double-battle layout so native damage math,
// abilities and side statuses work unchanged:
//   0 = player lead (native body 0)   2 = player partner (squad wing 0)
//   1 = enemy lead  (native body 1)   3 = enemy wing     (squad wing 1)
// Team = battler & 1. Wings are full combatants: own HP in gBattleMons[2/3]
// and the party, own cooldowns, targeting, movement over native world terrain,
// projectiles through the shared native shot pool (owner tracked per shot),
// damage through RealtimeArena_ResolveDamage. When a lead faints while its
// wing lives, the wing takes the field as that team's lead ("promotion"), so
// a team is eliminated only when both members are down.

#define SQUAD_ENEMY_WING_TAG (MON_TAG + 5)
#define SQUAD_OWNER_WING 0x80

struct SquadWing
{
    s32 x, y;
    u32 animClock;
    const struct ArenaSpriteSet *art;
    u16 species, cooldown, shotTimer, shotElapsed, tag;
    s16 waypointX, waypointY, aimX, aimY;
    u8 sprite, shadow, marker, facing, moving, drawnFrame, drawnDirection;
    u8 animation, active, alive, battler, team, partyIndex, shotSlot, shotFacing;
    u8 target, flash, stuck;
    u16 fallbackMove, stuckClock, regroups;
    s32 lastX, lastY;
};

static EWRAM_DATA struct SquadWing sSquadWings[2] = {};
// sSquadShotOwner[SHOTS_COUNT] is defined beside the prototypes (squad_apply.py).
// [0] active [1..2] shots by wing0/1 [3..4] damaging hits by wing0/1
// [5..6] hits taken by wing0/1 [7..8] wing0/1 hp [9..10] promotions team0/1
// [11] wing KOs [12] enemy lead retargets to partner [13..14] wing0/1 target
// [15] friendly hits (must stay 0)
EWRAM_DATA u32 gWildlandsSquadTelemetry[16] = {};

static const u16 sSquadWingSpecies[] = {
    SPECIES_SCYTHER, SPECIES_PIDGEOT, SPECIES_ARCANINE, SPECIES_VAPOREON,
    SPECIES_JOLTEON, SPECIES_SANDSLASH, SPECIES_GOLEM, SPECIES_NIDOKING,
};

static struct Pokemon *SquadPartyMon(u8 battler)
{
    u8 index = battler < 2 ? gBattlerPartyIndexes[battler] : sSquadWings[battler - 2].partyIndex;
    return (battler & 1) ? &gEnemyParty[index] : &gPlayerParty[index];
}

static void SquadFillBattleMon(u8 battler, struct Pokemon *mon)
{
    struct BattlePokemon *b = &gBattleMons[battler];
    u32 i;
    memset(b, 0, sizeof(*b));
    b->species = GetMonData(mon, MON_DATA_SPECIES);
    b->item = GetMonData(mon, MON_DATA_HELD_ITEM);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        b->moves[i] = GetMonData(mon, MON_DATA_MOVE1 + i);
        b->pp[i] = GetMonData(mon, MON_DATA_PP1 + i);
    }
    b->ppBonuses = GetMonData(mon, MON_DATA_PP_BONUSES);
    b->personality = GetMonData(mon, MON_DATA_PERSONALITY);
    b->otId = GetMonData(mon, MON_DATA_OT_ID);
    b->status1 = GetMonData(mon, MON_DATA_STATUS);
    b->level = GetMonData(mon, MON_DATA_LEVEL);
    b->hp = GetMonData(mon, MON_DATA_HP);
    b->maxHP = GetMonData(mon, MON_DATA_MAX_HP);
    b->attack = GetMonData(mon, MON_DATA_ATK);
    b->defense = GetMonData(mon, MON_DATA_DEF);
    b->speed = GetMonData(mon, MON_DATA_SPEED);
    b->spAttack = GetMonData(mon, MON_DATA_SPATK);
    b->spDefense = GetMonData(mon, MON_DATA_SPDEF);
    b->abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM);
    b->types[0] = gSpeciesInfo[b->species].types[0];
    b->types[1] = gSpeciesInfo[b->species].types[1];
    b->ability = GetAbilityBySpecies(b->species, b->abilityNum);
    for (i = 0; i < NUM_BATTLE_STATS; i++)
        b->statStages[i] = DEFAULT_STAT_STAGE;
    GetMonData(mon, MON_DATA_NICKNAME, b->nickname);
}

static bool8 SquadAlive(u8 battler)
{
    if (battler < 2)
        return gBattleMons[battler].hp != 0;
    return sSquadWings[battler - 2].active && sSquadWings[battler - 2].alive;
}

static void SquadPos(u8 battler, s32 *x, s32 *y)
{
    if (battler < 2) { *x = sArena.bodies[battler].x; *y = sArena.bodies[battler].y; }
    else { *x = sSquadWings[battler - 2].x; *y = sSquadWings[battler - 2].y; }
}

static void SquadCreateSprites(struct SquadWing *w)
{
    struct SpriteTemplate t = sMonTemplate;
    struct SpriteSheet sheet;
    struct SpritePalette pal;
    struct Sprite *spr;
    u8 *buffer = (u8 *)gDecompressionBuffer + w->team * 2048;
    ArenaSprites_Decode(&w->art->animations[ARENA_ANIM_IDLE], FACE_DOWN, 0, (u32 *)buffer);
    sheet.data = buffer; sheet.size = 2048; sheet.tag = w->tag;
    LoadSpriteSheet(&sheet);
    pal.data = w->art->palette; pal.tag = w->tag;
    LoadSpritePalette(&pal);
    t.tileTag = w->tag; t.paletteTag = w->tag;
    w->sprite = CreateSprite(&t, w->x / Q, w->y / Q, 1);
    w->shadow = CreateSprite(&sShadowTemplate, w->x / Q, w->y / Q + 8, 9);
    w->marker = CreateSprite(&sShotTemplate, w->x / Q, w->y / Q - 27, 0);
    spr = &gSprites[w->sprite];
    spr->affineAnimPaused = TRUE; spr->affineAnimBeginning = FALSE;
    SetOamMatrix(spr->oam.matrixNum, 256 * 256 / 230, 0, 0, 256 * 256 / 230);
    gSprites[w->marker].oam.paletteNum = IndexOfSpritePaletteTag(w->team ? SHOT_TAG + 1 : SHOT_TAG);
    w->drawnFrame = w->drawnDirection = 255;
    w->active = TRUE;
}

static void SquadSpawnWing(u8 team)
{
    struct SquadWing *w = &sSquadWings[team];
    struct Pokemon *mon;
    memset(w, 0, sizeof(*w));
    w->team = team;
    w->battler = 2 + team;
    w->partyIndex = 1;
    w->tag = team ? SQUAD_ENEMY_WING_TAG : WILDLANDS_PARTNER_TAG;
    if (team == 0)
    {
        if (gPlayerPartyCount < 2)
            return;
    }
    else if (!GetMonData(&gEnemyParty[1], MON_DATA_SPECIES)
        || !GetMonData(&gEnemyParty[1], MON_DATA_HP))
    {
        u16 species = sSquadWingSpecies[(gBattleMons[1].personality ^ gMain.vblankCounter1) % ARRAY_COUNT(sSquadWingSpecies)];
        u8 level = gBattleMons[1].level ? gBattleMons[1].level : 20;
        if (!ArenaSprites_Get(species))
            species = gBattleMons[1].species;
        CreateMon(&gEnemyParty[1], species, level, USE_RANDOM_IVS, FALSE, 0, OT_ID_PLAYER_ID, 0);
    }
    mon = team ? &gEnemyParty[1] : &gPlayerParty[1];
    if (!GetMonData(mon, MON_DATA_HP) || GetMonData(mon, MON_DATA_IS_EGG))
        return;
    w->species = GetMonData(mon, MON_DATA_SPECIES);
    w->art = ArenaSprites_Get(w->species);
    if (!w->art)
        return;
    SquadFillBattleMon(w->battler, mon);
    gBattlerPartyIndexes[w->battler] = 1;
    w->x = sArena.bodies[team].x + (team ? -24 : 24) * Q;
    w->y = sArena.bodies[team].y + 20 * Q;
    if (WildlandsWorld_Active() && !WildlandsWorld_CanStandSpecies(w->species, w->x / Q, w->y / Q, 6))
    { w->x = sArena.bodies[team].x; w->y = sArena.bodies[team].y; }
    w->waypointX = w->x / Q; w->waypointY = w->y / Q;
    w->facing = team ? FACE_LEFT : FACE_RIGHT;
    w->target = team ? 0 : 1;
    w->cooldown = 45 + team * 15;
    w->alive = TRUE;
    {
        // Every wing can always fight: if none of its own moves is
        // Arena-supported and damaging, it uses the first available basic
        // attack (no PP) instead of standing idle.
        static const u16 sFallback[] = {MOVE_TACKLE, MOVE_SCRATCH, MOVE_POUND, MOVE_QUICK_ATTACK,
            MOVE_EMBER, MOVE_WATER_GUN, MOVE_GUST, MOVE_BITE, MOVE_STRUGGLE};
        u32 k;
        w->fallbackMove = MOVE_NONE;
        for (k = 0; k < ARRAY_COUNT(sFallback) && !w->fallbackMove; k++)
            if (ArenaMoves_Get(sFallback[k]) && gBattleMoves[sFallback[k]].power)
                w->fallbackMove = sFallback[k];
    }
    w->lastX = w->x; w->lastY = w->y;
    SquadCreateSprites(w);
}

static void SquadHideWing(struct SquadWing *w)
{
    if (!w->active)
        return;
    FreeOamMatrix(gSprites[w->sprite].oam.matrixNum);
    DestroySprite(&gSprites[w->sprite]);
    DestroySprite(&gSprites[w->shadow]);
    DestroySprite(&gSprites[w->marker]);
    FreeSpriteTilesByTag(w->tag);
    FreeSpritePaletteByTag(w->tag);
    w->active = FALSE;
}

static void SquadInit(void)
{
    u32 i;
    memset(sSquadShotOwner, 0, sizeof(sSquadShotOwner));
    if (sWildlandsEncounterLive)
    {
        // Re-entry after a native menu: same wings, same HP, same places.
        for (i = 0; i < 2; i++)
            if (sSquadWings[i].alive && sSquadWings[i].art)
                SquadCreateSprites(&sSquadWings[i]);
        return;
    }
    memset(gWildlandsSquadTelemetry, 0, sizeof(gWildlandsSquadTelemetry));
    memset(sSquadWings, 0, sizeof(sSquadWings));
    memset(gWildlandsPartnerTelemetry, 0, sizeof(gWildlandsPartnerTelemetry));
    if (!WildlandsWorld_Active() || VarGet(VAR_ASCENSION_CAREER_ACTIVE) != 1)
        return;
    SquadSpawnWing(0);
    SquadSpawnWing(1);
    gWildlandsSquadTelemetry[0] = sSquadWings[0].active | (sSquadWings[1].active << 1);
    // Keep the V4 partner smoke contract: [0]=partner present, [1]=species.
    gWildlandsPartnerTelemetry[0] = sSquadWings[0].active;
    gWildlandsPartnerTelemetry[1] = sSquadWings[0].species;
}

static void SquadDestroy(void)
{
    WildlandsWorld_ReleaseNav();
    SquadHideWing(&sSquadWings[0]);
    SquadHideWing(&sSquadWings[1]);
}

#define SQUAD_SIGHT 220
// Nearest living opponent of `team` that this wing can actually perceive:
// within SQUAD_SIGHT px, not hidden in tall grass beyond 48px. The player's
// partner weighs distance from the player too, so it defends its lead.
static u8 SquadPickTarget(u8 team, s32 x, s32 y)
{
    u8 best = 0xFF, cand[2];
    u32 i, bestD = 0xFFFF;
    struct ArenaBody *lead = &sArena.bodies[team];
    cand[0] = team ^ 1;
    cand[1] = 2 + (team ^ 1);
    for (i = 0; i < 2; i++)
    {
        s32 tx, ty;
        u16 d;
        if (!SquadAlive(cand[i]))
            continue;
        SquadPos(cand[i], &tx, &ty);
        d = ArenaNav_Distance(x / Q, y / Q, tx / Q, ty / Q);
        if (WildlandsWorld_Active() && d > 48 && WildlandsWorld_IsConcealed(tx / Q, ty / Q))
            continue; // tall grass hides beyond close range
        if (d > SQUAD_SIGHT)
            continue;
        if (team == 0 && SquadAlive(0))
        {
            u16 dl = ArenaNav_Distance(lead->x / Q, lead->y / Q, tx / Q, ty / Q);
            if (dl < d) d = dl;
        }
        if (d < bestD) { bestD = d; best = cand[i]; }
    }
    return best;
}

#define SQUAD_FALLBACK_SLOT 4
static u16 SquadMoveAt(struct SquadWing *w, u8 slot)
{
    return slot == SQUAD_FALLBACK_SLOT ? w->fallbackMove : gBattleMons[w->battler].moves[slot];
}

static u8 SquadChooseMove(struct SquadWing *w)
{
    u32 i;
    u8 battler = w->battler;
    u8 fallback = 0xFF;
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        u16 move = gBattleMons[battler].moves[i];
        const struct ArenaMoveProfile *p;
        if (!move || !gBattleMons[battler].pp[i] || !SupportedMove(move) || !gBattleMoves[move].power)
            continue;
        p = ArenaMoves_Get(move);
        if (!p)
            continue;
        if (p->kind == ARENA_MOVE_PROJECTILE && !ArenaMoves_Beam(move))
            return i;
        if (fallback == 0xFF)
            fallback = i;
    }
    if (fallback == 0xFF && w->fallbackMove)
        return SQUAD_FALLBACK_SLOT;
    return fallback;
}

static void SquadApplyHit(u8 attacker, u8 target, u16 move);

static bool8 SquadSpawnShot(struct SquadWing *w, const struct ArenaMoveProfile *profile, s32 dx, s32 dy)
{
    u32 i, t;
    s32 len = max(Abs(dx), Abs(dy)) + min(Abs(dx), Abs(dy)) / 2;
    if (!len) { dx = Q; len = Q; }
    for (i = 0; i < SHOTS_COUNT; i++) if (!sArena.shots[i].life) break;
    if (i == SHOTS_COUNT || !ArenaTerrain_ReserveProjectile())
        return FALSE;
    sArena.shots[i].sprite = ArenaMoveFx_CreateBolt(profile, w->x / Q, w->y / Q, w->shotFacing, i);
    if (sArena.shots[i].sprite == MAX_SPRITES)
        return FALSE;
    sArena.shots[i].x = w->x; sArena.shots[i].y = w->y;
    sArena.shots[i].vx = dx * profile->speed / len;
    sArena.shots[i].vy = dy * profile->speed / len;
    sArena.shots[i].side = w->team;
    sArena.shots[i].move = profile->move;
    sArena.shots[i].life = profile->range * Q / profile->speed;
    sArena.shots[i].direction = w->shotFacing;
    sArena.shots[i].age = 0;
    sArena.shots[i].elementMask = 0;
    for (t = 0; t < 2; t++) sArena.shots[i].trail[t] = MAX_SPRITES;
    sSquadShotOwner[i] = SQUAD_OWNER_WING | w->battler;
    return TRUE;
}

static void SquadFire(struct SquadWing *w)
{
    u16 move = SquadMoveAt(w, w->shotSlot);
    const struct ArenaMoveProfile *p = ArenaMoves_Get(move);
    u8 pp;
    s32 tx, ty;
    if (!p || (w->shotSlot != SQUAD_FALLBACK_SLOT && !gBattleMons[w->battler].pp[w->shotSlot]))
        return;
    if (p->kind == ARENA_MOVE_PROJECTILE && !ArenaMoves_Beam(move))
    {
        if (!SquadSpawnShot(w, p, w->aimX - w->x, w->aimY - w->y))
        {
            gWildlandsPartnerTelemetry[7] += 0x10000;   // diag: spawn failures
            return;
        }
    }
    else if (w->target != 0xFF && SquadAlive(w->target))
    {
        // Contact/close moves: resolved at release against the chosen target
        // if still within reach and not behind cover.
        SquadPos(w->target, &tx, &ty);
        if (ArenaNav_Distance(w->x / Q, w->y / Q, tx / Q, ty / Q) <= 34
            && (!WildlandsWorld_Active() || WildlandsWorld_LineClear(w->x / Q, w->y / Q, tx / Q, ty / Q, 2)))
            SquadApplyHit(w->battler, w->target, move);
        else
            ArenaFeedback_Impact(w->team, w->x / Q, w->y / Q, 0, ARENA_FEEDBACK_MISS);
    }
    if (w->shotSlot != SQUAD_FALLBACK_SLOT)
    {
        pp = gBattleMons[w->battler].pp[w->shotSlot] - 1;
        gBattleMons[w->battler].pp[w->shotSlot] = pp;
        SetMonData(SquadPartyMon(w->battler), MON_DATA_PP1 + w->shotSlot, &pp);
    }
    w->cooldown = p->recovery + 10;
    gWildlandsSquadTelemetry[1 + w->team]++;
    PlaySE(p->kind == ARENA_MOVE_PROJECTILE ? SE_M_SWIFT : SE_M_SCRATCH);
}

static void SquadMoveWing(struct SquadWing *w, s32 goalX, s32 goalY, s32 step)
{
    s32 dx, dy, d, nx, ny;
    if (WildlandsWorld_Active() && !((sArena.frame + w->team * 8) & 15))
    {
        struct ArenaPoint wp;
        if (WildlandsWorld_NextWaypointSpecies(w->species, w->x / Q, w->y / Q, goalX / Q, goalY / Q, &wp))
        { w->waypointX = wp.x; w->waypointY = wp.y; }
        else
        {
            // No route found: head straight for the goal and let terrain
            // slide it; the stuck detector regroups it if that fails too
            // (it used to freeze in place, e.g. storm-steering on the slice).
            w->waypointX = goalX / Q; w->waypointY = goalY / Q;
        }
    }
    else if (!WildlandsWorld_Active())
    { w->waypointX = goalX / Q; w->waypointY = goalY / Q; }
    dx = w->waypointX * Q - w->x;
    dy = w->waypointY * Q - w->y;
    w->moving = Abs(dx) > 2 * Q || Abs(dy) > 2 * Q;
    if (!w->moving)
        return;
    d = max(1, max(Abs(dx), Abs(dy)));
    nx = Clamp(w->x + dx * step / d, ARENA_MIN_X * Q, ARENA_MAX_X * Q);
    ny = Clamp(w->y + dy * step / d, ARENA_MIN_Y * Q, ARENA_MAX_Y * Q);
    w->facing = Facing(dx, dy);
    if (!WildlandsWorld_Active() || WildlandsWorld_SpeciesLineClear(w->species, w->x / Q, w->y / Q, nx / Q, w->y / Q, 10))
        w->x = nx;
    if (!WildlandsWorld_Active() || WildlandsWorld_SpeciesLineClear(w->species, w->x / Q, w->y / Q, w->x / Q, ny / Q, 10))
        w->y = ny;
}

// Leash: a wing that falls far behind its lead, or is stuck against
// terrain while trying to follow, regroups beside the lead on legal ground.
static void SquadRegroup(struct SquadWing *w, struct ArenaBody *lead)
{
    static const s8 ox[8] = {28, -28, 0, 0, 22, -22, 22, -22};
    static const s8 oy[8] = {0, 0, 24, -24, 20, 20, -20, -20};
    u32 k;
    for (k = 0; k < 8; k++)
    {
        s32 nx = lead->x / Q + ox[k], ny = lead->y / Q + oy[k];
        if (WildlandsWorld_Active() && !WildlandsWorld_CanStandSpecies(w->species, nx, ny, 6))
            continue;
        ArenaFeedback_Dust(w->x / Q, w->y / Q, TRUE);
        w->x = nx * Q; w->y = ny * Q;
        w->waypointX = nx; w->waypointY = ny;
        w->stuckClock = 0;
        w->regroups++;
        if (w->team == 0) gWildlandsPartnerTelemetry[5] = w->regroups;
        ArenaFeedback_Dust(nx, ny, TRUE);
        return;
    }
}

static void SquadThink(struct SquadWing *w)
{
    if (gWildlandsTestPeace) { w->moving = FALSE; return; }
    {
    struct ArenaBody *lead = &sArena.bodies[w->team];
    s32 tx, ty, goalX, goalY, step;
    u8 spd = gBattleMons[w->battler].statStages[STAT_SPEED];
    u16 dist = 0xFFFF;
    u8 slot;
    const struct ArenaMoveProfile *p = NULL;
    step = 300 * gStatStageRatios[spd][0] / gStatStageRatios[spd][1];
    if (w->cooldown && !w->shotTimer) w->cooldown--;
    if (SquadAlive(w->team) && !w->shotTimer)
    {
        u16 ld = ArenaNav_Distance(w->x / Q, w->y / Q, lead->x / Q, lead->y / Q);
        if (w->moving && w->x == w->lastX && w->y == w->lastY) w->stuckClock++;
        else if (w->moving) w->stuckClock = 0;
        w->lastX = w->x; w->lastY = w->y;
        if (ld > 260 || (ld > 64 && w->stuckClock > 90) || w->stuckClock > 180)
            SquadRegroup(w, lead);
    }
    if (!(sArena.frame & 15) || w->target == 0xFF || !SquadAlive(w->target))
    {
        w->target = SquadPickTarget(w->team, w->x, w->y);
        if (w->team && w->target != 0xFF)
            w->target = BrainWingTarget(w->target);   // enemy duo focuses fire
    }
    gWildlandsSquadTelemetry[13 + w->team] = w->target;
    if (w->shotTimer)
    {
        p = ArenaMoves_Get(SquadMoveAt(w, w->shotSlot));
        if (p && w->shotElapsed == p->windup)
            SquadFire(w);
        w->shotElapsed++;
        w->shotTimer--;
        w->moving = FALSE;
        return;
    }
    if (w->target != 0xFF)
    {
        SquadPos(w->target, &tx, &ty);
        dist = ArenaNav_Distance(w->x / Q, w->y / Q, tx / Q, ty / Q);
    }
    {
        // The storm wins over a fight only when this wing is already taking
        // storm damage or nothing is in reach; pre-rotation and edge margins
        // otherwise wait until the skirmish ends.
        s32 zx, zy;
        bool8 engaged = w->target != 0xFF && dist < 160;
        if ((!engaged || ZoneOutside(w->x / Q, w->y / Q, 0)) && ZoneSteer(w->x / Q, w->y / Q, &zx, &zy))
        {
            if (!w->team) gWildlandsPartnerTelemetry[7]++;   // diag: storm-steer frames (partner)
            SquadMoveWing(w, zx * Q, zy * Q, 420);
            return;
        }
    }
    slot = SquadChooseMove(w);
    if (slot != 0xFF)
        p = ArenaMoves_Get(SquadMoveAt(w, slot));
    if (p && w->target != 0xFF && !w->cooldown
        && dist < (p->kind == ARENA_MOVE_PROJECTILE ? p->range : 30) && dist > 6
        && (!WildlandsWorld_Active() || WildlandsWorld_LineClear(w->x / Q, w->y / Q, tx / Q, ty / Q, 2))
        && !(gBattleMons[w->battler].status1 & (STATUS1_SLEEP | STATUS1_FREEZE)))
    {
        gWildlandsPartnerTelemetry[6] += w->team ? 0x10000 : 1;   // diag: fire attempts
        w->shotSlot = slot;
        w->aimX = tx; w->aimY = ty;
        w->shotFacing = Facing(tx - w->x, ty - w->y);
        w->facing = w->shotFacing;
        w->shotElapsed = 0;
        w->shotTimer = p->windup + p->active + 8;
        w->animation = p->animation;
        w->animClock = 0;
        w->drawnFrame = 255;
        w->moving = FALSE;
        return;
    }
    if (w->target != 0xFF && dist < 220 && !(w->team && BrainWingFollows()))
    {
        // Engage: close to ~2/3 of range, never closer than 24px.
        u16 want = p ? max(24, (p->kind == ARENA_MOVE_PROJECTILE ? p->range : 26) * 2 / 3) : 40;
        if (dist > want) { goalX = tx; goalY = ty; }
        else { goalX = w->x + (w->x - tx) / 4; goalY = w->y + (w->y - ty) / 4; }
    }
    else if (SquadAlive(w->team))
    {
        // Formation on the living lead of this team.
        goalX = lead->x + (w->team ? -30 : 30) * Q;
        goalY = lead->y + 22 * Q;
        if (max(Abs(goalX - w->x), Abs(goalY - w->y)) > 120 * Q) step = 520;
    }
    else
    { goalX = w->x; goalY = w->y; }
    SquadMoveWing(w, goalX, goalY, step);
    }
}

static void SquadDraw(struct SquadWing *w)
{
    const struct ArenaSpriteAnimation *anim;
    struct Sprite *spr = &gSprites[w->sprite];
    u8 animation = w->shotTimer ? w->animation : w->moving ? ARENA_ANIM_WALK : ARENA_ANIM_IDLE;
    u8 frame;
    u16 tick = w->animClock / Q;
    u8 *buffer = (u8 *)gDecompressionBuffer + w->team * 2048;
    spr->x = w->x / Q; spr->y = w->y / Q;
    gSprites[w->shadow].x = spr->x; gSprites[w->shadow].y = w->y / Q + 8;
    gSprites[w->marker].x = spr->x;
    gSprites[w->marker].y = w->y / Q - 28 + ((sArena.frame >> 3) & 1);
    anim = &w->art->animations[animation];
    if (w->shotTimer)
    {
        const struct ArenaMoveProfile *p = ArenaMoves_Get(SquadMoveAt(w, w->shotSlot));
        if (p && p->windup)
            tick = w->shotElapsed < p->windup ? w->shotElapsed * anim->hitTick / p->windup : anim->hitTick;
    }
    frame = ArenaSprites_Frame(anim, tick);
    spr->y += 8 - w->art->ground[animation * 8 + w->facing] * 230 / 256;
    if (frame != w->drawnFrame || w->facing != w->drawnDirection)
    {
        ArenaSprites_Decode(anim, w->facing, frame, (u32 *)buffer);
        ArenaRender_Copy(buffer, (u8 *)OBJ_VRAM0 + GetSpriteTileStartByTag(w->tag) * 32, 2048);
        w->drawnFrame = frame; w->drawnDirection = w->facing;
    }
    if (!sArena.paused) w->animClock += (animation == ARENA_ANIM_WALK ? 300 : Q) * sWildlandsSimSteps;
    if (w->flash)
    {
        BlendPalette(OBJ_PLTT_ID(IndexOfSpritePaletteTag(w->tag)), 16, w->flash + 3, RGB_WHITE);
        w->flash--;
    }
    else
        BlendPalette(OBJ_PLTT_ID(IndexOfSpritePaletteTag(w->tag)), 16, 0, RGB_WHITE);
}

#define WL_NOW() (gMain.vblankCounter1 * 228 + (REG_VCOUNT + 68) % 228)
static void ZoneSim(void);
static void LootSim(void);

// OAM only has 9-bit X / 8-bit Y: an actor ~100-250px off screen wraps
// around and appears on the far side (the "enemy appears when it is not
// near me" playtest report). Hide every world sprite well outside the view
// for the OAM build only, then restore it, so no gameplay flag changes.
static void WildlandsBuildOam(void)
{
    u32 hidden[2] = {0, 0}, i;
    if (WildlandsWorld_Active())
        for (i = 0; i < MAX_SPRITES; i++)
        {
            struct Sprite *s = &gSprites[i];
            s32 sx, sy;
            if (!s->inUse || s->invisible || !s->coordOffsetEnabled)
                continue;
            sx = s->x + s->x2 + gSpriteCoordOffsetX;
            sy = s->y + s->y2 + gSpriteCoordOffsetY;
            if (sx < -64 || sx > 304 || sy < -64 || sy > 224)
            {
                s->invisible = TRUE;
                hidden[i >> 5] |= 1u << (i & 31);
            }
        }
    BuildOamBuffer();
    for (i = 0; i < MAX_SPRITES; i++)
        if (hidden[i >> 5] & (1u << (i & 31)))
            gSprites[i].invisible = FALSE;
}
// Doors: the player walks into a house / lair door (or back onto a room's
// exit) and the duo moves together; the region swap itself happens in the
// world renderer when the camera arrives.
static void SquadDoorSim(void)
{
    struct ArenaBody *lead = &sArena.bodies[0];
    s16 nx, ny;
    if (!WildlandsWorld_Active() || sArena.resultTimer || !SquadAlive(0))
        return;
    if (gWildlandsTestWarp)
    {
        u8 k = gWildlandsTestWarp;
        bool8 lair;
        gWildlandsTestWarp = 0;
        nx = lead->x / Q; ny = lead->y / Q;
        if (k >= 10 && k - 10 < WildlandsWorld_DoorCount())
        { WildlandsWorld_DoorInfo(k - 10, &nx, &ny, &lair); lead->facing = FACE_UP; }
        else if (k == 2 && WildlandsWorld_RoomExitPos(nx, ny, &nx, &ny))
            lead->facing = FACE_DOWN;
        else if (k == 3)
            LootLastSpot(&nx, &ny);
        else if (k == 1)
        { nx = WL_PLAYER_START_X; ny = WL_PLAYER_START_Y; }
        lead->x = nx * Q; lead->y = ny * Q;
        if (k == 1 && sSquadWings[0].active && sSquadWings[0].alive)
            SquadRegroup(&sSquadWings[0], lead);
    }
    if (!WildlandsWorld_PollDoor(lead->x / Q, lead->y / Q, lead->facing == FACE_UP,
            lead->facing == FACE_DOWN, &nx, &ny))
        return;
    lead->x = nx * Q;
    lead->y = ny * Q;
    lead->facing = WildlandsWorld_InRoom(nx, ny) ? FACE_UP : FACE_DOWN;
    if (sSquadWings[0].active && sSquadWings[0].alive)
        SquadRegroup(&sSquadWings[0], lead);
    PlaySE(SE_DOOR);
}
// One fixed 60Hz simulation step for the Wildlands layer: storm clock and
// exposure, pickups and wing AI. CB2_Arena runs it once per sim step, so a
// render that misses a VBlank still advances game time correctly.
static void SquadSimStep(void)
{
    u32 i;
    ZoneSim();
    LootSim();
    if (sArena.paused || sArena.resultTimer)
        return;
    SquadDoorSim();
    for (i = 0; i < 2; i++)
        if (sSquadWings[i].active && sSquadWings[i].alive)
            SquadThink(&sSquadWings[i]);
}
static void SquadTick(void)
{
    u32 i, t0 = WL_NOW(), t1;
    ZoneTick();
    t1 = WL_NOW(); gWildlandsProfile[0] = t1 - t0; t0 = t1;
    LootTick();
    t1 = WL_NOW(); gWildlandsProfile[1] = t1 - t0; t0 = t1;
    for (i = 0; i < 2; i++)
    {
        struct SquadWing *w = &sSquadWings[i];
        if (!w->active || !w->alive)
            continue;
        t1 = WL_NOW(); gWildlandsProfile[2 + i * 2] = t1 - t0; t0 = t1;
        SquadDraw(w);
        t1 = WL_NOW(); gWildlandsProfile[3 + i * 2] = t1 - t0; t0 = t1;
        gWildlandsSquadTelemetry[7 + i] = gBattleMons[w->battler].hp;
    }
    if (sSquadWings[0].active)
    {
        gWildlandsPartnerTelemetry[2] = sSquadWings[0].target;
        gWildlandsPartnerTelemetry[3] = sSquadWings[0].x / Q;
        gWildlandsPartnerTelemetry[4] = sSquadWings[0].y / Q;
    }
}

// The wing replaces its fallen lead in place, keeping its own HP/PP.
static bool8 SquadPromote(u8 side)
{
    struct SquadWing *w = &sSquadWings[side];
    struct ArenaBody *body = &sArena.bodies[side];
    if (!w->active || !w->alive)
        return FALSE;
    gBattlerPartyIndexes[side] = w->partyIndex;
    gBattleMons[side] = gBattleMons[w->battler];
    body->x = w->x; body->y = w->y;
    body->facing = w->facing;
    body->art = w->art;
    body->drawnFrame = body->drawnDirection = 255;
    body->shotTimer = body->actionLife = body->dash = 0;
    body->cooldown = 20; body->knockX = body->knockY = 0;
    body->moveSlot = FirstMove(side, TRUE);
    LoadPalette(body->art->palette, OBJ_PLTT_ID(side), PLTT_SIZE_4BPP);
    gSprites[body->shadow].invisible = FALSE;
    w->alive = FALSE;
    SquadHideWing(w);
    gWildlandsSquadTelemetry[9 + side]++;
    sArena.hudDirty = TRUE;
    PlayCry_Normal(gBattleMons[side].species, 0);
    return TRUE;
}

static void SquadKO(u8 target, u8 attacker)
{
    if (target >= 2)
    {
        struct SquadWing *w = &sSquadWings[target - 2];
        w->alive = FALSE;
        gWildlandsSquadTelemetry[11]++;
        SquadHideWing(w);
        return;
    }
    if (SquadPromote(target))
        return;
    sArena.resultTimer = 12;
    sArena.lastAttacker = target ^ 1;
    sArena.lastTarget = target;
    gArenaResultTelemetry.started = gMain.vblankCounter1;
}

static void SquadApplyHit(u8 attacker, u8 target, u16 move)
{
    s32 x, y, damage;
    u16 hp;
    if ((attacker & 1) == (target & 1))
    { gWildlandsSquadTelemetry[15]++; return; }
    SquadPos(target, &x, &y);
    damage = RealtimeArena_ResolveDamage(attacker, target, move);
    if (damage <= 0)
    {
        ArenaFeedback_Impact(target & 1, x / Q, y / Q, 0,
            (gMoveResultFlags & MOVE_RESULT_DOESNT_AFFECT_FOE) ? ARENA_FEEDBACK_IMMUNE : ARENA_FEEDBACK_MISS);
        return;
    }
    hp = gBattleMons[target].hp;
    damage = min(damage, hp);
    hp -= damage;
    gBattleMons[target].hp = hp;
    SetMonData(SquadPartyMon(target), MON_DATA_HP, &hp);
    ArenaFeedback_Impact(target & 1, x / Q, y / Q, damage, ARENA_FEEDBACK_DAMAGE);
    sArena.hitstop = max(sArena.hitstop, 2);
    sArena.hudDirty = TRUE;
    if (target < 2) sArena.bodies[target].flash = 8;
    else { sSquadWings[target - 2].flash = 8; gWildlandsSquadTelemetry[5 + target - 2]++; }
    if (attacker >= 2) gWildlandsSquadTelemetry[3 + attacker - 2]++;
    gRealtimeArenaTelemetry.hits[attacker & 1]++;
    PlaySE(SE_M_COMET_PUNCH);
    if (!hp)
        SquadKO(target, attacker);
}

// Called from TickShots before the native 1v1 hit test. Returns TRUE when the
// shot has been fully handled for this step (hit a wing, or is wing-owned and
// must not be credited to a native body).
static bool8 SquadShotStep(u8 index, struct ArenaShot *shot, const struct ArenaMoveProfile *p, s16 oldX, s16 oldY)
{
    u8 owner = sSquadShotOwner[index];
    u8 attacker = (owner & SQUAD_OWNER_WING) ? (owner & 3) : shot->side;
    struct SquadWing *foe = &sSquadWings[shot->side ^ 1];
    struct ArenaBody *body = &sArena.bodies[shot->side ^ 1];
    if (foe->active && foe->alive
        && ArenaMoves_SegmentHit(oldX, oldY, shot->x / Q, shot->y / Q, foe->x / Q, foe->y / Q, p->radius))
    {
        SquadApplyHit(attacker, foe->battler, shot->move);
        shot->life = 1;
        return TRUE;
    }
    if (!(owner & SQUAD_OWNER_WING))
        return FALSE;
    if (gBattleMons[shot->side ^ 1].hp && !body->dash
        && ArenaMoves_SegmentHit(oldX, oldY, shot->x / Q, shot->y / Q, body->x / Q, body->y / Q, p->radius))
    {
        if (!SpecialInvulnerable(shot->side ^ 1))
            SquadApplyHit(attacker, shot->side ^ 1, shot->move);
        shot->life = 1;
    }
    return TRUE;
}

// Enemy lead perception: it only engages a member of the player duo it can
// actually see (within SQUAD_SIGHT, clear line of sight, not hidden in tall
// grass beyond 48px). Otherwise it roams, and pre-rotates with the storm via
// ZoneSteerEnemy. Native code calls this right after refreshing `observed`.
static EWRAM_DATA struct { u16 lost, roamClock; } sEnemySight = {};
static bool8 SquadEnemySees(void)
{
    return !WildlandsWorld_Active() || (sEnemySight.lost < 20 && BrainAllowsFire());
}

static void SquadEnemyRetarget(struct ArenaBody *body)
{
    struct SquadWing *w = &sSquadWings[0];
    u8 i, mask = 0;
    if (!WildlandsWorld_Active())
        return;
    for (i = 0; i < 2; i++)
    {
        s32 tx, ty;
        u16 d;
        u8 b = i ? 2 : 0;
        if (!SquadAlive(b) || (b == 2 && !w->active))
            continue;
        SquadPos(b, &tx, &ty);
        d = ArenaNav_Distance(body->x / Q, body->y / Q, tx / Q, ty / Q);
        if (d > SQUAD_SIGHT)
            continue;
        if (d > 48 && WildlandsWorld_IsConcealed(tx / Q, ty / Q))
            continue;
        if (!WildlandsWorld_LineClear(body->x / Q, body->y / Q, tx / Q, ty / Q, 2))
            continue;
        mask |= 1 << i;
    }
    if (mask)
    {
        if (mask & 2) gWildlandsSquadTelemetry[12]++;
        sEnemySight.lost = 0;
    }
    else if (sEnemySight.lost < 0xFFFF)
        sEnemySight.lost++;
    // The duo brain turns what it can see into a goal (sArena.observed).
    BrainDecide(body, mask);
}
