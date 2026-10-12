// Wildlands V5 team upgrades: visible, reachable, collect-once pickups.
//
// Placements are generated at build time on legal dry ground
// (wildlands_loot.inc). Rules (proposed defaults, not locked tuning):
//  - proximity auto-pickup within 12px; any living actor of either team may
//    collect; the nearest actor wins a contested frame (lower battler id on an
//    exact tie) and the orb is removed atomically, so it can never be taken
//    twice even when actors overlap;
//  - ATK = +1 Attack and Sp. Atk stage, DEF = +1 Defense and Sp. Def stage,
//    SPD = +1 Speed stage (movement only; cooldowns are not affected) for BOTH
//    members of the collecting team, capped at +2 per stat per team; an orb
//    whose stat is already capped for the nearest team stays on the ground;
//  - state is per encounter and survives Arena re-entry after menus; the
//    stages live in gBattleMons so they end with the battle.

#define LOOT_ATK 0
#define LOOT_DEF 1
#define LOOT_SPD 2
#define LOOT_HEAL 3   // house supplies: both members recover 40% max HP
#define LOOT_CACHE 4  // lair cache: +1 ATK, DEF and SPD at once (caps apply)
#define LOOT_TYPES 5
#define LOOT_MAX 64
#define LOOT_CAP 3
#define LOOT_TAG 0xA7C0
#define LOOT_SPRITES 4

struct LootSpot { s16 x, y; u8 type; };
static const struct LootSpot sLootSpots[] = {
#include "wildlands_loot.inc"
};

static EWRAM_DATA struct {
    u32 collected[2];
    u8 boost[2][3];
    u8 sprite[LOOT_SPRITES];
    u8 live;
    u8 popupTimer, popupType, popupTeam;
} sLoot = {};
// [0] orbs collected [1..3] team0 atk/def/spd [4..6] team1 atk/def/spd
// [7] capped refusals [8] spot count [9] last collector battler
// [10] contested frames resolved [11] duplicate-collect attempts (must be 0)
// [12] heals collected [13] lair caches collected
EWRAM_DATA u32 gWildlandsLootTelemetry[14] = {};

static void LootLastSpot(s16 *x, s16 *y)
{
    *x = sLootSpots[ARRAY_COUNT(sLootSpots) - 1].x;
    *y = sLootSpots[ARRAY_COUNT(sLootSpots) - 1].y;
}

static bool8 LootTaken(u32 i)
{
    return (sLoot.collected[i >> 5] >> (i & 31)) & 1;
}

static const struct OamData sLootOam = {.shape = SPRITE_SHAPE(16x16), .size = SPRITE_SIZE(16x16), .priority = 1};
static const struct SpriteTemplate sLootTemplate = {
    .tileTag = LOOT_TAG, .paletteTag = SHOT_TAG, .oam = &sLootOam,
    .anims = gDummySpriteAnimTable, .images = NULL, .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};
// Loot shares the player shot palette (OBJ palettes are all spoken for):
// entries 2 (white) and 3 (dark) are the shot palette's own; 5..14 are free
// and carry the five gem colours (body, shade).
static const u16 sLootColors[10] = {
    RGB(31, 8, 6), RGB(20, 2, 2),     // ATK red
    RGB(8, 16, 31), RGB(2, 6, 20),    // DEF blue
    RGB(31, 27, 4), RGB(20, 14, 0),   // SPD gold
    RGB(8, 28, 10), RGB(2, 14, 4),    // HEAL green
    RGB(26, 10, 31), RGB(14, 2, 20),  // CACHE violet
};

