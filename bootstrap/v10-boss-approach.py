#!/usr/bin/env python3
"""V10 Friends Beta: deliberate Arena leader approach and safe original-game rooms.

Nine leaders including the World Champion: correct physical spawn, reachable
NPC, optional press-A fight, visible arena gatekeeper, walkable escape, no
on-frame auto-battle. Master stays sideline during ordinary tower fights.
No new renderer or unsupported GBA graphics.
"""
from pathlib import Path
import collections,json,re,struct,sys

root=Path(sys.argv[1])
maps=root/"data/maps"
layout_defs={entry["id"]:entry for entry in json.loads((root/"data/layouts/layouts.json").read_text())["layouts"]}
# Tiles derived from the *original* map.bin, not the previous incorrect
# base64-only audit. Boss positions selected to retain their Emerald theme.
# Coordinates: (player entry, leader position).
placements=[
 ("AscensionBronzeBoss",(5,8),(5,2),"MAP_ASCENSION_BRONZE_BOSS","AscensionTower1"),
 ("AscensionLeader2",(14,5),(15,2),"MAP_ASCENSION_LEADER_2","AscensionTower2"),
 ("AscensionLeader3",(11,6),(13,2),"MAP_ASCENSION_LEADER_3","AscensionTower3"),
 ("AscensionLeader4",(6,8),(5,4),"MAP_ASCENSION_LEADER_4","AscensionTower4"),
 ("AscensionLeader5",(13,12),(13,9),"MAP_ASCENSION_LEADER_5","AscensionTower5"),
 ("AscensionLeader6",(8,7),(8,2),"MAP_ASCENSION_LEADER_6","AscensionTower6"),
 ("AscensionLeader7",(5,6),(5,2),"MAP_ASCENSION_LEADER_7","AscensionTower7"),
 ("AscensionLeader8",(21,10),(23,8),"MAP_ASCENSION_LEADER_8","AscensionTower8"),
 ("AscensionLeader9",(6,9),(6,5),"MAP_ASCENSION_LEADER_9","AscensionSummit")
]

def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{label}: expected 1 source anchor, found {n}: {a[:100]!r}")
    return s.replace(a,b,1)

def load_layout(map_data):
    lay=layout_defs[map_data["layout"]]
    w,h=lay["width"],lay["height"]
    raw=(root/lay["blockdata_filepath"]).read_bytes()
    if len(raw)!=2*w*h:
        raise RuntimeError(f"unexpected native layout data for {lay['id']}: {len(raw)}, {w}x{h}")
    met=struct.unpack("<"+str(w*h)+"H",raw)
    def good(pt):
        x,y=pt
        return 0<=x<w and 0<=y<h and ((met[y*w+x]>>10)&3)==0
    return w,h,good

def walk(start,good,blocked=frozenset()):
    if not good(start) or start in blocked:return {},{}
    q=collections.deque([start]);dist={start:0};prev={}
    while q:
        x,y=q.popleft()
        for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if good(p) and p not in blocked and p not in dist:
                dist[p]=dist[x,y]+1;prev[p]=(x,y);q.append(p)
    return dist,prev

