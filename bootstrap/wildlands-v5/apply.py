#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

root=Path(sys.argv[1])
here=Path(__file__).resolve().parent

def patch(path, old, new, count=1):
    p=root/path
    s=p.read_text()
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {n}: {old[:120]!r}")
    p.write_text(s.replace(old,new,count))

# Runtime world module generated from real Emerald map/metatile data.
shutil.copy(here/'wildlands_world.c',root/'src/wildlands_world.c')
shutil.copy(here/'wildlands_world.h',root/'include/wildlands_world.h')

# ---------------------------------------------------------------------------
# Arena navigation: the world grid becomes the shared static LOS/cover layer.
# Legacy seven destructible props are disabled only in Wildlands world mode.
# ---------------------------------------------------------------------------
p=root/'src/arena_navigation.c'
s=p.read_text()
s=s.replace('#include "arena_navigation.h"\n',
'''#include "arena_navigation.h"
#include "wildlands_world.h"
''',1)
s=s.replace('''u8 ArenaNav_LineClear(s16 x1,s16 y1,s16 x2,s16 y2,u8 radius)
{
    u8 i;
    // Visibility queries do not need closest-hit sorting or all intersections.''',
'''u8 ArenaNav_LineClear(s16 x1,s16 y1,s16 x2,s16 y2,u8 radius)
{
    u8 i;
    if(WildlandsWorld_Active() && !WildlandsWorld_LineClear(x1,y1,x2,y2,radius))
        return 0;
    // Visibility queries do not need closest-hit sorting or all intersections.''',1)
s=s.replace('''    sSolidMask=(1<<ARENA_OBSTACLES)-1;''',
'''    sSolidMask=WildlandsWorld_Active()?0:(1<<ARENA_OBSTACLES)-1;''',1)
p.write_text(s)

# ---------------------------------------------------------------------------
# Old Arena prop sprites: static world trees/cliffs/buildings replace them.
# Explosion fragments/prop destruction are cosmetic-only and disabled in the
# validation slice; native map cover is not destructible yet.
# ---------------------------------------------------------------------------
p=root/'src/arena_terrain.c'
s=p.read_text()
s=s.replace('#include "realtime_arena.h"\n',
'''#include "realtime_arena.h"
#include "wildlands_world.h"
''',1)
s=s.replace('''void ArenaTerrain_Init(void)
{
    u32 i;
    struct SpritePalette pal={sPalette,TAG};
    struct SpriteSheet pieces={sBiomePieces[gArenaBiome],sizeof(sPieces),TAG+ARENA_OBSTACLES};
    struct SpriteSheet blast={sBlast,2048,TAG+ARENA_OBSTACLES+1};
    struct SpriteSheet crater={sCrater,1024,TAG+ARENA_OBSTACLES+2};
    struct SpriteTemplate template=sTemplate;''',
'''void ArenaTerrain_Init(void)
{
    u32 i;
    struct SpritePalette pal={sPalette,TAG};
    struct SpriteSheet pieces={sBiomePieces[gArenaBiome],sizeof(sPieces),TAG+ARENA_OBSTACLES};
    struct SpriteSheet blast={sBlast,2048,TAG+ARENA_OBSTACLES+1};
    struct SpriteSheet crater={sCrater,1024,TAG+ARENA_OBSTACLES+2};
    struct SpriteTemplate template=sTemplate;
    if(WildlandsWorld_Active())
    {
        for(i=0;i<ARENA_OBSTACLES;i++)sPropSprite[i]=MAX_SPRITES;
        for(i=0;i<ARENA_FRAGMENTS;i++)sPieceSprite[i]=MAX_SPRITES;
        sBlastSprite=sCraterSprite=MAX_SPRITES;
        sBlastLife=sCraterAge=0;
        memset(gArenaOamTelemetry,0,sizeof(gArenaOamTelemetry));
        return;
    }''',1)
s=s.replace('''void ArenaTerrain_Draw(bool8 paused,bool8 frozen)
{
    u32 i;''',
'''void ArenaTerrain_Draw(bool8 paused,bool8 frozen)
{
    u32 i;
    if(WildlandsWorld_Active())return;''',1)