// Beta: loot owns its palette when a slot is free (the shared shot palette
// gets rewritten by move effects, which turned every pickup into the same
// odd-coloured sparkle). Falls back to the shared palette otherwise.
static EWRAM_DATA u8 sLootPal = 0xFF;
EWRAM_DATA u8 gWildlandsLootPalDiag = 0;
static u8 LootPaletteNum(void)
{
    return sLootPal != 0xFF ? sLootPal : IndexOfSpritePaletteTag(SHOT_TAG);
}
// The gem colours live in the shared shot palette (entries 5..14). Anything
// that reloads that palette wipes them, so they are re-asserted whenever they
// differ (cheap compare of ten colours, done while loot is drawn).
static void LootAssertColors(void)
{
    u8 pal = IndexOfSpritePaletteTag(SHOT_TAG);
    u32 k, base;
    if (pal == 0xFF)
        return;
    base = OBJ_PLTT_ID(pal) + 5;
    for (k = 0; k < ARRAY_COUNT(sLootColors); k++)
        if (gPlttBufferUnfaded[base + k] != sLootColors[k])
            break;
    if (k == ARRAY_COUNT(sLootColors))
        return;
    LoadPalette(sLootColors, base, sizeof(sLootColors));
    gWildlandsLootPalDiag++;
}
static void LootLoadGraphics(void)
{
    static const u16 sLootPalette[16] = {
        0, RGB(31, 31, 31), RGB(31, 31, 31), RGB(4, 5, 8), RGB(31, 31, 31),
        RGB(31, 8, 6), RGB(20, 2, 2), RGB(8, 16, 31), RGB(2, 6, 20),
        RGB(31, 27, 4), RGB(20, 14, 0), RGB(8, 28, 10), RGB(2, 14, 4),
        RGB(26, 10, 31), RGB(14, 2, 20), RGB(20, 26, 31),
    };
    struct SpritePalette ownPal = {sLootPalette, LOOT_TAG};
    u32 tiles[LOOT_TYPES * 32 + 24] = {0};
    // Extra tile for the storm rain streak (arena_zone.inc): blue tail, white head.
    static const u32 sRainStreak[8] = {
        0x77000000, 0x07700000, 0x07700000, 0x00770000,
        0x00226000, 0x00022000, 0x00022000, 0x00002200,
    };
    // Biome weather particles: a desert sand streak (gold) and a volcano ash
    // flake (dark), drawn by the same streak sprites as the storm rain.
    static const u32 sSandStreak[8] = {
        0x00000000, 0x00000000, 0x00099999, 0x09999A00, 0x0AA00000, 0x00000000, 0x00000000, 0x00000000,
    };
    static const u32 sAshFlake[8] = {
        0x00000000, 0x00030000, 0x00333000, 0x00030300, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
    };
    struct SpriteSheet sheet = {tiles, sizeof(tiles), LOOT_TAG};
    u32 t, x, y;
    // Code-native 16x16 gem per type: outline, body, shade, highlight.
    for (t = 0; t < LOOT_TYPES; t++)
        for (y = 0; y < 16; y++)
            for (x = 0; x < 16; x++)
            {
                s32 dx = (s32)x * 2 - 15, dy = (s32)y * 2 - 15;
                u32 d = Abs(dx) + Abs(dy);
                u32 c = 0;
                if (d <= 13) c = 5 + t * 2;
                if (d <= 13 && dx + dy > 4) c = 6 + t * 2;
                if (d > 13 && d <= 16) c = 3;
                if (d <= 5 && dx < 0 && dy < 0) c = 2;
                // Supplies read as a cross, caches as a gem with a bright core.
                if (t == LOOT_HEAL && d <= 11 && (Abs(dx) <= 1 || Abs(dy) <= 1)) c = 2;
                if (t == LOOT_CACHE && d <= 4) c = 2;
                // Readable marks: ATK up-arrow, DEF ring, SPD chevrons.
                if (t == 0 && ((Abs(dx) <= 1 && dy >= -7 && dy <= 7) || (dy == -8 + Abs(dx) && Abs(dx) <= 7))) c = 2;
                if (t == 1 && d >= 6 && d <= 8) c = 2;
                if (t == 2 && Abs(dy) <= 7 && (dx == 4 - Abs(dy) || dx == -2 - Abs(dy))) c = 2;
                if (c)
                {
                    u32 tile = t * 4 + (y / 8) * 2 + x / 8;
                    tiles[tile * 8 + y % 8] |= c << ((x % 8) * 4);
                }
            }
    memcpy(&tiles[LOOT_TYPES * 32], sRainStreak, sizeof(sRainStreak));
    memcpy(&tiles[LOOT_TYPES * 32 + 8], sSandStreak, sizeof(sSandStreak));
    memcpy(&tiles[LOOT_TYPES * 32 + 16], sAshFlake, sizeof(sAshFlake));
    LoadSpriteSheet(&sheet);
    (void)ownPal;   // OBJ palette slots are all needed by move effects: share
    sLootPal = 0xFF;
    gWildlandsLootPalDiag = IndexOfSpritePaletteTag(SHOT_TAG);
    LootAssertColors();
}

