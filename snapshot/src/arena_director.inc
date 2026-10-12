// Wildlands duo director: a 30-duo battle royale on a GBA.
//
// Full-fidelity combat exists for two duos at a time (Emerald's four
// battlers): the player's duo and ONE "active" enemy duo (native body 1 +
// squad wing 3). Every other duo lives here as a light record (two species,
// level, HP%, position) and is simulated off screen at one duo per frame:
// it travels on legal ground toward the safe circle (or a legendary lair),
// takes storm damage, and fights other simulated duos abstractly (power from
// base stats x level x HP). The director keeps the nearest threat active:
//   - when the active duo is wiped out, the nearest surviving duo takes over;
//   - when the active duo is far away and another duo is close, they swap
//     (the active duo's HP and position are written back to its record).
// Legendaries wait in their lair rooms as solo boss "duos" (level +5, double
// HP, +1 DEF/SPDEF). Entering a lair with a living legendary makes it the
// active enemy. Beating it: the legendary replaces the player's partner for
// the rest of the match (the original partner is restored afterwards) and
// the team is fully healed with +1 ATK/DEF/SPD. A simulated duo that reaches
// a lair first can take the legendary for itself.
// State lives on the heap for the whole encounter (menus keep it).

#define DIR_LEGENDS 5
#define DIR_MAX (WL_DIRECTOR_DUOS + DIR_LEGENDS)
#define DIR_NONE 0xFF

enum { DIR_DEAD, DIR_SIM, DIR_ACTIVE, DIR_PLAYER, DIR_LAIR };

struct DirDuo
{
    u16 species[2];
    s16 x, y, gx, gy;
    u8 level, state, hp[2];     // hp in percent; 0 = fainted member
    u8 legend, room, kills, plan;  // AI: room = lair fight countdown, plan = legend slot + 1
    u16 planBest;                  // boss run: closest distance to the door so far
    u8 planStall, pad2;            // ticks without getting closer
};

struct DirState
{
    struct DirDuo duo[DIR_MAX];
    struct Pokemon savedPartner, savedLead;
    u8 count, active, cursor, partnerSaved;
    u16 clock;
    struct { u16 t; u8 text[20]; } log[12];   // Beta: pause-menu match log
    u8 logHead, logCount, playerKOs, pad3;
    u16 bossCooldown, bossEvalStamp;
    u8 activePlan, bossDoor;
};

static EWRAM_DATA struct DirState *sDir = NULL;
static EWRAM_DATA struct { u8 timer, color; u8 text[18]; } sDirPopup = {};
// [0] AI duos alive [1] active index [2] swaps [3] sim eliminations
// [4] legendaries joined [5] legendaries taken by AI [6] duos loaded
// [7] sim fight ticks
EWRAM_DATA u32 gWildlandsDirectorTelemetry[8] = {};
// Boss runs by AI duos: [0] attempts [1] won (legend joined them) [2] lost
// but escaped [3] wiped out [4] storm stage of the first attempt + 1
// [5] aborted on the way [6] attempts by the on-screen duo [7] last score+1000
// [8] lair evaluations [9] blocked by cooldown [10] best score seen + 1000
// [11] last gate that ruled a lair out (1 legend gone 2 storm 3 next circle 4 opening phase)
// [12] plans started [13] planned duo died on the way [14] nav detour steps
// [15] planned-duo sim ticks
EWRAM_DATA u16 gWildlandsBossTelemetry[16] = {};
// TEST HOOK ONLY: harness adds this to every boss score and lifts the
// first-phase gate so a short run can exercise boss runs; 0 in play.
EWRAM_DATA u8 gWildlandsBossTestBias = 0;

static const u16 sDirRoster[] = {
    SPECIES_CHARIZARD, SPECIES_BLASTOISE, SPECIES_VENUSAUR, SPECIES_SCEPTILE, SPECIES_BLAZIKEN,
    SPECIES_SWAMPERT, SPECIES_GARDEVOIR, SPECIES_AGGRON, SPECIES_SALAMENCE, SPECIES_METAGROSS,
    SPECIES_FLYGON, SPECIES_ALTARIA, SPECIES_GYARADOS, SPECIES_DRAGONITE, SPECIES_GENGAR,
    SPECIES_ALAKAZAM, SPECIES_MACHAMP, SPECIES_ARCANINE, SPECIES_NINETALES, SPECIES_RAPIDASH,
    SPECIES_STARMIE, SPECIES_KINGDRA, SPECIES_WALREIN, SPECIES_GLALIE, SPECIES_ABSOL,
    SPECIES_BANETTE, SPECIES_DUSCLOPS, SPECIES_CACTURNE, SPECIES_SHIFTRY, SPECIES_LUDICOLO,
    SPECIES_BRELOOM, SPECIES_HARIYAMA, SPECIES_SHARPEDO, SPECIES_CRAWDAUNT, SPECIES_MANECTRIC,
    SPECIES_SWELLOW, SPECIES_PELIPPER, SPECIES_MIGHTYENA, SPECIES_EXPLOUD, SPECIES_SLAKING,
    SPECIES_NINJASK, SPECIES_SABLEYE, SPECIES_SWALOT, SPECIES_GOLEM, SPECIES_CROBAT,
    SPECIES_AZUMARILL, SPECIES_NIDOKING, SPECIES_NIDOQUEEN, SPECIES_PIDGEOT, SPECIES_SCIZOR,
    SPECIES_SCYTHER, SPECIES_SANDSLASH, SPECIES_CLEFABLE, SPECIES_GOLDUCK, SPECIES_POLIWRATH,
    SPECIES_SLOWBRO, SPECIES_CLOYSTER, SPECIES_KINGLER, SPECIES_EXEGGUTOR, SPECIES_MAROWAK,
    SPECIES_JYNX, SPECIES_FLAREON, SPECIES_LAPRAS, SPECIES_TORKOAL, SPECIES_SOLROCK,
    SPECIES_WHISCASH, SPECIES_RAICHU, SPECIES_DUGTRIO, SPECIES_VILEPLUME, SPECIES_ARBOK,
};

static void DirRestorePartner(void);

static u32 DirRand(void)
{
    return Random() | ((u32)Random() << 16);
}

static u32 DirBst(u16 species)
{
    const struct SpeciesInfo *s = &gSpeciesInfo[species];
    return s->baseHP + s->baseAttack + s->baseDefense + s->baseSpeed + s->baseSpAttack + s->baseSpDefense;
}

static u32 DirPower(const struct DirDuo *d)
{
    u32 p = 0, m;
    for (m = 0; m < 2; m++)
        if (d->species[m] && d->hp[m])
            p += DirBst(d->species[m]) * d->level / 10 * d->hp[m] / 100 * (d->legend ? 2 : 1);
    return p ? p : 1;
}

static bool8 DirAlive(const struct DirDuo *d)
{
    return (d->species[0] && d->hp[0]) || (d->species[1] && d->hp[1]);
}

// ---- Boss runs: when is a lair worth it? ---------------------------------
// Type multiplier x10 of attack type `atk` against a defender's two types.
static u32 DirTypeMult(u8 atk, u8 def1, u8 def2)
{
    u32 k, m = 10;
    for (k = 0; TYPE_EFFECT_ATK_TYPE(k) != TYPE_ENDTABLE; k += 3)
    {
        if (TYPE_EFFECT_ATK_TYPE(k) != atk)
            continue;
        if (TYPE_EFFECT_DEF_TYPE(k) == def1)
            m = m * TYPE_EFFECT_MULTIPLIER(k) / 10;
        if (TYPE_EFFECT_DEF_TYPE(k) == def2 && def2 != def1)
            m = m * TYPE_EFFECT_MULTIPLIER(k) / 10;
    }
    return m;
}

// Matchup bonus (-30..+80 per member, averaged): STAB types of the duo's
// living members against the legendary's typing.
static s32 DirMatchup(const struct DirDuo *d, const struct DirDuo *l)
{
    const struct SpeciesInfo *ls = &gSpeciesInfo[l->species[0]];
    s32 total = 0, n = 0;
    u32 m;
    for (m = 0; m < 2; m++)
    {
        const struct SpeciesInfo *s;
        u32 best;
        if (!d->species[m] || !d->hp[m])
            continue;
        s = &gSpeciesInfo[d->species[m]];
        best = max(DirTypeMult(s->types[0], ls->types[0], ls->types[1]),
                   DirTypeMult(s->types[1], ls->types[0], ls->types[1]));
        total += best >= 40 ? 80 : best >= 20 ? 50 : best >= 10 ? 0 : -30;
        n++;
    }
    return n ? total / n : -100;
}

