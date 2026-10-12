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
# V6.4 FPS: move profile lookup is a direct ROM index (move id -> profile),
# replacing the 8-slot memo that thrashed with a full duo's moves.
import re as _re
_mp = root / 'src/arena_moves.c'
_mt = _mp.read_text()
_body = _mt[_mt.index('static const struct ArenaMoveProfile sProfiles[] =\n{'):]
_body = _body[:_body.index('\n};')]
_seen, _rows = set(), []
for _k, _m in enumerate(_re.findall(r'^\s*\{(MOVE_[A-Z0-9_]+),', _body, _re.M)):
    if _m not in _seen:
        _seen.add(_m); _rows.append('    [%s] = %d,' % (_m, _k + 1))
_start = _mt.index('const struct ArenaMoveProfile *ArenaMoves_Get(u16 move)\n{')
_end = _mt.index('\n}\n', _start) + 3
_mt = (_mt[:_start] + 'static const u8 sProfileIndex[MOVES_COUNT] =\n{\n' + '\n'.join(_rows) + '\n};\n'
       'const struct ArenaMoveProfile *ArenaMoves_Get(u16 move)\n{\n'
       '    if (move >= MOVES_COUNT || !sProfileIndex[move])\n        return 0;\n'
       '    return &sProfiles[sProfileIndex[move] - 1];\n}\n' + _mt[_end:])
_mt = _mt.replace('static EWRAM_DATA u16 sProfileMemoMove[8] = {0};\n', '').replace('static EWRAM_DATA u8 sProfileMemoIdx[8] = {0};\n', '')
_mp.write_text(_mt)
print('move profile index:', len(_rows), 'moves')
# V6.4 FPS: pushing into a wall asked the corner assist (up to 20 footprint
# tests) every frame from the same spot; a blocked spot's "no opening" answer
# is reused until the player, the direction or the room changes.
patch(WW, 's8 WildlandsWorld_SlideNudge(u8 side, s16 x, s16 y, s8 sx, s8 sy)\n{',
      'static s8 SlideNudgeRaw(u8 side, s16 x, s16 y, s8 sx, s8 sy);\n'
      'static s16 sNudgeX, sNudgeY;\nstatic bool8 sNudgeValid;   /* no initialisers: .data is discarded for this object */\nstatic s8 sNudgeSx, sNudgeSy;\nstatic u32 sNudgeRoom;\nstatic u16 sNudgeSpecies;\n'
      's8 WildlandsWorld_SlideNudge(u8 side, s16 x, s16 y, s8 sx, s8 sy)\n{\n'
      '    s8 n;\n'
      '    if (sNudgeValid && x == sNudgeX && y == sNudgeY && sx == sNudgeSx && sy == sNudgeSy && sNudgeRoom == gWildlandsRoomTelemetry[2] && sNudgeSpecies == gBattleMons[side].species)\n'
      '        return 0;\n'
      '    n = SlideNudgeRaw(side, x, y, sx, sy);\n'
      '    if (n)\n        sNudgeValid = FALSE;\n'
      '    else\n    { sNudgeValid = TRUE; sNudgeX = x; sNudgeY = y; sNudgeSx = sx; sNudgeSy = sy; sNudgeRoom = gWildlandsRoomTelemetry[2]; sNudgeSpecies = gBattleMons[side].species; }\n'
      '    return n;\n}\n'
      'static s8 SlideNudgeRaw(u8 side, s16 x, s16 y, s8 sx, s8 sy)\n{')
# V6.5: effects that count down once per drawn frame (hit flash, rollout
# squash, damage numbers, hit sparks) were tuned at the locked 30. At 60 they
# would run twice as fast, so in the world they advance at a steady 30/s.
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nstatic u8 sWlDrawAcc;\nstatic bool8 sWlDrawTick;\n')
patch(A, '    WildlandsPaceUpdate(gap);\n',
      '    WildlandsPaceUpdate(gap);\n'
      '    if (!WildlandsWorld_Active())\n        sWlDrawTick = TRUE;\n'
      '    else\n    {\n        sWlDrawAcc += gap >= 2 ? 2 : 1;\n        sWlDrawTick = sWlDrawAcc >= 2;\n        if (sWlDrawTick)\n            sWlDrawAcc -= 2;\n    }\n')