static void LootInit(void)
{
    u32 i;
    if (!sWildlandsEncounterLive)
    {
        memset(&sLoot, 0, sizeof(sLoot));
        memset(gWildlandsLootTelemetry, 0, sizeof(gWildlandsLootTelemetry));
    }
    for (i = 0; i < LOOT_SPRITES; i++) sLoot.sprite[i] = MAX_SPRITES;
    gWildlandsLootTelemetry[8] = ARRAY_COUNT(sLootSpots);
    if (!WildlandsWorld_Active())
        return;
    sLoot.live = TRUE;
    LootLoadGraphics();
    for (i = 0; i < LOOT_SPRITES; i++)
    {
        sLoot.sprite[i] = CreateSprite(&sLootTemplate, 0, 0, 3);
        if (sLoot.sprite[i] != MAX_SPRITES) { gSprites[sLoot.sprite[i]].invisible = TRUE; gSprites[sLoot.sprite[i]].animPaused = TRUE; gSprites[sLoot.sprite[i]].oam.paletteNum = LootPaletteNum(); }
    }
}

static void LootDestroy(void)
{
    u32 i;
    for (i = 0; i < LOOT_SPRITES; i++)
        if (sLoot.sprite[i] != MAX_SPRITES)
        { DestroySprite(&gSprites[sLoot.sprite[i]]); sLoot.sprite[i] = MAX_SPRITES; }
    FreeSpriteTilesByTag(LOOT_TAG);
    FreeSpritePaletteByTag(LOOT_TAG);
    sLootPal = 0xFF;
}

static const u8 sLootStats[3][2] = {{STAT_ATK, STAT_SPATK}, {STAT_DEF, STAT_SPDEF}, {STAT_SPEED, STAT_SPEED}};

static void LootStat(u8 team, u8 type)
{
    u32 m, k;
    sLoot.boost[team][type]++;
    for (m = 0; m < 2; m++)
    {
        u8 b = team + m * 2;
        for (k = 0; k < (type == LOOT_SPD ? 1u : 2u); k++)
            if (gBattleMons[b].statStages[sLootStats[type][k]] < MAX_STAT_STAGE)
                gBattleMons[b].statStages[sLootStats[type][k]]++;
    }
    gWildlandsLootTelemetry[1 + team * 3 + type] = sLoot.boost[team][type];
}

static bool8 LootUseless(u8 team, u8 type)
{
    // Beta: no dead pickups. A capped stat orb or cache heals the team
    // instead (LootApply), so every pickup is worth walking to.
    if (WildlandsWorld_Active())
        return FALSE;
    if (type < 3)
        return sLoot.boost[team][type] >= LOOT_CAP;
    if (type == LOOT_CACHE)
        return sLoot.boost[team][0] >= LOOT_CAP && sLoot.boost[team][1] >= LOOT_CAP
            && sLoot.boost[team][2] >= LOOT_CAP;
    return FALSE;
}

