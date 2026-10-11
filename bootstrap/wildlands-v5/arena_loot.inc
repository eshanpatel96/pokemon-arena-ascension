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
#define LOOT_CAP 2
#define LOOT_TAG 0xA7C0
#define LOOT_SPRITES 4

struct LootSpot { s16 x, y; u8 type; };
static const struct LootSpot sLootSpots[] = {
#include "wildlands_loot.inc"
};

static EWRAM_DATA struct {
    u32 collected;
    u8 boost[2][3];
    u8 sprite[LOOT_SPRITES];
    u8 live;
} sLoot = {};
// [0] orbs collected [1..3] team0 atk/def/spd [4..6] team1 atk/def/spd
// [7] capped refusals [8] spot count [9] last collector battler
// [10] contested frames resolved [11] duplicate-collect attempts (must be 0)
EWRAM_DATA u32 gWildlandsLootTelemetry[12] = {};

static const struct OamData sLootOam = {.shape = SPRITE_SHAPE(16x16), .size = SPRITE_SIZE(16x16), .priority = 1};
static const struct SpriteTemplate sLootTemplate = {
    .tileTag = LOOT_TAG, .paletteTag = LOOT_TAG, .oam = &sLootOam,
    .anims = gDummySpriteAnimTable, .images = NULL, .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};
static const u16 sLootPalette[16] = {
    RGB(0, 0, 0), RGB(31, 31, 31), RGB(4, 4, 6),
    RGB(31, 8, 6), RGB(20, 2, 2),     // ATK red
    RGB(8, 16, 31), RGB(2, 6, 20),    // DEF blue
    RGB(31, 27, 4), RGB(20, 14, 0),   // SPD gold
};

static void LootLoadGraphics(void)
{
    u32 tiles[3 * 32] = {0};
    struct SpriteSheet sheet = {tiles, sizeof(tiles), LOOT_TAG};
    struct SpritePalette pal = {sLootPalette, LOOT_TAG};
    u32 t, x, y;
    // Code-native 16x16 gem per type: outline, body, shade, highlight.
    for (t = 0; t < 3; t++)
        for (y = 0; y < 16; y++)
            for (x = 0; x < 16; x++)
            {
                s32 dx = (s32)x * 2 - 15, dy = (s32)y * 2 - 15;
                u32 d = Abs(dx) + Abs(dy);
                u32 c = 0;
                if (d <= 13) c = 3 + t * 2;
                if (d <= 13 && dx + dy > 4) c = 4 + t * 2;
                if (d > 13 && d <= 16) c = 2;
                if (d <= 5 && dx < 0 && dy < 0) c = 1;
                if (c)
                {
                    u32 tile = t * 4 + (y / 8) * 2 + x / 8;
                    tiles[tile * 8 + y % 8] |= c << ((x % 8) * 4);
                }
            }
    LoadSpriteSheet(&sheet);
    LoadSpritePalette(&pal);
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
        if (sLoot.sprite[i] != MAX_SPRITES) { gSprites[sLoot.sprite[i]].invisible = TRUE; gSprites[sLoot.sprite[i]].animPaused = TRUE; }
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
}

static void LootApply(u8 team, u8 type, s32 x, s32 y)
{
    static const u8 sStats[3][2] = {{STAT_ATK, STAT_SPATK}, {STAT_DEF, STAT_SPDEF}, {STAT_SPEED, STAT_SPEED}};
    u32 m;
    sLoot.boost[team][type]++;
    for (m = 0; m < 2; m++)
    {
        u8 b = team + m * 2;
        u32 k;
        for (k = 0; k < (type == LOOT_SPD ? 1u : 2u); k++)
            if (gBattleMons[b].statStages[sStats[type][k]] < MAX_STAT_STAGE)
                gBattleMons[b].statStages[sStats[type][k]]++;
        if (SquadAlive(b))
        {
            s32 bx, by;
            SquadPos(b, &bx, &by);
            ArenaFeedback_Impact(b & 1, bx / Q, by / Q, sStats[type][0] | 256, ARENA_FEEDBACK_STAT);
        }
    }
    gWildlandsLootTelemetry[1 + team * 3 + type] = sLoot.boost[team][type];
    PlaySE(SE_SUCCESS);
    sArena.hudDirty = TRUE;
}

// Simulation step: atomic pickups.
static void LootSim(void)
{
    u32 i, b;
    if (!sLoot.live || sArena.paused || sArena.resultTimer)
        return;
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < 32; i++)
    {
        const struct LootSpot *s = &sLootSpots[i];
        u8 winner = 0xFF, contenders = 0;
        u32 best = 0xFFFF;
        if (sLoot.collected & (1u << i))
            continue;
        for (b = 0; b < 4; b++)
        {
            s32 x, y;
            u16 d;
            if (!SquadAlive(b))
                continue;
            SquadPos(b, &x, &y);
            d = ArenaNav_Distance(x / Q, y / Q, s->x, s->y);
            if (d > 12)
                continue;
            contenders++;
            if (d < best) { best = d; winner = b; } // strict: lower id keeps ties
        }
        if (winner == 0xFF)
            continue;
        if (contenders > 1) gWildlandsLootTelemetry[10]++;
        if (sLoot.boost[winner & 1][s->type] >= LOOT_CAP)
        { gWildlandsLootTelemetry[7]++; continue; }
        if (sLoot.collected & (1u << i)) gWildlandsLootTelemetry[11]++;
        sLoot.collected |= 1u << i;   // atomic: removed before any effect
        gWildlandsLootTelemetry[0]++;
        gWildlandsLootTelemetry[9] = winner;
        LootApply(winner & 1, s->type, s->x, s->y);
    }
}

// Render step: only orbs inside the camera use one of the pooled sprites.
static void LootTick(void)
{
    u32 i, n = 0;
    if (!sLoot.live)
        return;
    for (i = 0; i < ARRAY_COUNT(sLootSpots) && i < 32 && n < LOOT_SPRITES; i++)
    {
        const struct LootSpot *s = &sLootSpots[i];
        if (sLoot.collected & (1u << i))
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

static void LootHudText(u8 *text)
{
    u8 team = 0;
    text[0] = CHAR_A; text[1] = CHAR_0 + sLoot.boost[team][LOOT_ATK];
    text[2] = CHAR_D; text[3] = CHAR_0 + sLoot.boost[team][LOOT_DEF];
    text[4] = CHAR_S; text[5] = CHAR_0 + sLoot.boost[team][LOOT_SPD];
    text[6] = EOS;
}