static void DirLairDoor(const struct DirDuo *l, s32 *x, s32 *y)
{
    *x = l->x; *y = l->y;
    WildlandsWorld_OutdoorPos(x, y);
}

static u8 DirLeft(void);
static void DirRandomGoal(struct DirDuo *d);
static void DirPopup(const u8 *a, const u8 *b, u8 color);
static void DirFeedOut(const struct DirDuo *d);

// Beta shinies: about 1 in 64 AI Pokemon (legendaries included) is shiny.
// pad2 holds a per-duo salt rolled at match start; shininess is a function
// of salt and species, so it survives promotion and re-creation.
// [0] legends placed [1] placed correctly [2] bad-room mask [3..8] live boss
EWRAM_DATA u16 gWildlandsBossAudit[10] = {0};
EWRAM_DATA u8 gWildlandsShinyTest = 0;          // test hook: every AI mon shiny
EWRAM_DATA u16 gWildlandsShinyTelemetry[2] = {0}; // shiny mons made, shiny palettes built
static bool8 DirShiny(const struct DirDuo *d, u16 sp)
{
    if (gWildlandsShinyTest)
        return TRUE;
    return d->pad2 && !(((d->pad2 * 131u) ^ (sp * 37u)) & 63);
}

// Utility of attacking legendary `l` now (>= 0 means go). Never in the first
// storm phase, never into a lair the storm will cover, rarely when the duo is
// hurt, more likely with a good type matchup, when nearby, and when the duo
// is behind (lost a member: a comeback gamble). Late game only if strong.
static s32 DirBossScore(const struct DirDuo *d, const struct DirDuo *l, s32 x, s32 y)
{
    s32 ox, oy, score, ratio, n = 0, hp = 0;
    u32 m, j;
    if (l->state != DIR_LAIR || !l->hp[0])
    { gWildlandsBossTelemetry[11] = 1; return -1000; }
    DirLairDoor(l, &ox, &oy);
    if (sZone.active)
    {
        if (sZone.stage == 0 && sZone.phase == ZONE_EXPLORING && !gWildlandsBossTestBias)
        { gWildlandsBossTelemetry[11] = 4; return -1000; }
        if (ZoneOutside(ox, oy, 48))
        { gWildlandsBossTelemetry[11] = 2; return -1000; }
        // Warning/shrinking: the lair must sit in the NEXT circle unless the
        // warning still leaves 30s to fight and get out.
        if (sZone.phase == ZONE_SHRINKING || sZone.phase == ZONE_SUDDEN_DEATH
            || (sZone.phase == ZONE_WARNING && ZoneSecondsLeft() < 30))
        {
            s32 dx = ox - sZone.toX, dy = oy - sZone.toY, r = (sZone.toR >> 8) - 48;
            if (r <= 0 || dx * dx + dy * dy > r * r)
            { gWildlandsBossTelemetry[11] = 3; return -1000; }
        }
    }
    ratio = (s32)(DirPower(d) * 100 / DirPower(l));
    score = ratio - 70 + DirMatchup(d, l) / 2;
    for (m = 0; m < 2; m++)
        if (d->species[m] && d->hp[m]) { hp += d->hp[m]; n++; }
    if (!n || hp / n < 60)
        score -= 50;
    if (n == 1 && d->species[1])
        score += 20;
    if (DirLeft() <= 5 && ratio < 110)
        score -= 40;
    score -= (s32)ArenaNav_Distance(x, y, ox, oy) / 25;
    score += gWildlandsBossTestBias;
    for (j = 1; j < WL_DIRECTOR_DUOS; j++)
        if (&sDir->duo[j] != d && sDir->duo[j].state == DIR_SIM
            && ArenaNav_Distance(sDir->duo[j].x, sDir->duo[j].y, ox, oy) < 200)
        { score -= 30; break; }
    return score;
}

// Best lair for duo d at (x,y): legend slot (index into duo[]) or DIR_NONE.
static u8 DirBossPick(const struct DirDuo *d, s32 x, s32 y, s32 *bestScore)
{
    u32 j;
    u8 pick = DIR_NONE;
    s32 best = 0;
    gWildlandsBossTelemetry[8]++;
    if (sDir->bossCooldown)
    {
        gWildlandsBossTelemetry[9]++;
        return DIR_NONE;
    }
    for (j = WL_DIRECTOR_DUOS; j < sDir->count; j++)
    {
        s32 sc = DirBossScore(d, &sDir->duo[j], x, y);
        gWildlandsBossTelemetry[7] = (u16)(sc + 1000);
        if (sc + 1000 > (s32)gWildlandsBossTelemetry[10])
            gWildlandsBossTelemetry[10] = (u16)(sc + 1000);
        if (sc >= best) { best = sc; pick = j; }
    }
    *bestScore = best;
    return pick;
}

static void DirBossStart(struct DirDuo *d)
{
    static const u8 sAttacked[] = _(" ATTACKED");
    struct DirDuo *l = &sDir->duo[d->plan - 1];
    d->room = 6;                       // ~6 sim ticks (about 6s) inside
    sDir->bossCooldown = 1800;         // one lair fight at a time, 30s apart
    gWildlandsBossTelemetry[0]++;
    if (!gWildlandsBossTelemetry[4])
        gWildlandsBossTelemetry[4] = (sZone.active ? sZone.stage : 0) + 1;
    DirPopup(gSpeciesNames[l->species[0]], sAttacked, 6);
}

// The fight inside: power with the matchup folded in. A win hands the
// legendary to the duo (it replaces the weaker member) with the same team
// buff the player gets: full heal and a level boost. A loss chips the
// legendary (the damage stays) and the duo either escapes hurt or is out.
static void DirBossResolve(struct DirDuo *d)
{
    static const u8 sTook[] = _("FOES TOOK ");
    struct DirDuo *l = &sDir->duo[d->plan - 1];
    u32 pa = DirPower(d) * (u32)max(20, 100 + DirMatchup(d, l)) / 100, pb = DirPower(l);
    d->plan = 0;
    d->room = 0;
    if (l->state != DIR_LAIR || !l->hp[0])
        return;                        // the player got there first
    if (DirRand() % (pa + pb) < pa)
    {
        u8 weak = (d->species[1] && (!d->hp[1] || d->hp[1] < d->hp[0])) ? 1 : 0;
        d->species[weak] = l->species[0];
        d->hp[0] = d->species[0] ? 100 : 0;
        d->hp[1] = d->species[1] ? 100 : 0;
        d->level = min(100, d->level + 2);
        l->state = DIR_DEAD;
        l->hp[0] = 0;
        gWildlandsDirectorTelemetry[5]++;
        gWildlandsBossTelemetry[1]++;
        DirPopup(sTook, gSpeciesNames[l->species[0]], 6);
        return;
    }
    l->hp[0] = l->hp[0] > 35 ? l->hp[0] - 25 : 10;
    if (DirRand() & 1)
    {
        if (d->hp[0]) d->hp[0] = min(d->hp[0], 25);
        if (d->hp[1]) d->hp[1] = min(d->hp[1], 25);
        gWildlandsBossTelemetry[2]++;
        DirRandomGoal(d);
        return;
    }
    d->hp[0] = d->hp[1] = 0;
    d->state = DIR_DEAD;
    gWildlandsDirectorTelemetry[3]++;
    gWildlandsBossTelemetry[3]++;
    DirFeedOut(d);
}

static u8 DirLeft(void)
{
    u32 i, n = 0;
    if (!sDir)
        return 0;
    for (i = 1; i < sDir->count; i++)
        if ((sDir->duo[i].state == DIR_SIM || sDir->duo[i].state == DIR_ACTIVE) && !sDir->duo[i].legend)
            n++;
    return n;
}

static void DirectorLog(const u8 *text);
static void DirPopup(const u8 *a, const u8 *b, u8 color)
{
    u8 tmp[48], *end = StringCopy(tmp, a);
    if (b)
        StringCopy(end, b);
    tmp[sizeof(sDirPopup.text) - 1] = EOS;   // long names never overrun the popup
    StringCopy(sDirPopup.text, tmp);
    sDirPopup.timer = 150;
    sDirPopup.color = color;
    sArena.hudDirty = TRUE;
    DirectorLog(sDirPopup.text);
}

