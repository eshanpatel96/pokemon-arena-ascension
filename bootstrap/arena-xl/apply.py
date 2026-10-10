#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])

def patch(path, old, new):
    p=root/path
    s=p.read_text()
    if s.count(old)!=1:
        raise SystemExit(f"{path}: expected one anchor, got {s.count(old)}: {old[:90]!r}")
    p.write_text(s.replace(old,new,1))

# 16,384 x 12,288 pixel native Arena world. Keep enough edge margin for 64x64 art.
p=root/'include/arena_navigation.h'
s=p.read_text()
s=s.replace('#define ARENA_MIN_X 12','#define ARENA_MIN_X 32')
s=s.replace('#define ARENA_MAX_X 228','#define ARENA_MAX_X 16352')
s=s.replace('#define ARENA_MIN_Y 32','#define ARENA_MIN_Y 32')
s=s.replace('#define ARENA_MAX_Y 143','#define ARENA_MAX_Y 12256')
p.write_text(s)

# Move the seven native destructible-cover rectangles to world center so the
# original obstacle physics/pathing remain exercised without defining the map.
p=root/'src/arena_navigation.c'
s=p.read_text()
old='''const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] =
{
    {108, 69, 133, 86},
    {60, 39, 81, 56},
    {169, 99, 190, 117},
    {24, 90, 42, 106},
    {28, 56, 45, 69},
    {201, 46, 213, 62},
    {202, 80, 218, 94}
};'''
new='''const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] =
{
    {8180, 6128, 8205, 6145},
    {8132, 6098, 8153, 6115},
    {8241, 6158, 8262, 6176},
    {8096, 6149, 8114, 6165},
    {8100, 6115, 8117, 6128},
    {8273, 6105, 8285, 6121},
    {8274, 6139, 8290, 6153}
};'''
if old not in s: raise SystemExit('navigation obstacle anchor drift')
p.write_text(s.replace(old,new,1))

p=root/'src/realtime_arena.c'
s=p.read_text()
anchor='#define Q 256\n'
insert='''#define Q 256
#define ARENA_XL_WORLD_W 16384
#define ARENA_XL_WORLD_H 12288
#define ARENA_XL_VIEW_W 240
#define ARENA_XL_VIEW_H 160
EWRAM_DATA u32 gArenaXLTelemetry[8] = {0};
static EWRAM_DATA s16 sArenaXLCameraX = 0;
static EWRAM_DATA s16 sArenaXLCameraY = 0;
static EWRAM_DATA s32 sArenaXLStartX = 0;
static EWRAM_DATA s32 sArenaXLStartY = 0;
'''
if s.count(anchor)!=1: raise SystemExit('Q anchor drift')
s=s.replace(anchor,insert,1)

anchor='''static s32 Abs(s32 n) { return n < 0 ? -n : n; }
static s32 Clamp(s32 n, s32 lo, s32 hi) { return n < lo ? lo : n > hi ? hi : n; }
'''
insert='''static s32 Abs(s32 n) { return n < 0 ? -n : n; }
static s32 Clamp(s32 n, s32 lo, s32 hi) { return n < lo ? lo : n > hi ? hi : n; }

static void ArenaXL_UpdateCamera(void)
{
    s32 px=sArena.bodies[0].x/Q,py=sArena.bodies[0].y/Q;
    s32 camX=Clamp(px-ARENA_XL_VIEW_W/2,0,ARENA_XL_WORLD_W-ARENA_XL_VIEW_W);
    s32 camY=Clamp(py-ARENA_XL_VIEW_H/2,0,ARENA_XL_WORLD_H-ARENA_XL_VIEW_H);
    u32 i;
    sArenaXLCameraX=camX;sArenaXLCameraY=camY;
    gSpriteCoordOffsetX=-sArenaXLCameraX;
    gSpriteCoordOffsetY=-sArenaXLCameraY;
    // BG1 is a fully populated 32x32 tilemap in this build. Hardware wrapping
    // gives us an effectively unbounded repeated test floor at zero EWRAM cost.
    SetGpuReg(REG_OFFSET_BG1HOFS,camX&0xFF);
    SetGpuReg(REG_OFFSET_BG1VOFS,camY&0xFF);
    for(i=0;i<MAX_SPRITES;i++)
        if(gSprites[i].inUse)gSprites[i].coordOffsetEnabled=TRUE;
    gArenaXLTelemetry[2]=px;
    gArenaXLTelemetry[3]=py;
    gArenaXLTelemetry[4]=ARENA_XL_WORLD_W;
    gArenaXLTelemetry[5]=ARENA_XL_WORLD_H;
    gArenaXLTelemetry[6]=sArenaXLCameraX;
    gArenaXLTelemetry[7]=sArenaXLCameraY;
    if(Abs(sArena.bodies[0].x-sArenaXLStartX)>=768*Q
        ||Abs(sArena.bodies[0].y-sArenaXLStartY)>=768*Q)
        gArenaXLTelemetry[0]=1;
    if(Abs(sArenaXLCameraX-(sArenaXLStartX/Q-ARENA_XL_VIEW_W/2))>=512
        ||Abs(sArenaXLCameraY-(sArenaXLStartY/Q-ARENA_XL_VIEW_H/2))>=512)
        gArenaXLTelemetry[1]=1;
}
'''
if s.count(anchor)!=1: raise SystemExit('Clamp anchor drift')
s=s.replace(anchor,insert,1)

