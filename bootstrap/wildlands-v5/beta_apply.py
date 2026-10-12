#!/usr/bin/env python3
"""WildLands Beta: status effects in the world, HUD status tags, biome weather
damage.

- A burn/poison tick that knocks out a lead goes through the squad (the
  partner takes over, a beaten enemy duo is replaced) instead of ending the
  match on the spot.
- The HUD shows each lead's status (PAR SLP BRN PSN FRZ) next to its level.
- Move damage takes the biome weather into account (Wildlands_WeatherPercent
  in arena_zone.inc): sandstorm, ashfall, storm rain.
"""
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
shutil.copy(here / 'arena_status.inc', root / 'src/arena_status.inc')


def patch(path, old, new, count=1):
    p = root / path
    s = p.read_text()
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new))


A = 'src/realtime_arena.c'
patch(A, """                if(!gBattleMons[side].hp)
                {
                    sArena.resultTimer=12;sArena.lastAttacker=side^1;sArena.lastTarget=side;
                    gArenaResultTelemetry.started=gMain.vblankCounter1;
                }
            }
        }
        else body->burnClock=0;""", """                if(!gBattleMons[side].hp)
                {
                    if(WildlandsWorld_Active())
                    {
                        // The squad decides: partner takes over / next duo.
                        gWildlandsStatusTelemetry[1]++;
                        SquadKO(side,side^1);
                        continue;
                    }
                    sArena.resultTimer=12;sArena.lastAttacker=side^1;sArena.lastTarget=side;
                    gArenaResultTelemetry.started=gMain.vblankCounter1;
                }
            }
        }
        else body->burnClock=0;""")

H = 'src/arena_hud.inc'
patch(H, 'static EWRAM_DATA u8 sHudLastLevel[2]={};',
      'static EWRAM_DATA u8 sHudLastLevel[2]={};\n'
      'static EWRAM_DATA u32 sHudStatusKey=0;\n'
      'static u8 WlStatusSeconds(u8 b);\n'
      'extern u16 gWildlandsStatusTelemetry[4];\n'
      '// 0 none, 1 PAR, 2 SLP, 3 BRN, 4 PSN, 5 FRZ\n'
      'static u8 HudStatusCode(u32 s)\n'
      '{\n'
      '    return (s&STATUS1_PARALYSIS)?1:(s&STATUS1_SLEEP)?2:(s&STATUS1_BURN)?3:(s&STATUS1_PSN_ANY)?4:(s&STATUS1_FREEZE)?5:0;\n'
      '}\n'
      'static u32 HudStatusKey(void)\n'
      '{\n'
      '    return HudStatusCode(gBattleMons[0].status1)|(HudStatusCode(gBattleMons[1].status1)<<4)\n'
      '        |((u32)WlStatusSeconds(0)<<8)|((u32)WlStatusSeconds(1)<<16);\n'
      '}\n')
patch(H, '        && sHudWingKey==WildlandsHudWingKey())return;',
      '        && sHudWingKey==WildlandsHudWingKey() && sHudStatusKey==HudStatusKey())return;')
patch(H, '        && sHudWingKey==WildlandsHudWingKey())\n    {',
      '        && sHudWingKey==WildlandsHudWingKey() && sHudStatusKey==HudStatusKey())\n    {')
patch(H, '        HudTiny(side?205:84,3,text,4,7);\n',
      '        HudTiny(side?205:84,3,text,4,7);\n'
      '        {\n'
      '            static const u8 sStatusTag[5][4]={_("PAR"),_("SLP"),_("BRN"),_("PSN"),_("FRZ")};\n'
      '            static const u8 sStatusColor[5]={7,4,6,6,4};\n'
      '            u8 code=HudStatusCode(mon->status1);\n'
      '            if(code)\n'
      '            {\n'
      '                u8 tag[8],*e=StringCopy(tag,sStatusTag[code-1]);\n'
      '                if(WlStatusSeconds(side))ConvertIntToDecimalStringN(e,WlStatusSeconds(side),STR_CONV_MODE_LEFT_ALIGN,2);\n'
      '                HudTiny(side?183:62,3,tag,sStatusColor[code-1],5);\n'
      '                gWildlandsStatusTelemetry[0]++;\n'
      '            }\n'
      '        }\n')