p.write_text(s)

# ---------------------------------------------------------------------------
# Arena biome compatibility: world mode still computes biome/stage identity
# for move/environment logic, but MUST NOT queue the legacy 8bpp court art.
# Those queued DMA writes otherwise land after the native Emerald 4bpp world
# tiles and corrupt the streamed background.
# ---------------------------------------------------------------------------
p=root/'src/arena_biomes.inc'
s=p.read_text()
old='''    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;
    LoadPalette(sStagePalettes[gArenaStage],0,512);
    StormBiome(sStageTiles[gArenaStage],sStagePalettes[gArenaStage]);
    LoadBgTiles(1,sStageTiles[gArenaStage],38400,0);
    LoadBgTilemap(1,sForestMap,sizeof(sForestMap),0);
}'''
new='''    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;
    if(WildlandsWorld_Active())
        return;
    LoadPalette(sStagePalettes[gArenaStage],0,512);
    StormBiome(sStageTiles[gArenaStage],sStagePalettes[gArenaStage]);
    LoadBgTiles(1,sStageTiles[gArenaStage],38400,0);
    LoadBgTilemap(1,sForestMap,sizeof(sForestMap),0);
}'''
if old not in s: raise SystemExit('arena biome world skip anchor drift')
p.write_text(s.replace(old,new,1))

# ---------------------------------------------------------------------------
# Core realtime Arena integration.
# ---------------------------------------------------------------------------
p=root/'src/realtime_arena.c'
s=p.read_text()
if '#include "wildlands_world.h"' not in s:
    # realtime_arena.c already includes arena_navigation.h in this tree.
    anchor='#include "arena_navigation.h"\n'
    if anchor not in s: raise SystemExit('realtime arena include anchor drift')
    s=s.replace(anchor,anchor+'#include "wildlands_world.h"\n#include "wildlands_world_data.h"\n',1)

# Fourth BG = native Emerald bottom terrain layer. Existing BG0 stays HUD.
old='''    { .bg = 2, .charBaseIndex = 3, .mapBaseIndex = 29,
      .screenSize = 0, .paletteMode = 0, .priority = 2, .baseTile = 0 }
};'''
new='''    { .bg = 2, .charBaseIndex = 3, .mapBaseIndex = 29,
      .screenSize = 0, .paletteMode = 0, .priority = 2, .baseTile = 0 },
    { .bg = 3, .charBaseIndex = 1, .mapBaseIndex = 28,
      .screenSize = 0, .paletteMode = 0, .priority = 3, .baseTile = 0 }
};'''
if old not in s: raise SystemExit('BG template anchor drift')
s=s.replace(old,new,1)

# World camera scrolls all three native terrain layers. Sprite world->screen
# transform remains the exact Arena XL path.
old='''    SetGpuReg(REG_OFFSET_BG1HOFS,camX&0xFF);
    SetGpuReg(REG_OFFSET_BG1VOFS,camY&0xFF);'''
new='''    if(WildlandsWorld_Active())WildlandsWorld_UpdateCamera(camX,camY);
    else
    {
        SetGpuReg(REG_OFFSET_BG1HOFS,camX&0xFF);
        SetGpuReg(REG_OFFSET_BG1VOFS,camY&0xFF);
    }'''
if old not in s: raise SystemExit('XL camera BG anchor drift')
s=s.replace(old,new,1)

# Init: preserve native Arena gameplay, replace only background/terrain renderer
# in Wildlands practice. Space/Toss tiles are not loaded into overlapping VRAM
# in this validation build.
old='''    LoadArenaBiome();
    LoadBgTiles(2, sSpaceTiles, sizeof(sSpaceTiles), 192);
    LoadBgTilemap(2, sSpaceMap, sizeof(sSpaceMap), 0);
    LoadPalette(sArenaPalette, 0, sizeof(sArenaPalette));
    DrawStage();
    ArenaNav_Init();'''
