#!/usr/bin/env python3
"""Install Wildlands V5 true duo combat (arena_squad.inc) into the Arena.

Applied after wildlands-v5/apply.py. Every anchor must match exactly once;
drift fails the build instead of silently dropping a feature.
"""
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
shutil.copy(here / 'arena_squad.inc', root / 'src/arena_squad.inc')
shutil.copy(here / 'arena_zone.inc', root / 'src/arena_zone.inc')
shutil.copy(here / 'arena_loot.inc', root / 'src/arena_loot.inc')
shutil.copy(here / 'arena_map.inc', root / 'src/arena_map.inc')
shutil.copy(here / 'arena_brain.inc', root / 'src/arena_brain.inc')
shutil.copy(here / 'arena_director.inc', root / 'src/arena_director.inc')


def patch(path, old, new, count=1):
    p = root / path
    s = p.read_text()
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new))


A = 'src/realtime_arena.c'
# Prototypes near the V4 partner definitions (used by CB2_ArenaInit/CB2_Arena).
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n'
      'static void SquadInit(void);\nstatic void SquadTick(void);\nstatic void SquadDestroy(void);\n'
      'static bool8 SquadPromote(u8 side);\nstruct ArenaShot;\n'
      'static bool8 SquadShotStep(u8 index, struct ArenaShot *shot, const struct ArenaMoveProfile *p, s16 oldX, s16 oldY);\n'
      'static void SquadEnemyRetarget(struct ArenaBody *body);\nstatic bool8 SquadEnemySees(void);\n'
      'extern EWRAM_DATA u32 gWildlandsSquadTelemetry[16];\n'
      'static EWRAM_DATA u8 sSquadShotOwner[SHOTS_COUNT] = {};\n'
      'static void SquadSimStep(void);\n'
      'static void ZoneInit(void);\nstatic void ZoneTick(void);\nstatic void ZoneDestroy(void);\n'
      'static void ZoneSteerEnemy(struct ArenaBody *body);\nstatic void ZoneHudLine(void);\nstatic u32 ZoneHudKey(void);\n'
      'static bool8 ZoneSteer(s32 x, s32 y, s32 *goalX, s32 *goalY);\n'
      'static bool8 ZoneOutside(s32 x, s32 y, s32 margin);\n'
      'static EWRAM_DATA u32 sZoneHudKeyShown = 0;\n'
      'static EWRAM_DATA bool8 sWildlandsEncounterLive = FALSE;\n'
      'static EWRAM_DATA u8 sWildlandsSimSteps = 1;\n'
      'static void LootInit(void);\nstatic void LootTick(void);\nstatic void LootDestroy(void);\n'
      'static void WildlandsPauseBoosts(void);\nstatic void MapDraw(void);\nEWRAM_DATA u32 gWildlandsMapTelemetry[4] = {};\n'
      'EWRAM_DATA u16 gWildlandsProfile[12] = {};\n'
      '// [0] max render gap (vblanks) [1] frames over 3 vblanks [2] last/[3] max\n'
      '// active-slot load cost [4] max biome swap cost (scanlines) [5] steps over cap\n'
      'EWRAM_DATA u16 gWildlandsHitch[12] = {};\n'
      '// TEST HOOK ONLY: harness sets 1 to hold AI fire/movement while checking\n'
      '// map/zone UI; always 0 in normal play.\n'
      'EWRAM_DATA u8 gWildlandsTestPeace = 0;\n'
      '// TEST HOOK ONLY: 1 = back to start, 2 = onto the current room exit,\n'
      '// 3 = onto the last pickup, 10+n = outside door n facing it; 0 in play.\n'
      'EWRAM_DATA u8 gWildlandsTestWarp = 0;\n'
      'static void LootLastSpot(s16 *x, s16 *y);\n'
      'static void BrainDecide(struct ArenaBody *body, u8 seenMask);\nstatic bool8 BrainAllowsFire(void);\n'
      'static void WildlandsBuildOam(void);\n'
      'static bool8 DirectorAdvance(void);\nstatic void DirectorInit(void);\nstatic void DirectorSim(void);\n'
      'static u8 DirectorBossDoor(void);\nstatic void DirectorBossEnter(void);\nstatic bool8 DirectorLairAnchor(s32 *x, s32 *y);\nstatic u32 WildlandsCramp(s32 x, s32 y);\nstatic u8 DirectorLairState(s32 x, s32 y);\nstatic void DirectorLog(const u8 *text);\nstatic bool8 LootPopupText(u8 *text);\nstatic void SquadSwapLead(void);\nstatic void WildlandsTeamDraw(void);\nstatic void WildlandsLogDraw(void);\n'
      'static void DirectorDestroy(void);\nstatic void DirRestorePartner(void);\nstatic bool8 DirectorSoloActive(void);\n'
      'static bool8 DirectorPopupText(u8 *text, u8 *color);\nstatic u8 DirectorLeft(void);\nstatic bool8 DirectorRunning(void);\n'
      'static bool8 DirectorPopupActive(void);\nstatic void DirectorPauseLine(void);\n'
      'void Wildlands_ArenaLoadout(struct Pokemon *mon);\nvoid Wildlands_TrimParty(void);\n'
      'static const u16 *ArenaMonPalette(const struct ArenaSpriteSet *art, struct Pokemon *mon);\n'
      'static void WildlandsSummaryDraw(void);\nstatic EWRAM_DATA bool8 sWildlandsSummary = FALSE;\n'
      'static u8 BrainWingTarget(u8 picked);\nstatic bool8 BrainWingFollows(void);\nstatic void BrainInit(void);\n')
# Shiny Pokemon get a shiny arena palette (lead/enemy bodies at match start).
patch(A, '            LoadPalette(body->art->palette, OBJ_PLTT_ID(i), PLTT_SIZE_4BPP);\n',
      '            LoadPalette(ArenaMonPalette(body->art, i ? &gEnemyParty[gBattlerPartyIndexes[1]] : &gPlayerParty[gBattlerPartyIndexes[0]]), OBJ_PLTT_ID(i), PLTT_SIZE_4BPP);\n')
