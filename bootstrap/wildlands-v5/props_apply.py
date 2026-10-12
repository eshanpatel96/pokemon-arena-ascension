#!/usr/bin/env python3
"""WildLands Beta: breakable arena props streamed through the world.

- gArenaObstacles becomes writable so world slots can move;
- arena_terrain.c draws props in the world (per-slot art and biome set) and
  exports ArenaTerrain_WorldSlot / ArenaTerrain_WorldRelease;
- arena_props.inc streams a pool of slots to generated sites near the camera;
- Psychic only lifts rocks near the caster in the world.
"""
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent


def patch(path, old, new, count=1):
    p = root / path
    s = p.read_text()
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new))


shutil.copy(here / 'arena_props.inc', root / 'src/arena_props.inc')
inc = root / 'include/wildlands_props.inc'
if not inc.exists():   # the Route 120 slice has no prop sites
    inc.write_text('#define WL_PROP_SITES 0\nstruct WlPropSite { u16 x, y; u8 set, art; };\n')

# Writable obstacle rectangles (the classic arena keeps its initial layout).
patch('include/arena_navigation.h', 'extern const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES];',
      'extern struct ArenaRect gArenaObstacles[ARENA_OBSTACLES];')
# (.data is discarded for this object by the linker script: keep the classic
# layout in ROM and copy it into an EWRAM table at every arena init.)
patch('src/arena_navigation.c', 'const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] =',
      'EWRAM_DATA struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] = {};\n'
      'static const struct ArenaRect sArenaObstaclesInit[ARENA_OBSTACLES] =')
patch('src/arena_navigation.c', 'void ArenaNav_Init(void)\n{\n    u16 i, j;\n',
      'void ArenaNav_Init(void)\n{\n    u16 i, j;\n'
      '    for (i = 0; i < ARENA_OBSTACLES; i++)\n        gArenaObstacles[i] = sArenaObstaclesInit[i];\n')

T = 'src/arena_terrain.c'
patch(T, 'static EWRAM_DATA u8 sPropFrame[ARENA_OBSTACLES]={};\n',
      'static EWRAM_DATA u8 sPropFrame[ARENA_OBSTACLES]={};\n'
      '// Per slot: which prop art (0..6) from which biome set. Classic: i, biome.\n'
      'static EWRAM_DATA u8 sPropArt[ARENA_OBSTACLES]={};\n'
      'static EWRAM_DATA u8 sPropSet[ARENA_OBSTACLES]={};\n')
# World init: palette + debris pieces only; props come and go per slot.
patch(T, '''    if(WildlandsWorld_Active())
    {
        for(i=0;i<ARENA_OBSTACLES;i++)sPropSprite[i]=MAX_SPRITES;''',
      '''    if(WildlandsWorld_Active())
    {
        LoadSpriteSheet(&pieces);   /* fragments take their material palette per frame */\n        {struct SpriteSheet block={(const u8*)sBiomeProps[0],WL_PROP_BLOCK_SLOTS*512,WL_PROP_BLOCK_TAG};LoadSpriteSheet(&block);}   /* one up-front block: slots never allocate later */
        for(i=0;i<ARENA_OBSTACLES;i++){sPropSprite[i]=MAX_SPRITES;sPropFrame[i]=255;sPropArt[i]=i;sPropSet[i]=0;}''')
patch(T, '''        struct SpriteSheet sheet={(const u8*)sBiomeProps[gArenaBiome]+i*3*512,512,TAG+i};''',
      '''        struct SpriteSheet sheet={(const u8*)sBiomeProps[gArenaBiome]+i*3*512,512,TAG+i};
        sPropArt[i]=i;sPropSet[i]=gArenaBiome;''')
patch(T, '''void ArenaTerrain_Draw(bool8 paused,bool8 frozen)
{
    u32 i;
    if(WildlandsWorld_Active())return;
''', '''void ArenaTerrain_Draw(bool8 paused,bool8 frozen)
{
    u32 i;
''')
patch(T, '''        u8 key=frame+(wet?3:0);
        if(sPropFrame[i]!=key)''',
      '''        u8 key=frame+(wet?3:0);
        if(WildlandsWorld_Active()&&sPropSprite[i]==MAX_SPRITES)continue;   /* C89: after the declarations */
        if(sPropFrame[i]!=key)''')
patch(T, '''        const u8 *source=wet?(const u8*)sWetProps+gArenaBiome*7*3*512:(const u8*)sBiomeProps[gArenaBiome];''',
      '''        const u8 *source=wet?(const u8*)sWetProps+sPropSet[i]*7*3*512:(const u8*)sBiomeProps[sPropSet[i]];''')
patch(T, '''            ArenaRender_Copy(source+(i*3+frame)*512,''',
      '''            ArenaRender_Copy(source+(sPropArt[i]*3+frame)*512,''')
