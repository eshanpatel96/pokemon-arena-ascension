#include "global.h"
#include "wildlands_v1.h"
#include "arena_moves.h"
#include "arena_sprites.h"
#include "arena_render.h"
#include "bg.h"
#include "battle_main.h"
#include "data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "field_message_box.h"
#include "field_effect.h"
#include "fieldmap.h"
#include "main.h"
#include "malloc.h"
#include "metatile_behavior.h"
#include "overworld.h"
#include "palette.h"
#include "pokemon.h"
#include "random.h"
#include "script.h"
#include "sound.h"
#include "task.h"
#include "text.h"
#include "window.h"
#include "menu.h"
#include "sprite.h"
#include "string_util.h"
#include "constants/event_objects.h"
#include "constants/field_effects.h"
#include "constants/maps.h"
#include "constants/moves.h"
#include "constants/rgb.h"
#include "constants/songs.h"
#include "constants/species.h"

#define WL_MAX_ACTORS 7
#define WL_MAX_SHOTS 12
#define WL_MAX_LOOT 4
#define WL_PLAYER 0
#define WL_PARTNER 1
#define WL_RAYQUAZA 6
#define WL_MON_TILE_TAG 0xB200
#define WL_MON_PAL_TAG 0xB240
#define WL_SHOT_TILE_TAG 0xB280
#define WL_SHOT_PAL_TAG 0xB281
#define WL_ALLY_TILE_TAG 0xB282
#define WL_ACTOR_PAL_BASE 8
#define WL_EFFECT_PAL 15
#define WL_Q 256
#define WL_BODY_RADIUS 10
#define WL_GRASS_HIDE_DISTANCE 56
#define WL_MIN_TEAM_SPAWN_TILES 18
#define WL_SPAWN_MIN_CONNECTED_TILES 36
#define WL_SPAWN_MIN_REACH_TILES 8
#define WL_LOADOUT_COUNT 16
#define WL_LOADOUT_MOVE_COUNT 6
#define WL_LOADOUT_NONE 0xFF
#define FACE_DOWN 0
#define FACE_RIGHT 2
#define FACE_UP 4
#define FACE_LEFT 6

struct WildActor
{
    bool8 active;
    bool8 ai;
    bool8 legendary;
    bool8 concealed;
    u8 team;
    u8 spriteId;
    u8 moveSlot;
    u8 facing;
    u8 revealTimer;
    u8 flash;
    u8 invuln;
    u8 attackTimer;
    u8 attackWindup;
    u8 attackMoveSlot;
    u8 attackElapsed;
    u8 attackTotal;
    u8 moving;
    u8 animation;
    u8 drawnFrame;
    u8 drawnDirection;
    u8 dash;
    s8 dashX;
    s8 dashY;
    s16 moveFracX;
    s16 moveFracY;
    u32 animClock;
    u16 species;
    u16 moves[4];
    u16 hp;
    u16 maxHp;
    u16 atk;
    u16 def;
    u16 cooldown;
    u16 dashCooldown;
    s32 x;
    s32 y;
    s16 attackX;
    s16 attackY;
    const struct ArenaSpriteSet *art;
};

struct WildShot
{
    bool8 active;
    u8 owner;
    u8 team;
    u8 spriteId;
    u8 life;
    u16 move;
    s32 x;
    s32 y;
    s16 vx;
    s16 vy;
};

struct WildLoot
{
    bool8 active;
    u8 kind;
    u8 spriteId;
    s16 x;
    s16 y;
};

static EWRAM_DATA struct WildActor sActors[WL_MAX_ACTORS] = {0};
static EWRAM_DATA struct WildShot sShots[WL_MAX_SHOTS] = {0};
static EWRAM_DATA struct WildLoot sLoot[WL_MAX_LOOT] = {0};
static EWRAM_DATA bool8 sInitialized = FALSE;
static EWRAM_DATA bool8 sRayquazaRecruitable = FALSE;
static EWRAM_DATA u8 sPartnerMarkerSprite = MAX_SPRITES;
static EWRAM_DATA u16 sFrames = 0;
static EWRAM_DATA u16 sWarmupTimer = 0;
EWRAM_DATA u8 gWildlandsSurfTransitions = 0;
EWRAM_DATA u8 gWildlandsSpawnAudit[4] = {0};
EWRAM_DATA u8 gWildlandsV2MotionAudit[6] = {0};
EWRAM_DATA u8 gWildlandsV2LoadoutAudit[4] = {0};
static EWRAM_DATA u16 sInputNewKeys = 0;
static EWRAM_DATA u16 sInputHeldKeys = 0;
static EWRAM_DATA bool8 sLoadoutPending = FALSE;
static EWRAM_DATA bool8 sLoadoutOpen = FALSE;
static EWRAM_DATA bool8 sLoadoutReady = FALSE;
static EWRAM_DATA u8 sLoadoutWindowId = WINDOW_NONE;
static EWRAM_DATA u8 sLoadoutPhase = 0;
static EWRAM_DATA u8 sLoadoutCursor = 0;
static EWRAM_DATA u8 sLoadoutMoveSlot = 0;
static EWRAM_DATA u16 sSelectedSpecies[2] = {SPECIES_CHARIZARD, SPECIES_BLASTOISE};
static EWRAM_DATA u16 sSelectedMoves[2][4] = {{0}};
static EWRAM_DATA u32 *sAnimScratch = NULL;

struct WildLoadoutChoice
{
    u16 species;
    u16 moves[WL_LOADOUT_MOVE_COUNT];
};

