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
import sys

root = Path(sys.argv[1])


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
      'static EWRAM_DATA u8 sHudStatusKey=0;\n'
      'extern u16 gWildlandsStatusTelemetry[4];\n'
      '// 0 none, 1 PAR, 2 SLP, 3 BRN, 4 PSN, 5 FRZ\n'
      'static u8 HudStatusCode(u32 s)\n'
      '{\n'
      '    return (s&STATUS1_PARALYSIS)?1:(s&STATUS1_SLEEP)?2:(s&STATUS1_BURN)?3:(s&STATUS1_PSN_ANY)?4:(s&STATUS1_FREEZE)?5:0;\n'
      '}\n'
      'static u8 HudStatusKey(void)\n'
      '{\n'
      '    return HudStatusCode(gBattleMons[0].status1)|(HudStatusCode(gBattleMons[1].status1)<<4);\n'
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
      '                HudTiny(side?189:68,3,sStatusTag[code-1],sStatusColor[code-1],3);\n'
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