// Match log: every announced event (eliminations, legendaries, pickups,
// storm phases) with its match time, newest first on the LOG page.
static void DirectorLog(const u8 *text)
{
    u32 k;
    if (!sDir)
        return;
    k = sDir->logHead;
    sDir->log[k].t = (sZone.active ? sZone.clock : sDir->clock) / 60;
    for (k = 0; k < 19 && text[k] != EOS; k++)
        sDir->log[sDir->logHead].text[k] = text[k];
    sDir->log[sDir->logHead].text[k] = EOS;
    sDir->logHead = (sDir->logHead + 1) % ARRAY_COUNT(sDir->log);
    if (sDir->logCount < ARRAY_COUNT(sDir->log))
        sDir->logCount++;
}

static bool8 DirectorPopupText(u8 *text, u8 *color)
{
    if (!sDirPopup.timer)
        return FALSE;
    StringCopy(text, sDirPopup.text);
    *color = sDirPopup.color;
    return TRUE;
}

// Feed: "<SPECIES> OUT 28 LEFT" (species names are at most 10 characters).
static void DirFeedOut(const struct DirDuo *d)
{
    u8 buf[18], *end;
    static const u8 sOut[] = _(" OUT ");
    end = StringCopy(buf, gSpeciesNames[d->species[0]]);
    if (end - buf > 8) end = buf + 8;
    end = StringCopy(end, sOut);
    end = ConvertIntToDecimalStringN(end, DirLeft(), STR_CONV_MODE_LEFT_ALIGN, 2);
    *end = EOS;
    DirPopup(buf, NULL, 6);
}

static void DirPlayerPos(s32 *x, s32 *y)
{
    *x = sArena.bodies[0].x / Q;
    *y = sArena.bodies[0].y / Q;
    WildlandsWorld_OutdoorPos(x, y);
}

static void DirRandomGoal(struct DirDuo *d)
{
    u32 k;
    for (k = 0; k < 4; k++)
    {
        s16 x, y;
        WildlandsWorld_NavPoint(DirRand() % WildlandsWorld_NavPointCount(), &x, &y);
        if (!sZone.active || !ZoneOutside(x, y, 24) || k == 3)
        { d->gx = x; d->gy = y; return; }
    }
}

// ---- Active slot -----------------------------------------------------------

static void DirMakeMon(struct Pokemon *mon, u16 species, u8 level, u8 hpPct, bool8 legend, bool8 shiny)
{
    u16 hp, maxHp;
    u32 exp;
    // Created at level 1 then raised: CreateMon at the real level replays the
    // whole level-up learnset through encrypted Get/Set calls (~9 frames per
    // mon on hardware timing, a visible hitch whenever a new duo swaps in).
    // The arena loadout replaces the moves anyway.
    if (shiny)
    {
        // Personality and OT chosen so the shiny value is 0 (native shiny).
        u32 pers = ((u32)Random() << 16) | Random();
        u32 ot = ((pers >> 16) ^ (pers & 0xFFFF)) << 16;
        CreateMon(mon, species, 1, USE_RANDOM_IVS, TRUE, pers, OT_ID_PRESET, ot);
        gWildlandsShinyTelemetry[0]++;
    }
    else
        CreateMon(mon, species, 1, USE_RANDOM_IVS, FALSE, 0, OT_ID_PLAYER_ID, 0);
    exp = gExperienceTables[gSpeciesInfo[species].growthRate][level];
    SetMonData(mon, MON_DATA_EXP, &exp);
    SetMonData(mon, MON_DATA_LEVEL, &level);
    CalculateMonStats(mon);
    Wildlands_ArenaLoadout(mon);
    maxHp = GetMonData(mon, MON_DATA_MAX_HP);
    if (legend)
    {
        maxHp = min(999, maxHp * 2);
        SetMonData(mon, MON_DATA_MAX_HP, &maxHp);
    }
    hp = hpPct ? max(1, maxHp * hpPct / 100) : 0;
    SetMonData(mon, MON_DATA_HP, &hp);
}

// Write the live active duo back into its record (HP%, position).
static void DirStoreActive(void)
{
    struct DirDuo *d;
    if (!sDir || sDir->active == DIR_NONE)
        return;
    d = &sDir->duo[sDir->active];
    // Lead slot (battler 1) holds whichever member is currently leading.
    d->species[0] = gBattleMons[1].hp ? gBattleMons[1].species : d->species[0];
    d->hp[0] = gBattleMons[1].maxHP ? (gBattleMons[1].hp * 100 + gBattleMons[1].maxHP - 1) / gBattleMons[1].maxHP : 0;
    if (sSquadWings[1].active && sSquadWings[1].alive)
    {
        d->species[1] = sSquadWings[1].species;
        d->hp[1] = gBattleMons[3].maxHP ? (gBattleMons[3].hp * 100 + gBattleMons[3].maxHP - 1) / gBattleMons[3].maxHP : 0;
    }
    else
        d->hp[1] = 0;
    {
        s32 x = sArena.bodies[1].x / Q, y = sArena.bodies[1].y / Q;
        if (!d->legend)
            WildlandsWorld_OutdoorPos(&x, &y);
        d->x = x; d->y = y;
    }
    d->state = DirAlive(d) ? (d->legend ? DIR_LAIR : DIR_SIM) : DIR_DEAD;
    sDir->active = DIR_NONE;
}

// A duo taking the field never pops into view: if its record sits on screen,
// it enters from a legal spot just beyond the camera instead.
static void DirOffscreenEntry(struct DirDuo *d)
{
    s32 cx = sArenaXLCameraX, cy = sArenaXLCameraY, px, py;
    u32 k;
    if (d->legend || WildlandsWorld_InRoom(d->x, d->y) || !gWildlandsDirectorTelemetry[6])
        return;   // (the opening practice duo starts where the match placed it)
    if (d->x < cx - 40 || d->x > cx + 280 || d->y < cy - 40 || d->y > cy + 200)
        return;
    DirPlayerPos(&px, &py);
    for (k = 0; k < 48; k++)
    {
        s16 x, y;
        u32 dist;
        WildlandsWorld_NavPoint(DirRand() % WildlandsWorld_NavPointCount(), &x, &y);
        if (x >= cx - 40 && x <= cx + 280 && y >= cy - 40 && y <= cy + 200)
            continue;
        dist = ArenaNav_Distance(px, py, x, y);
        if (dist < 200 || dist > 420 || (sZone.active && ZoneOutside(x, y, 24)))
            continue;
        d->x = x; d->y = y;
        return;
    }
}