static const struct WildLoadoutChoice sLoadoutChoices[WL_LOADOUT_COUNT] =
{
    {SPECIES_CHARIZARD, {MOVE_FLAMETHROWER, MOVE_FIRE_BLAST, MOVE_WING_ATTACK, MOVE_AERIAL_ACE, MOVE_SLASH, MOVE_PROTECT}},
    {SPECIES_BLASTOISE, {MOVE_WATER_GUN, MOVE_HYDRO_PUMP, MOVE_SURF, MOVE_BITE, MOVE_ICY_WIND, MOVE_PROTECT}},
    {SPECIES_VENUSAUR, {MOVE_GIGA_DRAIN, MOVE_SOLAR_BEAM, MOVE_GROWTH, MOVE_BODY_SLAM, MOVE_TACKLE, MOVE_PROTECT}},
    {SPECIES_GENGAR, {MOVE_SHADOW_BALL, MOVE_SHADOW_PUNCH, MOVE_NIGHT_SHADE, MOVE_PSYCHIC, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
    {SPECIES_ALAKAZAM, {MOVE_PSYCHIC, MOVE_SHOCK_WAVE, MOVE_LIGHT_SCREEN, MOVE_REFLECT, MOVE_TELEPORT, MOVE_PROTECT}},
    {SPECIES_MACHAMP, {MOVE_CROSS_CHOP, MOVE_SEISMIC_TOSS, MOVE_BODY_SLAM, MOVE_ROCK_SLIDE, MOVE_FOCUS_ENERGY, MOVE_PROTECT}},
    {SPECIES_SNORLAX, {MOVE_BODY_SLAM, MOVE_SLAM, MOVE_ROLLOUT, MOVE_DEFENSE_CURL, MOVE_HYPER_BEAM, MOVE_PROTECT}},
    {SPECIES_DRAGONITE, {MOVE_DRAGON_CLAW, MOVE_WING_ATTACK, MOVE_SLAM, MOVE_HYPER_BEAM, MOVE_AGILITY, MOVE_PROTECT}},
    {SPECIES_TYRANITAR, {MOVE_CRUNCH, MOVE_ROCK_SLIDE, MOVE_ROCK_TOMB, MOVE_BITE, MOVE_HYPER_BEAM, MOVE_PROTECT}},
    {SPECIES_SCEPTILE, {MOVE_LEAF_BLADE, MOVE_GIGA_DRAIN, MOVE_QUICK_ATTACK, MOVE_AERIAL_ACE, MOVE_AGILITY, MOVE_PROTECT}},
    {SPECIES_BLAZIKEN, {MOVE_BLAZE_KICK, MOVE_FIRE_PUNCH, MOVE_MACH_PUNCH, MOVE_AERIAL_ACE, MOVE_SLASH, MOVE_PROTECT}},
    {SPECIES_SWAMPERT, {MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_MUD_SHOT, MOVE_ROCK_SLIDE, MOVE_SLAM, MOVE_PROTECT}},
    {SPECIES_GARDEVOIR, {MOVE_PSYCHIC, MOVE_SHOCK_WAVE, MOVE_REFLECT, MOVE_LIGHT_SCREEN, MOVE_DOUBLE_TEAM, MOVE_PROTECT}},
    {SPECIES_METAGROSS, {MOVE_METEOR_MASH, MOVE_PSYCHIC, MOVE_ROCK_SLIDE, MOVE_BODY_SLAM, MOVE_AGILITY, MOVE_PROTECT}},
    {SPECIES_SALAMENCE, {MOVE_DRAGON_CLAW, MOVE_AERIAL_ACE, MOVE_FLY, MOVE_CRUNCH, MOVE_FLAMETHROWER, MOVE_PROTECT}},
    {SPECIES_MILOTIC, {MOVE_SURF, MOVE_HYDRO_PUMP, MOVE_ICY_WIND, MOVE_AURORA_BEAM, MOVE_RAIN_DANCE, MOVE_PROTECT}},
};

static const u32 sShotTiles[8] =
{
    0x00022000, 0x00211200, 0x02111120, 0x21111112,
    0x21111112, 0x02111120, 0x00211200, 0x00022000
};
static const u16 sShotPalette[16] =
{
    RGB_BLACK, RGB_WHITE, RGB(31, 20, 4), RGB(7, 26, 31),
    RGB(18, 31, 10), RGB(27, 8, 31), RGB(31, 8, 8)
};
static const u32 sAllyTiles[8] =
{
    0x00033000, 0x00333300, 0x03333330, 0x33333333,
    0x03333330, 0x00333300, 0x00033000, 0x00000000
};
static const struct OamData sMonOam =
{
    .shape = SPRITE_SHAPE(64x64),
    .size = SPRITE_SIZE(64x64),
    .priority = 1,
};
static const struct OamData sShotOam =
{
    .shape = SPRITE_SHAPE(8x8),
    .size = SPRITE_SIZE(8x8),
    .priority = 0,
};
static const struct SpriteTemplate sMonTemplate =
{
    .tileTag = TAG_NONE,
    .paletteTag = TAG_NONE,
    .oam = &sMonOam,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};
static const struct SpriteSheet sShotSheet =
{
    sShotTiles, sizeof(sShotTiles), WL_SHOT_TILE_TAG
};
static const struct SpriteSheet sAllySheet =
{
    sAllyTiles, sizeof(sAllyTiles), WL_ALLY_TILE_TAG
};
static const struct SpriteTemplate sAllyTemplate =
{
    .tileTag = WL_ALLY_TILE_TAG,
    .paletteTag = TAG_NONE,
    .oam = &sShotOam,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};
static const struct SpriteTemplate sShotTemplate =
{
    .tileTag = WL_SHOT_TILE_TAG,
    .paletteTag = TAG_NONE,
    .oam = &sShotOam,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCallbackDummy,
};

static const u8 sTextHp[] = _("HP BOOST FOUND!$");
static const u8 sTextAtk[] = _("ATTACK BOOST FOUND!$");
static const u8 sTextDef[] = _("DEFENSE BOOST FOUND!$");
static const u8 sTextMove[] = _("MOVE LOOT: FIRE BLAST!$");
static const u8 sTextRay[] = _("RAYQUAZA JOINED YOUR TEAM!$");

static s32 Abs32(s32 n) { return n < 0 ? -n : n; }
static s32 Max32(s32 a, s32 b) { return a > b ? a : b; }
static s32 Min32(s32 a, s32 b) { return a < b ? a : b; }
static s32 Dist(s32 ax, s32 ay, s32 bx, s32 by)
{
    s32 dx = Abs32(ax - bx);
    s32 dy = Abs32(ay - by);
    return Max32(dx, dy) + Min32(dx, dy) / 2;
}

static bool8 OnWildlandsMap(void)
{
    return gSaveBlock1Ptr != NULL
        && gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE119)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ROUTE119);
}

bool8 WildlandsV1_IsActive(void)
{
    return OnWildlandsMap();
}

static bool8 IsWater(u8 behavior)
{
    return MetatileBehavior_IsSurfableWaterOrUnderwater(behavior)
        || MetatileBehavior_IsDeepOrOceanWater(behavior)
        || MetatileBehavior_IsShallowFlowingWater(behavior);
}

static bool8 IsGrass(u8 behavior)
{
    return MetatileBehavior_IsPokeGrass(behavior)
        || MetatileBehavior_IsTallGrass(behavior)
        || MetatileBehavior_IsLongGrass(behavior);
}


static const u8 sLoadoutTitlePlayer[] = _("WILDLANDS - PICK YOUR POKEMON");
static const u8 sLoadoutTitlePartner[] = _("WILDLANDS - PICK AI PARTNER");
static const u8 sLoadoutTitleMoves[] = _("PICK 4 MOVES");
static const u8 sLoadoutTitleConfirm[] = _("READY TO DEPLOY?");
static const u8 sLoadoutHintSpecies[] = _("< > CHANGE   A SELECT");
static const u8 sLoadoutHintMoves[] = _("< > MOVE   A ADD   B BACK");
static const u8 sLoadoutHintConfirm[] = _("A DEPLOY   B EDIT");
static const u8 sTraitFly[] = _("FLY");
static const u8 sTraitSwim[] = _("SWIM");
static const u8 sTraitBurrow[] = _("BURROW");
static const u8 sTraitLand[] = _("LAND");

static u8 FacingFromDelta(s32 dx, s32 dy)
{
    if (Abs32(dx) * 2 < Abs32(dy))
        return dy < 0 ? FACE_UP : FACE_DOWN;
    if (Abs32(dy) * 2 < Abs32(dx))
        return dx < 0 ? FACE_LEFT : FACE_RIGHT;
    return dy < 0 ? (dx < 0 ? 5 : 3) : (dx < 0 ? 7 : 1);
}

static const u8 *TraversalName(u16 species)
{
    if (CanFly(species))
        return sTraitFly;
    if (CanSwim(species))
        return sTraitSwim;
    if (CanBurrow(species))
        return sTraitBurrow;
    return sTraitLand;
}

static u8 FindLoadoutChoice(u16 species)
{
    u8 i;
    for (i = 0; i < WL_LOADOUT_COUNT; i++)
        if (sLoadoutChoices[i].species == species)
            return i;
    return 0;
}

static void LoadoutPrint(const u8 *text, u8 x, u8 y)
{
    AddTextPrinterParameterized(sLoadoutWindowId, FONT_NORMAL, text, x, y,
                                TEXT_SKIP_DRAW, NULL);
}

static void LoadoutPrintNumber(const u8 *label, s32 value, u8 x, u8 y)
{
    StringCopy(gStringVar4, label);
    ConvertIntToDecimalStringN(gStringVar1, value, STR_CONV_MODE_LEFT_ALIGN, 3);
    StringAppend(gStringVar4, gStringVar1);
    LoadoutPrint(gStringVar4, x, y);
}

static void DrawLoadout(void)
{
    const struct SpeciesInfo *info;
    u16 species;
    u8 side;
    u8 choice;
    u8 i;

    if (!sLoadoutOpen || sLoadoutWindowId == WINDOW_NONE)
        return;

    FillWindowPixelBuffer(sLoadoutWindowId, PIXEL_FILL(1));

    if (sLoadoutPhase <= 1)
    {
        species = sLoadoutChoices[sLoadoutCursor].species;
        info = &gSpeciesInfo[species];
        LoadoutPrint(sLoadoutPhase == 0 ? sLoadoutTitlePlayer : sLoadoutTitlePartner, 4, 2);
        LoadoutPrint(gSpeciesNames[species], 72, 22);
        LoadoutPrint(gTypeNames[info->types[0]], 12, 42);
        if (info->types[1] != info->types[0])
            LoadoutPrint(gTypeNames[info->types[1]], 100, 42);
        LoadoutPrintNumber(_("HP "), info->baseHP, 12, 62);
        LoadoutPrintNumber(_("ATK "), Max32(info->baseAttack, info->baseSpAttack), 100, 62);
        LoadoutPrintNumber(_("DEF "), Max32(info->baseDefense, info->baseSpDefense), 12, 80);
        LoadoutPrintNumber(_("SPD "), info->baseSpeed, 100, 80);
        LoadoutPrint(_("TRAVEL "), 12, 100);
        LoadoutPrint(TraversalName(species), 76, 100);
        LoadoutPrint(sLoadoutHintSpecies, 26, 124);
    }
    else if (sLoadoutPhase <= 3)
    {
        side = sLoadoutPhase - 2;
        choice = FindLoadoutChoice(sSelectedSpecies[side]);
        LoadoutPrint(sLoadoutTitleMoves, 70, 2);
        LoadoutPrint(gSpeciesNames[sSelectedSpecies[side]], 72, 20);
        LoadoutPrint(_("CANDIDATE"), 10, 40);
        LoadoutPrint(gMoveNames[sLoadoutChoices[choice].moves[sLoadoutCursor]], 92, 40);
        LoadoutPrint(gTypeNames[gBattleMoves[sLoadoutChoices[choice].moves[sLoadoutCursor]].type], 92, 56);
        for (i = 0; i < 4; i++)
        {
            ConvertIntToDecimalStringN(gStringVar1, i + 1, STR_CONV_MODE_LEFT_ALIGN, 1);
            StringCopy(gStringVar4, gStringVar1);
            StringAppend(gStringVar4, _(". "));
            if (i < sLoadoutMoveSlot)
                StringAppend(gStringVar4, gMoveNames[sSelectedMoves[side][i]]);
            else
                StringAppend(gStringVar4, _("---"));
            LoadoutPrint(gStringVar4, 20, 72 + i * 12);
        }
        LoadoutPrint(sLoadoutHintMoves, 14, 124);
    }
    else
    {
        LoadoutPrint(sLoadoutTitleConfirm, 66, 4);
        LoadoutPrint(_("YOU"), 20, 28);
        LoadoutPrint(gSpeciesNames[sSelectedSpecies[0]], 78, 28);
        LoadoutPrint(_("ALLY"), 20, 46);
        LoadoutPrint(gSpeciesNames[sSelectedSpecies[1]], 78, 46);
        LoadoutPrint(_("PLAYER MOVES"), 20, 68);
        for (i = 0; i < 4; i++)
            LoadoutPrint(gMoveNames[sSelectedMoves[0][i]], 34 + (i & 1) * 104, 84 + (i >> 1) * 14);
        LoadoutPrint(_("ALLY MOVES"), 20, 112);
        LoadoutPrint(sLoadoutHintConfirm, 128, 124);
    }

    PutWindowTilemap(sLoadoutWindowId);
    CopyWindowToVram(sLoadoutWindowId, COPYWIN_FULL);
}