# World-centered sendout positions. The two battlers start 640 px apart; the AI
# must traverse the same native movement/pathing system to engage.
old='''        body->x = 120 * Q;
        body->y = (i ? ARENA_MIN_Y : ARENA_MAX_Y) * Q;
        body->facing = i ? FACE_DOWN : FACE_UP;'''
new='''        body->x = (ARENA_XL_WORLD_W / 2) * Q;
        body->y = (ARENA_XL_WORLD_H / 2 + (i ? -320 : 320)) * Q;
        body->facing = i ? FACE_DOWN : FACE_UP;'''
if s.count(old)!=1: raise SystemExit('body start anchor drift')
s=s.replace(old,new,1)

old='''    CreateSidelineTrainers();
    CaptureInit();'''
new='''    // XL is a pure Pokemon-scale stress test: no screen-edge human spectators.
    memset(gArenaTrainerTelemetry,MAX_SPRITES,sizeof(gArenaTrainerTelemetry));
    CaptureInit();
    sCapture.ready=FALSE;'''
if s.count(old)!=1: raise SystemExit('sideline anchor drift')
s=s.replace(old,new,1)

old='''    sArena.observed.x = sArena.previous.x = 120;
    sArena.observed.y = sArena.previous.y = ARENA_MAX_Y;
    sArena.goal.x = sArena.waypoint.x = 120;
    sArena.goal.y = sArena.waypoint.y = ARENA_MIN_Y;'''
new='''    sArena.observed.x = sArena.previous.x = sArena.bodies[0].x/Q;
    sArena.observed.y = sArena.previous.y = sArena.bodies[0].y/Q;
    sArena.goal.x = sArena.waypoint.x = sArena.bodies[0].x/Q;
    sArena.goal.y = sArena.waypoint.y = sArena.bodies[1].y/Q;'''
if s.count(old)!=1: raise SystemExit('AI start anchor drift')
s=s.replace(old,new,1)

old='''    sArena.frame = 0;
    sArena.active = TRUE;'''
new='''    sArena.frame = 0;
    sArena.active = TRUE;
    memset(gArenaXLTelemetry,0,sizeof(gArenaXLTelemetry));
    sArenaXLStartX=sArena.bodies[0].x;
    sArenaXLStartY=sArena.bodies[0].y;
    ArenaXL_UpdateCamera();'''
if s.count(old)!=1: raise SystemExit('active anchor drift')
s=s.replace(old,new,1)

old='''    MonVisualScaleApply();
    AnimateSprites();BuildOamBuffer();'''
new='''    MonVisualScaleApply();
    ArenaXL_UpdateCamera();
    AnimateSprites();BuildOamBuffer();'''
if s.count(old)!=1: raise SystemExit('initial OAM anchor drift')
s=s.replace(old,new,1)

# Apply camera after all Arena systems have written their world-space sprite
# coordinates but before OAM is committed.
old='''    now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;
    gArenaRenderTelemetry[1]=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228-now;
    now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;
    AnimateSprites();
    BuildOamBuffer();'''
new='''    now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;
    gArenaRenderTelemetry[1]=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228-now;
    now=gMain.vblankCounter1*228+(REG_VCOUNT+68)%228;
    ArenaXL_UpdateCamera();
    AnimateSprites();
    BuildOamBuffer();'''
if s.count(old)!=1: raise SystemExit('frame OAM anchor drift')
s=s.replace(old,new,1)

p.write_text(s)

# The original water-deposit bounds live in the included element module and
# were hard-coded to the 240x160 screen. Make them world bounds too.
p=root/'src/arena_elements.inc'
s=p.read_text()
old='''    if(x<30||x>210||y<45||y>132||!ArenaNav_LineClear(x,y,x,y,4))return;'''
new='''    if(x<ARENA_MIN_X+18||x>ARENA_MAX_X-18||y<ARENA_MIN_Y+13||y>ARENA_MAX_Y-11
        ||!ArenaNav_LineClear(x,y,x,y,4))return;'''
if s.count(old)!=1: raise SystemExit('element deposit anchor drift')
p.write_text(s.replace(old,new,1))

print('Applied native Arena XL 16384x12288 camera/world stress patch')
