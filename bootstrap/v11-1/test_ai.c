#define ARENA_MOVES_HOST
#include "arena_moves.h"
#include "ai_tactics.inc"
#include <stdio.h>
#include <assert.h>
#include <string.h>
int main(void)
{
    struct ArenaMoveProfile fast={0}, slow={0}, ranged={0}, self={0};
    int count=0, style, d;
    fast.kind=ARENA_MOVE_MELEE;fast.windup=7;fast.recovery=30;fast.range=44;
    slow=fast;slow.windup=28;slow.recovery=120;
    ranged=fast;ranged.kind=ARENA_MOVE_PROJECTILE;ranged.range=180;
    self=fast;self.kind=ARENA_MOVE_SELF;
    for(style=0;style<5;style++) for(d=20;d<=180;d+=40)
    {
        assert(AscensionAi_AdjustScore(&fast,-1000,d,0,1,1,style)==-1000);count++;
        assert(AscensionAi_AdjustScore(&self,-1000,d,0,1,1,style)==-1000);count++;
    }
    assert(AscensionAi_AdjustScore(&fast,140,30,0,0,0,4)>AscensionAi_AdjustScore(&slow,140,30,0,0,0,4));count++;
    assert(AscensionAi_AdjustScore(&fast,140,30,0,1,0,3)>AscensionAi_AdjustScore(&fast,140,30,0,0,0,3));count++;
    assert(AscensionAi_AdjustScore(&ranged,140,90,1,0,0,1)<AscensionAi_AdjustScore(&ranged,140,90,0,0,0,1));count++;
    assert(AscensionAi_AdjustScore(&ranged,140,90,0,0,1,1)>AscensionAi_AdjustScore(&ranged,140,90,0,0,0,1));count++;
    assert(AscensionAi_AdjustScore(&ranged,140,90,0,0,0,1)>AscensionAi_AdjustScore(&ranged,140,90,0,0,0,0));count++;
    assert(AscensionAi_AdjustScore(&fast,140,30,0,0,0,0)>AscensionAi_AdjustScore(&fast,140,30,0,0,0,1));count++;
    assert(AscensionAi_AdjustScore(&self,100,30,0,0,1,2)>AscensionAi_AdjustScore(&self,100,30,0,0,0,2));count++;
    assert(fast.windup==7 && fast.recovery==30 && fast.range==44);count++;
    printf("PASS: %d pure native AI scoring assertions; not a full battle/Delta test.\n",count);
    return 0;
}