static bool8 MoveAlreadyPicked(u8 side, u16 move)
{
    u8 i;
    for (i = 0; i < sLoadoutMoveSlot; i++)
        if (sSelectedMoves[side][i] == move)
            return TRUE;
    return FALSE;
}

static void ApplySelectedLoadout(void)
{
    u8 side;
    u8 slot;

    ZeroPlayerPartyMons();
    gPlayerPartyCount = 2;
    for (side = 0; side < 2; side++)
    {
        CreateMon(&gPlayerParty[side], sSelectedSpecies[side], 60,
                  20, TRUE, side * 2, OT_ID_PLAYER_ID, 0);
        for (slot = 0; slot < 4; slot++)
            SetMonMoveSlot(&gPlayerParty[side], sSelectedMoves[side][slot], slot);
    }

    gWildlandsV2LoadoutAudit[3] = 1;
    sLoadoutReady = TRUE;
    sLoadoutOpen = FALSE;
    if (sLoadoutWindowId != WINDOW_NONE)
    {
        ClearStdWindowAndFrameToTransparent(sLoadoutWindowId, TRUE);
        RemoveWindow(sLoadoutWindowId);
        sLoadoutWindowId = WINDOW_NONE;
    }
    UnlockPlayerFieldControls();
}

static void OpenLoadout(void)
{
    struct WindowTemplate window;

    if (sLoadoutOpen)
        return;

    window = CreateWindowTemplate(0, 1, 1, 28, 18, 15, 0x100);
    sLoadoutWindowId = AddWindow(&window);
    SetStandardWindowBorderStyle(sLoadoutWindowId, FALSE);
    sLoadoutOpen = TRUE;
    sLoadoutPending = FALSE;
    sLoadoutReady = FALSE;
    sLoadoutPhase = 0;
    sLoadoutCursor = 0;
    sLoadoutMoveSlot = 0;
    memset(sSelectedMoves, 0, sizeof(sSelectedMoves));
    gWildlandsV2LoadoutAudit[0] = 1;
    LockPlayerFieldControls();
    DrawLoadout();
}

void WildlandsV1_StartLoadout(void)
{
    sLoadoutPending = TRUE;
    sLoadoutReady = FALSE;
    memset(gWildlandsV2LoadoutAudit, 0, sizeof(gWildlandsV2LoadoutAudit));
}

static void HandleLoadoutInput(u16 newKeys)
{
    u8 side;
    u8 choice;
    u16 move;

    if (!sLoadoutOpen)
        return;

    if (sLoadoutPhase <= 1)
    {
        if (newKeys & DPAD_LEFT)
        {
            do
                sLoadoutCursor = (sLoadoutCursor + WL_LOADOUT_COUNT - 1) % WL_LOADOUT_COUNT;
            while (sLoadoutPhase == 1
                && sLoadoutChoices[sLoadoutCursor].species == sSelectedSpecies[0]);
            PlaySE(SE_SELECT);
            DrawLoadout();
        }
        else if (newKeys & DPAD_RIGHT)
        {
            do
                sLoadoutCursor = (sLoadoutCursor + 1) % WL_LOADOUT_COUNT;
            while (sLoadoutPhase == 1
                && sLoadoutChoices[sLoadoutCursor].species == sSelectedSpecies[0]);
            PlaySE(SE_SELECT);
            DrawLoadout();
        }
        else if (newKeys & A_BUTTON)
        {
            sSelectedSpecies[sLoadoutPhase] = sLoadoutChoices[sLoadoutCursor].species;
            gWildlandsV2LoadoutAudit[sLoadoutPhase + 1] = 1;
            sLoadoutPhase++;
            sLoadoutCursor = 0;
            if (sLoadoutPhase == 1
                && sLoadoutChoices[0].species == sSelectedSpecies[0])
                sLoadoutCursor = 1;
            if (sLoadoutPhase == 2)
                sLoadoutMoveSlot = 0;
            PlaySE(SE_SELECT);
            DrawLoadout();
        }
        else if ((newKeys & B_BUTTON) && sLoadoutPhase == 1)
        {
            sLoadoutPhase = 0;
            sLoadoutCursor = FindLoadoutChoice(sSelectedSpecies[0]);
            DrawLoadout();
        }
        return;
    }

    if (sLoadoutPhase <= 3)
    {
        side = sLoadoutPhase - 2;
        choice = FindLoadoutChoice(sSelectedSpecies[side]);
        if (newKeys & DPAD_LEFT)
        {
            sLoadoutCursor = (sLoadoutCursor + WL_LOADOUT_MOVE_COUNT - 1) % WL_LOADOUT_MOVE_COUNT;
            PlaySE(SE_SELECT);
            DrawLoadout();
        }
        else if (newKeys & DPAD_RIGHT)
        {
            sLoadoutCursor = (sLoadoutCursor + 1) % WL_LOADOUT_MOVE_COUNT;
            PlaySE(SE_SELECT);
            DrawLoadout();
        }
        else if (newKeys & A_BUTTON)
        {
            move = sLoadoutChoices[choice].moves[sLoadoutCursor];
            if (!MoveAlreadyPicked(side, move))
            {
                sSelectedMoves[side][sLoadoutMoveSlot++] = move;
                PlaySE(SE_SELECT);
                if (sLoadoutMoveSlot >= 4)
                {
                    sLoadoutPhase++;
                    sLoadoutMoveSlot = 0;
                    sLoadoutCursor = 0;
                }
                DrawLoadout();
            }
            else
                PlaySE(SE_FAILURE);
        }
        else if (newKeys & B_BUTTON)
        {
            if (sLoadoutMoveSlot)
            {
                sLoadoutMoveSlot--;
                sSelectedMoves[side][sLoadoutMoveSlot] = MOVE_NONE;
            }
            else if (sLoadoutPhase == 2)
            {
                sLoadoutPhase = 1;
                sLoadoutCursor = FindLoadoutChoice(sSelectedSpecies[1]);
            }
            else
            {
                sLoadoutPhase = 2;
                sLoadoutMoveSlot = 3;
                sLoadoutCursor = 0;
            }
            DrawLoadout();
        }
        return;
    }

    if (newKeys & A_BUTTON)
    {
        PlaySE(SE_SELECT);
        ApplySelectedLoadout();
    }
    else if (newKeys & B_BUTTON)
    {
        sLoadoutPhase = 3;
        sLoadoutMoveSlot = 3;
        sLoadoutCursor = 0;
        DrawLoadout();
    }
}

static bool8 SpawnLandTile(s16 x, s16 y)
{
    u8 behavior = MapGridGetMetatileBehaviorAt(x, y);
    return MapGridGetCollisionAt(x, y) == 0 && !IsWater(behavior);
}