new='''    WildlandsWorld_Init();
    LoadArenaBiome();
    if(WildlandsWorld_Active())
        WildlandsWorld_LoadGraphics();
    else
    {
        LoadBgTiles(2, sSpaceTiles, sizeof(sSpaceTiles), 192);
        LoadBgTilemap(2, sSpaceMap, sizeof(sSpaceMap), 0);
    }
    LoadPalette(sArenaPalette, 0, sizeof(sArenaPalette));
    DrawStage();
    ArenaNav_Init();'''
if old not in s: raise SystemExit('arena init graphics anchor drift')
s=s.replace(old,new,1)

# Spawn on opposite sides of Route 120's native bridge in the validation slice.
old='''        body->x = (ARENA_XL_WORLD_W / 2) * Q;
        body->y = (ARENA_XL_WORLD_H / 2 + (i ? -320 : 320)) * Q;
        body->facing = i ? FACE_DOWN : FACE_UP;'''
new='''        if(WildlandsWorld_Active())
        {
            body->x=(i?WL_ENEMY_START_X:WL_PLAYER_START_X)*Q;
            body->y=(i?WL_ENEMY_START_Y:WL_PLAYER_START_Y)*Q;
            body->facing=i?FACE_LEFT:FACE_RIGHT;
        }
        else
        {
            body->x = (ARENA_XL_WORLD_W / 2) * Q;
            body->y = (ARENA_XL_WORLD_H / 2 + (i ? -320 : 320)) * Q;
            body->facing = i ? FACE_DOWN : FACE_UP;
        }'''
if old not in s: raise SystemExit('world spawn anchor drift')
s=s.replace(old,new,1)

# Show exact Emerald bottom/middle/top layers only in world mode.
old='''    ShowBg(0);
    ShowBg(1);
    SetVBlankCallback(VBlank_Arena);'''
new='''    ShowBg(0);
    ShowBg(1);
    if(WildlandsWorld_Active()){ShowBg(3);ShowBg(2);}
    SetVBlankCallback(VBlank_Arena);'''
if old not in s: raise SystemExit('show bg anchor drift')
s=s.replace(old,new,1)

# VBlank owns streamed tilemap writes: no terrain VRAM mutation during HDraw.
old='''static void VBlank_Arena(void)
{
    LoadOam();'''
new='''static void VBlank_Arena(void)
{
    WildlandsWorld_VBlank();
    LoadOam();'''
if old not in s: raise SystemExit('vblank anchor drift')
s=s.replace(old,new,1)

# Arena movement remains axis-separated Q8 sweep. In Wildlands mode
# WildlandsWorld_BodyLineClear owns both solid-cover and water traversal.
# The ordinary ArenaNav_LineClear also consults the world, so calling it
# first is redundant and can reject an otherwise valid species crossing.
# Legacy ArenaNav collision is retained for non-Wildlands encounters.
old='''    if ((ghost || ArenaNav_LineClear(body->x / Q, body->y / Q, x / Q, body->y / Q, ARENA_BODY_RADIUS))
        && CoverCanStep(x/Q,body->y/Q)'''
new='''    if ((ghost || (WildlandsWorld_Active()
            ? WildlandsWorld_BodyLineClear(side,body->x/Q,body->y/Q,x/Q,body->y/Q,ARENA_BODY_RADIUS)
            : ArenaNav_LineClear(body->x/Q,body->y/Q,x/Q,body->y/Q,ARENA_BODY_RADIUS)))
        && CoverCanStep(x/Q,body->y/Q)'''
if old not in s: raise SystemExit('movement X anchor drift')
s=s.replace(old,new,1)
old='''    if ((ghost || ArenaNav_LineClear(body->x / Q, body->y / Q, body->x / Q, y / Q, ARENA_BODY_RADIUS))
        && CoverCanStep(body->x/Q,y/Q)'''
new='''    if ((ghost || (WildlandsWorld_Active()
            ? WildlandsWorld_BodyLineClear(side,body->x/Q,body->y/Q,body->x/Q,y/Q,ARENA_BODY_RADIUS)
            : ArenaNav_LineClear(body->x/Q,body->y/Q,body->x/Q,y/Q,ARENA_BODY_RADIUS)))
        && CoverCanStep(body->x/Q,y/Q)'''