patch(H, '    WildlandsHudWingBars();\n    sHudWingKey=WildlandsHudWingKey();\n',
      '    WildlandsHudWingBars();\n    sHudWingKey=WildlandsHudWingKey();\n    sHudStatusKey=HudStatusKey();\n')

B = 'src/battle_script_commands.c'
patch(B, 's32 RealtimeArena_ResolveDamage(u8 attacker, u8 target, u16 move)\n{',
      'u16 Wildlands_WeatherPercent(u8 type);\n'
      's32 RealtimeArena_ResolveDamage(u8 attacker, u8 target, u16 move)\n{')
patch(B, '    result = (gMoveResultFlags & MOVE_RESULT_NO_EFFECT) ? 0 : gBattleMoveDamage;\n'
         '    if (attacker == 0) gBattleResults.lastUsedMovePlayer = move;',
      '    result = (gMoveResultFlags & MOVE_RESULT_NO_EFFECT) ? 0 : gBattleMoveDamage;\n'
      '    if (result > 0)\n'
      '        result = max(1, result * Wildlands_WeatherPercent(gBattleMoves[move].type) / 100);   // biome weather\n'
      '    if (attacker == 0) gBattleResults.lastUsedMovePlayer = move;')
print('Beta status/weather installed: squad-routed status KOs, HUD status tags, biome weather damage')

# V6.2 status: short world statuses for all four battlers (arena_status.inc).
patch(A, '#include "arena_props.inc"\n', '#include "arena_props.inc"\n#include "arena_status.inc"\n')
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n'
      '// World: paralysis is a short full stun like sleep and freeze.\n'
      '#define WL_STUN_MASK (WildlandsWorld_Active() ? (STATUS1_SLEEP|STATUS1_FREEZE|STATUS1_PARALYSIS) : (STATUS1_SLEEP|STATUS1_FREEZE))\n')
patch(A, '        || (gBattleMons[side].status1&(STATUS1_SLEEP|STATUS1_FREEZE))) return;',
      '        || (gBattleMons[side].status1&WL_STUN_MASK)) return;')
patch(A, '        if(gBattleMons[side].status1&(STATUS1_SLEEP|STATUS1_FREEZE))\n        {body->shotTimer=body->actionLife=body->dash=0;continue;}',
      '        if(gBattleMons[side].status1&WL_STUN_MASK)\n        {body->shotTimer=body->actionLife=body->dash=0;continue;}')
patch(A, '    if(gBattleMons[0].status1&(STATUS1_SLEEP|STATUS1_FREEZE))\n    {body->moving=FALSE;',
      '    if(gBattleMons[0].status1&WL_STUN_MASK)\n    {body->moving=FALSE;')
patch(A, '    if(gBattleMons[1].status1&(STATUS1_SLEEP|STATUS1_FREEZE))return;',
      '    if(gBattleMons[1].status1&WL_STUN_MASK)return;')
patch(A, 'static void TickBurn(void)\n{\n    u32 side;\n',
      'static void TickBurn(void)\n{\n    u32 side;\n    if(WildlandsWorld_Active())return;   // the world runs its own status clock (arena_status.inc)\n')
# Memory: a 20-piece debris pool (was 32) frees EWRAM for the status and AI state.
patch('include/arena_physics.h', '#define ARENA_FRAGMENTS 32', '#define ARENA_FRAGMENTS 20')
# V6.2 AI: enemy duos strafe around their target (firing-spot score), a
# winding-up boss stands still.
patch(A, '            + (WildlandsWorld_Active() ? WildlandsCramp(p.x,p.y) * 18 : 0);\n',
      '            + (WildlandsWorld_Active() ? WildlandsCramp(p.x,p.y) * 18 - WildlandsStrafe(body->x/Q,body->y/Q,p.x,p.y) : 0);\n')
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nstatic s32 WildlandsStrafe(s32 bx, s32 by, s32 px, s32 py);\nstatic bool8 DirectorBossWindup(void);\n')
patch(A, '    body->moving = FALSE;\n    if (gWildlandsTestPeace) return;\n',
      '    body->moving = FALSE;\n    if (gWildlandsTestPeace) return;\n    if (DirectorBossWindup()) return;\n')
print('V6.2 status installed: short stuns, timed burn/poison, partners included, HUD countdown, debris pool 20')
