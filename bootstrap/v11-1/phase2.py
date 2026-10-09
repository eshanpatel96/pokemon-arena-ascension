#!/usr/bin/env python3
"""Reproducible V11.1 gameplay pass after v11-1/apply.py. No title/save refactor."""
from pathlib import Path
from collections import deque
import hashlib, json, re, struct, sys
r=Path(sys.argv[1]); changed={}

def read(p): return (r/p).read_text()
def put(p,data):
 p=Path(p); f=r/p
 if str(p) not in changed: changed[str(p)]=f.read_bytes() if f.exists() else None
 f.parent.mkdir(parents=True,exist_ok=True)
 f.write_bytes(data if isinstance(data,bytes) else data.encode())
def once(s,a,b):
 assert s.count(a)==1,('source drift',a[:90],s.count(a))
 return s.replace(a,b,1)
def sha(p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
protected=['src/title_screen.c','src/main_menu.c','src/save.c','src/load_save.c','src/new_game.c','include/global.h','include/constants/vars.h','include/constants/flags.h']
protected += [f'data/maps/AscensionTower{i}/scripts.inc' for i in range(1,9)]
pinned={p:sha(p) for p in protected}
layout_index={x['id']:x for x in json.loads(read('data/layouts/layouts.json'))['layouts']}
rooms=json.loads(read('v11-room-manifest.json')); roomproof=[]
# Compact the active court; retain the surrounding 19x21 native architecture.
floors=[0x221,0x201,0x206,0x2e6,0x201,0x201,0x201,0x20a,0x313,0x211,0x230,0x201,0x20a]
accents=[0x201,0x202,0x214,0x2e7,0x221,0x211,0x230,0x201,0x2a0,0x201,0x201,0x230,0x201]
patterns=['010111010','101010101','010101010','101111101','101010111','010101101','001010100','101010101','010111101','101010101','111101111','001010100','101010101']
for idx,entry in enumerate(rooms):
 name=entry['name']; doc=json.loads(read(f'data/maps/{name}/map.json')); l=layout_index[doc['layout']]
 w,h=l['width'],l['height']; assert (w,h)==(19,21)
 a=list(struct.unpack('<399H',(r/l['blockdata_filepath']).read_bytes()))
 floor,accent=floors[idx],accents[idx]
 def tile(x,y,t):a[y*w+x]=0x3000|t
 # Remove the oversized old border without changing side scenery/columns.
 for y in range(7,14):
  for x in range(4,15):tile(x,y,floor)
 for y in range(8,13):
  for x in range(6,13):
   if x in (6,12) or y in (8,12):tile(x,y,accent)
 # A small native mosaic emblem instead of a blank center. All cells walkable.
 for j,on in enumerate(patterns[idx]):
  if on=='1':tile(8+j%3,9+j//3,accent)
 scriptpath=f'data/maps/{name}/scripts.inc';s=read(scriptpath)
 paths={
  'PlayerStage':['walk_down']*3+['walk_left']*2+['walk_down']*2+['face_right'],
  'BossStage':['walk_down']*6+['walk_right']*2+['face_left']}
 for role,steps in paths.items():
  pat=r'('+re.escape(name+'_Move_'+role)+r':\n)(?: [^\n]*\n)*? step_end\n'
  s,n=re.subn(pat,lambda m:m[1]+''.join(' '+x+'\n' for x in steps)+' step_end\n',s)
  assert n==1,(name,role,n)
 def walkable(p):
  x,y=p;return 0<=x<w and 0<=y<h and not(a[y*w+x]&0xc00)
 occupied={(z['x'],z['y']) for z in doc['object_events']}
 seen={(9,18)};q=deque(seen)
 while q:
  x,y=q.popleft()
  for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if walkable(p) and p not in occupied and p not in seen:seen.add(p);q.append(p)
 assert (9,5) in seen and (11,18) in seen,(name,'approach/exit')
 # Check every choreography step including interaction with the other actor.
 for start,role,other,end in [((9,5),'PlayerStage',(9,4),(7,10)),((9,4),'BossStage',(7,10),(11,10))]:
  x,y=start
  for step in paths[role]:
   if step.startswith('walk_'):
    dx,dy={'walk_down':(0,1),'walk_left':(-1,0),'walk_right':(1,0)}[step]
    x+=dx;y+=dy
    assert walkable((x,y)) and (x,y)!=other,(name,role,x,y)
  assert (x,y)==end
 put(l['blockdata_filepath'],struct.pack('<399H',*a));put(scriptpath,s)
 entry['player_fight']=[7,10];entry['enemy_fight']=[11,10]
 roomproof.append({'map':name,'court_tiles':[7,5],'actor_separation_pixels':64,'reachable_tiles':len(seen),'every_staging_step':'pass'})
put('v11-room-manifest.json',json.dumps(rooms,indent=2)+'\n')
# Extend the actual preparation-campus floor and add intact native planters.
p='data/layouts/AscensionCity/map.bin';a=list(struct.unpack('<4032H',(r/p).read_bytes()));before=a[:]
doc=json.loads(read('data/maps/AscensionCity/map.json'));w,h=56,72
actors=doc['object_events'];blocked={(z['x'],z['y']) for z in actors}
occupied={(z['x'],z['y']) for k in ('object_events','warp_events','bg_events') for z in doc[k]}
floorcount=0
for y in range(39,51):
 for x in range(8,55):
  if a[y*w+x]&1023==0x5e:
   a[y*w+x]=(a[y*w+x]&~1023)|(0x268 if (x+y)%2==0 else 0x269);floorcount+=1
# Reuse a complete 5x3 native flower-bed, preserving all its top/edge/bottom tiles.
planter=[before[(45+y)*w+17+x] for y in range(3) for x in range(5)]
planters=[]
for x0,y0 in [(9,43),(23,43),(33,48)]:
 cells=[(x0+x,y0+y) for y in range(3) for x in range(5)]
 if any((x,y) in occupied or a[y*w+x]&0xc00 or (a[y*w+x]&1023) not in (0x5e,0x268,0x269) for x,y in cells):continue
 if any(abs(z['x']-x)<=z.get('movement_range_x',0) and abs(z['y']-y)<=z.get('movement_range_y',0) for z in actors for x,y in cells):continue
 for n,(x,y) in enumerate(cells):a[y*w+x]=(a[y*w+x]&0xf000)|(planter[n]&0xfff)
 planters.append([x0,y0])
def reach(arr):
 q=deque([(26,40)]);seen=set(q)
 while q:
  x,y=q.popleft()
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=xx<w and 0<=yy<h and (xx,yy) not in blocked and (xx,yy) not in seen and not(arr[yy*w+xx]&0xc00):seen.add((xx,yy));q.append((xx,yy))
 return seen
was,now=reach(before),reach(a);doors=[]
for z in doc['warp_events']:
 pt=z['x'],z['y']+1
 if pt in was:assert pt in now,(z,'blocked doorstep');doors.append(z['dest_map'])
assert floorcount>100
put(p,struct.pack('<4032H',*a))
# Add native services as an include after the existing species-legal move table.
service_path=Path(__file__).with_name('services.inc')
put('src/ascension_v111_services.inc',service_path.read_bytes())
s=read('src/ascension_career.c')
s=once(s,'// Persistent for a single native trainer fight;', 'static void Ascension_V111LegalizeEnemyParty(void);\n\n// Persistent for a single native trainer fight;')
# Existing trainer membership/counts/ace order stay; illegal old moves get legal supported replacements.
s,n=re.subn(r'(^[ \t]*)gAscensionTrainerPartyActive\s*=\s*TRUE;',r'\1Ascension_V111LegalizeEnemyParty();\n\1gAscensionTrainerPartyActive=TRUE;',s,flags=re.M)
assert n==4,('enemy build paths',n)
s=once(s,'u8 pick=mon==5?5:(mon+cycle)%5;','u8 pick=floor==4 ? mon : (mon==5?5:(mon+cycle)%5);')
s+='\n#include "ascension_v111_services.inc"\n';put('src/ascension_career.c',s)
p='include/ascension_progress.h';s=read(p);s=s.replace('#endif','void Ascension_V111StartRosterTask(void);\n#endif');put(p,s)
p='src/realtime_arena.c';s=read(p)
s=once(s,'void RealtimeArena_DemoFieldCallback(void)\n{\n    FieldCB_WarpExitFadeFromBlack();\n}', 'void RealtimeArena_DemoFieldCallback(void)\n{\n    Ascension_V111StartRosterTask();\n}')
if '#include "ascension_progress.h"' not in s:s='#include "global.h"\n#include "ascension_progress.h"\n'+s
put(p,s)
p='data/specials.inc';s=read(p)
for fn in ['Ascension_V111SyncRoster','Ascension_V111ResetEVs']:s+='\tdef_special '+fn+'\n'
put(p,s)
# Birch no longer bulk-registers starters; existing saves have an opt-in assistant recovery.
p='data/maps/AscensionTeamLab/scripts.inc';s=read(p)
a=s.index(' msgbox AscensionTeamLab_Text_StarterOffer, MSGBOX_YESNO');b=s.index('AscensionTeamLab_EventScript_ProfessorOpen::',a)
s=s[:a]+' goto AscensionTeamLab_EventScript_ProfessorOpen\n'+s[b:]
s=once(s,'AscensionTeamLab_EventScript_Assistant::\n lock\n faceplayer\n','AscensionTeamLab_EventScript_Assistant::\n lock\n faceplayer\n checkflag FLAG_ASCENSION_STARTER_ROSTER_CLAIMED\n goto_if_set AscensionV111_RosterReady\n msgbox AscensionV111_RosterSyncText, MSGBOX_YESNO\n goto_if_eq VAR_RESULT, NO, AscensionV111_RosterReady\n closemessage\n special Ascension_V111SyncRoster\n waitstate\n goto_if_eq VAR_RESULT, 0, AscensionV111_RosterFull\n msgbox AscensionV111_RosterDoneText, MSGBOX_DEFAULT\nAscensionV111_RosterReady::\n')
s+='''\nAscensionV111_RosterFull::
 msgbox AscensionTeamLab_Text_NoStorage, MSGBOX_DEFAULT
 goto AscensionV111_RosterReady
AscensionV111_RosterSyncText:
 .string "Sync your starting collection?\\nExisting POKEMON stay unchanged.$"
AscensionV111_RosterDoneText:
 .string "Starting collection ready!\\nBIRCH handles earned rewards.$"
'''
put(p,s)
# Reversible EV reset added in the existing training dialogue, not a save-system change.
p='data/maps/AscensionCity/scripts.inc';s=read(p)
s=once(s,' msgbox AscensionV101_Text_HP, MSGBOX_YESNO',' msgbox AscensionV111_Text_ResetEVs, MSGBOX_YESNO\n goto_if_eq VAR_RESULT, YES, AscensionV111_ResetEVs\n msgbox AscensionV101_Text_HP, MSGBOX_YESNO')
s+='''\nAscensionV111_ResetEVs::
 msgbox AscensionV111_Text_ConfirmReset, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionV101_EventScript_TrainingEnd
 special Ascension_V111ResetEVs
 goto_if_eq VAR_RESULT, 0, AscensionV101_EventScript_Unavailable
 msgbox AscensionV111_Text_ResetDone, MSGBOX_DEFAULT
 goto AscensionV101_EventScript_TrainingEnd
AscensionV111_Text_ResetEVs:
 .string "Reset this POKEMON's EVs?\\nNO continues to stat training.$"
AscensionV111_Text_ConfirmReset:
 .string "Clear all six EV values?\\nSpecies, IVs and moves stay.$"
AscensionV111_Text_ResetDone:
 .string "EVs cleared. Stats updated!\\nTrain a new focus any time.$"
''';put(p,s)
assert pinned=={p:sha(p) for p in protected},'protected startup/save/ordinary scripts changed'
report={'milestone':'V11.1 second gameplay pass, not full feature acceptance','native_save_work':'unchanged; expanded validation deferred by user','protected_sha256':pinned,'boss_courts':roomproof,'additional_campus_floor_tiles':floorcount,'intact_native_planters':planters,'preserved_door_routes':doors,'starter_catalog':'80 species; batches of two per frame; deduplicated against current party and PC; legacy initial team retained','enemy_move_policy':'retain legal supported preferred moves, replace illegal slots using species legal native profiles; no enemy membership changes','new_move_profiles':0,'EV_reset':'native six-stat reset after confirmation','remaining':'Full legal move profiles/Box chooser, nature service, interactive hazards, remaining architecture, full campaign and Delta playtest'}
put('v11-1-phase2-report.json',json.dumps(report,indent=2)+'\n')
if '--backup' in sys.argv:
 out=Path(sys.argv[sys.argv.index('--backup')+1]);out.mkdir(parents=True,exist_ok=True)
 for p,data in changed.items():
  if data is not None:f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
print(json.dumps({k:v for k,v in report.items() if k!='protected_sha256'},indent=2))