patch(T, '''                (u8*)OBJ_VRAM0+GetSpriteTileStartByTag(TAG+i)*32,512);''',
      '''                (u8*)OBJ_VRAM0+(WildlandsWorld_Active()?GetSpriteTileStartByTag(WL_PROP_BLOCK_TAG)+i*16:GetSpriteTileStartByTag(TAG+i))*32,512);''')
patch(T, '''            s->oam.priority=r->state?0:1;''',
      '''            s->oam.priority=r->state?0:1;
            if(WildlandsWorld_Active())s->oam.tileNum=GetSpriteTileStartByTag(WL_PROP_BLOCK_TAG)+i*16;''')
patch(T, '''static EWRAM_DATA u8 sPropFrame[ARENA_OBSTACLES]={};\n''',
      '''static EWRAM_DATA u8 sPropFrame[ARENA_OBSTACLES]={};\n#define WL_PROP_BLOCK_TAG (TAG+ARENA_OBSTACLES+3)\n#define WL_PROP_BLOCK_SLOTS 7\n''')
s = (root / T).read_text()
s += r'''
// WildLands Beta: one prop slot moved onto a world site (see arena_props.inc).
void ArenaTerrain_WorldRelease(u8 i)
{
    if(i>=ARENA_OBSTACLES)return;
    if(sPropSprite[i]!=MAX_SPRITES){DestroySprite(&gSprites[sPropSprite[i]]);sPropSprite[i]=MAX_SPRITES;}
    FreeSpriteTilesByTag(TAG+i);
    ArenaNav_SetObstacle(i,0);
    gArenaPhysicsTelemetry.solidMask&=~(1<<i);
    gArenaProps[i].broken=1;gArenaProps[i].hp=0;gArenaProps[i].fuse=0;gArenaProps[i].reserved=0;
    sPropFrame[i]=255;
}
bool8 ArenaTerrain_WorldSlot(u8 i,s16 x,s16 y,u8 set,u8 art,u8 kind,u8 hp,u8 maxHp)
{
    struct SpriteTemplate template=sTemplate;
    struct SpriteSheet sheet;
    struct ArenaRect *r;
    if(i>=WL_PROP_BLOCK_SLOTS||art>6||set>4)return FALSE;
    ArenaTerrain_WorldRelease(i);
    (void)sheet;
    if(GetSpriteTileStartByTag(WL_PROP_BLOCK_TAG)==0xFFFF)return FALSE;
    template.tileTag=WL_PROP_BLOCK_TAG;
    sPropSprite[i]=CreateSprite(&template,x,y,8);
    if(sPropSprite[i]==MAX_SPRITES)return FALSE;
    gSprites[sPropSprite[i]].animPaused=TRUE;
    gSprites[sPropSprite[i]].oam.tileNum=GetSpriteTileStartByTag(WL_PROP_BLOCK_TAG)+i*16;
    gSprites[sPropSprite[i]].oam.paletteNum=ArenaMoveFx_Palette(kind);
    gSprites[sPropSprite[i]].coordOffsetEnabled=TRUE;
    r=&gArenaObstacles[i];
    r->left=x-10;r->right=x+10;r->top=y-6;r->bottom=y+8;
    memset(&gArenaProps[i],0,sizeof(gArenaProps[i]));
    gArenaProps[i].kind=kind;gArenaProps[i].hp=hp;gArenaProps[i].maxHp=maxHp;
    sPropArt[i]=art;sPropSet[i]=set;sPropFrame[i]=255;
    ArenaNav_SetObstacle(i,1);
    gArenaPhysicsTelemetry.solidMask|=1<<i;
    gArenaPhysicsTelemetry.hp[i]=hp;
    return TRUE;
}
'''
(root / T).write_text(s)

# Psychic in the world: only rocks near the caster fly.
patch('src/arena_psychic.inc', '        if(p->kind!=ARENA_PROP_ROCK||p->broken||p->reserved)continue;\n',
      '        if(p->kind!=ARENA_PROP_ROCK||p->broken||p->reserved)continue;\n'
      '        if(WildlandsWorld_Active()&&(Abs((rect->left+rect->right)/2-sArena.bodies[side].x/Q)>200\n'
      '            ||Abs((rect->top+rect->bottom)/2-sArena.bodies[side].y/Q)>150))continue;\n')

A = 'src/realtime_arena.c'
patch(A, '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n',
      '#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)\n'
      'static void PropsInit(void);\nstatic void PropsSim(void);\nstatic void PropsFree(void);\n')
patch(A, '#include "arena_director.inc"\n', '#include "arena_props.inc"\n#include "arena_director.inc"\n')
patch(A, '    DirectorInit();\n    sWildlandsEncounterLive = WildlandsWorld_Active();\n',
      '    DirectorInit();\n    PropsInit();\n    sWildlandsEncounterLive = WildlandsWorld_Active();\n')
print('World props installed: writable obstacle slots, streamed breakable cover, local Psychic rocks')