# End-of-match summary (V6 C4): the result holds ~4s on a summary card in the
# world (A skips) before returning to the Lab.
patch(A, '        if (sArena.resultTimer)\n        {\n            SpecialTick();GuardTick();\n',
      '        if (sArena.resultTimer)\n        {\n'
      '            if (WildlandsWorld_Active() && !sWildlandsSummary)\n'
      '            { sWildlandsSummary = TRUE; sArena.resultTimer = 240; WildlandsSummaryDraw(); }\n'
      '            if (sWildlandsSummary && sArena.resultTimer > 2 && JOY_NEW(A_BUTTON))\n'
      '                sArena.resultTimer = 2;\n'
      '            SpecialTick();GuardTick();\n')
# The follower actor is superseded by real squad wings.
patch(A, '    WildlandsPartner_Init();\n', '    SquadInit();\n    ZoneInit();\n    LootInit();\n    BrainInit();\n    DirectorInit();\n    sWildlandsEncounterLive = WildlandsWorld_Active();\n')
patch(A, '    WildlandsPartner_Update();\n', '    SquadTick();\n')
patch(A, 'WildlandsPartner_Destroy();', 'DirectorDestroy();SquadDestroy();ZoneDestroy();LootDestroy();', count=2)
# A new encounter (not a menu round trip) starts squad/zone/loot fresh.
patch(A, '    sEnvironmentInitialized=FALSE;\n    memset(&sArena, 0, sizeof(sArena));', '    sEnvironmentInitialized=FALSE;\n    sWildlandsEncounterLive=FALSE;\n    memset(&sArena, 0, sizeof(sArena));')
# Native shots clear wing ownership of their pool slot.
patch(A, '        sArena.shots[i].side = side; sArena.shots[i].move = profile->move;\n',
      '        sArena.shots[i].side = side; sArena.shots[i].move = profile->move;\n'
      '        sSquadShotOwner[i] = 0;\n')
# Squad hit test runs first; wing-owned shots never credit a native body.
patch(A, '        if (ArenaMoves_SegmentHit(oldX,oldY,shot->x/Q,shot->y/Q,target->x/Q,target->y/Q,p->radius) && !target->dash)\n',
      '        if (SquadShotStep(i,shot,p,oldX,oldY)) {}\n'
      '        else if (ArenaMoves_SegmentHit(oldX,oldY,shot->x/Q,shot->y/Q,target->x/Q,target->y/Q,p->radius) && !target->dash)\n')
# A KO'd lead is replaced by its living wing instead of ending the encounter.
patch(A, '        if(!hp)\n        {\n            // Let a committed beam finish its visual release after a KO.',
      '        if(!hp && !SquadPromote(targetSide))\n        {\n            // Let a committed beam finish its visual release after a KO.')
# Enemy lead targets the nearer visible member of the player duo.
patch(A, '        {sArena.observed.x = sArena.bodies[0].x / Q;sArena.observed.y = sArena.bodies[0].y / Q;}\n',
      '        {sArena.observed.x = sArena.bodies[0].x / Q;sArena.observed.y = sArena.bodies[0].y / Q;SquadEnemyRetarget(body);}\n')
# The duo brain also runs while the player hides in grass or smoke.
patch(A, '        else gArenaCoverTelemetry[5]++;\n        if(sDecoys[0].life', '        else {gArenaCoverTelemetry[5]++;SquadEnemyRetarget(body);}\n        if(sDecoys[0].life')
# Module body: after DestroyShot (needs shots, Fire helpers, SpecialInvulnerable).
patch(A, 'static void TickShots(void)\n{', '#include "arena_squad.inc"\n#include "arena_loot.inc"\n#include "arena_zone.inc"\n#include "arena_map.inc"\n#include "arena_brain.inc"\n#include "arena_director.inc"\n\nstatic void TickShots(void)\n{')
# Enemy lead rotates toward the safe circle when exposed or pre-rotating.
patch(A, '    dx = sArena.waypoint.x * Q - body->x;\n', '    ZoneSteerEnemy(body);\n    dx = sArena.waypoint.x * Q - body->x;\n')
# Bottom HUD: zone countdown and squad HP replace the capture-ball help.
C = 'src/arena_capture.inc'
patch(C, '        && sCapture.hudMove==move && sCapture.hudPP==pp)return;',
      '        && sCapture.hudMove==move && sCapture.hudPP==pp && sZoneHudKeyShown==ZoneHudKey())return;')
patch(C, '            HudTinyWindow(2,81,10,text,4,5);\n        }\n        PutWindowTilemap(2);',
      '            HudTinyWindow(2,81,10,text,4,5);\n        }\n        ZoneHudLine();sZoneHudKeyShown=ZoneHudKey();\n        PutWindowTilemap(2);')

# Live map: fifth pause page (POKEMON/BAG/MOVES/RESUME/MAP).
patch(A, 'static const u8 labels[4][18]={_("POKEMON"),_("BAG"),_("MOVES"),_("RESUME")};',
      'static const u8 labels[5][18]={_("POKEMON"),_("BAG"),_("MOVES"),_("RESUME"),_("MAP")};')
patch(A, '            for(side=0;side<4;side++)\n            {\n                if(side==sPauseChoice)WindowRect(1,7,18+side*11,4,7,5);\n                PrintPopup(18,16+side*11,labels[side],side==sPauseChoice?5:4);',
      '            for(side=0;side<5;side++)\n            {\n                if(side==sPauseChoice)WindowRect(1,7,17+side*10,4,7,5);\n                PrintPopup(18,15+side*10,labels[side],side==sPauseChoice?5:4);')
patch(A, '        else if(sPausePage)\n        {\n            FillWindowPixelBuffer(1, PIXEL_FILL(9));',
      '        else if(sPausePage==4)MapDraw();\n        else if(sPausePage)\n        {\n            FillWindowPixelBuffer(1, PIXEL_FILL(9));')
patch(A, '{sPauseChoice=(sPauseChoice+(JOY_NEW(DPAD_DOWN)?1:3))%4;sArena.hudDirty=TRUE;}',
      '{sPauseChoice=(sPauseChoice+(JOY_NEW(DPAD_DOWN)?1:4))%5;sArena.hudDirty=TRUE;}')
