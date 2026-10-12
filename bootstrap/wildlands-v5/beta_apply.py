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
patch(A, '#include "arena_director.inc"\n', '#include "arena_status.inc"\n#include "arena_director.inc"\n')
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
# V6.2: 60 fps while exploring (adaptive, see WildlandsPaceUpdate).
patch(A, '    if(WildlandsWorld_Active()&&gap<2){sWildlandsHeldNew|=gMain.newKeys;return;}\n',
      '    if(WildlandsWorld_Active()&&gap<(WildlandsFastPace()?1:2)){sWildlandsHeldNew|=gMain.newKeys;return;}\n'
      '    WildlandsPaceUpdate(gap);\n')
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nstatic bool8 WildlandsFastPace(void);\nstatic void WildlandsPaceUpdate(u32 gap);\n')
# V6.3: no EXP in Wildlands (fixed levels; a won match used to pop
# "+914 EXP" in the Lab and level the duo past the match level).
patch(B, '#include "event_data.h"\n', '#include "event_data.h"\n#include "constants/vars.h"\n#include "constants/flags.h"\n')
patch(B, '    gBattlerFainted = GetBattlerForBattleScript(gBattlescriptCurrInstr[1]);\n    sentIn = gSentPokesToOpponent[(gBattlerFainted & 2) >> 1];\n',
      '    gBattlerFainted = GetBattlerForBattleScript(gBattlescriptCurrInstr[1]);\n    sentIn = gSentPokesToOpponent[(gBattlerFainted & 2) >> 1];\n'
      '    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 && FlagGet(FLAG_ARENA_PRACTICE))\n'
      '    {\n        gBattleScripting.getexpState = 0;\n        gBattlescriptCurrInstr += 2;\n        return;\n    }\n')
# The classic arena's 7 fixed props do not exist in the world: retire them
# so Psychic / toss chains never reach for an invisible rock.
patch(A, '    DirectorInit();\n    sWildlandsEncounterLive = WildlandsWorld_Active();\n',
      '    DirectorInit();\n'
      '    if (WildlandsWorld_Active())\n    {\n        u32 k;\n        for (k = 0; k < ARENA_OBSTACLES; k++)\n'
      '        { gArenaProps[k].broken = 1; gArenaProps[k].hp = 0; ArenaNav_SetObstacle(k, 0); }\n    }\n'
      '    sWildlandsEncounterLive = WildlandsWorld_Active();\n')
# FPS: the enemy's move choice (a type-chart walk per move) ran every frame
# its cooldown was 0; in the world it re-picks every 4th frame.
patch(A, '        if(!body->cooldown)AiChooseMove(distance);\n',
      '        if(!body->cooldown && (!WildlandsWorld_Active() || (sArena.frame & 3) == 2))AiChooseMove(distance);\n')
