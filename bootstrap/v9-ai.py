#!/usr/bin/env python3
"""V9 Arena opponent move choice improvements, scoped to career battles.
Reuses original real-time AI scorer, telemetry and move cooldowns.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/realtime_arena.c"
s=p.read_text()
anchor="        if(ArenaMovePP(1,i)<=2)score-=12;"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        // Ascension career should reward reading patterns and positioning,
        // not repeatedly firing the single highest-power 'ball' projectile.
        // Use native damage/type estimates, keep immunities and PP rules.
        if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1)
        {
            if(move==gArenaCombatTelemetry.lastMove[1] && gBattleMoves[move].power)
                score-=max(75,score/3);
            if(p->kind==ARENA_MOVE_MELEE && distance<47)
                score+=48;
            else if(p->kind==ARENA_MOVE_RUSH && distance<80)
                score+=32;
            else if(p->kind==ARENA_MOVE_PROJECTILE && distance>58)
                score+=26;
            else if(p->kind==ARENA_MOVE_CONE && distance<95)
                score+=18;
            if(gBattleMons[1].hp*2<gBattleMons[1].maxHP
                && (move==MOVE_PROTECT || move==MOVE_DOUBLE_TEAM))
                score+=45;
            if(move==MOVE_HYPER_BEAM && distance<35)
                score-=35; // punish obvious point-blank committed windup
        }
""",1)
# User's recent V8 fights exposed an opponent trainer graphic bug: the source
# derives arena sidelines from the trainer ID, not the overworld sprite.
# v9-core sets both; prevent regressions with a static source assertion.
assert "gTrainers[gTrainerBattleOpponent_A].trainerPic" in s
assert "static void AiChooseMove(s32 distance)" in s
p.write_text(s)
print("V9 native opponent AI: move recency penalty, range/archetype utility, defense near low HP.")