patch(A, '                if(sPauseChoice==3){sArena.paused=FALSE;DrawStage();sArena.hudDirty=TRUE;}',
      '                if(sPauseChoice==3){sArena.paused=FALSE;DrawStage();sArena.hudDirty=TRUE;}\n                if(sPauseChoice==4){sPausePage=4;sArena.hudDirty=TRUE;}')
patch(A, '        else if(JOY_NEW(L_BUTTON|R_BUTTON))\n        {\n            sPausePage=(sPausePage+(JOY_NEW(R_BUTTON)?1:2))%3;',
      '        else if(sPausePage<3 && JOY_NEW(L_BUTTON|R_BUTTON))\n        {\n            sPausePage=(sPausePage+(JOY_NEW(R_BUTTON)?1:2))%3;')

# Fixed-timestep catch-up (Wildlands only): when the previous render overran
# a VBlank, run the simulation block once per elapsed frame (max 3) and render
# once, so movement, AI, cooldowns, projectiles and the storm advance in real
# time. Edge-triggered input is consumed by the first step only.
patch(A, '        sArena.frame++;\n        for(i=0;i<2;i++)\n',
      '        {\n        u8 simStep, simSteps = WildlandsWorld_Active() ? (gap >= 6 ? 6 : gap >= 2 ? gap : 1) : 1;\n'
      '        u16 savedNewKeys = gMain.newKeys;\n'
      '        if (gap > gWildlandsHitch[0]) gWildlandsHitch[0] = gap;\n'
      '        if (gap > 3) gWildlandsHitch[1]++;\n'
      '        if (gap > 6) gWildlandsHitch[5] += gap - 6;\n'
      '        sWildlandsSimSteps = simSteps;\n'
      '        gWildlandsProfile[10] += simSteps; gWildlandsProfile[11]++;\n'
      '        for (simStep = 0; simStep < simSteps; simStep++)\n        {\n'
      '        if (simStep) { if (sArena.resultTimer || !sArena.active) break; gMain.newKeys = 0; }\n'
      '        sArena.frame++;\n        SquadSimStep();\n        for(i=0;i<2;i++)\n')
patch(A, '''                        PlaySE(SE_M_MORNING_SUN);
                    }
                }
            }
        }
    }
    CaptureTick();''', '''                        PlaySE(SE_M_MORNING_SUN);
                    }
                }
            }
        }
        }
        gMain.newKeys = savedNewKeys;
        }
    }
    CaptureTick();''')

# Ball capture is not part of the battle royale: L+R launches matches and
# must not raise the capture-aim prompt over the Wildlands HUD.
patch(A, '    if(!ClashBusy()&&!GuardBusy()&&!SpecialBusy(0)&&!SpecialBusy(1))CaptureInput();',
      '    if(!WildlandsWorld_Active()&&!ClashBusy()&&!GuardBusy()&&!SpecialBusy(0)&&!SpecialBusy(1))CaptureInput();')

# A failed route leaves the waypoint on the body; never re-search every frame.
patch(A, '        && ArenaNav_Distance(body->x/Q,body->y/Q,sArena.goal.x,sArena.goal.y) >= 4) AiRoute();',
      '        && ArenaNav_Distance(body->x/Q,body->y/Q,sArena.goal.x,sArena.goal.y) >= 4 && !(sArena.frame & 7)) AiRoute();')

patch(A, 'static void TickEnemy(void)\n{\n    struct ArenaBody *body = &sArena.bodies[1];\n    s32 dx, dy, len;\n    body->moving = FALSE;\n',
      'static void TickEnemy(void)\n{\n    struct ArenaBody *body = &sArena.bodies[1];\n    s32 dx, dy, len;\n    body->moving = FALSE;\n    if (gWildlandsTestPeace) return;\n')

patch(C, '    bool8 notice=sCapture.notice!=0;', '    bool8 notice=sCapture.notice!=0 && !WildlandsWorld_Active();')

# Animation clocks follow game time, not render rate.
patch(A, '                body->animClock += animation == ARENA_ANIM_WALK ? Clamp(Speed(i) * Q / 220, 128, 512) : Q;',
      '                body->animClock += (animation == ARENA_ANIM_WALK ? Clamp(Speed(i) * Q / 220, 128, 512) : Q) * sWildlandsSimSteps;')

# The enemy lead only aims at a target it can see (not at a roam point).
patch(A, '''            if (!body->cooldown && ArenaMovePP(1,body->moveSlot)
                && distance < p->range && distance > 8''', '''            if (!body->cooldown && ArenaMovePP(1,body->moveSlot) && SquadEnemySees()
                && distance < p->range && distance > 8''')

patch(A, '            FillWindowPixelBuffer(1,PIXEL_FILL(9));\n            PrintPopup(8,3,title,5);',
      '            FillWindowPixelBuffer(1,PIXEL_FILL(9));\n            PrintPopup(8,3,title,5);\n            WildlandsPauseBoosts();')

# Profiling: camera/stream, sprite animation, OAM build (scanlines).
patch(A, '    ArenaXL_UpdateCamera();\n    AnimateSprites();\n    BuildOamBuffer();',
      '    {u32 p0=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228,p1;\n'
      '    ArenaXL_UpdateCamera();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[6]=p1-p0;p0=p1;\n'
      '    AnimateSprites();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[7]=p1-p0;p0=p1;\n'
      '    WildlandsBuildOam();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[8]=p1-p0;\n'
      '    {u32 n=0,k;for(k=0;k<MAX_SPRITES;k++)if(gSprites[k].inUse)n++;gWildlandsProfile[9]=n;}}')

# Interiors: rooms clamp the camera onto themselves.
patch(A, '''    u32 i;
    sArenaXLCameraX=camX;sArenaXLCameraY=camY;''', '''    u32 i;
    if(WildlandsWorld_Active())WildlandsWorld_ClampCamera(px,py,&camX,&camY);
    sArenaXLCameraX=camX;sArenaXLCameraY=camY;''')