static void LootApply(u8 team, u8 type, s32 x, s32 y)
{
    u32 m, t;
    if (WildlandsWorld_Active() && ((type < 3 && sLoot.boost[team][type] >= LOOT_CAP)
        || (type == LOOT_CACHE && sLoot.boost[team][0] >= LOOT_CAP && sLoot.boost[team][1] >= LOOT_CAP
            && sLoot.boost[team][2] >= LOOT_CAP)))
        type = LOOT_HEAL;
    sLoot.popupTimer = 150;
    sLoot.popupType = type;
    sLoot.popupTeam = team;
    if (type == LOOT_HEAL)
    {
        gWildlandsLootTelemetry[12]++;
        for (m = 0; m < 2; m++)
        {
            u8 b = team + m * 2;
            u16 hp;
            if (!SquadAlive(b))
                continue;
            hp = min(gBattleMons[b].maxHP, gBattleMons[b].hp + gBattleMons[b].maxHP * 2 / 5);
            gBattleMons[b].hp = hp;
            SetMonData(SquadPartyMon(b), MON_DATA_HP, &hp);
            // Supplies cure status too (burn, poison, paralysis, sleep, freeze).
            if (gBattleMons[b].status1)
            {
                u32 none = 0;
                gBattleMons[b].status1 = 0;
                SetMonData(SquadPartyMon(b), MON_DATA_STATUS, &none);
                if (b < 2) sArena.bodies[b].burnClock = 0;
                gWildlandsStatusTelemetry[2]++;
            }
            // Supplies also restock PP (+4 per move, up to its maximum).
            {
                u32 k;
                for (k = 0; k < MAX_MON_MOVES; k++)
                {
                    u16 move = gBattleMons[b].moves[k];
                    u8 max, pp;
                    if (!move) continue;
                    max = CalculatePPWithBonus(move, gBattleMons[b].ppBonuses, k);
                    pp = min(max, gBattleMons[b].pp[k] + 4);
                    gBattleMons[b].pp[k] = pp;
                    SetMonData(SquadPartyMon(b), MON_DATA_PP1 + k, &pp);
                }
            }
        }
    }
    else if (type == LOOT_CACHE)
    {
        gWildlandsLootTelemetry[13]++;
        for (t = 0; t < 3; t++)
            if (sLoot.boost[team][t] < LOOT_CAP)
                LootStat(team, t);
    }
    else
        LootStat(team, type);
    {
        u8 logText[24];
        if (LootPopupText(logText))
            DirectorLog(logText);
    }
    for (m = 0; m < 2; m++)
    {
        u8 b = team + m * 2;
        if (SquadAlive(b))
        {
            s32 bx, by;
            SquadPos(b, &bx, &by);
            ArenaFeedback_Impact(b & 1, bx / Q, by / Q,
                (type == LOOT_HEAL ? STAT_DEF : type == LOOT_CACHE ? STAT_ATK : sLootStats[type][0]) | 256,
                ARENA_FEEDBACK_STAT);
        }
    }
    PlaySE(type >= LOOT_HEAL ? SE_EXP_MAX : SE_SUCCESS);
    sArena.hudDirty = TRUE;
}

// Simulation step: atomic pickups.
static void LootSim(void)
{
    u32 i, b;
    if (sLoot.live && !sArena.paused && !sArena.resultTimer && sLoot.popupTimer && !--sLoot.popupTimer)
        sArena.hudDirty = TRUE;
    {
    s32 ax[4], ay[4], x0 = 0x7FFF, x1 = -0x7FFF, y0 = 0x7FFF, y1 = -0x7FFF;
    bool8 alive[4];
    if (!sLoot.live || sArena.paused || sArena.resultTimer)
        return;
    // Pickup scan every other step (pickup radius 12px, actors move <= 6px
    // per step): halves the cost of 64 spots x 4 actors.
    if (sArena.frame & 1)
        return;
    for (b = 0; b < 4; b++)
    {
        alive[b] = SquadAlive(b);
        if (alive[b])
        {
            SquadPos(b, &ax[b], &ay[b]); ax[b] /= Q; ay[b] /= Q;
            if (ax[b] < x0) x0 = ax[b];
            if (ax[b] > x1) x1 = ax[b];
            if (ay[b] < y0) y0 = ay[b];
            if (ay[b] > y1) y1 = ay[b];
        }
    }
    x0 -= 12; x1 += 12; y0 -= 12; y1 += 12;
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < LOOT_MAX; i++)
    {
        const struct LootSpot *s = &sLootSpots[i];
        u8 winner = 0xFF, contenders = 0;
        u32 best = 0xFFFF;
        if (s->x < x0 || s->x > x1 || s->y < y0 || s->y > y1 || LootTaken(i))
            continue;
        for (b = 0; b < 4; b++)
        {
            u16 d;
            if (!alive[b] || Abs(ax[b] - s->x) > 12 || Abs(ay[b] - s->y) > 12)
                continue;
            d = ArenaNav_Distance(ax[b], ay[b], s->x, s->y);
            if (d > 12)
                continue;
            contenders++;
            if (d < best) { best = d; winner = b; } // strict: lower id keeps ties
        }
        if (winner == 0xFF)
            continue;
        if (contenders > 1) gWildlandsLootTelemetry[10]++;
        if (LootUseless(winner & 1, s->type))
        { gWildlandsLootTelemetry[7]++; continue; }
        if (LootTaken(i)) gWildlandsLootTelemetry[11]++;
        sLoot.collected[i >> 5] |= 1u << (i & 31);   // atomic: removed before any effect
        gWildlandsLootTelemetry[0]++;
        gWildlandsLootTelemetry[9] = winner;
        LootApply(winner & 1, s->type, s->x, s->y);
    }
    }
}