// Bounded flood-fill at deployment time. A legal spawn must have enough
// connected dry land and must be able to reach meaningfully away from the
// starting tile without requiring Surf/Fly/Dig. This rejects trees, tiny
// ledges, shoreline pockets and small islands for every possible team comp.
static bool8 SpawnAreaSafe(s16 startX, s16 startY)
{
    s16 qx[64];
    s16 qy[64];
    u8 head = 0;
    u8 tail = 0;
    u8 i;
    u8 connected = 0;
    u8 farthest = 0;

    if (!SpawnLandTile(startX, startY))
        return FALSE;

    qx[tail] = startX;
    qy[tail] = startY;
    tail++;

    while (head < tail && tail < ARRAY_COUNT(qx))
    {
        s16 x = qx[head];
        s16 y = qy[head];
        static const s8 dirs[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
        u8 d;
        u8 dist;
        head++;
        connected++;
        dist = Abs32(x - startX) + Abs32(y - startY);
        if (dist > farthest)
            farthest = dist;

        for (d = 0; d < 4; d++)
        {
            s16 nx = x + dirs[d][0];
            s16 ny = y + dirs[d][1];
            bool8 seen = FALSE;
            if (!SpawnLandTile(nx, ny))
                continue;
            for (i = 0; i < tail; i++)
            {
                if (qx[i] == nx && qy[i] == ny)
                {
                    seen = TRUE;
                    break;
                }
            }
            if (!seen && tail < ARRAY_COUNT(qx))
            {
                qx[tail] = nx;
                qy[tail] = ny;
                tail++;
            }
        }
    }

    return connected >= WL_SPAWN_MIN_CONNECTED_TILES
        && farthest >= WL_SPAWN_MIN_REACH_TILES;
}

static bool8 FindSafeSpawnNear(s16 startX, s16 startY, s16 *outX, s16 *outY, u8 maxRadius)
{
    s16 radius;
    s16 dx;
    s16 dy;
    for (radius = 0; radius <= maxRadius; radius++)
    {
        for (dy = -radius; dy <= radius; dy++)
        {
            for (dx = -radius; dx <= radius; dx++)
            {
                if (radius && Abs32(dx) != radius && Abs32(dy) != radius)
                    continue;
                if (SpawnAreaSafe(startX + dx, startY + dy))
                {
                    *outX = startX + dx;
                    *outY = startY + dy;
                    return TRUE;
                }
            }
        }
    }
    return FALSE;
}

static bool8 SpawnFarFromOtherTeams(u8 actorId, s16 x, s16 y, u8 minTiles)
{
    u32 i;
    u8 seenTeams = 0;
    struct WildActor *actor = &sActors[actorId];
    for (i = 0; i < WL_MAX_ACTORS; i++)
    {
        s32 tx;
        s32 ty;
        if (i == actorId || !sActors[i].active
            || sActors[i].team == actor->team
            || sActors[i].team >= 8
            || (seenTeams & (1 << sActors[i].team)))
            continue;
        seenTeams |= 1 << sActors[i].team;
        tx = sActors[i].x / 16;
        ty = sActors[i].y / 16;
        if (Dist(x, y, tx, ty) < minTiles)
            return FALSE;
    }
    return TRUE;
}

static bool8 CanSwim(u16 species)
{
    switch (species)
    {
    case SPECIES_BLASTOISE:
    case SPECIES_SWAMPERT:
    case SPECIES_GYARADOS:
    case SPECIES_MILOTIC:
    case SPECIES_LAPRAS:
    case SPECIES_FERALIGATR:
    case SPECIES_KINGDRA:
        return TRUE;
    }
    return FALSE;
}

static bool8 CanFly(u16 species)
{
    switch (species)
    {
    case SPECIES_CHARIZARD:
    case SPECIES_DRAGONITE:
    case SPECIES_SALAMENCE:
    case SPECIES_CROBAT:
    case SPECIES_SKARMORY:
    case SPECIES_RAYQUAZA:
        return TRUE;
    }
    return FALSE;
}

static bool8 CanBurrow(u16 species)
{
    switch (species)
    {
    case SPECIES_DUGTRIO:
    case SPECIES_SANDSLASH:
    case SPECIES_FLYGON:
    case SPECIES_RHYDON:
        return TRUE;
    }
    return FALSE;
}

static bool8 ActorCanUseTile(const struct WildActor *actor, s16 px, s16 py)
{
    s16 tx = px / 16;
    s16 ty = py / 16;
    u8 behavior = MapGridGetMetatileBehaviorAt(tx, ty);
    if (IsWater(behavior))
        return CanSwim(actor->species) || CanFly(actor->species);
    return MapGridGetCollisionAt(tx, ty) == 0;
}

static void FreeActorArt(u8 id)
{
    if (sActors[id].spriteId < MAX_SPRITES && gSprites[sActors[id].spriteId].inUse)
        DestroySprite(&gSprites[sActors[id].spriteId]);
    FreeSpriteTilesByTag(WL_MON_TILE_TAG + id);
    sActors[id].spriteId = MAX_SPRITES;
}

static bool8 LoadActorArt(u8 id)
{
    struct WildActor *actor = &sActors[id];
    struct SpriteSheet sheet;
    struct SpriteTemplate tmpl = sMonTemplate;
    u32 *frameTiles;
    u8 spriteId;

    actor->art = ArenaSprites_Get(actor->species);
    if (actor->art == NULL)
        return FALSE;

    // ArenaSprites_Decode needs a 2 KB scratch frame, but LoadSpriteSheet copies
    // those bytes into OBJ VRAM immediately. Reuse the engine heap instead of
    // permanently reserving one 2 KB EWRAM frame for every active Pokemon.
    frameTiles = Alloc(2048);
    if (frameTiles == NULL)
        return FALSE;
    if (!ArenaSprites_Decode(&actor->art->animations[ARENA_ANIM_IDLE], 0, 0, frameTiles))
    {
        Free(frameTiles);
        return FALSE;
    }
    sheet.data = frameTiles;
    sheet.size = 2048;
    sheet.tag = WL_MON_TILE_TAG + id;
    if (LoadSpriteSheet(&sheet) == 0xFFFF)
    {
        Free(frameTiles);
        return FALSE;
    }
    Free(frameTiles);

    // Reserve OBJ palette banks 8-14 for the seven local Pokemon. The ordinary
    // overworld dynamic palette allocator can be exhausted even though those
    // hardware palette banks are available; the Arena renderer uses the same
    // direct-palette strategy for its battlers.
    LoadPalette(actor->art->palette, OBJ_PLTT_ID(WL_ACTOR_PAL_BASE + id), PLTT_SIZE_4BPP);
    tmpl.tileTag = sheet.tag;
    tmpl.paletteTag = TAG_NONE;
    spriteId = CreateSprite(&tmpl, 120, 80, 1);
    if (spriteId == MAX_SPRITES)
    {
        FreeSpriteTilesByTag(sheet.tag);
        return FALSE;
    }
    actor->spriteId = spriteId;
    gSprites[spriteId].oam.paletteNum = WL_ACTOR_PAL_BASE + id;
    gSprites[spriteId].coordOffsetEnabled = TRUE;
    return TRUE;
}

static void ConfigureStats(struct WildActor *actor)
{
    const struct SpeciesInfo *base = &gSpeciesInfo[actor->species];
    actor->maxHp = 120 + base->baseHP;
    actor->hp = actor->maxHp;
    actor->atk = (base->baseAttack + base->baseSpAttack) / 2 + 40;
    actor->def = (base->baseDefense + base->baseSpDefense) / 2 + 40;
}

static void InitActor(u8 id, u16 species, u8 team, bool8 ai, bool8 legendary,
                      s16 mapX, s16 mapY, u16 m0, u16 m1, u16 m2, u16 m3)
{
    struct WildActor *actor = &sActors[id];
    if (actor->spriteId < MAX_SPRITES && gSprites[actor->spriteId].inUse)
        FreeActorArt(id);
    memset(actor, 0, sizeof(*actor));
    actor->active = TRUE;
    actor->species = species;
    actor->team = team;
    actor->ai = ai;
    actor->legendary = legendary;
    actor->spriteId = MAX_SPRITES;
    actor->moves[0] = m0;
    actor->moves[1] = m1;
    actor->moves[2] = m2;
    actor->moves[3] = m3;
    actor->moveSlot = 0;
    actor->x = mapX * 16 + 8;
    actor->y = mapY * 16 + 8;
    actor->facing = DIR_SOUTH;
    ConfigureStats(actor);
    if (!LoadActorArt(id))
        actor->active = FALSE;
}

static void InitLoot(void)
{
    static const s16 pos[WL_MAX_LOOT][2] =
    {
        {12 + MAP_OFFSET, 121 + MAP_OFFSET},
        {33 + MAP_OFFSET, 117 + MAP_OFFSET},
        {4 + MAP_OFFSET, 96 + MAP_OFFSET},
        {29 + MAP_OFFSET, 53 + MAP_OFFSET},
    };
    u32 i;
    for (i = 0; i < WL_MAX_LOOT; i++)
    {
        sLoot[i].active = TRUE;
        sLoot[i].kind = i;
        sLoot[i].x = pos[i][0];
        sLoot[i].y = pos[i][1];
        sLoot[i].spriteId = CreateObjectGraphicsSprite(OBJ_EVENT_GFX_ITEM_BALL,
                                                       SpriteCallbackDummy, 0, 0, 1);
        if (sLoot[i].spriteId < MAX_SPRITES)
            gSprites[sLoot[i].spriteId].coordOffsetEnabled = TRUE;
    }
}

static void PositionMapSprite(u8 spriteId, s32 px, s32 py, s8 yLift)
{
    s16 tx = px / 16;
    s16 ty = py / 16;
    s16 dx = 8 + (px & 15);
    s16 dy = 8 + (py & 15) + yLift;
    SetSpritePosToOffsetMapCoords(&tx, &ty, dx, dy);
    gSprites[spriteId].x = tx;
    gSprites[spriteId].y = ty;
}

void WildlandsV1_PreOam(void)
{
    u32 i;
    bool8 mounted;
    struct ObjectEvent *playerObj;
    struct Sprite *playerSprite;
    s32 playerX;
    s32 playerY;

    if (!sInitialized || !OnWildlandsMap() || gPlayerAvatar.spriteId >= MAX_SPRITES)
        return;

    playerObj = &gObjectEvents[gPlayerAvatar.objectEventId];
    playerSprite = &gSprites[gPlayerAvatar.spriteId];

    // Emerald's overworld palette allocator can reuse hardware OBJ banks after
    // map setup/field effects. Restore the banks reserved by Wildlands before
    // this frame's OAM commit; UpdatePaletteFade runs immediately afterward.
    for (i = 0; i < WL_MAX_ACTORS; i++)
        if (sActors[i].active && sActors[i].art != NULL)
            LoadPalette(sActors[i].art->palette,
                        OBJ_PLTT_ID(WL_ACTOR_PAL_BASE + i), PLTT_SIZE_4BPP);
    LoadPalette(sShotPalette, OBJ_PLTT_ID(WL_EFFECT_PAL), PLTT_SIZE_4BPP);

    playerX = playerObj->currentCoords.x * 16 + 8;
    playerY = playerObj->currentCoords.y * 16 + 8;
    mounted = TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING)
        && sActors[WL_PARTNER].active
        && (CanSwim(sActors[WL_PARTNER].species) || CanFly(sActors[WL_PARTNER].species));

    sActors[WL_PLAYER].x = playerX;
    sActors[WL_PLAYER].y = playerY;

    // The native player object remains the collision/camera anchor but must never
    // be rendered in Wildlands. Do this after AnimateSprites and CameraUpdate so
    // Emerald cannot restore the trainer sprite later in the frame.
    playerSprite->invisible = TRUE;

    if (sActors[WL_PLAYER].active && sActors[WL_PLAYER].spriteId < MAX_SPRITES)
    {
        struct Sprite *sprite = &gSprites[sActors[WL_PLAYER].spriteId];
        sprite->coordOffsetEnabled = FALSE;
        sprite->x = playerSprite->x;
        sprite->y = playerSprite->y - 12;
        sprite->invisible = mounted;
    }

    if (mounted)
    {
        // During partner Surf, the teammate becomes the visible mount/body.
        sActors[WL_PARTNER].x = playerX;
        sActors[WL_PARTNER].y = playerY;
        if (playerObj->fieldEffectSpriteId < MAX_SPRITES
            && gSprites[playerObj->fieldEffectSpriteId].inUse)
            gSprites[playerObj->fieldEffectSpriteId].invisible = TRUE;
    }

    for (i = 1; i < WL_MAX_ACTORS; i++)
    {
        struct WildActor *actor = &sActors[i];
        if (!actor->active || actor->spriteId >= MAX_SPRITES)
            continue;
        if (mounted && i == WL_PARTNER)
        {
            struct Sprite *sprite = &gSprites[actor->spriteId];
            sprite->coordOffsetEnabled = FALSE;
            sprite->x = playerSprite->x;
            sprite->y = playerSprite->y - 12;
            sprite->invisible = FALSE;
        }
        else
        {
            PositionMapSprite(actor->spriteId, actor->x, actor->y, -12);
            gSprites[actor->spriteId].invisible = actor->concealed && actor->team != 0
                && Dist(actor->x, actor->y, playerX, playerY) > WL_GRASS_HIDE_DISTANCE;
        }
        if (actor->flash)
            gSprites[actor->spriteId].invisible ^= (sFrames & 2) != 0;
    }

    // Persistent cyan ally marker: always identifies the current AI teammate,
    // including a recruited Rayquaza and while moving through tall grass.
    if (sPartnerMarkerSprite < MAX_SPRITES && sActors[WL_PARTNER].active)
    {
        if (mounted)
        {
            gSprites[sPartnerMarkerSprite].coordOffsetEnabled = FALSE;
            gSprites[sPartnerMarkerSprite].x = playerSprite->x + 22;
            gSprites[sPartnerMarkerSprite].y = playerSprite->y - 30;
        }
        else
        {
            gSprites[sPartnerMarkerSprite].coordOffsetEnabled = TRUE;
            PositionMapSprite(sPartnerMarkerSprite,
                              sActors[WL_PARTNER].x + 20, sActors[WL_PARTNER].y, -28);
        }
        gSprites[sPartnerMarkerSprite].invisible = FALSE;
    }
    else if (sPartnerMarkerSprite < MAX_SPRITES)
        gSprites[sPartnerMarkerSprite].invisible = TRUE;

    for (i = 0; i < WL_MAX_SHOTS; i++)
        if (sShots[i].active && sShots[i].spriteId < MAX_SPRITES)
            PositionMapSprite(sShots[i].spriteId, sShots[i].x, sShots[i].y, -4);

    for (i = 0; i < WL_MAX_LOOT; i++)
        if (sLoot[i].active && sLoot[i].spriteId < MAX_SPRITES)
            PositionMapSprite(sLoot[i].spriteId, sLoot[i].x * 16 + 8, sLoot[i].y * 16 + 8, -8);
}