# Corner assist (player only; AI routes around): a blocked straight move
# slides 1px toward a one-tile opening.
patch(A, '''    else if (dx) gArenaAiTelemetry.wallBlocks[side]++;
''', '''    else if (dx)
    {
        gArenaAiTelemetry.wallBlocks[side]++;
        if (WildlandsWorld_Active() && !side && !dy && !ghost)
        {
            s8 n = WildlandsWorld_SlideNudge(side, body->x / Q, body->y / Q, dx > 0 ? 1 : -1, 0);
            if (n) body->y += n * Q;
        }
    }
''')
patch(A, '''    else if (dy) gArenaAiTelemetry.wallBlocks[side]++;
''', '''    else if (dy)
    {
        gArenaAiTelemetry.wallBlocks[side]++;
        if (WildlandsWorld_Active() && !side && !dx && !ghost)
        {
            s8 n = WildlandsWorld_SlideNudge(side, body->x / Q, body->y / Q, 0, dy > 0 ? 1 : -1);
            if (n) body->x += n * Q;
        }
    }
''')
# The world now extends below the island (room strip).
patch('include/arena_navigation.h', '#define ARENA_MAX_Y 3040\n',
      '#include "wildlands_world_data.h"\n#ifdef WL_ARENA_MAX_Y\n#define ARENA_MAX_Y WL_ARENA_MAX_Y\n#else\n#define ARENA_MAX_Y 3040\n#endif\n')

# Director: Arena-legal loadouts for the AI lobby (career's own legal-move bank).
p = root / 'src/ascension_career.c'
t = p.read_text()
if 'Wildlands_ArenaLoadout' not in t:
    p.write_text(t + r'''
#include "arena_moves.h"
// Beta: a Wildlands match is a duo. Anything beyond the first two party
// slots goes back to the PC before the match (the PC's move mode could
// place a third).
#include "pokemon_storage_system.h"
void Wildlands_TrimParty(void)
{
    u32 k, box;
    for (k = 2; k < PARTY_SIZE; k++)
    {
        if (!GetMonData(&gPlayerParty[k], MON_DATA_SPECIES))
            continue;
        for (box = 0; box < TOTAL_BOXES_COUNT; box++)
        {
            s16 pos = GetFirstFreeBoxSpot(box);
            if (pos >= 0)
            {
                SetBoxMonAt(box, pos, &gPlayerParty[k].box);
                break;
            }
        }
        ZeroMonData(&gPlayerParty[k]);
    }
    CompactPartySlots();
    CalculatePlayerPartyCount();
}
// Wildlands loadout: species-legal moves (Ascension studio bank) that the
// real-time Arena can actually perform. Keeps the current moves that qualify
// (player choices survive), then fills by power + STAB + type coverage.
static bool8 WildlandsRealtimeMove(u16 move)
{
    return move && ArenaMoves_Get(move) != NULL;
}
void Wildlands_ArenaLoadout(struct Pokemon *mon)
{
    u16 species = GetMonData(mon, MON_DATA_SPECIES), chosen[4] = {0}, i, j, n = 0;
    const struct AscensionStudioEntry *e = V111LegalEntry(species);
    bool8 damaging = FALSE;
    if (!e || GetMonData(mon, MON_DATA_IS_EGG))
    {
        V111Loadout(mon, NULL);
        return;
    }
    for (i = 0; i < 4; i++)
    {
        u16 move = GetMonData(mon, MON_DATA_MOVE1 + i);
        if (!V111LegalMove(e, move) || !WildlandsRealtimeMove(move))
            continue;
        for (j = 0; j < n; j++) if (chosen[j] == move) break;
        if (j == n) chosen[n++] = move;
    }
    while (n < 4)
    {
        s16 best = -32767;
        u16 pick = MOVE_NONE;
        for (i = 0; i < e->count; i++)
        {
            u16 move = sAscensionStudioMoveBank[e->start + i];
            u8 type = gBattleMoves[move].type;
            s16 score = gBattleMoves[move].power;
            if (!WildlandsRealtimeMove(move))
                continue;
            for (j = 0; j < n; j++) if (chosen[j] == move) break;
            if (j < n) continue;
            if (score > 120) score = 120;
            if (score)
            {
                if (type == gSpeciesInfo[species].types[0] || type == gSpeciesInfo[species].types[1]) score += 35;
                for (j = 0; j < n; j++) if (gBattleMoves[chosen[j]].power && gBattleMoves[chosen[j]].type == type) break;
                if (j == n) score += 25;
            }
            else if (move == MOVE_PROTECT) score = 25;
            if (score > best) { best = score; pick = move; }
        }
        if (!pick) break;
        chosen[n++] = pick;
    }
    for (i = 0; i < n; i++)
        if (gBattleMoves[chosen[i]].power) damaging = TRUE;
    if (!damaging)
    {
        V111Loadout(mon, NULL);   // no real-time attack in the bank: legacy pick
        return;
    }
    for (i = 0; i < 4; i++)
    {
        u16 cur = GetMonData(mon, MON_DATA_MOVE1 + i);
        if (cur != chosen[i])
            SetMonMoveSlot(mon, chosen[i], i);
    }
}
''')

# HUD: thin partner / enemy-wing HP bars under the two main bars.
H = 'src/arena_hud.inc'
patch(H, '&& sHudLastLevel[0]==gBattleMons[0].level && sHudLastLevel[1]==gBattleMons[1].level)return;',
      '&& sHudLastLevel[0]==gBattleMons[0].level && sHudLastLevel[1]==gBattleMons[1].level\n'
      '        && sHudWingKey==WildlandsHudWingKey())return;')
patch(H, 'static EWRAM_DATA u8 sHudLastLevel[2]={};',
      'static EWRAM_DATA u8 sHudLastLevel[2]={};\nstatic EWRAM_DATA u32 sHudWingKey=0;\nstatic u32 WildlandsHudWingKey(void);\nstatic void WildlandsHudWingBars(void);')
patch(H, '    sHudCached=TRUE;\n}', '    WildlandsHudWingBars();\n    sHudWingKey=WildlandsHudWingKey();\n    sHudCached=TRUE;\n}')

# Playtest "pixels go crazy when moving": several move effects (warp/toss
# shake, flame clash tremor, toss landing) wrote BG1 scroll registers every
# render, which in Wildlands is the streamed MIDDLE terrain layer. On frames
# where the effect code ran after the camera, BG1 snapped to 0,0 while BG2/BG3
# stayed on the camera, so the ground layer jumped every other frame. In
# Wildlands these writes are dropped (the camera owns all three layers).
patch(A, '#include "wildlands_world_data.h"\n',
      '#include "wildlands_world_data.h"\n'
      '#define WL_BG1(reg, value) do { if (!WildlandsWorld_Active()) SetGpuReg(reg, value); } while (0)\n')