if old not in s: raise SystemExit('movement Y anchor drift')
s=s.replace(old,new,1)

# Dash landing uses the same static terrain and water rules.
old='''    if(!ArenaNav_CanStand(x/Q,y/Q) || !CoverCanStep(x/Q,y/Q)
        || (Abs(x-sArena.bodies[1].x)<22*Q && Abs(y-sArena.bodies[1].y)<22*Q))return FALSE;'''
new='''    if(!ArenaNav_CanStand(x/Q,y/Q) || !CoverCanStep(x/Q,y/Q)
        || (WildlandsWorld_Active() && !WildlandsWorld_CanStandSide(
            body==&sArena.bodies[1],x/Q,y/Q,ARENA_BODY_RADIUS))
        || (Abs(x-sArena.bodies[1].x)<22*Q && Abs(y-sArena.bodies[1].y)<22*Q))return FALSE;'''
if old not in s: raise SystemExit('dash landing anchor drift')
s=s.replace(old,new,1)

# AI route uses the same world terrain graph as movement.
old='''    if (ArenaNav_NextWaypoint(body->x / Q, body->y / Q, sArena.goal.x, sArena.goal.y, &sArena.waypoint))
        gArenaAiTelemetry.paths++;'''
new='''    if ((WildlandsWorld_Active()
            ? WildlandsWorld_NextWaypointSide(1,body->x/Q,body->y/Q,
                sArena.goal.x,sArena.goal.y,&sArena.waypoint)
            : ArenaNav_NextWaypoint(body->x / Q, body->y / Q,
                sArena.goal.x, sArena.goal.y, &sArena.waypoint)))
        gArenaAiTelemetry.paths++;'''
if old not in s: raise SystemExit('AI route anchor drift')
s=s.replace(old,new,1)

# Tactical goal candidates/evades must also be legal for the enemy's traversal.
old='''        if (!ArenaNav_CanStand(p.x, p.y) || !CoverCanStep(p.x,p.y)
            || !ArenaNav_LineClear(p.x, p.y, sArena.observed.x, sArena.observed.y, 2)) continue;'''
new='''        if (!ArenaNav_CanStand(p.x, p.y) || !CoverCanStep(p.x,p.y)
            || (WildlandsWorld_Active() && !WildlandsWorld_CanStandSide(1,p.x,p.y,ARENA_BODY_RADIUS))
            || !ArenaNav_LineClear(p.x, p.y, sArena.observed.x, sArena.observed.y, 2)) continue;'''
if old not in s: raise SystemExit('AI choose goal terrain anchor drift')
s=s.replace(old,new,1)
old='''            if (ArenaNav_CanStand(goal.x,goal.y)
                && ArenaNav_LineClear(body->x/Q,body->y/Q,goal.x,goal.y,ARENA_BODY_RADIUS))'''
new='''            if (ArenaNav_CanStand(goal.x,goal.y)
                && (!WildlandsWorld_Active() || WildlandsWorld_CanStandSide(1,goal.x,goal.y,ARENA_BODY_RADIUS))
                && ArenaNav_LineClear(body->x/Q,body->y/Q,goal.x,goal.y,ARENA_BODY_RADIUS))'''
if old not in s: raise SystemExit('AI evade terrain anchor drift')
s=s.replace(old,new,1)

# Tall/long grass = concealment at distance. AI retains last known position;
# close enemies still detect each other, so grass is not invulnerability.
old='''        if(!SmokeBlocks(body->x/Q,body->y/Q,sArena.bodies[0].x/Q,sArena.bodies[0].y/Q))
        {sArena.observed.x = sArena.bodies[0].x / Q;sArena.observed.y = sArena.bodies[0].y / Q;}
        else gArenaCoverTelemetry[5]++;'''
new='''        if(!SmokeBlocks(body->x/Q,body->y/Q,sArena.bodies[0].x/Q,sArena.bodies[0].y/Q)
            && !(WildlandsWorld_Active()
                && WildlandsWorld_IsConcealed(sArena.bodies[0].x/Q,sArena.bodies[0].y/Q)
                && ArenaNav_Distance(body->x/Q,body->y/Q,
                    sArena.bodies[0].x/Q,sArena.bodies[0].y/Q)>48))
        {sArena.observed.x = sArena.bodies[0].x / Q;sArena.observed.y = sArena.bodies[0].y / Q;}
        else gArenaCoverTelemetry[5]++;'''
