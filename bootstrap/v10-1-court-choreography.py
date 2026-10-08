#!/usr/bin/env python3
"""V10.1: stage a visible horizontal tournament with a Master who returns to
the center only after player leaves. Native 10x9 Emerald Battle Tower chamber.
Player left, challenger right and Master back of the arena; mid-round
checkpoints visually bring Master beside player before offering recovery.
This is source-level choreography; an actual Delta video is still necessary.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);maps=root/"data/maps"
def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: {n} anchors for {old[:90]!r}")
    return s.replace(old,new,1)

for rank in range(1,9):
    name=f"AscensionTower{rank}"
    path=maps/name/"scripts.inc"
    s=path.read_text()
    # Match the actual native room: Master starts (5,5), player approaches
    # from door below (5,6), opposing challenger spawns at (5,1).
    # Player finishes (3,4), opponent (7,3) and Master (4,6).
    movements={
       "MasterAside":" walk_left\n walk_down\n face_up",
       "MasterReturn":" walk_up\n walk_right\n face_down",
       "MasterFacing":" walk_up\n walk_left\n face_up",
       "PlayerAdvance":" walk_up\n walk_left\n walk_left\n walk_up\n face_right",
       "PlayerRetreat":" walk_down\n walk_right\n walk_right\n walk_down\n face_up",
       "ChallengerEnter":" walk_down\n walk_down\n walk_right\n walk_right\n face_left",
       "ChallengerExit":" walk_left\n walk_left\n walk_up\n walk_up",
    }
    for key,moves in movements.items():
        start=f"{name}_Move_{key}:\n"
        a=s.index(start);b=s.index("\n step_end",a)+len("\n step_end")
        s=s[:a]+start+moves+"\n step_end"+s[b:]

    # With opposite-side staging, Master (4,6) walks to (3,5), directly
    # below the player (3,4), and visually conducts the recovery.
    # Then Master steps back to (4,6) before next challenger enters.
    checkpoint_back=f"{name}_Move_MasterBackToSide:\n walk_right\n walk_down\n face_up\n step_end\n"
    mark=f"{name}_Move_PlayerAdvance:\n"
    s=once(s,mark,checkpoint_back+mark,name+" checkin-retreat movement")
    for suffix in ("Recovery","MidRecovery"):
        label=f"{name}_EventScript_{suffix}::"
        if label not in s:continue
        # only alter the logical body of this checkpoint (not boss dialogue)
        a=s.index(label)
        b=s.index("\n"+name+"_EventScript_",a+2)
        body=s[a:b]
        body=once(body,
                  f"goto_if_eq VAR_RESULT, NO, {name}_EventScript_NextOpponent",
                  f"goto_if_eq VAR_RESULT, NO, {name}_EventScript_{suffix}Return",
                  name+" "+suffix+" decline")
        body=once(body,
                  f"goto {name}_EventScript_NextOpponent",
                  f"goto {name}_EventScript_{suffix}Return",
                  name+" "+suffix+" accept")
        body+=f"\n{name}_EventScript_{suffix}Return::\n"
        body+=f" applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterBackToSide\n"
        body+=f" goto {name}_EventScript_NextOpponent\n"
        s=s[:a]+body+s[b:]
    # Boss has Master walk up to the player to deliver recovery/intro too.
    # The event's existing "MasterFacing" movement has been converted to
    # physical movement (4,6)->(3,5), so return them before boss warp.
    mark=f"{name}_EventScript_BossWarp::\n"
    if mark in s:
        s=once(s,mark,mark+f" applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterBackToSide\n",
               name+" boss master retreat")
    path.write_text(s)
    assert s.count(f"{name}_Move_ChallengerEnter:")==1
    assert f"{name}_Move_MasterBackToSide:" in s
    assert " walk_right\n walk_right\n face_left\n step_end" in s

print("V10.1 Tower court: all eight player-left/opponent-right staged walk-ins, Master visible behind court, Master steps adjacent for heal prompt and retreats, challenger walk-out and safe player/Master reset.")