for inc in ('src/arena_warp_toss.inc', 'src/arena_toss.inc', 'src/arena_flame_clash.inc'):
    p = root / inc
    t = p.read_text()
    n = t.count('SetGpuReg(REG_OFFSET_BG1HOFS,') + t.count('SetGpuReg(REG_OFFSET_BG1VOFS,')
    if not n:
        raise SystemExit(f'{inc}: BG1 scroll writes not found')
    t = t.replace('SetGpuReg(REG_OFFSET_BG1HOFS,', 'WL_BG1(REG_OFFSET_BG1HOFS,').replace('SetGpuReg(REG_OFFSET_BG1VOFS,', 'WL_BG1(REG_OFFSET_BG1VOFS,')
    p.write_text(t)
    print(inc, n, 'BG1 scroll writes guarded')
for src in sorted((root / 'src').glob('arena_*')):
    t = src.read_text(errors='ignore')
    for reg in ('BG2HOFS', 'BG2VOFS', 'BG3HOFS', 'BG3VOFS'):
        if 'REG_OFFSET_' + reg in t:
            print('WARNING other terrain scroll writer:', src.name, reg)

# ---- Frame rate (render cost) --------------------------------------------
# The scenery warm-light pass re-blended all 240 BG colours every rendered
# frame even at strength 0 (a pure copy). Blend only while lit, plus once to
# restore. Every other writer (LoadPalette, ZoneTint) keeps both buffers equal.
patch(A, '        BlendPalette(16,240,sArena.paused?0:warmth,RGB(31,16,4));\n',
      '        {\n'
      '            u8 lit = sArena.paused ? 0 : warmth;\n'
      '            if (lit || sWildlandsSceneryLit)\n'
      '                BlendPalette(16,240,lit,RGB(31,16,4));\n'
      '            sWildlandsSceneryLit = lit;\n'
      '        }\n')
patch(A, 'static EWRAM_DATA u8 sWildlandsSimSteps = 1;\n',
      'static EWRAM_DATA u8 sWildlandsSimSteps = 1;\nstatic EWRAM_DATA u8 sWildlandsSceneryLit = 0;\n')
# Move profile lookup: ~20 linear scans of the 89-entry table per frame.
patch('src/arena_moves.c', 'const struct ArenaMoveProfile *ArenaMoves_Get(u16 move)\n{\n    unsigned i;\n'
      '    for (i = 0; i < sizeof(sProfiles)/sizeof(sProfiles[0]); i++)\n'
      '        if (sProfiles[i].move == move) return &sProfiles[i];\n    return 0;\n}\n',
      '#if defined(ARENA_MOVES_HOST) && !defined(EWRAM_DATA)\n#define EWRAM_DATA\n#endif\n'
      'static EWRAM_DATA u16 sProfileMemoMove[8] = {0};\n'
      'static EWRAM_DATA u8 sProfileMemoIdx[8] = {0};\n'
      'const struct ArenaMoveProfile *ArenaMoves_Get(u16 move)\n{\n    unsigned i, slot = move & 7;\n'
      '    if (sProfileMemoIdx[slot] && sProfileMemoMove[slot] == move)\n'
      '        return &sProfiles[sProfileMemoIdx[slot] - 1];\n'
      '    for (i = 0; i < sizeof(sProfiles)/sizeof(sProfiles[0]); i++)\n'
      '        if (sProfiles[i].move == move)\n'
      '        {\n'
      '            if (i < 255) { sProfileMemoMove[slot] = move; sProfileMemoIdx[slot] = i + 1; }\n'
      '            return &sProfiles[i];\n'
      '        }\n    return 0;\n}\n')

# Locked 30 fps world render: every rendered frame advances exactly two fixed
# 60 Hz steps, so motion is evenly paced (no 1-2-1 judder) and game time stays
# real. Button presses that land on the skipped VBlank carry to the next one.
patch(A, '    if(sSendout.active){gArenaFrameTelemetry.lastVBlank=gMain.vblankCounter1;StormDraw(40);SendoutTick();return;}\n',
      '    if(sSendout.active){gArenaFrameTelemetry.lastVBlank=gMain.vblankCounter1;StormDraw(40);SendoutTick();return;}\n'
      '    if(WildlandsWorld_Active()&&gap<2){sWildlandsHeldNew|=gMain.newKeys;return;}\n'
      '    gMain.newKeys|=sWildlandsHeldNew;sWildlandsHeldNew=0;\n'
      '    {u16 ln=(REG_VCOUNT+68)%228; if(ln>gWildlandsLoop[3])gWildlandsLoop[3]=ln; gWildlandsLoop[gap>=3?2:gap>=2?1:0]++;}\n')
patch(A, 'static EWRAM_DATA u8 sWildlandsSceneryLit = 0;\n',
      'static EWRAM_DATA u8 sWildlandsSceneryLit = 0;\n'
      'static EWRAM_DATA u16 sWildlandsHeldNew = 0;\n'
      '// renders after [0] one VBlank [1] two (the locked pace) [2] three or more (a hitch)\n'
      '// [3] latest scanline a render started at\n'
      'EWRAM_DATA u16 gWildlandsLoop[4] = {};\n')

# Spike telemetry: which part of a render overran its two-VBlank slot.
patch(A, 'EWRAM_DATA u16 gWildlandsLoop[4] = {};\n',
      'EWRAM_DATA u16 gWildlandsLoop[4] = {};\n'
      '// maxima (scanlines): [0] simulation steps [1] render [2] world VBlank streaming\n'
      '// [3] whole callback [4] renders over 400 scanlines [5] last sim length\n'
      'EWRAM_DATA u16 gWildlandsSpike[6] = {};\n')
patch(A, '    CaptureTick();\n',
      '    {u16 t=(u16)(gMain.vblankCounter1*228+(REG_VCOUNT+68)%228-stamp); gWildlandsSpike[5]=t; if(t>gWildlandsSpike[0])gWildlandsSpike[0]=t;}\n'
      '    CaptureTick();\n')