def setup(name, entry, boss, label, venue):
    f=maps/name/"map.json"
    m=json.loads(f.read_text())
    w,h,good=load_layout(m)
    if not good(entry) or not good(boss):
        raise RuntimeError(f"{name}: entry {entry} or boss {boss} blocked on {w}x{h} native layout")
    dist,prev=walk(entry,good,{boss})
    adjacent=[(boss[0]-1,boss[1]),(boss[0]+1,boss[1]),(boss[0],boss[1]-1),(boss[0],boss[1]+1)]
    reachable=[p for p in adjacent if p in dist]
    if not reachable:raise RuntimeError(f"{name}: player cannot approach leader")
    target=min(reachable,key=lambda p:dist[p])
    if dist[target]<2:raise RuntimeError(f"{name}: player has no visual approach to leader")
    route={target};p=target
    while p!=entry:
        p=prev[p];route.add(p)
    # Pick a visible gatekeeper reachable from entry but not sitting on the
    # necessary player-to-boss path. Fallback is a passive facing-A sign.
    allcells=[p for p in dist if p not in route and p not in adjacent
              and p!=entry and abs(p[0]-entry[0])+abs(p[1]-entry[1])<8]
    attendants=sorted(allcells,key=lambda p:dist[p])
    attendant=None
    for c in attendants:
        rest,_=walk(entry,good,{boss,c})
        if target in rest and any(abs(c[0]-q[0])+abs(c[1]-q[1])==1 for q in rest):
            attendant=c;break
    if attendant is None:raise RuntimeError(f"{name}: cannot position walkable gatekeeper")
    if len(m["object_events"])!=1:raise RuntimeError(f"{name}: unexpected NPC count")
    m["object_events"][0]["x"],m["object_events"][0]["y"]=boss
    m["object_events"][0]["script"]=name+"_EventScript_Leader"
    helper=dict(graphics_id="OBJ_EVENT_GFX_GENTLEMAN",
                x=attendant[0],y=attendant[1],elevation=3,
                movement_type="MOVEMENT_TYPE_FACE_DOWN",
                movement_range_x=0,movement_range_y=0,
                trainer_type="TRAINER_TYPE_NONE",
                trainer_sight_or_berry_tree_id="0",
                script=name+"_EventScript_ExitAttendant",flag="0")
    m["object_events"].append(helper)
    # Existing Gym puzzle exits are in unrelated disconnected regions in
    # several maps and point to a numerical warp index, not a safe doorway.
    # A real visible Gatekeeper now handles return directly.
    m["warp_events"]=[]
    m["coord_events"]=[]
    m["bg_events"]=[]
    f.write_text(json.dumps(m,indent=2)+"\n")
    source=maps/name/"scripts.inc"
    original=source.read_text()
    first=original.find(name+"_Text_")
    # Keep the original dialogue definitions from the first standalone
    # map text label, not references in the old auto-start script.
    patterns=(name+"_Text_Intro:\n",name+"_Text_Welcome:\n")
    candidates=[original.find(q) for q in patterns if q in original]
    if not candidates:raise RuntimeError(name+": original dialogue definitions missing")
    dialogue=original[min(candidates):]
    # Stage leader stands inside the arena until A-pressed. Never start
    # battle as soon as map loads, unlike old MAP_SCRIPT_ON_FRAME_TABLE.
    parts=[
       f"{name}_MapScripts::\n .byte 0\n",
       f"""{name}_EventScript_Leader::
 lockall
 faceplayer
 msgbox {name}_Text_Intro, MSGBOX_DEFAULT
 msgbox {name}_Text_Ready, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_Cancel
 closemessage
 special Ascension_PrepareChallenge
 goto_if_eq VAR_RESULT, 0, {name}_EventScript_NoTeam
 dowildbattle
 specialvar VAR_RESULT, GetBattleOutcome
 goto_if_ne VAR_RESULT, B_OUTCOME_WON, {name}_EventScript_Lost
 special Ascension_RecordVictory
 msgbox {name}_Text_Win, MSGBOX_DEFAULT
 warp MAP_ASCENSION_{'SUMMIT' if venue=='AscensionSummit' else 'TOWER_'+venue.removeprefix('AscensionTower')}, 5, 6
 waitstate
 end
{name}_EventScript_Lost::
 special Ascension_RecordDefeat
 msgbox {name}_Text_Lost, MSGBOX_DEFAULT
 special HealPlayerParty
 warp {('MAP_ASCENSION_CITY' if venue in ('AscensionTower1','AscensionTower2','AscensionTower3','AscensionTower4') else 'MAP_ASCENSION_CITY_EAST')}, {('42, 28' if venue=='AscensionTower1' else '19, 18' if venue=='AscensionTower2' else '11, 39' if venue=='AscensionTower3' else '5, 21' if venue=='AscensionTower4' else '58, 15' if venue=='AscensionTower5' else '45, 57' if venue=='AscensionTower6' else '39, 30' if venue=='AscensionTower7' else '16, 15' if venue=='AscensionTower8' else '35, 13')}
 waitstate
 end
{name}_EventScript_NoTeam::
 msgbox {name}_Text_NoTeam, MSGBOX_DEFAULT
{name}_EventScript_Cancel::
 releaseall
 end
{name}_EventScript_ExitAttendant::
 lock
 faceplayer
 msgbox {name}_Text_Exit, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_Stay
 closemessage
 warp MAP_ASCENSION_{'SUMMIT' if venue=='AscensionSummit' else 'TOWER_'+venue.removeprefix('AscensionTower')}, 5, 6
 waitstate
 end
{name}_EventScript_Stay::
 release
 end
{name}_Text_Ready:
 .string "CHALLENGE THE MASTER?\\\\nYour rival's whole team awaits.$"
{name}_Text_NoTeam:
 .string "No battle-ready team!\\\\nRecover your POKEMON.$"
{name}_Text_Exit:
 .string "RETURN TO THE TOWER?\\\\nNo battle will start.$"
"""
    ]
    # Old name-specific dialogue may have aliases depending on Bronze/Elite.
    if name=="AscensionBronzeBoss":
        pass # existing Text_Intro/Text_Win/Text_Lost
    else:
        # Other leader scripts use Text_Welcome and Text_Lead, not Intro.
        parts[1]=parts[1].replace("msgbox "+name+"_Text_Intro, MSGBOX_DEFAULT",
                                  "msgbox "+name+"_Text_Welcome, MSGBOX_DEFAULT\n msgbox "+name+"_Text_Lead, MSGBOX_DEFAULT")
    source.write_text("\n".join(parts)+"\n"+dialogue)
    # Patch the preceding Tower/Summit warp into valid native walkable tile.
    tour=maps/venue/"scripts.inc"
    txt=tour.read_text()
    pat=re.compile(r"( warp "+re.escape(label)+r", )(\d+), (\d+)\n")
    txt,n=pat.subn(lambda _ :f" warp {label}, {entry[0]}, {entry[1]}\n",txt)
    if n!=1:raise RuntimeError(f"{venue}: expected one boss warp, found {n}")
    tour.write_text(txt)
    print(f"V10 APPROACH {name}: player={entry}, leader={boss}, gatekeeper={attendant}, walk={dist[target]} steps; original Gym collisions respected")
    return (name,entry,boss,attendant)