if old not in s: raise SystemExit('AI concealment anchor drift')
s=s.replace(old,new,1)

# Player auto-lock follows the same concealment rule; explicit directional aim
# still fires wherever the player points.
old='''        if(!dx&&!dy&&(ArenaMoveId(0,body->moveSlot)==MOVE_ROLLOUT
            ||SmokeBlocks(body->x/Q,body->y/Q,sArena.bodies[1].x/Q,sArena.bodies[1].y/Q)))'''
new='''        if(!dx&&!dy&&(ArenaMoveId(0,body->moveSlot)==MOVE_ROLLOUT
            ||SmokeBlocks(body->x/Q,body->y/Q,sArena.bodies[1].x/Q,sArena.bodies[1].y/Q)
            ||(WildlandsWorld_Active()
                &&WildlandsWorld_IsConcealed(sArena.bodies[1].x/Q,sArena.bodies[1].y/Q)
                &&ArenaNav_Distance(body->x/Q,body->y/Q,
                    sArena.bodies[1].x/Q,sArena.bodies[1].y/Q)>48)))'''
if old not in s: raise SystemExit('player concealment anchor drift')
s=s.replace(old,new,1)

# Body terrain telemetry for proof of grass/water interactions.
old='''                if(sCapture.state!=ARENA_CAPTURE_AIM)TickPlayer();
                TickEnemy();
                now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;'''
new='''                if(sCapture.state!=ARENA_CAPTURE_AIM)TickPlayer();
                TickEnemy();
                if(WildlandsWorld_Active())
                {
                    WildlandsWorld_TickBody(0,sArena.bodies[0].x/Q,sArena.bodies[0].y/Q);
                    WildlandsWorld_TickBody(1,sArena.bodies[1].x/Q,sArena.bodies[1].y/Q);
                }
                now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;'''
if old not in s: raise SystemExit('terrain tick anchor drift')
s=s.replace(old,new,1)

# World-static cover destroys projectiles too. Dynamic props retain their old
# destructible response outside Wildlands.
old='''        if (obstacle>=0)
        {
            gArenaAiTelemetry.blockedShots[shot->side]++;
            ArenaFeedback_Wall(shot->x/Q,shot->y/Q);
            PlaySE(SE_WALL_HIT);
            HitTerrain(obstacle,p,shot->vx,shot->vy);
            DestroyShot(shot);
            continue;
        }
        shot->x += shot->vx; shot->y += shot->vy;'''
new='''        if (obstacle>=0
            || (WildlandsWorld_Active()
                && !WildlandsWorld_LineClear(shot->x/Q,shot->y/Q,
                    (shot->x+shot->vx)/Q,(shot->y+shot->vy)/Q,2)))
        {
            gArenaAiTelemetry.blockedShots[shot->side]++;
            ArenaFeedback_Wall(shot->x/Q,shot->y/Q);
            PlaySE(SE_WALL_HIT);
            if(obstacle>=0)HitTerrain(obstacle,p,shot->vx,shot->vy);
            else WildlandsWorld_RecordProjectileBlock();
            DestroyShot(shot);
            continue;
        }
        shot->x += shot->vx; shot->y += shot->vy;'''
if old not in s: raise SystemExit('projectile world cover anchor drift')
s=s.replace(old,new,1)
s=s.replace('''        if (shot->x < 3 * Q || shot->x > 237 * Q || shot->y < 19 * Q || shot->y > 157 * Q) shot->life = 1;''',
'''        if (shot->x < ARENA_MIN_X * Q || shot->x > ARENA_MAX_X * Q
            || shot->y < ARENA_MIN_Y * Q || shot->y > ARENA_MAX_Y * Q) shot->life = 1;''',1)