static void DirLoadActive(u8 index)
{
    static const u8 sShinyPre[] = _("SHINY ");
    struct DirDuo *d = &sDir->duo[index];
    struct ArenaBody *body = &sArena.bodies[1];
    u8 lead, other;
    u32 t0 = WL_NOW();
    u32 t1;
    DirOffscreenEntry(d);
    lead = (d->species[0] && d->hp[0]) ? 0 : 1;
    other = lead ^ 1;
    DirMakeMon(&gEnemyParty[0], d->species[lead], d->level, d->hp[lead], d->legend, DirShiny(d, d->species[lead]));
    t1 = WL_NOW(); gWildlandsHitch[6] = t1 - t0;
    if (IsMonShiny(&gEnemyParty[0]))
        DirPopup(sShinyPre, gSpeciesNames[d->species[lead]], 5);
    if (d->species[other] && d->hp[other])
        DirMakeMon(&gEnemyParty[1], d->species[other], d->level, d->hp[other], FALSE, DirShiny(d, d->species[other]));
    else
        ZeroMonData(&gEnemyParty[1]);
    gBattlerPartyIndexes[1] = 0;
    gWildlandsHitch[7] = WL_NOW() - t1; t1 = WL_NOW();
    SquadFillBattleMon(1, &gEnemyParty[0]);
    if (d->legend)
    {
        gBattleMons[1].statStages[STAT_DEF]++;
        gBattleMons[1].statStages[STAT_SPDEF]++;
    }
    body->x = d->x * Q; body->y = d->y * Q;
    body->art = ArenaSprites_Get(gBattleMons[1].species);
    body->drawnFrame = body->drawnDirection = 255;
    body->shotTimer = body->actionLife = body->dash = 0;
    body->cooldown = 30; body->knockX = body->knockY = 0;
    body->moveSlot = FirstMove(1, TRUE);
    if (body->art)
        LoadPalette(ArenaMonPalette(body->art, &gEnemyParty[0]), OBJ_PLTT_ID(1), PLTT_SIZE_4BPP);
    gSprites[body->shadow].invisible = FALSE;
    sArena.observed.x = sArena.goal.x = sArena.waypoint.x = d->x;
    sArena.observed.y = sArena.goal.y = sArena.waypoint.y = d->y;
    sArena.thinkTimer = 1; sArena.aiState = AI_REPOSITION; sArena.goalTimer = 0;
    gWildlandsHitch[8] = WL_NOW() - t1; t1 = WL_NOW();
    SquadHideWing(&sSquadWings[1]);
    sSquadWings[1].alive = FALSE;
    if (GetMonData(&gEnemyParty[1], MON_DATA_SPECIES))
        SquadSpawnWing(1);   // creates its sprites
    gWildlandsHitch[9] = WL_NOW() - t1; t1 = WL_NOW();
    memset(&sBrain, 0, sizeof(sBrain));
    sBrain.focus = 0xFF;
    sEnemySight.lost = 99;
    d->state = DIR_ACTIVE;
    sDir->active = index;
    gWildlandsDirectorTelemetry[1] = index;
    gWildlandsDirectorTelemetry[6]++;
    ArenaFeedback_Dust(d->x, d->y, TRUE);
    sArena.hudDirty = TRUE;
    gWildlandsHitch[10] = WL_NOW() - t1;
    gWildlandsHitch[2] = WL_NOW() - t0;
    if (gWildlandsHitch[2] > gWildlandsHitch[3]) gWildlandsHitch[3] = gWildlandsHitch[2];
}

static u8 DirNearest(bool8 includeLegends)
{
    u32 i, best = 0xFFFFFFFF;
    u8 pick = DIR_NONE;
    s32 px, py;
    DirPlayerPos(&px, &py);
    for (i = 1; i < sDir->count; i++)
    {
        struct DirDuo *d = &sDir->duo[i];
        u32 dist;
        if (d->state != DIR_SIM && !(includeLegends && d->state == DIR_LAIR))
            continue;
        if (!d->legend && d->room)
            continue;   // inside a lair fighting its legendary
        dist = ArenaNav_Distance(px, py, d->x, d->y);
        if (dist < best) { best = dist; pick = i; }
    }
    return pick;
}

// The legendary the player just beat joins as the partner, plus a team buff.
static void DirLegendJoins(struct DirDuo *d)
{
    static const u8 sJoined[] = _(" JOINED");
    struct SquadWing *w = &sSquadWings[0];
    u16 hp;
    u32 t;
    u8 slot = gBattlerPartyIndexes[0] == 1 ? 0 : 1;   // never the current lead's slot
    if (!sDir->partnerSaved)
    {
        sDir->savedLead = gPlayerParty[0];
        sDir->savedPartner = gPlayerParty[1];
        sDir->partnerSaved = TRUE;
    }
    DirMakeMon(&gPlayerParty[slot], d->species[0], gBattleMons[0].level ? gBattleMons[0].level : d->level, 100, FALSE, DirShiny(d, d->species[0]));
    if (gPlayerPartyCount < 2) gPlayerPartyCount = 2;
    SquadHideWing(w);
    w->alive = FALSE;
    SquadSpawnWing(0);   // creates its sprites
    gWildlandsPartnerTelemetry[1] = w->species;
    // Team buff: full heal and +1 ATK/DEF/SPD (pickup caps still apply).
    hp = gBattleMons[0].maxHP;
    gBattleMons[0].hp = hp;
    SetMonData(SquadPartyMon(0), MON_DATA_HP, &hp);
    for (t = 0; t < 3; t++)
        if (sLoot.boost[0][t] < LOOT_CAP)
            LootStat(0, t);
    gWildlandsDirectorTelemetry[4]++;
    DirPopup(gSpeciesNames[d->species[0]], sJoined, 5);
    PlaySE(SE_EXP_MAX);
    PlayCry_Normal(d->species[0], 0);
    d->state = DIR_DEAD;
    d->hp[0] = 0;
}

// Called when the active enemy lead is down and no wing can take over.
// Returns TRUE when the match continues (next duo loaded).
static bool8 DirectorAdvance(void)
{
    u8 next;
    if (!sDir || !WildlandsWorld_Active())
        return FALSE;
    if (sDir->active != DIR_NONE)
    {
        struct DirDuo *d = &sDir->duo[sDir->active];
        d->hp[0] = d->hp[1] = 0;
        d->state = DIR_DEAD;
        sDir->active = DIR_NONE;
        if (d->legend)
            DirLegendJoins(d);
        else
        {
            sDir->playerKOs++;
            DirFeedOut(d);
        }
    }
    gWildlandsDirectorTelemetry[0] = DirLeft();
    next = DirNearest(FALSE);
    if (next == DIR_NONE)
    {
        DirRestorePartner();
        return FALSE;            // last duo standing: the native result runs
    }
    DirLoadActive(next);
    return TRUE;
}

static bool8 DirectorSoloActive(void)
{
    return sDir && sDir->active != DIR_NONE && sDir->duo[sDir->active].legend;
}

// ---- Off-screen simulation ------------------------------------------------

static void DirSimDamage(struct DirDuo *d, u8 pct)
{
    u8 m = (d->hp[0] && d->species[0]) ? 0 : 1;
    if (d->hp[m] && d->species[1 - m] && d->hp[1 - m] && (DirRand() & 1))
        m = 1 - m;
    d->hp[m] = d->hp[m] > pct ? d->hp[m] - pct : 0;
}