patch(A, '                if (!sArena.paused && !frozen && !--body->flat)\n',
      '                if (!sArena.paused && !frozen && sWlDrawTick && !--body->flat)\n')
patch(A, '        if (body->flash && !sArena.paused && !frozen) body->flash--;\n',
      '        if (body->flash && !sArena.paused && !frozen && sWlDrawTick) body->flash--;\n')
patch(A, '    ArenaFeedback_Update(sArena.paused, frozen && !CaptureLocked() && !ClashBusy());\n',
      '    ArenaFeedback_Update(sArena.paused, (frozen && !CaptureLocked() && !ClashBusy()) || !sWlDrawTick);\n')
# ---- V6.6 -----------------------------------------------------------------
# Legendaries press instead of kiting when hurt, and never pick a move that
# heals them or warps them away (bosses do not heal).
patch(A, '    if (p->kind == ARENA_MOVE_PROJECTILE && gBattleMons[1].hp * 3 < gBattleMons[1].maxHP) preferred += 12;\n',
      '    gWildlandsCost[4]++;\n'
      '    if (WildlandsWorld_Active() && DirectorSoloActive())\n'
      '    {\n        if (gBattleMons[1].hp * 2 < gBattleMons[1].maxHP)\n            preferred = preferred * 3 / 4;   /* V6.6: a hurt legend presses */\n    }\n'
      '    else if (p->kind == ARENA_MOVE_PROJECTILE && gBattleMons[1].hp * 3 < gBattleMons[1].maxHP) preferred += 12;\n')
patch(A, '        if(ArenaMovePP(1,i)<=2)score-=12;\n',
      '        if(ArenaMovePP(1,i)<=2)score-=12;\n'
      '        if(WildlandsWorld_Active()&&DirectorSoloActive()&&(move==MOVE_TELEPORT||move==MOVE_RECOVER||move==MOVE_REST\n'
      '            ||move==MOVE_SOFT_BOILED||move==MOVE_MILK_DRINK||move==MOVE_SYNTHESIS||move==MOVE_MOONLIGHT\n'
      '            ||move==MOVE_MORNING_SUN||move==MOVE_SLACK_OFF||move==MOVE_ABSORB||move==MOVE_MEGA_DRAIN\n'
      '            ||move==MOVE_GIGA_DRAIN||move==MOVE_LEECH_LIFE))score=-1000;\n')
patch(A, '                gBattleMons[1].hp*2<gBattleMons[1].maxHP,sArena.style);\n',
      '                gBattleMons[1].hp*2<gBattleMons[1].maxHP&&!(WildlandsWorld_Active()&&DirectorSoloActive()),sArena.style);\n')
# A lost Wildlands match ends the battle directly (like a capture does):
# no native faint/whiteout scripts, so no classic battle screen can appear
# (any unexpected battle text used to rebuild the original UI).
patch('src/battle_main.c', 'void RealtimeArena_FinishCapture(void)\n{',
      'void RealtimeArena_FinishLoss(void)\n{\n'
      '    gBattleOutcome = B_OUTCOME_LOST;\n'
      '    gCurrentActionFuncId = B_ACTION_FINISHED;\n'
      '    gBattleMainFunc = HandleEndTurn_FinishBattle;\n'
      '}\n\n'
      'void RealtimeArena_FinishCapture(void)\n{')
patch('include/arena_capture.h', 'void RealtimeArena_FinishCapture(void);\n',
      'void RealtimeArena_FinishCapture(void);\nvoid RealtimeArena_FinishLoss(void);\n')
