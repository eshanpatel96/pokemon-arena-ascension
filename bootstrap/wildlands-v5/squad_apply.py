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
      'static void SquadEnemyRetarget(struct ArenaBody *body);\n'
      'extern EWRAM_DATA u32 gWildlandsSquadTelemetry[16];\n'
      'static EWRAM_DATA u8 sSquadShotOwner[SHOTS_COUNT] = {};\n'
      'static void SquadSimStep(void);\n'
      'static void ZoneInit(void);\nstatic void ZoneTick(void);\nstatic void ZoneDestroy(void);\n'
      'static void ZoneSteerEnemy(struct ArenaBody *body);\nstatic void ZoneHudLine(void);\nstatic u32 ZoneHudKey(void);\n'
      'static bool8 ZoneSteer(s32 x, s32 y, s32 *goalX, s32 *goalY);\n'
      'static EWRAM_DATA u32 sZoneHudKeyShown = 0;\n'
      'static EWRAM_DATA bool8 sWildlandsEncounterLive = FALSE;\n'
      'static EWRAM_DATA u8 sWildlandsSimSteps = 1;\n'
      'static void LootInit(void);\nstatic void LootTick(void);\nstatic void LootDestroy(void);\n'
      'static void MapDraw(void);\nEWRAM_DATA u32 gWildlandsMapTelemetry[4] = {};\n'
      'EWRAM_DATA u16 gWildlandsProfile[12] = {};\n'
      '// TEST HOOK ONLY: harness sets 1 to hold AI fire/movement while checking\n'
      '// map/zone UI; always 0 in normal play.\n'
      'EWRAM_DATA u8 gWildlandsTestPeace = 0;\n')
# The follower actor is superseded by real squad wings.
patch(A, '    WildlandsPartner_Init();\n', '    SquadInit();\n    ZoneInit();\n    LootInit();\n    sWildlandsEncounterLive = WildlandsWorld_Active();\n')
patch(A, '    WildlandsPartner_Update();\n', '    SquadTick();\n')
patch(A, 'WildlandsPartner_Destroy();', 'SquadDestroy();ZoneDestroy();LootDestroy();', count=2)
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
# Module body: after DestroyShot (needs shots, Fire helpers, SpecialInvulnerable).
patch(A, 'static void TickShots(void)\n{', '#include "arena_squad.inc"\n#include "arena_loot.inc"\n#include "arena_zone.inc"\n#include "arena_map.inc"\n\nstatic void TickShots(void)\n{')
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
      '        {\n        u8 simStep, simSteps = WildlandsWorld_Active() ? (gap >= 3 ? 3 : gap >= 2 ? 2 : 1) : 1;\n'
      '        u16 savedNewKeys = gMain.newKeys;\n'
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

# Profiling: camera/stream, sprite animation, OAM build (scanlines).
patch(A, '    ArenaXL_UpdateCamera();\n    AnimateSprites();\n    BuildOamBuffer();',
      '    {u32 p0=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228,p1;\n'
      '    ArenaXL_UpdateCamera();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[6]=p1-p0;p0=p1;\n'
      '    AnimateSprites();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[7]=p1-p0;p0=p1;\n'
      '    BuildOamBuffer();\n    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[8]=p1-p0;\n'
      '    {u32 n=0,k;for(k=0;k<MAX_SPRITES;k++)if(gSprites[k].inUse)n++;gWildlandsProfile[9]=n;}}')

# Native resolver: battler parity selects the party (battlers 2/3 exist now).
patch('src/battle_script_commands.c',
      'SetMonData(target?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);',
      'SetMonData((target&1)?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);')
print('Wildlands V5 squad combat + closing zone installed: 4 battlers, wing combat, team targeting, promotion on KO, world-coordinate storm with time-based exposure')