patch(A, '    gArenaFrameTelemetry.scanlines[5]=now-stamp;\n',
      '    gArenaFrameTelemetry.scanlines[5]=now-stamp;\n'
      '    {u16 t=(u16)(now-stamp); if(t>gWildlandsSpike[3])gWildlandsSpike[3]=t; if(t>400)gWildlandsSpike[4]++;\n'
      '     if(t>gWildlandsSpike[5]&&(u16)(t-gWildlandsSpike[5])>gWildlandsSpike[1])gWildlandsSpike[1]=t-gWildlandsSpike[5];}\n')
patch(A, 'static void VBlank_Arena(void)\n{\n    WildlandsWorld_VBlank();\n',
      'static void VBlank_Arena(void)\n{\n'
      '    {u16 v0=REG_VCOUNT,d; WildlandsWorld_VBlank(); d=(u16)(REG_VCOUNT-v0); if(d<228&&d>gWildlandsSpike[2])gWildlandsSpike[2]=d;}\n')

# Spike attribution inside a step: squad/director simulation vs enemy AI.
patch(A, 'EWRAM_DATA u16 gWildlandsSpike[6] = {};\n',
      'EWRAM_DATA u16 gWildlandsSpike[6] = {};\n'
      '// maxima (scanlines): [0] SquadSimStep (zone, loot, doors, director, wings) [1] TickEnemy\n'
      'EWRAM_DATA u16 gWildlandsSpikeSim[2] = {};\n')
patch(A, '        SquadSimStep();\n',
      '        {u32 q0=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228,q1; SquadSimStep();\n'
      '         q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; if(q1-q0>gWildlandsSpikeSim[0])gWildlandsSpikeSim[0]=q1-q0;}\n')
patch(A, '                TickEnemy();\n',
      '                {u32 q0=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228,q1; TickEnemy();\n'
      '                 q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; if(q1-q0>gWildlandsSpikeSim[1])gWildlandsSpikeSim[1]=q1-q0;}\n')

# Render spikes: a HUD change redrew the status panel AND the bottom line in
# one frame (up to ~200 scanlines); spread them over two frames.
patch(A, 'static EWRAM_DATA u8 sWildlandsSceneryLit = 0;\n',
      'static EWRAM_DATA u8 sWildlandsSceneryLit = 0;\n'
      'static EWRAM_DATA bool8 sWildlandsHudDrew = FALSE, sWildlandsHudDeferred = FALSE;\n')
patch('src/arena_hud.inc', '    sHudCached=TRUE;\n', '    sHudCached=TRUE;\n    sWildlandsHudDrew=TRUE;\n')
patch(A, '    DrawStatusHud();\n', '    sWildlandsHudDrew=FALSE;\n    DrawStatusHud();\n')
patch(A, '    CaptureHud();\n    sArena.hudDirty = FALSE;\n',
      '    if(!sWildlandsHudDrew||sArena.paused||!WildlandsWorld_Active()||sWildlandsHudDeferred)\n'
      '    {CaptureHud();sArena.hudDirty = FALSE;sWildlandsHudDeferred=FALSE;}\n'
      '    else {sArena.hudDirty = TRUE;sWildlandsHudDeferred=TRUE;}\n')
# Enemy goal choice: the arena-corner fallback scan is meaningless on the island.
patch(A, '        if(i==8&&best!=0x7FFFFFFF)break;\n', '        if(i==8&&(best!=0x7FFFFFFF||WildlandsWorld_Active()))break;\n')

# HUD: an HP-only change (the common case: hits, storm ticks) repaints just
# that side's bar and number instead of the whole panel and both names.
patch('src/arena_hud.inc', '    // One small authored background; preserve the terrain through alpha corners.\n',
      '    if(sHudCached && sHudLastMax[0]==gBattleMons[0].maxHP && sHudLastMax[1]==gBattleMons[1].maxHP\n'
      '        && sHudLastSpecies[0]==gBattleMons[0].species && sHudLastSpecies[1]==gBattleMons[1].species\n'
      '        && sHudLastLevel[0]==gBattleMons[0].level && sHudLastLevel[1]==gBattleMons[1].level\n'
      '        && sHudWingKey==WildlandsHudWingKey())\n'
      '    {\n'
      '        for(side=0;side<2;side++)\n'
      '        {\n'
      '            const struct BattlePokemon *mon=&gBattleMons[side];\n'
      '            u32 bar=side?129:8,fill=mon->maxHP?mon->hp*102/mon->maxHP:0;\n'
      '            u8 color=mon->hp*5<=mon->maxHP?6:mon->hp*2<=mon->maxHP?7:5;\n'
      '            if(sHudLastHp[side]==mon->hp)continue;\n'
      '            if(mon->hp&&!fill)fill=1;\n'
      '            HudRect(side?126:5,15,109,7,1);\n'
      '            HudRect(bar,13,102,8,12);HudRect(bar,13,fill,1,4);HudRect(bar,14,fill,7,color);\n'
      '            ConvertIntToDecimalStringN(text,mon->hp,STR_CONV_MODE_LEFT_ALIGN,3);\n'
      '            HudTiny(bar+46,16,text,9,3);HudTiny(bar+45,15,text,4,3);\n'
      '            sHudLastHp[side]=mon->hp;\n'
      '        }\n'
      '        return;\n'
      '    }\n'
      '    // One small authored background; preserve the terrain through alpha corners.\n')

# Match end stays in Wildlands: a lost match whites out to the Team Lab (not
# Ascension City), with no money penalty, and skips the native "Use next
# POKEMON?" prompt (the duo is out; the match is over).
patch('src/overworld.c',
      '    SetMoney(&gSaveBlock1Ptr->money, GetMoney(&gSaveBlock1Ptr->money) / 2);\n    HealPlayerParty();\n    Overworld_ResetStateAfterWhiteOut();\n    SetWarpDestinationToLastHealLocation();\n',
      '    if (!(VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE)))\n'
      '        SetMoney(&gSaveBlock1Ptr->money, GetMoney(&gSaveBlock1Ptr->money) / 2);\n'
      '    HealPlayerParty();\n    Overworld_ResetStateAfterWhiteOut();\n'
      '    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE))\n'
      '        SetWarpDestination(MAP_GROUP(MAP_ASCENSION_TEAM_LAB), MAP_NUM(MAP_ASCENSION_TEAM_LAB), WARP_ID_NONE, 6, 10);\n'
      '    else\n'
      '        SetWarpDestinationToLastHealLocation();\n')