static void DirSimOne(u8 i)
{
    struct DirDuo *d = &sDir->duo[i];
    u32 j;
    s32 dx, dy, dist;
    if (d->state != DIR_SIM)
        return;
    // Storm.
    if (sZone.active && ZoneOutside(d->x, d->y, 0))
    {
        u8 pct = (sZonePctPerSec[min(sZone.stage, ZONE_STAGES)] + 1) / 2 + 1;
        if (d->hp[0]) d->hp[0] = d->hp[0] > pct ? d->hp[0] - pct : 0;
        if (d->hp[1]) d->hp[1] = d->hp[1] > pct ? d->hp[1] - pct : 0;
        if (!DirAlive(d))
        {
            d->state = DIR_DEAD;
            if (d->plan) gWildlandsBossTelemetry[13]++;
            gWildlandsDirectorTelemetry[3]++;
            DirFeedOut(d);
            return;
        }
    }
    // Boss run in progress: walk to the lair, fight inside, resolve.
    if (d->plan)
    {
        struct DirDuo *l = &sDir->duo[d->plan - 1];
        s32 ox, oy;
        gWildlandsBossTelemetry[15]++;
        if (d->room)
        {
            if (!--d->room)
                DirBossResolve(d);
            return;
        }
        DirLairDoor(l, &ox, &oy);
        if (DirBossScore(d, l, d->x, d->y) < -200)
        {
            d->plan = 0;              // storm turned or the legendary is gone
            gWildlandsBossTelemetry[5]++;
            DirRandomGoal(d);
        }
        else if (ArenaNav_Distance(d->x, d->y, ox, oy) <= 40
                 || (ArenaNav_Distance(d->x, d->y, ox, oy) <= 160
                     && !WildlandsWorld_SpeciesLineClear(d->species[d->hp[0] ? 0 : 1], d->x, d->y, ox, oy, 6))
                 || (d->planStall >= 8 && d->planBest <= 480))
        {
            d->x = ox; d->y = oy;
            DirBossStart(d);
            return;
        }
        else if (d->planStall >= 8)
        {
            d->plan = 0;              // no progress and still far: give up
            gWildlandsBossTelemetry[5]++;
            DirRandomGoal(d);
        }
        else
        {
            u16 now = ArenaNav_Distance(d->x, d->y, ox, oy);
            if (!d->planBest || now + 8 < d->planBest) { d->planBest = now; d->planStall = 0; }
            else d->planStall++;
            d->gx = ox; d->gy = oy;
        }
    }
    // Skirmish with another simulated duo in range.
    for (j = 1; j < sDir->count; j++)
    {
        struct DirDuo *o = &sDir->duo[j];
        u32 pa, pb;
        if (j == i || o->state != DIR_SIM || o->room || ArenaNav_Distance(d->x, d->y, o->x, o->y) > 140)
            continue;
        pa = DirPower(d); pb = DirPower(o);
        DirSimDamage(d, 3 + 14 * pb / (pa + pb));
        DirSimDamage(o, 3 + 14 * pa / (pa + pb));
        gWildlandsDirectorTelemetry[7]++;
        if (!DirAlive(o)) { o->state = DIR_DEAD; d->kills++; gWildlandsDirectorTelemetry[3]++; DirFeedOut(o); }
        if (!DirAlive(d)) { if (d->plan) gWildlandsBossTelemetry[13]++; d->state = DIR_DEAD; o->kills++; gWildlandsDirectorTelemetry[3]++; DirFeedOut(d); }
        return;   // fighting duos hold position this tick
    }
    // Travel: ~40px per update toward the goal on legal ground.
    dx = d->gx - d->x; dy = d->gy - d->y;
    dist = max(Abs(dx), Abs(dy));
    // A duo on a boss run follows the island nav graph (validated edges, so
    // every intermediate point is legal ground if it becomes the active duo).
    if (d->plan)
    {
        struct ArenaPoint wp;
        u16 sp = d->species[d->hp[0] ? 0 : 1];
        s32 sx = dist > 48 ? dx * 48 / dist : dx, sy = dist > 48 ? dy * 48 / dist : dy;
        if (dist && WildlandsWorld_SpeciesLineClear(sp, d->x, d->y, d->x + sx, d->y + sy, 6))
        {
            d->x += sx; d->y += sy;
            return;
        }
        if (WildlandsWorld_NextWaypointSpecies(sp, d->x, d->y, d->gx, d->gy, &wp))
        {
            s32 wx = wp.x - d->x, wy = wp.y - d->y, wd = max(Abs(wx), Abs(wy));
            if (wd > 48) { wx = wx * 48 / wd; wy = wy * 48 / wd; }
            if (wd)
            {
                d->x += wx; d->y += wy;
                gWildlandsBossTelemetry[14]++;
                return;
            }
        }
        // Squeezed off the graph (slides can leave a duo in a corner): hop
        // onto the nearest node; this is off screen and the node is legal.
        {
            s16 nx = d->x, ny = d->y;
            if (WildlandsWorld_SnapToNav(&nx, &ny) && (nx != d->x || ny != d->y))
            {
                d->x = nx; d->y = ny;
                gWildlandsBossTelemetry[14]++;
                return;
            }
        }
        d->plan = 0;
        gWildlandsBossTelemetry[5]++;
        DirRandomGoal(d);
        return;
    }
    if (dist < 24 || (sZone.active && ZoneOutside(d->gx, d->gy, 24) && !(DirRand() & 3)))
    {
        // New goal: a lair when a boss run scores well (see DirBossScore),
        // otherwise mostly inside the circle, sometimes toward the player.
        u32 r = DirRand() & 15;
        s32 bossScore;
        u8 lair = d->plan ? DIR_NONE : DirBossPick(d, d->x, d->y, &bossScore);
        DirRandomGoal(d);
        if (lair != DIR_NONE)
        {
            s32 ox, oy;
            DirLairDoor(&sDir->duo[lair], &ox, &oy);
            d->plan = lair + 1;
            d->planBest = 0; d->planStall = 0;
            d->gx = ox; d->gy = oy;
            sDir->bossCooldown = max(sDir->bossCooldown, 600);   // others wait while it travels
            gWildlandsBossTelemetry[12]++;
        }
        else if (r < 3)
        {
            s32 px, py;
            DirPlayerPos(&px, &py);
            d->gx = px; d->gy = py;
        }
        return;
    }
    {
        s32 nx = d->x + dx * 40 / dist, ny = d->y + dy * 40 / dist;
        if (WildlandsWorld_SpeciesLineClear(d->species[d->hp[0] ? 0 : 1], d->x, d->y, nx, ny, 6))
        { d->x = nx; d->y = ny; }
        else if (d->plan)
        {
            // No straight way: follow the island nav graph toward the lair;
            // drop the plan only if even that has no step.
            struct ArenaPoint wp;
            u16 sp = d->species[d->hp[0] ? 0 : 1];
            bool8 moved = FALSE;
            if (WildlandsWorld_NextWaypointSpecies(sp, d->x, d->y, d->gx, d->gy, &wp))
            {
                s32 wx = wp.x - d->x, wy = wp.y - d->y, wd = max(Abs(wx), Abs(wy));
                if (wd > 40) { wx = wx * 40 / wd; wy = wy * 40 / wd; }
                if (wd && WildlandsWorld_SpeciesLineClear(sp, d->x, d->y, d->x + wx, d->y + wy, 6))
                { d->x += wx; d->y += wy; moved = TRUE; gWildlandsBossTelemetry[14]++; }
            }
            if (!moved)
            {
                d->plan = 0;
                gWildlandsBossTelemetry[5]++;
                DirRandomGoal(d);
            }
        }
        else if (WildlandsWorld_SpeciesLineClear(d->species[d->hp[0] ? 0 : 1], d->x, d->y,
                     d->x + (dx > 0 ? 40 : -40), d->y, 6) && Abs(dx) > 24)
            d->x += dx > 0 ? 40 : -40;   // slide along the obstacle
        else if (WildlandsWorld_SpeciesLineClear(d->species[d->hp[0] ? 0 : 1], d->x, d->y,
                     d->x, d->y + (dy > 0 ? 40 : -40), 6) && Abs(dy) > 24)
            d->y += dy > 0 ? 40 : -40;
        else
        {
            // Blocked: most goal changes happen here, so this is also where a
            // duo reconsiders a lair (one blocked tick in four).
            s32 bossScore;
            u8 lair = (DirRand() & 3) ? DIR_NONE : DirBossPick(d, d->x, d->y, &bossScore);
            DirRandomGoal(d);
            if (lair != DIR_NONE)
            {
                s32 ox, oy;
                DirLairDoor(&sDir->duo[lair], &ox, &oy);
                d->plan = lair + 1;
                d->planBest = 0; d->planStall = 0;
                d->gx = ox; d->gy = oy;
                sDir->bossCooldown = max(sDir->bossCooldown, 600);
                gWildlandsBossTelemetry[12]++;
            }
        }
    }
}

// Active-slot policy, every 64 frames: keep the closest threat in play.
static void DirPolicy(void)
{
    s32 px, py;
    s8 room;
    u8 near;
    DirPlayerPos(&px, &py);
    // A legendary in the room the player just entered becomes the active enemy.
    room = WildlandsWorld_RoomIndexAt(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q);
    if (room >= 0 && WildlandsWorld_RoomLegend(room))
    {
        u32 j;
        for (j = WL_DIRECTOR_DUOS; j < sDir->count; j++)
            if (sDir->duo[j].state == DIR_LAIR && sDir->duo[j].room == (u8)room)
            {
                DirStoreActive();
                DirLoadActive(j);
                gWildlandsDirectorTelemetry[2]++;
                return;
            }
        return;
    }
    // Leaving a lair with the legendary still alive: it stays home.
    if (DirectorSoloActive() && room < 0)
    {
        DirStoreActive();
        near = DirNearest(FALSE);
        if (near != DIR_NONE) DirLoadActive(near);
        gWildlandsDirectorTelemetry[2]++;
        return;
    }
    if (sDir->active == DIR_NONE)
    {
        near = DirNearest(FALSE);
        if (near != DIR_NONE) DirLoadActive(near);
        return;
    }
    near = DirNearest(FALSE);
    if (near == DIR_NONE || DirectorSoloActive())
        return;
    {
        u32 activeD = ArenaNav_Distance(px, py, sArena.bodies[1].x / Q, sArena.bodies[1].y / Q);
        u32 nearD = ArenaNav_Distance(px, py, sDir->duo[near].x, sDir->duo[near].y);
        // Only swap a duo the player cannot see for one that is off screen.
        if (activeD > 640 && nearD < 360 && nearD > 180)
        {
            DirStoreActive();
            DirLoadActive(near);
            gWildlandsDirectorTelemetry[2]++;
        }
    }
}