static u16 TypeMultiplier(u16 move, u16 species)
{
    u32 i;
    u16 mult = 100;
    u8 type = gBattleMoves[move].type;
    const struct SpeciesInfo *target = &gSpeciesInfo[species];
    for (i = 0; i < sizeof(gTypeEffectiveness); i += 3)
    {
        u8 attack = TYPE_EFFECT_ATK_TYPE(i);
        u8 defense = TYPE_EFFECT_DEF_TYPE(i);
        if (attack == TYPE_ENDTABLE)
            break;
        if (attack == TYPE_FORESIGHT)
            continue;
        if (attack == type && (defense == target->types[0] || defense == target->types[1]))
            mult = mult * TYPE_EFFECT_MULTIPLIER(i) / 10;
    }
    return mult;
}

static void DamageActor(u8 source, u8 target, u16 move)
{
    struct WildActor *a = &sActors[source];
    struct WildActor *b = &sActors[target];
    s32 damage;
    u16 mult;
    if (!a->active || !b->active || b->invuln)
        return;
    mult = TypeMultiplier(move, b->species);
    if (mult == 0)
        return;
    damage = gBattleMoves[move].power / 2 + a->atk / 5 - b->def / 8;
    if (damage < 3)
        damage = 3;
    damage = damage * mult / 100;
    if (damage < 1)
        damage = 1;
    if (damage > b->hp)
        damage = b->hp;
    b->hp -= damage;
    b->flash = 12;
    b->revealTimer = 90;
    PlaySE(SE_M_COMET_PUNCH);
    if (b->hp == 0)
    {
        b->active = FALSE;
        if (b->spriteId < MAX_SPRITES)
            gSprites[b->spriteId].invisible = TRUE;
        if (target == WL_RAYQUAZA)
            sRayquazaRecruitable = TRUE;
    }
}

static s8 FindNearestEnemy(u8 source, s32 maxDistance)
{
    u32 i;
    s8 bestId = -1;
    s32 best = maxDistance + 1;
    struct WildActor *actor = &sActors[source];
    for (i = 0; i < WL_MAX_ACTORS; i++)
    {
        s32 d;
        if (i == source || !sActors[i].active || sActors[i].team == actor->team)
            continue;
        d = Dist(actor->x, actor->y, sActors[i].x, sActors[i].y);
        if (sActors[i].concealed && sActors[i].revealTimer == 0 && d > WL_GRASS_HIDE_DISTANCE)
            continue;
        if (d < best)
        {
            best = d;
            bestId = i;
        }
    }
    return bestId;
}

static void NormalizeAim(s32 dx, s32 dy, s16 *outX, s16 *outY)
{
    s32 len = Max32(Abs32(dx), Abs32(dy)) + Min32(Abs32(dx), Abs32(dy)) / 2;
    if (len < 1)
    {
        *outX = 0;
        *outY = -WL_Q;
        return;
    }
    *outX = dx * WL_Q / len;
    *outY = dy * WL_Q / len;
}