patch(A, '        gMain.callback1=sArena.savedCB1;\n        RealtimeArena_ResumeBattle(TRUE);\n        SetMainCallback2(BattleMainCB2);\n',
      '        gMain.callback1=sArena.savedCB1;\n'
      '        if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && FlagGet(FLAG_ARENA_PRACTICE) && gBattleMons[0].hp==0)\n'
      '        {\n            gRealtimeArenaRestoringFaint=FALSE;\n            RealtimeArena_FinishLoss();   /* V6.6: straight to the whiteout */\n        }\n'
      '        else\n            RealtimeArena_ResumeBattle(TRUE);\n'
      '        SetMainCallback2(BattleMainCB2);\n')
# ---- V6.8 -----------------------------------------------------------------
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nstatic bool8 DirectorTpFocus(void);\nvoid Wildlands_ShopSelfTest(void);\n')
# Wins pay into the Shiny Shop balance; every 5th straight win pays 2 more.
# A loss resets the streak. (Saved vars: two unused Emerald slots.)
patch(A, '            VarSet(VAR_ASCENSION_MASTERS_BEST,min(9999,VarGet(VAR_ASCENSION_MASTERS_BEST)+1));\n',
      '            VarSet(VAR_ASCENSION_MASTERS_BEST,min(9999,VarGet(VAR_ASCENSION_MASTERS_BEST)+1));\n'
      '            if(gBattleMons[0].hp)\n            {\n'
      '                u16 streak=min(9999,VarGet(VAR_WL_STREAK)+1);\n'
      '                VarSet(VAR_WL_STREAK,streak);\n'
      '                VarSet(VAR_WL_SHOP_WINS,min(9999,VarGet(VAR_WL_SHOP_WINS)+1+(streak%5==0?2:0)));\n'
      '            }\n')