patch(A, '            VarSet(VAR_ASCENSION_MASTERS_BEST,min(9999,VarGet(VAR_ASCENSION_MASTERS_BEST)+1));\n        }\n',
      '            VarSet(VAR_ASCENSION_MASTERS_BEST,min(9999,VarGet(VAR_ASCENSION_MASTERS_BEST)+1));\n        }\n'
      '        if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && FlagGet(FLAG_ARENA_PRACTICE) && gBattleMons[0].hp==0)\n'
      '        {\n'
      '            u16 zero=0; u32 k;\n'
      '            for(k=0;k<PARTY_SIZE;k++)\n'
      '                if(GetMonData(&gPlayerParty[k],MON_DATA_SPECIES))SetMonData(&gPlayerParty[k],MON_DATA_HP,&zero);\n'
      '        }\n')

# Out of PP must never drop a Wildlands match into the classic turn-based
# battle (playtest: "kicked out after I won", then every battle was classic
# because the saved party had no PP left). In the world, an actor with no PP
# uses Struggle, eligibility ignores PP, and the arena never exits for PP.
patch(A, '    if(FirstMove(side,TRUE)==ARENA_NO_MOVE)return FALSE;\n',
      '    if(FirstMove(side,!WildlandsWorld_Active())==ARENA_NO_MOVE)return FALSE;\n')
patch(A, '            && (FirstMove(0,TRUE)==ARENA_NO_MOVE || FirstMove(1,TRUE)==ARENA_NO_MOVE))\n',
      '            && !WildlandsWorld_Active()\n'
      '            && (FirstMove(0,TRUE)==ARENA_NO_MOVE || FirstMove(1,TRUE)==ARENA_NO_MOVE))\n')

patch(A, '                sArena.bodies[i].moveSlot=FirstMove(i,TRUE);\n',
      '                {u8 m=FirstMove(i,TRUE); sArena.bodies[i].moveSlot=(m==ARENA_NO_MOVE&&WildlandsWorld_Active())?ARENA_STRUGGLE_SLOT:m;}\n')

# Sprite size normalisation (playtest: Zapdos drawn tiny).
patch(A, 'static u16 MonVisualScale(u8 side)\n{\n    switch (gBattleMons[side].species)\n    {\n    case SPECIES_MEWTWO:\n    case SPECIES_LUGIA:\n    case SPECIES_HO_OH:\n    case SPECIES_KYOGRE:\n    case SPECIES_RAYQUAZA: return 304;\n    case SPECIES_ARTICUNO:\n    case SPECIES_ZAPDOS:\n    case SPECIES_RAIKOU:\n    case SPECIES_ENTEI:\n    case SPECIES_SUICUNE:\n    case SPECIES_REGIROCK:\n    case SPECIES_REGICE:\n    case SPECIES_REGISTEEL: return 248;\n    case SPECIES_DRAGONITE:\n    case SPECIES_SNORLAX:\n    case SPECIES_BLASTOISE:\n    case SPECIES_CHARIZARD:\n    case SPECIES_SALAMENCE:\n    case SPECIES_METAGROSS: return 236;\n    default: return 230;\n    }\n}\n', '// Visual size from the art itself: the PMD frames vary a lot (Zapdos is\n// drawn 23px wide, Lapras 43px), so small art is scaled up toward a target\n// from the Pokedex height. Never shrinks below the old default; the five\n// lair legendaries keep their tuned boss size. Cached per side.\nextern const struct PokedexEntry gPokedexEntries[];\nstatic EWRAM_DATA u16 sScaleSpecies[2] = {0};\nstatic EWRAM_DATA u16 sScaleValue[2] = {0};\nstatic u32 MonArtExtent(const struct ArenaSpriteSet *art)\n{\n    const struct ArenaSpriteAnimation *anim = &art->animations[ARENA_ANIM_IDLE];\n    const u32 *header = (const u32 *)anim->tiles;\n    const u16 *map = (const u16 *)(anim->tiles + 8);\n    const u32 *dict = (const u32 *)(anim->tiles + header[0]);\n    s32 x0 = 64, x1 = -1, y0 = 64, y1 = -1;\n    u32 t, y, x;\n    for (t = 0; t < 64; t++)\n    {\n        const u32 *src;\n        if (map[t] >= header[1]) continue;\n        src = dict + map[t] * 8;\n        for (y = 0; y < 8; y++)\n        {\n            u32 row = src[y];\n            if (!row) continue;\n            for (x = 0; x < 8; x++)\n                if ((row >> (x * 4)) & 15)\n                {\n                    s32 px = (t % 8) * 8 + x, py = (t / 8) * 8 + y;\n                    if (px < x0) x0 = px;\n                    if (px > x1) x1 = px;\n                    if (py < y0) y0 = py;\n                    if (py > y1) y1 = py;\n                }\n        }\n    }\n    if (x1 < 0) return 0;\n    return max(x1 - x0, y1 - y0) + 1;\n}\nstatic u16 WildlandsArtScale(u16 species, const struct ArenaSpriteSet *art)\n{\n    u32 extent, target, scale = 230, h;\n    switch (species)\n    {\n    case SPECIES_MEWTWO:\n    case SPECIES_LUGIA:\n    case SPECIES_HO_OH:\n    case SPECIES_KYOGRE:\n    case SPECIES_RAYQUAZA: return 304;\n    }\n    if (art && (extent = MonArtExtent(art)) != 0)\n    {\n        h = gPokedexEntries[SpeciesToNationalPokedexNum(species)].height;\n        target = h <= 6 ? 21 : h <= 12 ? 24 : h <= 20 ? 27 : 30;\n        scale = target * 256 / extent;\n        if (scale < 230) scale = 230;\n        if (scale > 400) scale = 400;\n    }\n    return scale;\n}\nstatic u16 MonVisualScale(u8 side)\n{\n    u16 species = gBattleMons[side].species;\n    u32 scale;\n    switch (species)\n    {\n    case SPECIES_MEWTWO:\n    case SPECIES_LUGIA:\n    case SPECIES_HO_OH:\n    case SPECIES_KYOGRE:\n    case SPECIES_RAYQUAZA: return 304;\n    }\n    if (sScaleSpecies[side] == species && sScaleValue[side])\n        return sScaleValue[side];\n    scale = WildlandsArtScale(species, sArena.bodies[side].art);\n    sScaleSpecies[side] = species;\n    sScaleValue[side] = scale;\n    return scale;\n}\n')