static void PlayerAim(s16 *x, s16 *y)
{
    switch (GetPlayerFacingDirection())
    {
    case DIR_NORTH: *x = 0; *y = -WL_Q; break;
    case DIR_SOUTH: *x = 0; *y = WL_Q; break;
    case DIR_WEST:  *x = -WL_Q; *y = 0; break;
    default:        *x = WL_Q; *y = 0; break;
    }
}

static void SpawnShot(u8 owner, u16 move, s16 aimX, s16 aimY)
{
    u32 i;
    const struct ArenaMoveProfile *profile = ArenaMoves_Get(move);
    if (profile == NULL)
        return;
    for (i = 0; i < WL_MAX_SHOTS; i++)
        if (!sShots[i].active)
            break;
    if (i == WL_MAX_SHOTS)
        return;
    memset(&sShots[i], 0, sizeof(sShots[i]));
    sShots[i].active = TRUE;
    sShots[i].owner = owner;
    sShots[i].team = sActors[owner].team;
    sShots[i].move = move;
    sShots[i].x = sActors[owner].x;
    sShots[i].y = sActors[owner].y - 8;
    sShots[i].vx = aimX * Max32(2, profile->speed / WL_Q) / WL_Q;
    sShots[i].vy = aimY * Max32(2, profile->speed / WL_Q) / WL_Q;
    if (profile->speed == 0)
    {
        sShots[i].vx = aimX * 4 / WL_Q;
        sShots[i].vy = aimY * 4 / WL_Q;
    }
    sShots[i].life = Min32(60, Max32(12, profile->range / Max32(1, Max32(Abs32(sShots[i].vx), Abs32(sShots[i].vy)))));
    sShots[i].spriteId = CreateSprite(&sShotTemplate, 120, 80, 0);
    if (sShots[i].spriteId == MAX_SPRITES)
        sShots[i].active = FALSE;
    else
    {
        gSprites[sShots[i].spriteId].oam.paletteNum = WL_EFFECT_PAL;
        gSprites[sShots[i].spriteId].coordOffsetEnabled = TRUE;
    }
}

static void ResolveDirectAttack(u8 owner, u16 move, s16 aimX, s16 aimY)
{
    u32 i;
    const struct ArenaMoveProfile *profile = ArenaMoves_Get(move);
    if (profile == NULL)
        return;
    for (i = 0; i < WL_MAX_ACTORS; i++)
    {
        s32 dx, dy;
        if (!sActors[i].active || sActors[i].team == sActors[owner].team || i == owner)
            continue;
        dx = sActors[i].x - sActors[owner].x;
        dy = sActors[i].y - sActors[owner].y;
        if (Dist(0, 0, dx, dy) > profile->range)
            continue;
        if (profile->kind == ARENA_MOVE_CONE)
        {
            if (!ArenaMoves_InCone(dx, dy, aimX, aimY, profile->range, profile->cone))
                continue;
        }
        else if (dx * aimX + dy * aimY <= 0)
            continue;
        DamageActor(owner, i, move);
        if (profile->kind != ARENA_MOVE_CONE)
            break;
    }
}

static void FireAttack(u8 id)
{
    struct WildActor *actor = &sActors[id];
    u16 move = actor->moves[actor->attackMoveSlot];
    const struct ArenaMoveProfile *profile = ArenaMoves_Get(move);
    if (profile == NULL)
        return;
    actor->revealTimer = 90;
    if (profile->kind == ARENA_MOVE_PROJECTILE || profile->kind == ARENA_MOVE_RUSH)
        SpawnShot(id, move, actor->attackX, actor->attackY);
    else if (profile->kind == ARENA_MOVE_MELEE || profile->kind == ARENA_MOVE_CONE)
        ResolveDirectAttack(id, move, actor->attackX, actor->attackY);
    else if (profile->kind == ARENA_MOVE_SELF)
    {
        if (move == MOVE_PROTECT)
            actor->invuln = 45;
        else if (move == MOVE_AGILITY)
            actor->dashCooldown = 0;
    }
}

static void BeginAttack(u8 id, s16 aimX, s16 aimY)
{
    struct WildActor *actor = &sActors[id];
    const struct ArenaMoveProfile *profile;
    u16 move;
    if (!actor->active || actor->cooldown || actor->attackTimer)
        return;
    move = actor->moves[actor->moveSlot];
    profile = ArenaMoves_Get(move);
    if (profile == NULL)
        return;
    actor->attackMoveSlot = actor->moveSlot;
    actor->attackX = aimX;
    actor->attackY = aimY;
    actor->attackWindup = profile->windup;
    actor->attackTimer = profile->windup + 1;
    actor->cooldown = profile->windup + profile->active + profile->recovery;
    if (profile->windup == 0)
    {
        FireAttack(id);
        actor->attackTimer = 0;
    }
}

static void TickActorAttack(u8 id)
{
    struct WildActor *actor = &sActors[id];
    if (actor->cooldown)
        actor->cooldown--;
    if (actor->dashCooldown)
        actor->dashCooldown--;
    if (actor->invuln)
        actor->invuln--;
    if (actor->flash)
        actor->flash--;
    if (actor->revealTimer)
        actor->revealTimer--;
    if (actor->attackTimer)
    {
        actor->attackTimer--;
        if (actor->attackTimer == 1)
            FireAttack(id);
    }
}

static void TickShots(void)
{
    u32 i, j;
    for (i = 0; i < WL_MAX_SHOTS; i++)
    {
        struct WildShot *shot = &sShots[i];
        s32 oldX, oldY;
        if (!shot->active)
            continue;
        oldX = shot->x;
        oldY = shot->y;
        shot->x += shot->vx;
        shot->y += shot->vy;
        for (j = 0; j < WL_MAX_ACTORS; j++)
        {
            if (!sActors[j].active || sActors[j].team == shot->team)
                continue;
            if (ArenaMoves_SegmentHit(oldX, oldY, shot->x, shot->y,
                                      sActors[j].x, sActors[j].y, WL_BODY_RADIUS))
            {
                DamageActor(shot->owner, j, shot->move);
                shot->life = 0;
                break;
            }
        }
        if (MapGridGetCollisionAt(shot->x / 16, shot->y / 16) && !IsWater(MapGridGetMetatileBehaviorAt(shot->x / 16, shot->y / 16)))
            shot->life = 0;
        if (shot->life)
            shot->life--;
        if (!shot->life)
        {
            shot->active = FALSE;
            if (shot->spriteId < MAX_SPRITES)
                DestroySprite(&gSprites[shot->spriteId]);
            shot->spriteId = MAX_SPRITES;
        }
    }
}

static void PartnerFormationTarget(s32 *x, s32 *y)
{
    // Keep the AI teammate visually distinct from the player rather than
    // stacking two 64x64 PMD bodies on the same collision anchor.
    *x = sActors[WL_PLAYER].x - 40;
    *y = sActors[WL_PLAYER].y + 24;
}

static void MoveActorToward(u8 id, s32 tx, s32 ty, s16 speed)
{
    struct WildActor *actor = &sActors[id];
    s32 dx = tx - actor->x;
    s32 dy = ty - actor->y;
    s32 len = Max32(Abs32(dx), Abs32(dy)) + Min32(Abs32(dx), Abs32(dy)) / 2;
    s16 mx, my;
    if (len < 1)
        return;
    mx = dx * speed / len;
    my = dy * speed / len;
    if (ActorCanUseTile(actor, actor->x + mx, actor->y))
        actor->x += mx;
    if (ActorCanUseTile(actor, actor->x, actor->y + my))
        actor->y += my;
}

static void TickAI(u8 id)
{
    struct WildActor *actor = &sActors[id];
    s8 target;
    const struct ArenaMoveProfile *profile;
    s32 distance;
    s16 ax, ay;
    if (!actor->active || !actor->ai || actor->attackTimer)
        return;
    if (id == WL_PARTNER && TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING))
        return;
    if (id == WL_PARTNER)
    {
        s32 followX;
        s32 followY;
        PartnerFormationTarget(&followX, &followY);
        distance = Dist(actor->x, actor->y, sActors[WL_PLAYER].x, sActors[WL_PLAYER].y);
        if (distance > 72)
        {
            MoveActorToward(id, followX, followY, 3);
            return;
        }
        target = FindNearestEnemy(id, 96);
        if (target < 0)
        {
            if (Dist(actor->x, actor->y, followX, followY) > 18)
                MoveActorToward(id, followX, followY, 2);
            return;
        }
    }
    else
        target = FindNearestEnemy(id, actor->legendary ? 220 : 150);
    if (target < 0)
        return;
    profile = ArenaMoves_Get(actor->moves[actor->moveSlot]);
    if (profile == NULL)
        return;
    distance = Dist(actor->x, actor->y, sActors[target].x, sActors[target].y);
    if (distance > profile->range * 3 / 4)
        MoveActorToward(id, sActors[target].x, sActors[target].y, actor->legendary ? 2 : 1);
    if (!actor->cooldown && distance <= profile->range)
    {
        NormalizeAim(sActors[target].x - actor->x, sActors[target].y - actor->y, &ax, &ay);
        BeginAttack(id, ax, ay);
        actor->moveSlot = (actor->moveSlot + 1) & 3;
    }
}