patch(A, '            u16 zero=0; u32 k;\n',
      '            u16 zero=0; u32 k;\n            VarSet(VAR_WL_STREAK,0);\n')
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n#define VAR_WL_SHOP_WINS VAR_UNUSED_0x404E\n#define VAR_WL_STREAK VAR_UNUSED_0x4083\n')
_mt = (root / A).read_text()
_mt += r"""
// ---- V6.8 Shiny Shop (Lab professor) -------------------------------------
// STR_VAR_1 balance, STR_VAR_2 streak; VAR_RESULT = can buy (10 wins).
void Wildlands_BufferShop(void)
{
    ConvertIntToDecimalStringN(gStringVar1, VarGet(VAR_WL_SHOP_WINS), STR_CONV_MODE_LEFT_ALIGN, 4);
    ConvertIntToDecimalStringN(gStringVar2, VarGet(VAR_WL_STREAK), STR_CONV_MODE_LEFT_ALIGN, 4);
    gSpecialVar_Result = VarGet(VAR_WL_SHOP_WINS) >= 10;
}

static bool8 WlShopLegend(u16 sp)
{
    switch (sp)
    {
    case SPECIES_ARTICUNO: case SPECIES_ZAPDOS: case SPECIES_MOLTRES: case SPECIES_MEWTWO: case SPECIES_MEW:
    case SPECIES_RAIKOU: case SPECIES_ENTEI: case SPECIES_SUICUNE: case SPECIES_LUGIA: case SPECIES_HO_OH:
    case SPECIES_CELEBI: case SPECIES_REGIROCK: case SPECIES_REGICE: case SPECIES_REGISTEEL:
    case SPECIES_LATIAS: case SPECIES_LATIOS: case SPECIES_KYOGRE: case SPECIES_GROUDON:
    case SPECIES_RAYQUAZA: case SPECIES_JIRACHI: case SPECIES_DEOXYS:
        return TRUE;
    }
    return FALSE;
}

// The party Pokemon in VAR_0x8004 becomes shiny for 10 wins. Its nature,
// gender, ability, IVs, EVs, moves, level, nickname and OT are kept (a new
// personality with the same nature and low byte is chosen).
// VAR_RESULT: 1 done, 2 legendary, 3 already shiny, 4 not enough wins, 0 none.
void Wildlands_MakeShiny(void)
{
    static const u8 sKeep[] = {
        MON_DATA_LANGUAGE, MON_DATA_OT_GENDER, MON_DATA_EXP, MON_DATA_FRIENDSHIP, MON_DATA_HELD_ITEM,
        MON_DATA_MOVE1, MON_DATA_MOVE2, MON_DATA_MOVE3, MON_DATA_MOVE4,
        MON_DATA_PP1, MON_DATA_PP2, MON_DATA_PP3, MON_DATA_PP4, MON_DATA_PP_BONUSES,
        MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV, MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV,
        MON_DATA_HP_IV, MON_DATA_ATK_IV, MON_DATA_DEF_IV, MON_DATA_SPEED_IV, MON_DATA_SPATK_IV, MON_DATA_SPDEF_IV,
        MON_DATA_ABILITY_NUM, MON_DATA_POKEBALL, MON_DATA_MET_LOCATION, MON_DATA_MET_LEVEL, MON_DATA_MET_GAME,
        MON_DATA_MARKINGS,
    };
    struct Pokemon old, *mon;
    u8 buf[POKEMON_NAME_LENGTH + 2];
    u16 sp, hp;
    u32 p, otId, lo, hi, np = 0, b, k, v;
    gSpecialVar_Result = 0;
    if (gSpecialVar_0x8004 >= PARTY_SIZE)
        return;
    mon = &gPlayerParty[gSpecialVar_0x8004];
    sp = GetMonData(mon, MON_DATA_SPECIES);
    if (!sp || GetMonData(mon, MON_DATA_IS_EGG))
        return;
    StringCopy(gStringVar1, gSpeciesNames[sp]);
    if (WlShopLegend(sp)) { gSpecialVar_Result = 2; return; }
    if (IsMonShiny(mon)) { gSpecialVar_Result = 3; return; }
    if (VarGet(VAR_WL_SHOP_WINS) < 10) { gSpecialVar_Result = 4; return; }
    p = GetMonData(mon, MON_DATA_PERSONALITY);
    otId = GetMonData(mon, MON_DATA_OT_ID);
    for (b = 0; b < 256 && !np; b++)
        for (k = 0; k < 8; k++)
        {
            lo = (p & 0xFF) | (b << 8);
            hi = ((otId >> 16) ^ (otId & 0xFFFF) ^ lo ^ k) & 0xFFFF;
            if (((hi << 16) | lo) % 25 == p % 25)
            { np = (hi << 16) | lo; break; }
        }
    if (!np)
        return;
    old = *mon;
    CreateMon(mon, sp, GetMonData(&old, MON_DATA_LEVEL), 0, TRUE, np, OT_ID_PRESET, otId);
    GetMonData(&old, MON_DATA_NICKNAME, buf); SetMonData(mon, MON_DATA_NICKNAME, buf);
    GetMonData(&old, MON_DATA_OT_NAME, buf); SetMonData(mon, MON_DATA_OT_NAME, buf);
    for (k = 0; k < ARRAY_COUNT(sKeep); k++)
    {
        v = GetMonData(&old, sKeep[k]);
        SetMonData(mon, sKeep[k], &v);
    }
    CalculateMonStats(mon);
    hp = GetMonData(mon, MON_DATA_MAX_HP);
    SetMonData(mon, MON_DATA_HP, &hp);
    VarSet(VAR_WL_SHOP_WINS, VarGet(VAR_WL_SHOP_WINS) - 10);
    gSpecialVar_Result = IsMonShiny(mon) ? 1 : 0;
}

// V6.9 browse: quote the party Pokemon in VAR_0x8004 without buying.
// STR_VAR_1 name, STR_VAR_2 wins still needed. VAR_RESULT: 1 affordable,
// 2 legendary, 3 already shiny, 4 not enough wins, 0 nothing chosen.
void Wildlands_ShopQuote(void)
{
    struct Pokemon *mon;
    u16 sp, have = VarGet(VAR_WL_SHOP_WINS);
    gSpecialVar_Result = 0;
    if (gSpecialVar_0x8004 >= PARTY_SIZE)
        return;
    mon = &gPlayerParty[gSpecialVar_0x8004];
    sp = GetMonData(mon, MON_DATA_SPECIES);
    if (!sp || GetMonData(mon, MON_DATA_IS_EGG))
        return;
    StringCopy(gStringVar1, gSpeciesNames[sp]);
    ConvertIntToDecimalStringN(gStringVar2, have >= 10 ? 0 : 10 - have, STR_CONV_MODE_LEFT_ALIGN, 2);
    gSpecialVar_Result = WlShopLegend(sp) ? 2 : IsMonShiny(mon) ? 3 : have < 10 ? 4 : 1;
}

// TEST HOOK ONLY: nonzero runs the shop core on party slot 1 at the next
// match start; [0] result [1] shiny [2] species/level/move/nature/IV kept [3] balance after.
EWRAM_DATA u8 gWildlandsShopTest = 0;
EWRAM_DATA u16 gWildlandsShopTelemetry[4] = {0};
void Wildlands_ShopSelfTest(void)
{
    struct Pokemon *mon = &gPlayerParty[1];
    u32 sp, lv, mv, nat, iv;
    if (!gWildlandsShopTest)
        return;
    gWildlandsShopTest = 0;
    sp = GetMonData(mon, MON_DATA_SPECIES); lv = GetMonData(mon, MON_DATA_LEVEL);
    mv = GetMonData(mon, MON_DATA_MOVE1); nat = GetMonData(mon, MON_DATA_PERSONALITY) % 25;
    iv = GetMonData(mon, MON_DATA_ATK_IV);
    VarSet(VAR_WL_SHOP_WINS, 10);
    gSpecialVar_0x8004 = 1;
    Wildlands_MakeShiny();
    gWildlandsShopTelemetry[0] = gSpecialVar_Result;
    gWildlandsShopTelemetry[1] = IsMonShiny(mon);
    gWildlandsShopTelemetry[2] = sp == GetMonData(mon, MON_DATA_SPECIES) && lv == GetMonData(mon, MON_DATA_LEVEL)
        && mv == GetMonData(mon, MON_DATA_MOVE1) && nat == GetMonData(mon, MON_DATA_PERSONALITY) % 25
        && iv == GetMonData(mon, MON_DATA_ATK_IV);
    gWildlandsShopTelemetry[3] = VarGet(VAR_WL_SHOP_WINS);
}
"""
(root / A).write_text(_mt)
_sp = root / 'data/specials.inc'
_t = _sp.read_text()
if '\tdef_special Wildlands_BufferStats' not in _t:
    raise SystemExit('beta: specials anchor drift (shop)')