# Enemy positioning: firing spots are scored by how boxed-in they are, so the
# AI keeps an exit instead of backing into a wall to stand and shoot.
patch(A, '        score = Abs(ArenaNav_Distance(p.x,p.y,sArena.observed.x,sArena.observed.y) - preferred) * 3\n'
         '            + ArenaNav_Distance(body->x/Q,body->y/Q,p.x,p.y) + AiRandom() % 24;\n',
      '        score = Abs(ArenaNav_Distance(p.x,p.y,sArena.observed.x,sArena.observed.y) - preferred) * 3\n'
      '            + ArenaNav_Distance(body->x/Q,body->y/Q,p.x,p.y) + AiRandom() % 24\n'
      '            + (WildlandsWorld_Active() ? WildlandsCramp(p.x,p.y) * 18 : 0);\n')

# Beta: a Wildlands match never falls back to the classic battle. A battler
# without a real-time attack gets the Wildlands loadout first; held items and
# abilities the arena does not model are tolerated instead of disqualifying.
patch(A, 'static bool8 SupportedBattler(u8 side)\n{\n    u32 i;\n',
      'static bool8 SupportedBattler(u8 side)\n{\n    u32 i;\n'
      '    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE))   /* eligibility runs before the world is initialised */\n'
      '    {\n'
      '        struct Pokemon *mon = side ? &gEnemyParty[gBattlerPartyIndexes[side]] : &gPlayerParty[gBattlerPartyIndexes[side]];\n'
      '        gArenaCompatibilityReason = ARENA_COMPAT_OK;\n'
      '        /* Only animated (real-time) moves in the world: the player duo is\n'
      '           swept every deploy (legal + arena-supported moves kept, gaps filled). */\n'
      '        if (!side)\n'
      '        {\n'
      '            u32 k;\n'
      '            for (k = 0; k < PARTY_SIZE; k++)\n'
      '                if (GetMonData(&gPlayerParty[k], MON_DATA_SPECIES) && !GetMonData(&gPlayerParty[k], MON_DATA_IS_EGG))\n'
      '                    Wildlands_ArenaLoadout(&gPlayerParty[k]);\n'
      '        }\n'
      '        if (!side || FirstMove(side, FALSE) == ARENA_NO_MOVE || !gBattleMoves[ArenaMoveId(side, FirstMove(side, FALSE))].power)\n'
      '        {\n'
      '            if (side) Wildlands_ArenaLoadout(mon);\n'
      '            for (i = 0; i < MAX_MON_MOVES; i++)\n'
      '            {\n'
      '                gBattleMons[side].moves[i] = GetMonData(mon, MON_DATA_MOVE1 + i);\n'
      '                gBattleMons[side].pp[i] = GetMonData(mon, MON_DATA_PP1 + i);\n'
      '            }\n'
      '        }\n'
      '        return gBattleMons[side].hp != 0;\n'
      '    }\n')

# Swimming in deep water is 3/4 speed (fliers unaffected).
patch(A, '    speed=speed*MonMassSpeedFactor(side)/256;\n',
      '    speed=speed*MonMassSpeedFactor(side)/256;\n'
      '    if(WildlandsWorld_Active())speed=speed*WildlandsWorld_SwimFactor(side,sArena.bodies[side].x/Q,sArena.bodies[side].y/Q)/256;\n')

# Beta controls and pause pages: SELECT swaps lead and partner in the world;
# the pause menu's POKEMON/BAG (which left the match for native menus) become
# TEAM and LOG pages.
patch(A, '    if (JOY_NEW(SELECT_BUTTON) && !ClashBusy()',
      '    if (JOY_NEW(SELECT_BUTTON) && WildlandsWorld_Active()) { if (!sArena.paused && !sArena.resultTimer) SquadSwapLead(); }\n'
      '    else if (JOY_NEW(SELECT_BUTTON) && !ClashBusy()')
patch(A, '            static const u8 labels[5][18]={_("POKEMON"),_("BAG"),_("MOVES"),_("RESUME"),_("MAP")};\n',
      '            static const u8 labels[5][18]={_("POKEMON"),_("BAG"),_("MOVES"),_("RESUME"),_("MAP")};\n'
      '            static const u8 wlabels[5][18]={_("TEAM"),_("LOG"),_("MOVES"),_("RESUME"),_("MAP")};\n')
patch(A, '                PrintPopup(18,15+side*10,labels[side],side==sPauseChoice?5:4);\n',
      '                PrintPopup(18,15+side*10,WildlandsWorld_Active()?wlabels[side]:labels[side],side==sPauseChoice?5:4);\n')
patch(A, '                if(sPauseChoice<2 && !ClashBusy() && !GuardBusy() && !SpecialBusy(0) && !SpecialBusy(1))\n',
      '                if(sPauseChoice<2 && WildlandsWorld_Active()){sPausePage=5+sPauseChoice;sArena.hudDirty=TRUE;}\n'
      '                else if(sPauseChoice<2 && !ClashBusy() && !GuardBusy() && !SpecialBusy(0) && !SpecialBusy(1))\n')
patch(A, '        else if(sPausePage==4)MapDraw();\n',
      '        else if(sPausePage==4)MapDraw();\n'
      '        else if(sPausePage==5)WildlandsTeamDraw();\n'
      '        else if(sPausePage==6)WildlandsLogDraw();\n')

# Native resolver: battler parity selects the party (battlers 2/3 exist now).
patch('src/battle_script_commands.c',
      'SetMonData(target?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);',
      'SetMonData((target&1)?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);')
print('Wildlands V5 squad combat + closing zone installed: 4 battlers, wing combat, team targeting, promotion on KO, world-coordinate storm with time-based exposure')