static void UpdateConcealment(void)
{
    u32 i;
    for (i = 0; i < WL_MAX_ACTORS; i++)
    {
        struct WildActor *actor = &sActors[i];
        u8 behavior;
        if (!actor->active)
            continue;
        behavior = MapGridGetMetatileBehaviorAt(actor->x / 16, actor->y / 16);
        actor->concealed = IsGrass(behavior) && actor->revealTimer == 0;
    }
}

static void TickPlayerInput(void)
{
    s16 ax, ay;
    struct WildActor *player = &sActors[WL_PLAYER];
    if (JOY_NEW(L_BUTTON))
        player->moveSlot = (player->moveSlot + 3) & 3;
    if (JOY_NEW(R_BUTTON))
        player->moveSlot = (player->moveSlot + 1) & 3;
    if (JOY_NEW(A_BUTTON) && !ArePlayerFieldControlsLocked())
    {
        PlayerAim(&ax, &ay);
        BeginAttack(WL_PLAYER, ax, ay);
    }
    if ((gMain.heldKeys & B_BUTTON) && (gMain.heldKeys & (DPAD_UP | DPAD_DOWN | DPAD_LEFT | DPAD_RIGHT))
        && !player->dashCooldown)
    {
        player->invuln = 8;
        player->dashCooldown = 45;
    }
}

static bool8 NearPlayer(s32 px, s32 py, s32 dist)
{
    return Dist(sActors[WL_PLAYER].x, sActors[WL_PLAYER].y, px, py) <= dist;
}

static bool8 TryLoot(void)
{
    u32 i;
    for (i = 0; i < WL_MAX_LOOT; i++)
    {
        struct WildLoot *loot = &sLoot[i];
        struct WildActor *p = &sActors[WL_PLAYER];
        if (!loot->active || !NearPlayer(loot->x * 16 + 8, loot->y * 16 + 8, 28))
            continue;
        loot->active = FALSE;
        if (loot->spriteId < MAX_SPRITES)
            DestroySprite(&gSprites[loot->spriteId]);
        switch (loot->kind)
        {
        case 0:
            p->maxHp += 30;
            p->hp += 30;
            ShowFieldMessage(sTextHp);
            break;
        case 1:
            p->moves[p->moveSlot] = MOVE_FIRE_BLAST;
            ShowFieldMessage(sTextMove);
            break;
        case 2:
            p->atk += 18;
            ShowFieldMessage(sTextAtk);
            break;
        default:
            p->def += 18;
            ShowFieldMessage(sTextDef);
            break;
        }
        return TRUE;
    }
    return FALSE;
}

static bool8 TryRecruitRayquaza(void)
{
    if (!sRayquazaRecruitable
        || !NearPlayer(sActors[WL_RAYQUAZA].x, sActors[WL_RAYQUAZA].y, 42))
        return FALSE;
    sRayquazaRecruitable = FALSE;
    InitActor(WL_PARTNER, SPECIES_RAYQUAZA, 0, TRUE, FALSE,
              sActors[WL_PLAYER].x / 16 + 1, sActors[WL_PLAYER].y / 16,
              MOVE_DRAGON_CLAW, MOVE_EXTREME_SPEED, MOVE_FLY, MOVE_HYPER_BEAM);
    sActors[WL_PARTNER].hp = sActors[WL_PARTNER].maxHp * 2 / 3;
    ShowFieldMessage(sTextRay);
    return TRUE;
}

static bool8 TryTraversal(void)
{
    s16 x, y;
    u8 behavior;

    // Wildlands owns traversal eligibility. Read the actual tile directly in
    // front of the player rather than Emerald's Surf helper, which also encodes
    // story-era elevation/HM assumptions that do not belong in a battle royale.
    PlayerGetDestCoords(&x, &y);
    behavior = MapGridGetMetatileBehaviorAt(x, y);
    if (!TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING)
        && IsWater(behavior)
        && sActors[WL_PARTNER].active
        && (CanSwim(sActors[WL_PARTNER].species) || CanFly(sActors[WL_PARTNER].species)))
    {
        SetPlayerAvatarTransitionFlags(PLAYER_AVATAR_FLAG_SURFING);
        gWildlandsSurfTransitions++;
        return TRUE;
    }
    if ((CanBurrow(sActors[WL_PLAYER].species) || CanBurrow(sActors[WL_PARTNER].species)
         || sActors[WL_PLAYER].moves[0] == MOVE_DIG || sActors[WL_PLAYER].moves[1] == MOVE_DIG
         || sActors[WL_PLAYER].moves[2] == MOVE_DIG || sActors[WL_PLAYER].moves[3] == MOVE_DIG)
        && (MetatileBehavior_IsSandOrDeepSand(behavior) || MetatileBehavior_IsMountain(behavior)))
    {
        // V1 burrow shortcut: two distant soft-ground checkpoints on Route 119.
        // Same-map warp keeps the BR simulation alive; V1.1 will replace the
        // instant relocation with a short visible dirt-trail traversal state.
        if (y > 105 + MAP_OFFSET)
        {
            SetWarpDestination(MAP_GROUP(MAP_ROUTE119), MAP_NUM(MAP_ROUTE119), WARP_ID_NONE, 8, 58);
            WarpIntoMap();
            return TRUE;
        }
        if (y < 70 + MAP_OFFSET)
        {
            SetWarpDestination(MAP_GROUP(MAP_ROUTE119), MAP_NUM(MAP_ROUTE119), WARP_ID_NONE, 19, 130);
            WarpIntoMap();
            return TRUE;
        }
    }
    return FALSE;
}

static void TickContextAction(void)
{
    if (!JOY_NEW(SELECT_BUTTON) || ArePlayerFieldControlsLocked())
        return;
    if (TryLoot())
        return;
    if (TryRecruitRayquaza())
        return;
    TryTraversal();
}

static void DestroyAll(void)
{
    u32 i;
    for (i = 0; i < WL_MAX_ACTORS; i++)
        if (sActors[i].spriteId < MAX_SPRITES && gSprites[sActors[i].spriteId].inUse)
            FreeActorArt(i);
    for (i = 0; i < WL_MAX_SHOTS; i++)
        if (sShots[i].active && sShots[i].spriteId < MAX_SPRITES)
            DestroySprite(&gSprites[sShots[i].spriteId]);
    for (i = 0; i < WL_MAX_LOOT; i++)
        if (sLoot[i].active && sLoot[i].spriteId < MAX_SPRITES)
            DestroySprite(&gSprites[sLoot[i].spriteId]);
    if (sPartnerMarkerSprite < MAX_SPRITES && gSprites[sPartnerMarkerSprite].inUse)
        DestroySprite(&gSprites[sPartnerMarkerSprite]);
    sPartnerMarkerSprite = MAX_SPRITES;
    FreeSpriteTilesByTag(WL_ALLY_TILE_TAG);
    FreeSpriteTilesByTag(WL_SHOT_TILE_TAG);
    memset(sActors, 0, sizeof(sActors));
    memset(sShots, 0, sizeof(sShots));
    memset(sLoot, 0, sizeof(sLoot));
}

void WildlandsV1_Reset(void)
{
    if (sInitialized)
        DestroyAll();
    sInitialized = FALSE;
    sRayquazaRecruitable = FALSE;
    sFrames = 0;
    sWarmupTimer = 0;
    gWildlandsSurfTransitions = 0;
    memset(gWildlandsSpawnAudit, 0, sizeof(gWildlandsSpawnAudit));
}

static bool8 PlaceActorSafe(u8 id, s16 targetX, s16 targetY, u8 maxRadius,
                            bool8 enforceTeamSpacing)
{
    s16 radius;
    s16 dx;
    s16 dy;
    s16 x;
    s16 y;
    struct WildActor *actor = &sActors[id];

    for (radius = 0; radius <= maxRadius; radius++)
    {
        for (dy = -radius; dy <= radius; dy++)
        {
            for (dx = -radius; dx <= radius; dx++)
            {
                if (radius && Abs32(dx) != radius && Abs32(dy) != radius)
                    continue;
                x = targetX + dx;
                y = targetY + dy;
                if (!SpawnAreaSafe(x, y))
                    continue;
                if (enforceTeamSpacing
                    && !SpawnFarFromOtherTeams(id, x, y, WL_MIN_TEAM_SPAWN_TILES))
                    continue;
                actor->x = x * 16 + 8;
                actor->y = y * 16 + 8;
                return TRUE;
            }
        }
    }
    actor->active = FALSE;
    return FALSE;
}

