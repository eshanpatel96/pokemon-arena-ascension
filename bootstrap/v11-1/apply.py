#!/usr/bin/env python3
"""V11.1 first implementation slice, not complete Beta acceptance.
Reproducible patches on assembled V11 after v11-hotfix.py. Fail on source drift.
Only combat scoring and west campus map/signs change; title/save/teams untouched.
"""
from pathlib import Path
from collections import deque
import hashlib,json,struct,sys
r=Path(sys.argv[1]); own=Path(__file__).resolve().parent

def once(s, old, new):
    if s.count(old)!=1: raise RuntimeError('source drift: '+repr(old[:100]))
    return s.replace(old,new,1)

# Preserve tested title, startup, save layouts, team and reward definitions.
protected=['src/title_screen.c','src/main_menu.c','src/ascension_career.c',
           'include/global.h','include/constants/vars.h','include/constants/flags.h']
hashes={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in protected}
p=r/'src/realtime_arena.c';s=p.read_text()
s=once(s,'    if(target->ability==ABILITY_LEVITATE && type==TYPE_GROUND)return 0;',
'''    if(target->ability==ABILITY_LEVITATE && type==TYPE_GROUND)return 0;
    // V11.1: don't feed the target's absorbing ability with damaging attacks.
    if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && gBattleMoves[move].power &&
       ((type==TYPE_WATER && target->ability==ABILITY_WATER_ABSORB)
        || (type==TYPE_ELECTRIC && target->ability==ABILITY_VOLT_ABSORB)
        || (type==TYPE_FIRE && target->ability==ABILITY_FLASH_FIRE)))return 0;''')
s=once(s,'static void AiChooseMove(s32 distance)\n{',
       '#include "ascension_ai_tactics.inc"\n\nstatic void AiChooseMove(s32 distance)\n{')
s=once(s,'    bool8 hasPhysical=FALSE,hasAttack=FALSE;',
'''    bool8 hasPhysical=FALSE,hasAttack=FALSE;
    bool8 career=VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1;
    bool8 visibleCommitment=FALSE;
    if(career
       && !SmokeBlocks(sArena.bodies[1].x/Q,sArena.bodies[1].y/Q,
                       sArena.bodies[0].x/Q,sArena.bodies[0].y/Q)
       && ArenaNav_LineClear(sArena.bodies[1].x/Q,sArena.bodies[1].y/Q,
                            sArena.bodies[0].x/Q,sArena.bodies[0].y/Q,2))
        visibleCommitment=sArena.bodies[0].shotTimer || sArena.bodies[0].actionLife;''')
s=once(s,'            if(move==MOVE_RAIN_DANCE)useful=!StormActive();',
'''            if(move==MOVE_RAIN_DANCE)useful=!StormActive();
            if(career && move==MOVE_PROTECT)
                useful=visibleCommitment && distance<140;''')
s=once(s,'            if(hasAttack && sArena.bodies[1].statusActions)useful=FALSE;',
'''            if(hasAttack && sArena.bodies[1].statusActions
               && !(career && move==MOVE_PROTECT))useful=FALSE;''')
start=s.index('        // Ascension career should reward reading patterns and positioning,')
end=s.index('        if(score>best)',start)
s=s[:start]+'''        if(career)
            score=AscensionAi_AdjustScore(p,score,distance,
                move==gArenaCombatTelemetry.lastMove[1],visibleCommitment,
                gBattleMons[1].hp*2<gBattleMons[1].maxHP,sArena.style);

'''+s[end:]
ai_text=s
assert (own/'ai_tactics.inc').is_file()