// Render step: only orbs inside the camera use one of the pooled sprites.
static void LootTick(void)
{
    u32 i, n = 0;
    if (!sLoot.live)
        return;
    if ((sArena.frame & 7) == 3)   // V6.4: periodic work staggered across frames
        LootAssertColors();
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < LOOT_MAX && n < LOOT_SPRITES; i++)
    {
        const struct LootSpot *s = &sLootSpots[i];
        if (s->x <= sArenaXLCameraX - 8 || s->x >= sArenaXLCameraX + 248
            || s->y <= sArenaXLCameraY - 8 || s->y >= sArenaXLCameraY + 168 || LootTaken(i))
            continue;
        if (sLoot.sprite[n] != MAX_SPRITES
            && s->x > sArenaXLCameraX - 8 && s->x < sArenaXLCameraX + 248
            && s->y > sArenaXLCameraY - 8 && s->y < sArenaXLCameraY + 168)
        {
            struct Sprite *spr = &gSprites[sLoot.sprite[n]];
            spr->x = s->x; spr->y = s->y - 2 + ((sArena.frame >> 4) & 1);
            spr->oam.tileNum = GetSpriteTileStartByTag(LOOT_TAG) + s->type * 4;
            spr->invisible = sArena.paused;
            n++;
        }
    }
    for (; n < LOOT_SPRITES; n++)
        if (sLoot.sprite[n] != MAX_SPRITES)
            gSprites[sLoot.sprite[n]].invisible = TRUE;
}

// Pickup popup for the bottom HUD line: "TEAM +1 ATK" / "FOES +1 SPD".
static bool8 LootPopupText(u8 *text)
{
    static const u8 sWho[2][6] = {_("TEAM "), _("FOES ")};
    static const u8 sStat[3][5] = {_(" ATK"), _(" DEF"), _(" SPD")};
    static const u8 sHeal[] = _("HEAL +PP +CURE");
    static const u8 sCache[] = _("+1 ATK DEF SPD");
    u8 *end;
    if (!sLoot.popupTimer)
        return FALSE;
    end = StringCopy(text, sWho[sLoot.popupTeam & 1]);
    if (sLoot.popupType == LOOT_HEAL) { StringCopy(end, sHeal); return TRUE; }
    if (sLoot.popupType == LOOT_CACHE) { StringCopy(end, sCache); return TRUE; }
    *end++ = CHAR_PLUS;
    *end++ = CHAR_0 + min(sLoot.boost[sLoot.popupTeam & 1][sLoot.popupType], 9);
    StringCopy(end, sStat[sLoot.popupType]);
    return TRUE;
}

static void LootHudText(u8 *text)
{
    u8 team = 0;
    text[0] = CHAR_A; text[1] = CHAR_0 + sLoot.boost[team][LOOT_ATK];
    text[2] = CHAR_D; text[3] = CHAR_0 + sLoot.boost[team][LOOT_DEF];
    text[4] = CHAR_S; text[5] = CHAR_0 + sLoot.boost[team][LOOT_SPD];
    text[6] = EOS;
}