static bool8 TeamsRespectSpawnSpacing(void)
{
    static const u8 reps[] = {WL_PLAYER, 2, 4};
    u32 a;
    u32 b;
    for (a = 0; a < ARRAY_COUNT(reps); a++)
    {
        if (!sActors[reps[a]].active)
            return FALSE;
        for (b = a + 1; b < ARRAY_COUNT(reps); b++)
        {
            if (!sActors[reps[b]].active)
                return FALSE;
            if (Dist(sActors[reps[a]].x / 16, sActors[reps[a]].y / 16,
                     sActors[reps[b]].x / 16, sActors[reps[b]].y / 16)
                < WL_MIN_TEAM_SPAWN_TILES)
                return FALSE;
        }
    }
    return TRUE;
}

static void InitWildlands(void)
{
    u32 i;
    s16 px;
    s16 py;
    struct ObjectEvent *playerObj;
    if (!OnWildlandsMap() || gPlayerAvatar.spriteId >= MAX_SPRITES)
        return;

    // A Wildlands deployment always begins on foot. Do not inherit a stale
    // Emerald avatar state from the native new-game/warp machinery.
    SetPlayerAvatarTransitionFlags(PLAYER_AVATAR_FLAG_ON_FOOT);
    gWildlandsSurfTransitions = 0;

    playerObj = &gObjectEvents[gPlayerAvatar.objectEventId];
    px = playerObj->currentCoords.x;
    py = playerObj->currentCoords.y;

    // Never accept the native warp landing blindly. Emerald maps can contain
    // shoreline pockets, narrow ledges or other legal collision tiles that are
    // poor Battle Royale deployments. Before creating any actors, normalize the
    // landing to the nearest certified connected-land spawn.
    if (!SpawnAreaSafe(px, py))
    {
        s16 safeX;
        s16 safeY;
        if (FindSafeSpawnNear(px, py, &safeX, &safeY, 18))
        {
            // Correct the already-loaded field position directly. A second
            // WarpIntoMap here can strand Emerald between field callbacks.
            MoveObjectEventToMapCoords(playerObj, safeX, safeY);
            gSaveBlock1Ptr->pos.x = safeX - MAP_OFFSET;
            gSaveBlock1Ptr->pos.y = safeY - MAP_OFFSET;
            px = safeX;
            py = safeY;
        }
    }

    memset(sActors, 0, sizeof(sActors));
    memset(sShots, 0, sizeof(sShots));
    memset(sLoot, 0, sizeof(sLoot));
    for (i = 0; i < WL_MAX_ACTORS; i++)
        sActors[i].spriteId = MAX_SPRITES;
    for (i = 0; i < WL_MAX_SHOTS; i++)
        sShots[i].spriteId = MAX_SPRITES;
    sPartnerMarkerSprite = MAX_SPRITES;

    LoadSpriteSheet(&sShotSheet);
    LoadSpriteSheet(&sAllySheet);
    LoadPalette(sShotPalette, OBJ_PLTT_ID(WL_EFFECT_PAL), PLTT_SIZE_4BPP);

    // Seed every actor from the actual native player coordinates rather than
    // assuming the requested warp coordinates survived Emerald's map setup.
    InitActor(WL_PLAYER, SPECIES_CHARIZARD, 0, FALSE, FALSE,
              px, py,
              MOVE_FLAMETHROWER, MOVE_SLASH, MOVE_WING_ATTACK, MOVE_DIG);
    memset(gWildlandsSpawnAudit, 0, sizeof(gWildlandsSpawnAudit));
    gWildlandsSpawnAudit[0] = SpawnAreaSafe(px, py);

    InitActor(WL_PARTNER, SPECIES_BLASTOISE, 0, TRUE, FALSE,
              px, py,
              MOVE_WATER_GUN, MOVE_BITE, MOVE_HYDRO_PUMP, MOVE_PROTECT);
    gWildlandsSpawnAudit[1] = PlaceActorSafe(WL_PARTNER, px - 2, py + 1, 6, FALSE);

    // V1 deliberately deploys enemy squads into separate Route 119 regions
    // instead of around the player. These anchors come from original valid
    // overworld positions and are still runtime-audited before acceptance.
    InitActor(2, SPECIES_SCEPTILE, 1, TRUE, FALSE,
              31 + MAP_OFFSET, 109 + MAP_OFFSET,
              MOVE_LEAF_BLADE, MOVE_GIGA_DRAIN, MOVE_QUICK_ATTACK, MOVE_AGILITY);
    gWildlandsSpawnAudit[1] &= PlaceActorSafe(2, 31 + MAP_OFFSET, 109 + MAP_OFFSET, 8, TRUE);
    InitActor(3, SPECIES_BLAZIKEN, 1, TRUE, FALSE,
              31 + MAP_OFFSET, 109 + MAP_OFFSET,
              MOVE_BLAZE_KICK, MOVE_FIRE_PUNCH, MOVE_MACH_PUNCH, MOVE_PROTECT);
    gWildlandsSpawnAudit[1] &= PlaceActorSafe(3,
        sActors[2].x / 16 + 2, sActors[2].y / 16 + 1, 5, FALSE);

    InitActor(4, SPECIES_GARDEVOIR, 2, TRUE, FALSE,
              25 + MAP_OFFSET, 32 + MAP_OFFSET,
              MOVE_PSYCHIC, MOVE_SHOCK_WAVE, MOVE_DOUBLE_TEAM, MOVE_PROTECT);
    gWildlandsSpawnAudit[1] &= PlaceActorSafe(4, 25 + MAP_OFFSET, 32 + MAP_OFFSET, 8, TRUE);
    InitActor(5, SPECIES_METAGROSS, 2, TRUE, FALSE,
              25 + MAP_OFFSET, 32 + MAP_OFFSET,
              MOVE_METEOR_MASH, MOVE_PSYCHIC, MOVE_SLAM, MOVE_PROTECT);
    gWildlandsSpawnAudit[1] &= PlaceActorSafe(5,
        sActors[4].x / 16 - 2, sActors[4].y / 16 + 1, 5, FALSE);

    gWildlandsSpawnAudit[2] = sActors[2].active && sActors[3].active
        && sActors[4].active && sActors[5].active;
    gWildlandsSpawnAudit[3] = TeamsRespectSpawnSpacing();

    // Known-valid northern Route 119 field coordinate (the original map uses
    // this walkable area for an overworld actor). Keep the legendary away from
    // the deployment pocket so a failed placement can never cover the player.
    InitActor(WL_RAYQUAZA, SPECIES_RAYQUAZA, 3, TRUE, TRUE,
              28 + MAP_OFFSET, 14 + MAP_OFFSET,
              MOVE_DRAGON_CLAW, MOVE_EXTREME_SPEED, MOVE_FLY, MOVE_HYPER_BEAM);

    sPartnerMarkerSprite = CreateSprite(&sAllyTemplate, 120, 48, 0);
    if (sPartnerMarkerSprite < MAX_SPRITES)
    {
        gSprites[sPartnerMarkerSprite].oam.paletteNum = WL_EFFECT_PAL;
        gSprites[sPartnerMarkerSprite].coordOffsetEnabled = TRUE;
    }
    if (sActors[WL_RAYQUAZA].active)
    {
        sActors[WL_RAYQUAZA].maxHp = sActors[WL_RAYQUAZA].maxHp * 2;
        sActors[WL_RAYQUAZA].hp = sActors[WL_RAYQUAZA].maxHp;
        sActors[WL_RAYQUAZA].atk += 40;
        sActors[WL_RAYQUAZA].def += 30;
    }
    InitLoot();
    sInitialized = TRUE;
    sFrames = 0;
    // Brief BR deployment grace: movement and traversal work, combat does not.
    sWarmupTimer = 360;
}

void WildlandsV1_Tick(void)
{
    u32 i;
    if (!OnWildlandsMap())
    {
        if (sInitialized)
            WildlandsV1_Reset();
        return;
    }
    if (!sInitialized)
    {
        InitWildlands();
        return;
    }
    sFrames++;
    if (ScriptContext_IsEnabled() || ArePlayerFieldControlsLocked() || gPaletteFade.active)
        return;

    if (sWarmupTimer)
    {
        sWarmupTimer--;
        TickContextAction();
        if (sActors[WL_PARTNER].active
            && !TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING))
        {
            s32 followX;
            s32 followY;
            PartnerFormationTarget(&followX, &followY);
            if (Dist(sActors[WL_PARTNER].x, sActors[WL_PARTNER].y,
                     followX, followY) > 18)
                MoveActorToward(WL_PARTNER, followX, followY, 2);
        }
        UpdateConcealment();
        return;
    }

    TickPlayerInput();
    TickContextAction();
    for (i = 0; i < WL_MAX_ACTORS; i++)
        if (sActors[i].active)
            TickActorAttack(i);
    for (i = 1; i < WL_MAX_ACTORS; i++)
        TickAI(i);
    TickShots();
    UpdateConcealment();
}