_sp.write_text(_t.replace('\tdef_special Wildlands_BufferStats',
    '\tdef_special Wildlands_BufferStats\n\tdef_special Wildlands_BufferShop\n\tdef_special Wildlands_MakeShiny\n\tdef_special Wildlands_ShopQuote', 1))
_sc = root / 'data/maps/AscensionTeamLab/scripts.inc'
_t = _sc.read_text()
_old = ' special Wildlands_BufferStats\n msgbox WildlandsLab_Text_Professor, MSGBOX_DEFAULT\n release\n end\n'
if _t.count(_old) != 1:
    raise SystemExit('beta: professor script anchor drift (shop)')
_t = _t.replace(_old, ' special Wildlands_BufferStats\n msgbox WildlandsLab_Text_Professor, MSGBOX_DEFAULT\n goto WildlandsLab_EventScript_Shop\n', 1)
_t += r"""
WildlandsLab_EventScript_Shop::
 special Wildlands_BufferShop
 msgbox WildlandsLab_Text_ShopInfo, MSGBOX_DEFAULT
 msgbox WildlandsLab_Text_ShopBrowse, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, WildlandsLab_EventScript_ShopBye
 msgbox WildlandsLab_Text_ShopPick, MSGBOX_DEFAULT
WildlandsLab_EventScript_ShopLook::
 special ChoosePartyMon
 waitstate
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, WildlandsLab_EventScript_ShopBye
 special Wildlands_ShopQuote
 goto_if_eq VAR_RESULT, 1, WildlandsLab_EventScript_ShopOffer
 goto_if_eq VAR_RESULT, 2, WildlandsLab_EventScript_ShopLegend
 goto_if_eq VAR_RESULT, 3, WildlandsLab_EventScript_ShopAlready
 goto_if_eq VAR_RESULT, 4, WildlandsLab_EventScript_ShopShort
 goto WildlandsLab_EventScript_ShopBye
WildlandsLab_EventScript_ShopOffer::
 msgbox WildlandsLab_Text_ShopAsk, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, WildlandsLab_EventScript_ShopAgain
 special Wildlands_MakeShiny
 goto_if_ne VAR_RESULT, 1, WildlandsLab_EventScript_ShopAgain
 playse SE_SHINY
 waitse
 msgbox WildlandsLab_Text_ShopDone, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_ShopBye
WildlandsLab_EventScript_ShopShort::
 msgbox WildlandsLab_Text_ShopShort, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_ShopAgain
WildlandsLab_EventScript_ShopLegend::
 msgbox WildlandsLab_Text_ShopLegend, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_ShopAgain
WildlandsLab_EventScript_ShopAlready::
 msgbox WildlandsLab_Text_ShopAlready, MSGBOX_DEFAULT
WildlandsLab_EventScript_ShopAgain::
 msgbox WildlandsLab_Text_ShopMore, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, WildlandsLab_EventScript_ShopLook
WildlandsLab_EventScript_ShopBye::
 release
 end

WildlandsLab_Text_ShopInfo:
 .string "SHINY SHOP: 10 WINS = 1 SHINY.\n"
 .string "WINS {STR_VAR_1}   STREAK {STR_VAR_2}\p"
 .string "Win 5 in a row for 2 bonus WINS.$"

WildlandsLab_Text_ShopBrowse:
 .string "Want to browse the SHINY SHOP?$"

WildlandsLab_Text_ShopAsk:
 .string "A SHINY {STR_VAR_1} costs 10 WINS.\n"
 .string "Buy it?$"

WildlandsLab_Text_ShopShort:
 .string "A SHINY {STR_VAR_1} costs 10 WINS.\n"
 .string "You need {STR_VAR_2} more WINS.$"

WildlandsLab_Text_ShopMore:
 .string "Look at another POKEMON?$"

WildlandsLab_Text_ShopPick:
 .string "Choose from your duo. To see\n"
 .string "others, use the COACH first.$"

WildlandsLab_Text_ShopDone:
 .string "{STR_VAR_1} is now SHINY!$"

WildlandsLab_Text_ShopLegend:
 .string "Legendary POKEMON can't be\n"
 .string "changed. Try another one.$"

WildlandsLab_Text_ShopAlready:
 .string "{STR_VAR_1} is already SHINY!$"
"""
_sc.write_text(_t)
# V6.8 diag: cost counters (see gWildlandsCost in arena_squad.inc).
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n', '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\nextern u32 gWildlandsCost[8];\n')
patch(A, 'q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; if(q1-q0>gWildlandsSpikeSim[0])gWildlandsSpikeSim[0]=q1-q0;}',
      'q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; gWildlandsCost[0]+=q1-q0; if(q1-q0>gWildlandsSpikeSim[0])gWildlandsSpikeSim[0]=q1-q0;}')
patch(A, 'q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; if(q1-q0>gWildlandsSpikeSim[1])gWildlandsSpikeSim[1]=q1-q0;}',
      'q1=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228; gWildlandsCost[1]+=q1-q0; if(q1-q0>gWildlandsSpikeSim[1])gWildlandsSpikeSim[1]=q1-q0;}')
patch(A, '    sWildlandsHudDrew=FALSE;\n    DrawStatusHud();\n', '    sWildlandsHudDrew=FALSE;\n    gWildlandsCost[5]++;\n    DrawStatusHud();\n')
patch(A, '    WildlandsPaceUpdate(gap);\n', '    WildlandsPaceUpdate(gap);\n    gWildlandsCost[7]++;\n')
print('V6.2 status installed: short stuns, timed burn/poison, partners included, HUD countdown, debris pool 20')