// Map ring for the lair whose outdoor door is (x,y): 0 taken or beaten,
// 1 legendary home, 2 under attack (a duo is fighting inside).
static u8 DirectorLairState(s32 x, s32 y)
{
    u32 j, k;
    if (!sDir)
        return 1;
    for (j = WL_DIRECTOR_DUOS; j < sDir->count; j++)
    {
        s32 ox, oy;
        DirLairDoor(&sDir->duo[j], &ox, &oy);
        if (ox != x || oy != y)
            continue;
        if (sDir->duo[j].state != DIR_LAIR && sDir->duo[j].state != DIR_ACTIVE)
            return 0;
        for (k = 1; k < WL_DIRECTOR_DUOS; k++)
            if (sDir->duo[k].state == DIR_SIM && sDir->duo[k].room && sDir->duo[k].plan == j + 1)
                return 2;
        return 1;
    }
    return 1;
}

// A random lair door whose legendary is still home (storm hot zones).
static bool8 DirectorLairAnchor(s32 *x, s32 *y)
{
    u32 j, n = 0, pick;
    if (!sDir)
        return FALSE;
    for (j = WL_DIRECTOR_DUOS; j < sDir->count; j++)
        if (sDir->duo[j].state == DIR_LAIR && sDir->duo[j].hp[0])
            n++;
    if (!n)
        return FALSE;
    pick = DirRand() % n;
    for (j = WL_DIRECTOR_DUOS; j < sDir->count; j++)
        if (sDir->duo[j].state == DIR_LAIR && sDir->duo[j].hp[0] && !pick--)
        {
            DirLairDoor(&sDir->duo[j], x, y);
            return TRUE;
        }
    return FALSE;
}

// ---- Boss runs by the on-screen enemy duo ---------------------------------
// The brain asks (when it sees nobody) whether a lair is worth it now; the
// answer is the lair's outdoor door index or 0xFF. Re-scored every 2s.
static u8 DirectorBossDoor(void)
{
    struct DirDuo tmp;
    s32 x, y, score;
    u8 lair;
    u32 k;
    if (!sDir || sDir->active == DIR_NONE || DirectorSoloActive())
        return 0xFF;
    if ((u16)(sDir->clock - sDir->bossEvalStamp) < 120 && sDir->bossEvalStamp)
        return sDir->bossDoor;
    sDir->bossEvalStamp = sDir->clock ? sDir->clock : 1;
    sDir->bossDoor = 0xFF;
    tmp = sDir->duo[sDir->active];
    tmp.species[0] = gBattleMons[1].hp ? gBattleMons[1].species : tmp.species[0];
    tmp.hp[0] = gBattleMons[1].maxHP ? (gBattleMons[1].hp * 100 + gBattleMons[1].maxHP - 1) / gBattleMons[1].maxHP : 0;
    tmp.hp[1] = (sSquadWings[1].active && sSquadWings[1].alive && gBattleMons[3].maxHP)
        ? (gBattleMons[3].hp * 100 + gBattleMons[3].maxHP - 1) / gBattleMons[3].maxHP : 0;
    x = sArena.bodies[1].x / Q; y = sArena.bodies[1].y / Q;
    if (WildlandsWorld_InRoom(x, y))
        return 0xFF;
    // A duo that was already on its way (planned off screen) keeps its plan
    // while it is the on-screen duo, unless that lair stopped being viable.
    if (tmp.plan && DirBossScore(&tmp, &sDir->duo[tmp.plan - 1], x, y) > -200)
        lair = tmp.plan - 1;
    else
        lair = DirBossPick(&tmp, x, y, &score);
    if (lair == DIR_NONE || DirNearest(FALSE) == DIR_NONE)
        return 0xFF;     // someone must be able to take the field meanwhile
    DirLairDoor(&sDir->duo[lair], &x, &y);
    for (k = 0; k < WildlandsWorld_DoorCount(); k++)
    {
        s16 ox, oy;
        bool8 isLair;
        WildlandsWorld_DoorInfo(k, &ox, &oy, &isLair);
        if (ox == x && oy == y)
        {
            sDir->bossDoor = k;
            sDir->activePlan = lair + 1;
            break;
        }
    }
    return sDir->bossDoor;
}

// The on-screen duo reached the lair door: it goes in to fight (simulated,
// the player is elsewhere) and the nearest other duo takes the field. If the
// player follows it in, the legendary is waiting there as usual.
static void DirectorBossEnter(void)
{
    u8 a, next;
    struct DirDuo *d;
    if (!sDir || sDir->active == DIR_NONE || !sDir->activePlan)
        return;
    a = sDir->active;
    DirStoreActive();
    d = &sDir->duo[a];
    if (d->state != DIR_SIM)
        return;
    d->plan = sDir->activePlan;
    d->planBest = 0; d->planStall = 0;
    sDir->activePlan = 0;
    sDir->bossEvalStamp = 0;
    {
        s32 ox, oy;
        DirLairDoor(&sDir->duo[d->plan - 1], &ox, &oy);
        d->x = d->gx = ox; d->y = d->gy = oy;
    }
    DirBossStart(d);
    gWildlandsBossTelemetry[6]++;
    next = DirNearest(FALSE);
    if (next != DIR_NONE)
        DirLoadActive(next);
}

static void DirectorSim(void)
{
    if (!sDir || !WildlandsWorld_Active() || sArena.paused || sArena.resultTimer)
        return;
    if (sDirPopup.timer && !--sDirPopup.timer)
        sArena.hudDirty = TRUE;
    sDir->clock++;
    if (sDir->active != DIR_NONE && sDir->duo[sDir->active].legend)
    {
        // Live boss check: [3] player room+1 [4] boss room+1 [5] boss species
        // [6] distance to the player [7] boss x [8] boss y
        s32 bx = sArena.bodies[1].x / Q, by = sArena.bodies[1].y / Q;
        gWildlandsBossAudit[3] = WildlandsWorld_RoomIndexAt(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q) + 1;
        gWildlandsBossAudit[4] = WildlandsWorld_RoomIndexAt(bx, by) + 1;
        gWildlandsBossAudit[5] = gBattleMons[1].species;
        gWildlandsBossAudit[6] = ArenaNav_Distance(sArena.bodies[0].x / Q, sArena.bodies[0].y / Q, bx, by);
        gWildlandsBossAudit[7] = bx; gWildlandsBossAudit[8] = by;
    }
    if (sDir->bossCooldown)
        sDir->bossCooldown--;
    if (sDir->count > 1)
    {
        sDir->cursor = sDir->cursor + 1 >= sDir->count ? 1 : sDir->cursor + 1;
        // Each duo advances every `count` frames: scale so 30 duos move ~80px/s.
        DirSimOne(sDir->cursor);
    }
    if (!(sDir->clock & 63))
    {
        DirPolicy();
        gWildlandsDirectorTelemetry[0] = DirLeft();
    }
}

// ---- Lifecycle --------------------------------------------------------------

static void DirRestorePartner(void)
{
    if (sDir && sDir->partnerSaved)
    {
        gPlayerParty[0] = sDir->savedLead;
        gPlayerParty[1] = sDir->savedPartner;
        sDir->partnerSaved = FALSE;
    }
}

#ifdef WL_ISLAND
// Beta: a fresh match drops the duo at a random legal spot (away from lair
// doors), with the opening enemy duo a short walk away.
EWRAM_DATA s16 gWildlandsSpawn[4] = {0};   // player x,y, enemy x,y
static void DirRandomSpawn(void)
{
    u32 k, j;
    s16 x = 0, y = 0;
    bool8 ok = FALSE;
    for (k = 0; k < 64 && !ok; k++)
    {
        WildlandsWorld_NavPoint(DirRand() % WildlandsWorld_NavPointCount(), &x, &y);
        if (WildlandsWorld_InRoom(x, y) || !WildlandsWorld_CanStandSide(0, x, y, 8))
            continue;
        ok = TRUE;
        for (j = 0; j < WildlandsWorld_DoorCount() && ok; j++)
        {
            s16 ox, oy;
            bool8 lair;
            WildlandsWorld_DoorInfo(j, &ox, &oy, &lair);
            if (lair && ArenaNav_Distance(x, y, ox, oy) < 320)
                ok = FALSE;
        }
    }
    if (!ok)
        return;
    sArena.bodies[0].x = x * Q; sArena.bodies[0].y = y * Q;
    gWildlandsSpawn[0] = x; gWildlandsSpawn[1] = y;
    for (k = 0; k < 48; k++)
    {
        s16 ex, ey;
        u32 d;
        WildlandsWorld_NavPoint(DirRand() % WildlandsWorld_NavPointCount(), &ex, &ey);
        d = ArenaNav_Distance(x, y, ex, ey);
        if (d < 200 || d > 340 || WildlandsWorld_InRoom(ex, ey) || !WildlandsWorld_CanStandSide(1, ex, ey, 8))
            continue;
        sArena.bodies[1].x = ex * Q; sArena.bodies[1].y = ey * Q;
        gWildlandsSpawn[2] = ex; gWildlandsSpawn[3] = ey;
        break;
    }
    if (sSquadWings[0].active) SquadRegroup(&sSquadWings[0], &sArena.bodies[0]);
    if (sSquadWings[1].active) SquadRegroup(&sSquadWings[1], &sArena.bodies[1]);
}
#endif