# FPS: a coarse 32px "anything solid or deep water here?" bitmap lets line
# and footprint checks over open ground return at once instead of marching
# a body circle every few pixels (SolidCircle was the top walking cost).
import re as _re
_hdr = (root / 'include/wildlands_world_data.h').read_text()
_W = int(_re.search(r'#define WL_SLICE_W (\d+)', _hdr).group(1))
_H = int(_re.search(r'#define WL_SLICE_H (\d+)', _hdr).group(1))
_terr = (root / 'data/wildlands_world/terrain.bin').read_bytes()
_cw, _ch = (_W + 1) // 2, (_H + 1) // 2
_bits = bytearray((_cw * _ch + 7) // 8)
for _by in range(_ch):
    for _bx in range(_cw):
        _dirty = False
        for _j in (0, 1):
            for _i in (0, 1):
                _x, _y = _bx * 2 + _i, _by * 2 + _j
                if _x >= _W or _y >= _H or (_terr[_y * _W + _x] & 3):
                    _dirty = True
        if _dirty:
            _k = _by * _cw + _bx
            _bits[_k >> 3] |= 1 << (_k & 7)
(root / 'include/wildlands_coarse.inc').write_text(
    f'#define WL_COARSE_W {_cw}\n#define WL_COARSE_H {_ch}\n'
    'static const u8 sWlCoarse[] = {' + ','.join(map(str, _bits)) + '};\n')
WW = 'src/wildlands_world.c'
patch(WW, '#include "wildlands_biomes.inc"\n', '#include "wildlands_biomes.inc"\n#include "wildlands_coarse.inc"\n')
patch(WW, 'static bool8 SolidCircle(s16 x, s16 y, u8 radius)\n{',
'''// TRUE when the segment's bounding box (grown by r) touches no solid or
// deep-water metatile: any sweep along it would pass.
EWRAM_DATA u32 gWildlandsCoarseTelemetry[2] = {0};   // [0] fast passes [1] full sweeps
static bool8 CoarseClear(s32 x1, s32 y1, s32 x2, s32 y2, s32 r)
{
    s32 bx0 = (((x1 < x2 ? x1 : x2) - r) >> 4) - WL_SLICE_BASE_X, bx1 = (((x1 > x2 ? x1 : x2) + r) >> 4) - WL_SLICE_BASE_X;
    s32 by0 = (((y1 < y2 ? y1 : y2) - r) >> 4) - WL_SLICE_BASE_Y, by1 = (((y1 > y2 ? y1 : y2) + r) >> 4) - WL_SLICE_BASE_Y;
    s32 bx, by;
    if (bx0 < 0 || by0 < 0 || bx1 >= WL_SLICE_W || by1 >= WL_SLICE_H)
        return FALSE;
    bx0 >>= 1; bx1 >>= 1; by0 >>= 1; by1 >>= 1;
    if ((bx1 - bx0 + 1) * (by1 - by0 + 1) > 64)
        return FALSE;
    for (by = by0; by <= by1; by++)
        for (bx = bx0; bx <= bx1; bx++)
        {
            u32 k = by * WL_COARSE_W + bx;
            if (sWlCoarse[k >> 3] & (1 << (k & 7)))
            { gWildlandsCoarseTelemetry[1]++; return FALSE; }
        }
    gWildlandsCoarseTelemetry[0]++;
    return TRUE;
}

static bool8 SolidCircle(s16 x, s16 y, u8 radius)
{''')
patch(WW, '''    if (!sActive)
        return TRUE;
    if (radius <= 2)
        return RayClear(x1, y1, x2, y2);''', '''    if (!sActive)
        return TRUE;
    if (CoarseClear(x1, y1, x2, y2, radius))
        return TRUE;
    if (radius <= 2)
        return RayClear(x1, y1, x2, y2);''')
patch(WW, '''    if (radius > WL_WORLD_BODY_RADIUS)
        radius = WL_WORLD_BODY_RADIUS;
''', '''    if (radius > WL_WORLD_BODY_RADIUS)
        radius = WL_WORLD_BODY_RADIUS;
    if (CoarseClear(x1, y1, x2, y2, radius))
        return TRUE;
''')
patch(WW, '''    if (!sActive)
        return distance;
    if (SolidCircle(x, y, radius))
        return 0;''', '''    if (!sActive)
        return distance;
    if (CoarseClear(x, y, x + dx * distance / 256, y + dy * distance / 256, radius))
        return distance;
    if (SolidCircle(x, y, radius))
        return 0;''')
# FPS: lean sprite animation in the world (parked sprites skipped).
patch(A, '    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[6]=p1-p0;p0=p1;\n    AnimateSprites();\n',
      '    p1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;gWildlandsProfile[6]=p1-p0;p0=p1;\n    WildlandsAnimateSprites();\n')
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n', '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nstatic void WildlandsAnimateSprites(void);\n')
# V6.4 FPS: world OAM build. The stock build sorts all 64 sprite slots with a
# pairwise insertion sort that re-derives Y for both sprites at every compare,
# and makes four passes. The world build makes one pass over visible,
# on-screen sprites, packs (priority, Y descending, index) into one key and
# sorts those keys. Same order rules as SortSprites; ties break by index.
p = root / 'src/sprite.c'
p.write_text(p.read_text() + r"""
void WildlandsBuildOamFast(void)
{
    u32 keys[MAX_SPRITES];
    u32 n = 0, i, j, k;
    u8 oamIndex = 0, temp;
    for (i = 0; i < MAX_SPRITES; i++)
    {
        struct Sprite *s = &gSprites[i];
        s32 x, y;
        if (!s->inUse || s->invisible)
            continue;
        x = s->x + s->x2;
        y = s->y + s->y2;
        if (s->coordOffsetEnabled)
        {
            x += gSpriteCoordOffsetX;
            y += gSpriteCoordOffsetY;
            if (x < -64 || x > 304 || y < -64 || y > 224)
                continue;   /* far off screen: 9-bit X / 8-bit Y would wrap */
        }
        s->oam.x = x + s->centerToCornerVecX;
        s->oam.y = y + s->centerToCornerVecY;
        y = s->oam.y;
        if (y >= DISPLAY_HEIGHT)
            y -= 256;
        if (s->oam.affineMode == ST_OAM_AFFINE_DOUBLE && s->oam.size == ST_OAM_SIZE_3
         && (s->oam.shape == ST_OAM_SQUARE || s->oam.shape == ST_OAM_V_RECTANGLE) && y > 128)
            y -= 256;
        k = ((u32)(s->subpriority | (s->oam.priority << 8)) << 15) | ((u32)(255 - y) << 6) | i;
        for (j = n; j > 0 && keys[j - 1] > k; j--)
            keys[j] = keys[j - 1];
        keys[j] = k;
        n++;
    }
    temp = gMain.oamLoadDisabled;
    gMain.oamLoadDisabled = TRUE;
    for (i = 0; i < n; i++)
        if (AddSpriteToOamBuffer(&gSprites[keys[i] & 63], &oamIndex))
            break;
    while (oamIndex < gOamLimit)
        gMain.oamBuffer[oamIndex++] = gDummyOamData;
    CopyMatricesToOamBuffer();
    gMain.oamLoadDisabled = temp;
    sShouldProcessSpriteCopyRequests = TRUE;
}
""")
# V6.4 FPS: the enemy's move scoring re-scanned the whole type chart up to
# five times per move; memoise per sim frame (target and attacker are fixed
# within one frame).
patch(A, 'static s32 AiTypeValue(u16 move)\n{\n', 'static s32 AiTypeValueRaw(u16 move)\n{\n')
patch(A, '    return value;\n}\n\n#include "ascension_ai_tactics.inc"\n',
      '    return value;\n}\n'
      'static u16 sAiTvFrame, sAiTvMove[6];\nstatic s32 sAiTvVal[6];\nstatic u8 sAiTvN;\n'
      'static s32 AiTypeValue(u16 move)\n{\n    u32 i;\n    s32 v;\n'
      '    if (sAiTvFrame != (u16)(sArena.frame + 1)) { sAiTvFrame = sArena.frame + 1; sAiTvN = 0; }\n'
      '    for (i = 0; i < sAiTvN; i++)\n        if (sAiTvMove[i] == move)\n            return sAiTvVal[i];\n'
      '    v = AiTypeValueRaw(move);\n'
      '    if (sAiTvN < 6) { sAiTvMove[sAiTvN] = move; sAiTvVal[sAiTvN] = v; sAiTvN++; }\n'
      '    return v;\n}\n\n#include "ascension_ai_tactics.inc"\n')
# The aim line's blocked tint: a line-of-sight sweep every rendered frame;
# in the world every 4th render is plenty.
patch(A, '    gArenaCombatTelemetry.aimBlocked = !ArenaNav_LineClear(sArena.bodies[0].x/Q,\n        sArena.bodies[0].y/Q, DecoyAim(1,FALSE)/Q, DecoyAim(1,TRUE)/Q, 2);\n',
      '    {\n        static u8 sAimTick;\n        if (!WildlandsWorld_Active() || !(++sAimTick & 3))\n'
      '            gArenaCombatTelemetry.aimBlocked = !ArenaNav_LineClear(sArena.bodies[0].x/Q,\n        sArena.bodies[0].y/Q, DecoyAim(1,FALSE)/Q, DecoyAim(1,TRUE)/Q, 2);\n    }\n')
print('V6.2 status installed: short stuns, timed burn/poison, partners included, HUD countdown, debris pool 20')