# Beam reach is clipped by world trees/cliffs/buildings but water remains
# transparent to projectiles.
old='''            sFlameReach[side]=reach;gArenaFlameTelemetry[1]++;'''
new='''            if(WildlandsWorld_Active())
                reach=min(reach,WildlandsWorld_ClipRay(oldX,oldY,
                    body->attackX,body->attackY,reach,1));
            sFlameReach[side]=reach;gArenaFlameTelemetry[1]++;'''
if old not in s: raise SystemExit('beam world clip anchor drift')
s=s.replace(old,new,1)

# Partner now routes around the same world collision/water grid instead of
# following through scenery. It is still explicitly non-damaging in V5.
old='''    s16 species;
    u8 sprite,shadow,marker,facing,moving,drawnFrame,drawnDirection,active,mode;
};'''
# Actual V4 struct uses u16 species (not s16); accept exact branch text below.
if old not in s:
    old='''    u16 species;
    u8 sprite,shadow,marker,facing,moving,drawnFrame,drawnDirection,active,mode;
};'''
new='''    u16 species;
    s16 waypointX,waypointY;
    u8 sprite,shadow,marker,facing,moving,drawnFrame,drawnDirection,active,mode;
};'''
if old not in s: raise SystemExit('partner waypoint struct anchor drift')
s=s.replace(old,new,1)
old='''    dx=tx-p->x;dy=ty-p->y;
    maxd=max(Abs(dx),Abs(dy));
    if(maxd>120*Q){step=520;p->mode=2;} // regroup/catch-up
    p->moving=maxd>2*Q;
    if(p->moving)
    {
        s32 mx=dx*step/max(1,maxd),my=dy*step/max(1,maxd);
        s32 nx=Clamp(p->x+mx,ARENA_MIN_X*Q,ARENA_MAX_X*Q);
        s32 ny=Clamp(p->y+my,ARENA_MIN_Y*Q,ARENA_MAX_Y*Q);
        p->facing=Facing(mx,my);
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,nx/Q,p->y/Q,10))p->x=nx;
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,p->x/Q,ny/Q,10))p->y=ny;
    }'''
new='''    // Replan the follower at a bounded 1/8 Arena-tick cadence. Replanning
    // again merely because it reached a waypoint caused almost one swept-route
    // query per gameplay update and starved the native realtime loop.
    if(WildlandsWorld_Active() && (sArena.frame&7)==7)
    {
        struct ArenaPoint wp;
        if(WildlandsWorld_NextWaypointSpecies(p->species,p->x/Q,p->y/Q,tx/Q,ty/Q,&wp))
        {p->waypointX=wp.x;p->waypointY=wp.y;}
        else {p->waypointX=p->x/Q;p->waypointY=p->y/Q;}
    }
    else if(!WildlandsWorld_Active())
    {p->waypointX=tx/Q;p->waypointY=ty/Q;}

    dx=p->waypointX*Q-p->x;dy=p->waypointY*Q-p->y;
    maxd=max(Abs(tx-p->x),Abs(ty-p->y));
    if(maxd>120*Q){step=520;p->mode=2;} // regroup/catch-up
    p->moving=Abs(dx)>2*Q||Abs(dy)>2*Q;
    if(p->moving)
    {
        s32 pathd=max(1,max(Abs(dx),Abs(dy)));
        s32 mx=dx*step/pathd,my=dy*step/pathd;
        s32 nx=Clamp(p->x+mx,ARENA_MIN_X*Q,ARENA_MAX_X*Q);
        s32 ny=Clamp(p->y+my,ARENA_MIN_Y*Q,ARENA_MAX_Y*Q);
        p->facing=Facing(mx,my);
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,nx/Q,p->y/Q,10)
            &&(!WildlandsWorld_Active()||WildlandsWorld_SpeciesLineClear(
                p->species,p->x/Q,p->y/Q,nx/Q,p->y/Q,10)))p->x=nx;
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,p->x/Q,ny/Q,10)
            &&(!WildlandsWorld_Active()||WildlandsWorld_SpeciesLineClear(
                p->species,p->x/Q,p->y/Q,p->x/Q,ny/Q,10)))p->y=ny;
    }'''