# Native geometry, not a replacement bitmap. The existing Gale plaza contains
# a compatible checker-paving pair (0x268/0x269). Connect the preparation campus
# using only ordinary sand tiles, leaving roofs, foliage, warps and elevations.
p=r/'data/layouts/AscensionCity/map.bin';words=list(struct.unpack('<4032H',p.read_bytes()));before=words[:];w,h=56,72
mp=r/'data/maps/AscensionCity/map.json';doc=json.loads(mp.read_text())
assert len(doc['object_events'])<=16
warps=json.loads(json.dumps(doc['warp_events']));actors=json.loads(json.dumps(doc['object_events']))
meta=r/'data/tilesets/secondary/battle_frontier_outside_west/metatile_attributes.bin'
attr=struct.unpack('<'+str(len(meta.read_bytes())//2)+'H',meta.read_bytes())
primary=r/'data/tilesets/primary/general/metatile_attributes.bin'
pa=struct.unpack('<'+str(len(primary.read_bytes())//2)+'H',primary.read_bytes())
assert (attr[0x268-512]&255)==(attr[0x269-512]&255)==(pa[0x5e]&255), 'floor behavior mismatch'
changed=[]
for y in range(h):
    for x in range(w):
        campus=(41<=x<=54 and 45<=y<=49)
        concourse=(18<=x<=43 and 41<=y<=44)
        approach=(25<=x<=28 and 36<=y<=44)
        if (campus or concourse or approach) and words[y*w+x]&1023==0x5e:
            words[y*w+x]=(words[y*w+x]&~1023)|(0x268 if (x+y)%2==0 else 0x269)
            changed.append((x,y))
assert len(changed)>=90
# No passability/elevation changes in the first campus slice, including scenery.
assert all((a&~1023)==(b&~1023) for a,b in zip(before,words))
# Two native sign objects, with normal stand-adjacent interaction. No NPC slot.
signsites=[(30,41,'AscensionV111_CampusDirectory'),(42,6,'AscensionV111_WardrobeSign')]
occupied={(z['x'],z['y']) for k in ('object_events','warp_events','bg_events') for z in doc[k]}
script=r/'data/maps/AscensionCity/scripts.inc';text=script.read_text()
messages={
'AscensionV111_CampusDirectory':r'PREPARATION CAMPUS\nSUPPLIES and MOVES: east.\pLAB and PC: southeast.\nWARDROBE: north coast.\pFollow the north road to\nthe STYLE HOUSE at the sea.',
'AscensionV111_WardrobeSign':r'STYLE HOUSE\nAvatar wardrobe and names.\pChoose your outfit inside.\nCancel keeps your current look.'}
for x,y,label in signsites:
    assert (x,y) not in occupied and ((words[y*w+x]>>10)&3)==0
    for a in actors:
        assert abs(a['x']-x)>a.get('movement_range_x',0) or abs(a['y']-y)>a.get('movement_range_y',0), 'sign in actor movement range'
    # Clone the ordinary city sign and retain the target elevation.
    words[y*w+x]=(words[y*w+x]&0xf000)|0x403
    doc['bg_events'].append(dict(type='sign',x=x,y=y,elevation=words[y*w+x]>>12,
        player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=label))
    assert label not in text
    text+='\n'+label+'::\n msgbox '+label+'_Text, MSGBOX_SIGN\n end\n'+label+'_Text:\n .string "'+messages[label]+'$"\n'

# Protect all previously reachable doors and approaches after placing signs.
def reachable(arr,blocked):
    seen={(26,40)};q=deque(seen)
    while q:
        x,y=q.popleft()
        for xx,yy in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0<=xx<w and 0<=yy<h and (xx,yy) not in blocked and (xx,yy) not in seen and not(arr[yy*w+xx]&0xc00):
                seen.add((xx,yy));q.append((xx,yy))
    return seen
blocked={(z['x'],z['y']) for z in actors}
was=reachable(before,blocked);now=reachable(words,blocked)
checks=[]
for warp in warps:
    # Doors can be collision-script tiles; use the walkable doorstep below.
    pos=(warp['x'],warp['y']+1)
    if pos in was:
        assert pos in now,('lost doorstep route',warp)
        checks.append({'destination':warp['dest_map'],'doorstep':pos})
for x,y,_ in signsites:
    assert any(p in now for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
assert doc['warp_events']==warps and doc['object_events']==actors
(r/'src/realtime_arena.c').write_text(ai_text)
(r/'src/ascension_ai_tactics.inc').write_text((own/'ai_tactics.inc').read_text())
p.write_bytes(struct.pack('<4032H',*words));mp.write_text(json.dumps(doc,indent=2)+'\n');script.write_text(text)
assert hashes=={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in protected}
report={'milestone':'V11.1 first code slice; not final Beta',
        'campus_floor_tiles_changed':len(changed),'new_native_signs':signsites,
        'npc_count':len(actors),'reachable_service_doorsteps':checks,
        'protected_file_sha256':hashes,'save_layout_changed':False,
        'new_legal_moves':0,'limitations':'Full town architecture, legal move coverage, hazards and save/campaign runtime acceptance remain open.'}
(r/'v11-1-first-slice-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
