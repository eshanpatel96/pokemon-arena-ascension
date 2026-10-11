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
      'static void ZoneInit(void);\nstatic void ZoneTick(void);\nstatic void ZoneDestroy(void);\n'
      'static void ZoneSteerEnemy(struct ArenaBody *body);\nstatic void ZoneHudLine(void);\nstatic u32 ZoneHudKey(void);\n'
      'static bool8 ZoneSteer(s32 x, s32 y, s32 *goalX, s32 *goalY);\n'
      'static EWRAM_DATA u32 sZoneHudKeyShown = 0;\n'
      'static EWRAM_DATA bool8 sWildlandsEncounterLive = FALSE;\n'
      'static void LootInit(void);\nstatic void LootTick(void);\nstatic void LootDestroy(void);\n')
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
patch(A, 'static void TickShots(void)\n{', '#include "arena_squad.inc"\n#include "arena_loot.inc"\n#include "arena_zone.inc"\n\nstatic void TickShots(void)\n{')
# Enemy lead rotates toward the safe circle when exposed or pre-rotating.
patch(A, '    dx = sArena.waypoint.x * Q - body->x;\n', '    ZoneSteerEnemy(body);\n    dx = sArena.waypoint.x * Q - body->x;\n')
# Bottom HUD: zone countdown and squad HP replace the capture-ball help.
C = 'src/arena_capture.inc'
patch(C, '        && sCapture.hudMove==move && sCapture.hudPP==pp)return;',
      '        && sCapture.hudMove==move && sCapture.hudPP==pp && sZoneHudKeyShown==ZoneHudKey())return;')
patch(C, '            HudTinyWindow(2,81,10,text,4,5);\n        }\n        PutWindowTilemap(2);',
      '            HudTinyWindow(2,81,10,text,4,5);\n        }\n        ZoneHudLine();sZoneHudKeyShown=ZoneHudKey();\n        PutWindowTilemap(2);')

# Native resolver: battler parity selects the party (battlers 2/3 exist now).
patch('src/battle_script_commands.c',
      'SetMonData(target?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);',
      'SetMonData((target&1)?&gEnemyParty[gBattlerPartyIndexes[target]]:&gPlayerParty[gBattlerPartyIndexes[target]],MON_DATA_HP,&hp);')
print('Wildlands V5 squad combat + closing zone installed: 4 battlers, wing combat, team targeting, promotion on KO, world-coordinate storm with time-based exposure')
