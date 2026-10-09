#!/usr/bin/env python3
"""Five native Arena enemy attack-style preferences: rush, zone, defend,
bait/counter, balanced. Built on existing range/type/PP/dodge AI and telemetry;
this does NOT pretend a new renderer or fully gameplay-validated strategic AI.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/realtime_arena.c"
s=p.read_text()
anchor="    sArena.style = gBattleMons[1].personality % 3;"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
    // Career styles are themed, then varied by encounter and rematch.
    if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1)
    {
        static const u8 careerStyles[9]={4,1,2,3,0,2,0,3,4};
        u16 rank=VarGet(VAR_ASCENSION_RANK);
        if(rank>=ARRAY_COUNT(careerStyles))rank=8;
        sArena.style=(careerStyles[rank]
            +VarGet(VAR_ASCENSION_FLOOR)%3
            +VarGet(VAR_ASCENSION_REMATCH_CYCLE))%5;
    }""",1)
anchor="""            if(move==MOVE_HYPER_BEAM && distance<35)
                score-=35; // punish obvious point-blank committed windup"""
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
            // Five visibly counterable attack patterns. Native move effects
            // and elemental interactions still drive the actual outcome.
            switch(sArena.style)
            {
            case 0: // Rushdown
                if(p->kind==ARENA_MOVE_MELEE||p->kind==ARENA_MOVE_RUSH)score+=68;
                else if(p->kind==ARENA_MOVE_PROJECTILE&&distance<55)score-=40;
                break;
            case 1: // Zoner/sniper
                if(p->kind==ARENA_MOVE_PROJECTILE&&distance>45)score+=62;
                else if(p->kind==ARENA_MOVE_CONE&&distance>65)score+=25;
                else if(p->kind==ARENA_MOVE_RUSH&&distance>85)score-=25;
                break;
            case 2: // Defender
                if((move==MOVE_PROTECT||move==MOVE_REFLECT
                    ||move==MOVE_LIGHT_SCREEN||move==MOVE_DOUBLE_TEAM)
                    && gBattleMons[1].hp*3<gBattleMons[1].maxHP*2)score+=95;
                else if(p->kind==ARENA_MOVE_CONE&&distance<85)score+=25;
                break;
            case 3: // Bait and counter: punish committed player windups
                if(sArena.bodies[0].shotTimer||sArena.bodies[0].actionLife)
                {
                    if(p->kind==ARENA_MOVE_MELEE||p->kind==ARENA_MOVE_RUSH)score+=75;
                    else if(move==MOVE_PROTECT)score+=50;
                }
                else if(move==MOVE_DOUBLE_TEAM||move==MOVE_SMOKESCREEN)score+=30;
                break;
            default: // Balanced type/range/PP selection
                if(p->kind==ARENA_MOVE_PROJECTILE&&distance>90)score+=15;
                if(p->kind==ARENA_MOVE_MELEE&&distance<40)score+=15;
                break;
            }
""",1)
p.write_text(s)
assert "switch(sArena.style)" in s and "careerStyles[9]" in s
print("V9 native AI: five role-specific attack preferences, deterministic themed variation, existing dodge and telemetry preserved.")