static void DirectorInit(void)
{
    u32 i, n = 0;
    u8 level;
    s32 px, py;
    if (!WildlandsWorld_Active())
        return;
    if (sWildlandsEncounterLive && sDir)
        return;   // menu round trip: same lobby
    sWildlandsSummary = FALSE;
    memset(gWildlandsBossAudit, 0, sizeof(gWildlandsBossAudit));
    if (sDir)
    {
        DirRestorePartner();
        Free(sDir);
    }
    sDir = AllocZeroed(sizeof(struct DirState));
    if (!sDir)
        return;
    memset(gWildlandsDirectorTelemetry, 0, sizeof(gWildlandsDirectorTelemetry));
    memset(&sDirPopup, 0, sizeof(sDirPopup));
#ifdef WL_ISLAND
    DirRandomSpawn();
#endif
    Wildlands_TrimParty();
    level = gBattleMons[0].level ? gBattleMons[0].level : 50;
    px = sArena.bodies[0].x / Q; py = sArena.bodies[0].y / Q;
    sDir->duo[0].state = DIR_PLAYER;
    for (i = 1; i < WL_DIRECTOR_DUOS; i++)
    {
        struct DirDuo *d = &sDir->duo[i];
        u32 k;
        for (k = 0; k < 2; k++)
        {
            u32 tries;
            u16 sp = SPECIES_PIDGEOT;
            for (tries = 0; tries < 8; tries++)
            {
                sp = sDirRoster[DirRand() % ARRAY_COUNT(sDirRoster)];
                if (ArenaSprites_Get(sp) && (k == 0 || sp != d->species[0]))
                    break;
            }
            d->species[k] = sp;
            d->hp[k] = 100;
        }
        d->pad2 = 1 + DirRand() % 255;
        d->level = level > 8 ? level - DirRand() % 9 : level;
        for (k = 0; k < 12; k++)
        {
            s16 x, y;
            WildlandsWorld_NavPoint(DirRand() % WildlandsWorld_NavPointCount(), &x, &y);
            d->x = x; d->y = y;
            if (ArenaNav_Distance(px, py, x, y) > 400)
                break;
        }
        DirRandomGoal(d);
        d->state = DIR_SIM;
        n++;
    }
    // Legendaries: one per lair room, guarding its cache.
    sDir->count = WL_DIRECTOR_DUOS;
    for (i = 0; i < WildlandsWorld_RoomCount() && sDir->count < DIR_MAX; i++)
    {
        u16 sp = WildlandsWorld_RoomLegend(i);
        struct DirDuo *d;
        if (!sp || !ArenaSprites_Get(sp))
            continue;
        d = &sDir->duo[sDir->count];
        d->species[0] = sp; d->hp[0] = 100;
        d->pad2 = 1 + DirRand() % 255;
        d->level = min(100, level + 5);
        d->legend = TRUE;
        d->room = i;
        d->state = DIR_LAIR;
        { s32 bx, by; WildlandsWorld_RoomBoss(i, &bx, &by); d->x = bx; d->y = by; }
        // Audit: the boss stands in its own room, the room names this legend,
        // and the spot is standable for its species.
        gWildlandsBossAudit[0]++;
        if (WildlandsWorld_RoomIndexAt(d->x, d->y) == (s8)i && WildlandsWorld_RoomLegend(i) == sp
            && WildlandsWorld_CanStandSpecies(sp, d->x, d->y, 6))
            gWildlandsBossAudit[1]++;
        else
            gWildlandsBossAudit[2] |= 1 << i;
        sDir->count++;
    }
    // The practice duo already on the field becomes AI duo 1 at its spawn,
    // re-rolled to the lobby's level band.
    sDir->duo[1].x = sArena.bodies[1].x / Q;
    sDir->duo[1].y = sArena.bodies[1].y / Q;
    sDir->active = DIR_NONE;
    DirLoadActive(1);
    gWildlandsDirectorTelemetry[0] = DirLeft();
}

static void DirectorDestroy(void)
{
    // A finished match (result shown) restores the player's real partner;
    // a menu round trip keeps the lobby and the legendary partner.
    if (sArena.resultTimer && sDir)
    {
        DirRestorePartner();
        Free(sDir);
        sDir = NULL;
        PropsFree();
        // Back to the Lab ready to play: a won match restores HP, PP and
        // status (a lost one whites out to the Lab, which heals too).
        if (gBattleMons[0].hp)
            HealPlayerParty();
    }
}

static u8 DirectorLeft(void) { return DirLeft(); }

// ---- Pause pages: TEAM and LOG ----------------------------------------------
static u8 *DirTimeString(u8 *end, u16 seconds)
{
    end = ConvertIntToDecimalStringN(end, seconds / 60, STR_CONV_MODE_LEFT_ALIGN, 2);
    *end++ = CHAR_COLON;
    return ConvertIntToDecimalStringN(end, seconds % 60, STR_CONV_MODE_LEADING_ZEROS, 2);
}

static void DirTeamMember(u8 battler, u32 y, bool8 lead)
{
    static const u8 sLv[] = _(" L");
    static const u8 sHp[] = _("  HP ");
    static const u8 sLeadMark[] = _("> ");
    static const u8 sOut[] = _("  FAINTED");
    static const u8 sNoMark[] = _("  ");
    u8 text[40], *end;
    u32 k;
    const struct BattlePokemon *m = &gBattleMons[battler];
    if (!SquadAlive(battler) || !m->species)
    {
        end = StringCopy(text, battler < 2 ? sLeadMark : sNoMark);
        if (m->species) end = StringCopy(end, gSpeciesNames[m->species]);
        StringCopy(end, sOut);
        HudTinyWindow(1, 6, y, text, 7, 38);
        return;
    }
    end = StringCopy(text, lead ? sLeadMark : sNoMark);
    end = StringCopy(end, gSpeciesNames[m->species]);
    end = StringCopy(end, sLv);
    end = ConvertIntToDecimalStringN(end, m->level, STR_CONV_MODE_LEFT_ALIGN, 3);
    end = StringCopy(end, sHp);
    end = ConvertIntToDecimalStringN(end, m->hp, STR_CONV_MODE_LEFT_ALIGN, 3);
    *end++ = CHAR_SLASH;
    end = ConvertIntToDecimalStringN(end, m->maxHP, STR_CONV_MODE_LEFT_ALIGN, 3);
    *end = EOS;
    HudTinyWindow(1, 6, y, text, lead ? 5 : 4, 38);
    for (k = 0; k < MAX_MON_MOVES; k++)
    {
        if (!m->moves[k])
            continue;
        end = StringCopy(text, gMoveNames[m->moves[k]]);
        *end++ = CHAR_SPACE;
        end = ConvertIntToDecimalStringN(end, m->pp[k], STR_CONV_MODE_LEFT_ALIGN, 2);
        *end = EOS;
        HudTinyWindow(1, 12 + (k & 1) * 104, y + 7 + (k >> 1) * 7, text,
            ArenaMoves_Get(m->moves[k]) ? (m->pp[k] ? 4 : 6) : 7, 18);
    }
}