if old not in s: raise SystemExit('partner navigation anchor drift')
s=s.replace(old,new,1)

# Initialize partner waypoint at an actual legal Wildlands field position.
# The V4 screen-relative offset lands inside solid Route120 scenery at the V5
# validation spawn, so world mode uses the adjacent clear metatile instead.
old='''    p->x=sArena.bodies[0].x-36*Q;p->y=sArena.bodies[0].y+28*Q;p->facing=FACE_DOWN;'''
new='''    if(WildlandsWorld_Active())
    {p->x=sArena.bodies[0].x+16*Q;p->y=sArena.bodies[0].y+16*Q;}
    else
    {p->x=sArena.bodies[0].x-36*Q;p->y=sArena.bodies[0].y+28*Q;}
    p->waypointX=p->x/Q;p->waypointY=p->y/Q;p->facing=FACE_DOWN;'''
if old not in s: raise SystemExit('partner init waypoint anchor drift')
s=s.replace(old,new,1)

p.write_text(s)

# ---------------------------------------------------------------------------
# Psychic world-rock interaction and bounds.
# ---------------------------------------------------------------------------
p=root/'src/arena_psychic.inc'
s=p.read_text()
s=s.replace('''            if(nx<12||nx>228||ny<30||ny>146||r->age>60)''',
'''            if(nx<ARENA_MIN_X||nx>ARENA_MAX_X||ny<ARENA_MIN_Y||ny>ARENA_MAX_Y||r->age>60)''',1)
# A thrown rock should hit static map cover even when no legacy prop exists.
old='''            obstacle=ArenaNav_FirstObstacle(ox,oy,nx,ny,5);
            r->x+=r->vx;r->y+=r->vy;
            if(obstacle>=0)
            {ArenaPhysics_Hit(obstacle,r->vx,r->vy,3);gArenaPsychicTelemetry[5]++;PsychicImpact(i);continue;}'''
new='''            obstacle=ArenaNav_FirstObstacle(ox,oy,nx,ny,5);
            r->x+=r->vx;r->y+=r->vy;
            if(obstacle>=0 || (WildlandsWorld_Active()
                && !WildlandsWorld_LineClear(ox,oy,nx,ny,5)))
            {
                if(obstacle>=0)ArenaPhysics_Hit(obstacle,r->vx,r->vy,3);
                else WildlandsWorld_RecordProjectileBlock();
                gArenaPsychicTelemetry[5]++;PsychicImpact(i);continue;
            }'''
if old not in s: raise SystemExit('psychic static cover anchor drift')
s=s.replace(old,new,1)
p.write_text(s)

# ---------------------------------------------------------------------------
# Seismic Toss world compatibility: preserve hit/damage/choreography but use a
# black cut rather than overwriting streamed map VRAM. This is cosmetic-only
# in the validation build and is explicitly reported as such.
# ---------------------------------------------------------------------------
p=root/'src/arena_toss.inc'
s=p.read_text()
old='''static void TossSpaceStep(u8 step)
{
    struct ArenaToss *t = &sArena.toss;
    switch (step)'''
new='''static void TossSpaceStep(u8 step)
{
    struct ArenaToss *t = &sArena.toss;
    if(WildlandsWorld_Active())
    {
        switch(step)
        {
        case 0:t->space=TRUE;t->blackout=TRUE;break;
        case 1:HideBg(3);HideBg(2);HideBg(1);HideBg(0);break;
        case 2:break;
        case 3:t->blackout=FALSE;break;
        case 4:t->blackout=TRUE;break;
        case 5:break;
        case 6:t->blackout=FALSE;break;
        case 7:
            ShowBg(3);ShowBg(2);ShowBg(1);ShowBg(0);
            WildlandsWorld_RestorePalettes();
            LoadPalette(sArenaPalette,0,sizeof(sArenaPalette));
            t->space=FALSE;
            break;
        }
        return;
    }
    switch (step)'''
if old not in s: raise SystemExit('toss world anchor drift')
s=s.replace(old,new,1)
p.write_text(s)

print('Applied Wildlands V5 native-metatile world validation integration')
