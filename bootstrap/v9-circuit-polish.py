#!/usr/bin/env python3
"""V9 post-expansion fight polish: Bronze semifinal, bounded enemy levels,
checkpoints, permanent recruits and clean loss returns to exact city doors.
Runs AFTER v9-campaign-depth.py; DOES NOT change its 4/5/.../9 floor schedule.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);maps=root/'data/maps';career=root/'src/ascension_career.c'
assert 'static inline unsigned Ascension_FloorCount' in (root/'include/ascension_progress.h').read_text()
returns=(('MAP_ASCENSION_CITY',42,28),('MAP_ASCENSION_CITY',19,18),
         ('MAP_ASCENSION_CITY',11,39),('MAP_ASCENSION_CITY',5,21),
         ('MAP_ASCENSION_CITY_EAST',58,15),('MAP_ASCENSION_CITY_EAST',45,57),
         ('MAP_ASCENSION_CITY_EAST',39,30),('MAP_ASCENSION_CITY_EAST',16,15))
names=('BRONZE TRIALS','GALE TOWER','VERDANT CROWN','PHANTOM SPIRE',
       'INFERNO FORGE','TIDAL BASTION','THUNDER CITADEL','ASTRAL APEX')
floors=(4,5,5,6,6,7,8,9)
def once(s,old,new,k):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'{k}: expected 1 anchor got {n} {old[:80]!r}')
 return s.replace(old,new,1)
def replace_text(s,label,line):
 p=re.compile('('+re.escape(label)+r':\n\s*\.string ")[^\"]+("\n)')
 s,n=p.subn(lambda m:m.group(1)+line.replace('\n',r'\n')+'$'+m.group(2),s)
 assert n==1,(label,n)
 return s

s=career.read_text()
# The career expansion reused Bronze Floor 2's three-mon team for Floor 3.
# Add a four-member semifinals variant; the Regirock boss remains Floor 4.
anchor='static const u8 sBronzeTeamSizes[3] = {2, 3, 4};'
semi='''
static const struct AscensionTrainerMon sBronzeSemiFinalTeams[3][4]={
    {
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_SCIZOR,{MOVE_QUICK_ATTACK,MOVE_SLASH,MOVE_DOUBLE_TEAM,MOVE_PROTECT}},
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
    },
    {
        {SPECIES_SANDSLASH,{MOVE_SCRATCH,MOVE_SLASH,MOVE_DIG,MOVE_SAND_ATTACK}},
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
    },
    {
        {SPECIES_RHYDON,{MOVE_ROCK_THROW,MOVE_ROCK_TOMB,MOVE_BODY_SLAM,MOVE_SUPERPOWER}},
        {SPECIES_SCIZOR,{MOVE_QUICK_ATTACK,MOVE_SLASH,MOVE_DOUBLE_TEAM,MOVE_PROTECT}},
        {SPECIES_GOLEM,{MOVE_ROCK_THROW,MOVE_ROCK_SLIDE,MOVE_BODY_SLAM,MOVE_DEFENSE_CURL}},
        {SPECIES_AGGRON,{MOVE_ROCK_TOMB,MOVE_HEADBUTT,MOVE_ROCK_SLIDE,MOVE_PROTECT}},
    },
};
'''
s=once(s,anchor,anchor+semi,'Bronze unique semifinal')
s=once(s,'u8 count = sBronzeTeamSizes[bronzePhase];',
       'u8 count = floor==2 ? 4 : sBronzeTeamSizes[bronzePhase];','Bronze semifinal four foes')
s=once(s,'const struct AscensionTrainerMon *op = &sBronzeRematchTeams[bronzePhase][VarGet(VAR_ASCENSION_REMATCH_CYCLE) % 3][mon];',
    'const struct AscensionTrainerMon *op = floor==2 ? &sBronzeSemiFinalTeams[VarGet(VAR_ASCENSION_REMATCH_CYCLE)%3][mon] : &sBronzeRematchTeams[bronzePhase][VarGet(VAR_ASCENSION_REMATCH_CYCLE)%3][mon];',
    'Bronze unique semifinal data')
# True five/six-member final boss teams, fixed last legendary, bounded
# enemy levels. Difficulty should emerge from tactics, not giant stat gaps.
s=once(s,
'''count=floor==0 ? 2 : floor==1 ? 3
         : floor+1==Ascension_FloorCount(rank) ? (rank==8 ? 6 : rank>=5 ? 5 : 4)
         : (floor>=4 && rank>=5 ? 5 : 4);''',
'''bool8 isBoss=floor+1==Ascension_FloorCount(rank);
     u8 level=59+rank+floor/2+(isBoss?2:0);
     count=isBoss ? (rank>=6?6:5) : floor==0?2 : floor==1?3 : floor>=4?5:4;''',
'level and full boss roster')
s=once(s,'CreateScriptedWildMon(op->species, 59+2*rank+floor, ITEM_NONE);',
     'CreateScriptedWildMon(op->species,level,ITEM_NONE);','first enemy level')
s=once(s,'CreateMon(&gEnemyParty[mon], op->species,59+2*rank+floor,',
     'CreateMon(&gEnemyParty[mon], op->species,level,','replacement enemy level')
s=once(s,'floor+1==Ascension_FloorCount(rank) ? (1500 + rank*200) : (350 + rank*55 + floor*125)',
       'floor+1==Ascension_FloorCount(rank) ? (1500 + rank*200) : (350 + rank*55 + floor*80)',
       'money pacing normal bouts')
s=once(s,'    VarSet(VAR_ASCENSION_REMATCH_CYCLE,(cycle+1)%3);',
       '    VarSet(VAR_ASCENSION_REMATCH_CYCLE,(cycle+1)%3);\n    VarSet(VAR_ASCENSION_FLOOR,0); // loss resets this run, not rank/unlocks',
       'tower loss reset')
s=once(s,
'''                if(part<2 || part>=6)continue;
                if(part<4 && floor<1)continue;
                if(part>=4 && floor<2)continue;''',
'''                if(part<2)continue; // boss legendary + partner AFTER clear
                if(floor < 1+(part-2)/2)continue;''',
'award six nonboss species after floors 1/2/3')
career.write_text(s)

for i in range(8):
 name=f'AscensionTower{i+1}';path=maps/name/'scripts.inc';s=path.read_text()
 s=replace_text(s,name+'_Text_Intro',
   f'TOWER {i+1}: {names[i]}!\n{floors[i]} fights incl. the Master.')
 if i<4:
  # Early towers receive a real advertised full-recovery checkpoint.
  mid=2 if i==0 else 3
  old=f' msgbox {name}_Text_Next, MSGBOX_DEFAULT\n goto {name}_EventScript_NextOpponent\n'
  new=f''' compare VAR_ASCENSION_FLOOR, {mid}
 goto_if_eq {name}_EventScript_Recovery
'''+old+f'''{name}_EventScript_Recovery::
 msgbox {name}_Text_Recovery, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, {name}_EventScript_NextOpponent
 special HealPlayerParty
 goto {name}_EventScript_NextOpponent
'''
  s=once(s,old,new,f'{name} early checkpoint')
  s+='\n'+name+'_Text_Recovery:\n\t.string "Recovery checkpoint!\\nFully heal your team?$"\n'
 if i==7:
  # Nine Astral fights: an additional sixth-floor checkpoint.
  old=f' compare VAR_ASCENSION_FLOOR, 4\n goto_if_eq {name}_EventScript_MidRecovery\n'
  s=once(s,old,old+f' compare VAR_ASCENSION_FLOOR, 6\n goto_if_eq {name}_EventScript_MidRecovery\n',
         'Astral second checkpoint')
 # A loss charges the fee exactly once, resets the run and recovers in town.
 dest,x,y=returns[i]
 old=f' setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT\n goto {name}_EventScript_Reset\n{name}_EventScript_NoTeam::'
 new=f''' setflag FLAG_HIDE_BATTLE_TOWER_OPPONENT
 special HealPlayerParty
 warp {dest}, {x}, {y}
 waitstate
 end
{name}_EventScript_NoTeam::'''
 s=once(s,old,new,f'{name} safe city loss return')
 path.write_text(s)

for i in range(8):
 name='AscensionBronzeBoss' if i==0 else f'AscensionLeader{i+1}'
 path=maps/name/'scripts.inc';s=path.read_text();dest,x,y=returns[i]
 back='Leave' if i==0 else 'Return'
 old=f' msgbox {name}_Text_Lost, MSGBOX_DEFAULT\n{name}_EventScript_{back}::'
 new=f''' msgbox {name}_Text_Lost, MSGBOX_DEFAULT
 special HealPlayerParty
 warp {dest}, {x}, {y}
 waitstate
 end
{name}_EventScript_{back}::'''
 s=once(s,old,new,f'{name} boss loss return')
 path.write_text(s)

path=root/'data/ascension_guide.inc';g=path.read_text()
g=once(g,'8 ASTRAL - WEST district','8 ASTRAL - EAST district','guide east district')
g=once(g,r'CHAMPION! All towers cleared.\nRematches await you.',
   r'All eight towers cleared!\nThe Summit is your next test.',
   'guide does not promise unfinished rematches')
path.write_text(g)
assert 'sBronzeSemiFinalTeams[3][4]' in career.read_text()
print('V9 circuit polish: Bronze unique four-mon semifinal, 5-6-mon leader rosters and bounded levels, 6 prior-floor unlocks, early/Astral heal checkpoints, one loss fee and auto city recovery, real tower names and guide corrections.')