static void WildlandsTeamDraw(void)
{
    static const u8 sTitle[] = _("TEAM");
    static const u8 sBoost[] = _("BOOSTS A+");
    static const u8 sCap[] = _("  CAP 3   KO ");
    static const u8 sLegend[] = _("LEGEND PARTNER: ");
    static const u8 sFoe[] = _("FOES A+");
    static const u8 sHelp[] = _("SELECT: SWAP LEAD   B: BACK");
    u8 text[48], *end;
    FillWindowPixelBuffer(1, PIXEL_FILL(9));
    PrintPopup(6, 0, sTitle, 5);
    HudTinyWindow(1, 64, 3, sHelp, 7, 30);
    DirTeamMember(0, 14, TRUE);
    DirTeamMember(2, 36, FALSE);
    end = StringCopy(text, sBoost);
    *end++ = CHAR_0 + sLoot.boost[0][0];
    *end++ = CHAR_SPACE; *end++ = CHAR_D; *end++ = CHAR_PLUS; *end++ = CHAR_0 + sLoot.boost[0][1];
    *end++ = CHAR_SPACE; *end++ = CHAR_S; *end++ = CHAR_PLUS; *end++ = CHAR_0 + sLoot.boost[0][2];
    end = StringCopy(end, sCap);
    end = ConvertIntToDecimalStringN(end, sDir ? sDir->playerKOs : 0, STR_CONV_MODE_LEFT_ALIGN, 2);
    *end = EOS;
    HudTinyWindow(1, 6, 58, text, 4, 44);
    if (sDir && sDir->partnerSaved)
    {
        end = StringCopy(text, sLegend);
        StringCopy(end, gSpeciesNames[gBattleMons[2].species]);
        HudTinyWindow(1, 6, 65, text, 5, 40);
    }
    else
    {
        end = StringCopy(text, sFoe);
        *end++ = CHAR_0 + sLoot.boost[1][0];
        *end++ = CHAR_SPACE; *end++ = CHAR_D; *end++ = CHAR_PLUS; *end++ = CHAR_0 + sLoot.boost[1][1];
        *end++ = CHAR_SPACE; *end++ = CHAR_S; *end++ = CHAR_PLUS; *end++ = CHAR_0 + sLoot.boost[1][2];
        *end = EOS;
        HudTinyWindow(1, 6, 65, text, 6, 30);
    }
    PutWindowTilemap(1);
    CopyWindowToVram(1, COPYWIN_FULL);
}

static void WildlandsLogDraw(void)
{
    static const u8 sTitle[] = _("LOG");
    static const u8 sEmpty[] = _("NOTHING YET");
    static const u8 sHelp[] = _("NEWEST FIRST   B: BACK");
    u8 text[32], *end;
    u32 i;
    FillWindowPixelBuffer(1, PIXEL_FILL(9));
    PrintPopup(6, 0, sTitle, 5);
    HudTinyWindow(1, 64, 3, sHelp, 7, 24);
    if (!sDir || !sDir->logCount)
        HudTinyWindow(1, 6, 16, sEmpty, 4, 12);
    else
        for (i = 0; i < sDir->logCount && i < 8; i++)
        {
            u32 k = (sDir->logHead + ARRAY_COUNT(sDir->log) - 1 - i) % ARRAY_COUNT(sDir->log);
            end = DirTimeString(text, sDir->log[k].t);
            *end++ = CHAR_SPACE; *end++ = CHAR_SPACE;
            StringCopy(end, sDir->log[k].text);
            HudTinyWindow(1, 6, 15 + i * 7, text, i ? 4 : 5, 30);
        }
    PutWindowTilemap(1);
    CopyWindowToVram(1, COPYWIN_FULL);
}
static bool8 DirectorRunning(void) { return sDir != NULL; }
static bool8 DirectorPopupActive(void) { return sDirPopup.timer != 0; }

// Pause screen line: duos left.
static void DirectorPauseLine(void)
{
    static const u8 sLeft[] = _("DUOS LEFT ");
    u8 text[16], *end;
    if (!sDir)
        return;
    end = StringCopy(text, sLeft);
    ConvertIntToDecimalStringN(end, DirLeft(), STR_CONV_MODE_LEFT_ALIGN, 2);
    HudTinyWindow(1, 120, 46, text, 5, 12);
}

// Shiny palettes for the arena sprites: each colour of the arena sprite is
// matched to its nearest colour in the species' normal battle palette and
// shifted by that colour's normal->shiny change, keeping the arena shading.
static EWRAM_DATA u16 sWlShinyPal[16] = {0};
static const u16 *ArenaMonPalette(const struct ArenaSpriteSet *art, struct Pokemon *mon)
{
    u16 normal[32], shiny[32];
    u16 species;
    u32 c, k;
    if (!art)
        return NULL;
    if (!mon || !(species = GetMonData(mon, MON_DATA_SPECIES)) || !IsMonShiny(mon))
        return art->palette;
    LZDecompressWram(gMonPaletteTable[species].data, normal);
    LZDecompressWram(gMonShinyPaletteTable[species].data, shiny);
    sWlShinyPal[0] = art->palette[0];
    for (c = 1; c < 16; c++)
    {
        u16 col = art->palette[c];
        s32 r = col & 31, g = (col >> 5) & 31, b = (col >> 10) & 31;
        s32 best = 0x7FFFFFFF;
        u32 bk = 1;
        for (k = 1; k < 16; k++)
        {
            s32 dr = r - (normal[k] & 31), dg = g - ((normal[k] >> 5) & 31), db = b - ((normal[k] >> 10) & 31);
            s32 dist = dr * dr + dg * dg + db * db;
            if (dist < best) { best = dist; bk = k; }
        }
        r += (shiny[bk] & 31) - (normal[bk] & 31);
        g += ((shiny[bk] >> 5) & 31) - ((normal[bk] >> 5) & 31);
        b += ((shiny[bk] >> 10) & 31) - ((normal[bk] >> 10) & 31);
        r = r < 0 ? 0 : (r > 31 ? 31 : r);
        g = g < 0 ? 0 : (g > 31 ? 31 : g);
        b = b < 0 ? 0 : (b > 31 ? 31 : b);
        sWlShinyPal[c] = r | (g << 5) | (b << 10);
    }
    gWildlandsShinyTelemetry[1]++;
    return sWlShinyPal;
}

// End-of-match summary card (pause window), shown while the result holds.
EWRAM_DATA u16 gWildlandsSummaryTelemetry[4] = {0};   // shown, won, place, KOs
static void WildlandsSummaryDraw(void)
{
    static const u8 sWin[] = _("VICTORY! LAST DUO STANDING");
    static const u8 sLose[] = _("ELIMINATED");
    static const u8 sPlace[] = _("PLACE ");
    static const u8 sOf[] = _(" OF ");
    static const u8 sKOs[] = _("KNOCKOUTS  ");
    static const u8 sTime[] = _("SURVIVED  ");
    static const u8 sHelp[] = _("A: BACK TO THE LAB");
    u8 text[32], *end;
    bool8 won = gBattleMons[0].hp != 0;
    u32 place = won ? 1 : DirLeft() + 1;
    u32 kos = sDir ? sDir->playerKOs : 0;
    u32 secs = sZone.active ? sZone.clock / 60 : (sDir ? sDir->clock / 60 : 0);
    gWildlandsSummaryTelemetry[0]++;
    gWildlandsSummaryTelemetry[1] = won;
    gWildlandsSummaryTelemetry[2] = place;
    gWildlandsSummaryTelemetry[3] = kos;
    FillWindowPixelBuffer(1, PIXEL_FILL(9));
    PrintPopup(8, 3, won ? sWin : sLose, won ? 5 : 6);
    end = StringCopy(text, sPlace);
    end = ConvertIntToDecimalStringN(end, place, STR_CONV_MODE_LEFT_ALIGN, 2);
    end = StringCopy(end, sOf);
    ConvertIntToDecimalStringN(end, WL_DIRECTOR_DUOS, STR_CONV_MODE_LEFT_ALIGN, 2);
    PrintPopup(8, 20, text, 4);
    end = StringCopy(text, sKOs);
    ConvertIntToDecimalStringN(end, kos, STR_CONV_MODE_LEFT_ALIGN, 2);
    PrintPopup(8, 34, text, 4);
    end = StringCopy(text, sTime);
    DirTimeString(end, secs > 5999 ? 5999 : secs);
    PrintPopup(8, 48, text, 4);
    HudTinyWindow(1, 8, 67, sHelp, 7, 52);
    PutWindowTilemap(1);
    CopyWindowToVram(1, COPYWIN_FULL);
}