proof=[]
for entry in placements:
    proof.append(setup(*entry))

# Ordinary Tower Master remains visibly at left sideline while challenger
# comes in from the far end. They speak to the player at each heal point.
for rank in range(1,9):
    name=f"AscensionTower{rank}"
    path=maps/name/"scripts.inc"
    s=path.read_text()
    s=once(s,
      f" applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterAside\n removeobject LOCALID_TOWER_BATTLE_ATTENDANT_1",
      f" applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterAside",
      name+" master stays at sideline")
    s=once(s,
      f" addobject LOCALID_TOWER_BATTLE_ATTENDANT_1\n goto {name}_EventScript_End",
      f" applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterReturn\n goto {name}_EventScript_End",
      name+" master restores starting position")
    s=once(s,
      f"{name}_Move_PlayerAdvance:\n",
      f"{name}_Move_MasterReturn:\n walk_right\n face_down\n step_end\n{name}_Move_MasterFacing:\n face_right\n step_end\n{name}_Move_PlayerAdvance:\n",
      name+" master movement")
    for suffix in ("Recovery","MidRecovery","BossApproach"):
        label=f"{name}_EventScript_{suffix}::"
        if label in s:
            s=once(s,label+"\n",label+f"\n applywaitmovement LOCALID_TOWER_BATTLE_ATTENDANT_1, {name}_Move_MasterFacing\n",
                   name+" "+suffix+" master appears")
    path.write_text(s)

# Verify the original Champion too, not only the eight ordinary towers.
assert len(proof)==9
print("V10 BOSS CHOREOGRAPHY: nine native walk-up A-button leaders, one visible exit gatekeeper each, no automatic on-frame fight; eight ordinary Tower Masters remain on sidelines and face player for checkpoint healing.")
