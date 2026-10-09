#!/usr/bin/env python3
"""V10.1 make the city Training Guide and Move Studio really selectable.

Native ChoosePartyMon, six useful +16 capped EV training focuses and three
supported original-Arena move drills (Protect / Double Team / Swift).
No fabricated stat bonuses, new effects, sprites, or mandatory XP grinding.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);maps=root/"data/maps"
career=root/"src/ascension_career.c";specials=root/"data/specials.inc"
def once(s,a,b,name):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{name}: expected one source anchor, got {n}: {a[:80]!r}")
    return s.replace(a,b,1)
s=career.read_text()
s+="""

// Free reversible build practice has real native Emerald EV/stat effects.
// Training caps each stat at 252 and full EV budget at 510; never changes
// the user's Pokemon species, moves, OT, nickname, IVs or personality.
void Ascension_TrainChosenStat(void)
{
    static const u8 fields[6]={
        MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV,
        MON_DATA_SPEED_EV, MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV
    };
    struct Pokemon *mon;
    u16 total=0,left;
    u8 stat,part,val;
    gSpecialVar_Result=0;
    part=gSpecialVar_0x8004;
    if(part>=PARTY_SIZE||gSpecialVar_0x8005>=6)return;
    mon=&gPlayerParty[part];
    if(GetMonData(mon,MON_DATA_IS_EGG))return;
    if(GetMonData(mon,MON_DATA_SPECIES)==SPECIES_NONE)return;
    stat=gSpecialVar_0x8005;
    for(part=0;part<6;part++)
        total+=GetMonData(mon,fields[part]);
    val=GetMonData(mon,fields[stat]);
    if(val>=252||total>=510)
    {
        gSpecialVar_Result=2;
        return;
    }
    left=510-total;
    if(left>252-val)left=252-val;
    if(left>16)left=16;
    val+=left;
    SetMonData(mon,fields[stat],&val);
    CalculateMonStats(mon);
    gSpecialVar_Result=1;
}
// Deliberate Move Studio choices actually change active native Arena move
// slots. All three drills are supported Arena engine moves, no fake menus.
void Ascension_TrainChosenArenaMove(void)
{
    struct Pokemon *mon;
    u16 move;
    u8 slot;
    gSpecialVar_Result=0;
    if(gSpecialVar_0x8004>=PARTY_SIZE)return;
    mon=&gPlayerParty[gSpecialVar_0x8004];
    if(GetMonData(mon,MON_DATA_IS_EGG))return;
    if(GetMonData(mon,MON_DATA_SPECIES)==SPECIES_NONE)return;
    switch(gSpecialVar_0x8005)
    {
    case 1:move=MOVE_PROTECT;slot=3;break;
    case 2:move=MOVE_DOUBLE_TEAM;slot=2;break;
    case 3:move=MOVE_SWIFT;slot=1;break;
    default:return;
    }
    SetMonMoveSlot(mon,move,slot);
    gSpecialVar_Result=1;
}
"""
career.write_text(s)
ss=specials.read_text()
ss=once(ss,"\tdef_special Ascension_ResetArenaMoves",
        "\tdef_special Ascension_ResetArenaMoves\n"
        "\tdef_special Ascension_TrainChosenStat\n"
        "\tdef_special Ascension_TrainChosenArenaMove",
        "new training specials")
specials.write_text(ss)

city=maps/"AscensionCity/scripts.inc";s=city.read_text()
a=s.index("AscensionCity_EventScript_Training::\n")
b=s.index("AscensionCity_EventScript_League::\n",a)
new="""AscensionCity_EventScript_Training::
 lock
 faceplayer
 msgbox AscensionV101_Text_StartEV, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionV101_EventScript_PracticeOffer
 msgbox AscensionV101_Text_Choose, MSGBOX_DEFAULT
 special ChoosePartyMon
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, AscensionV101_EventScript_TrainingEnd
 msgbox AscensionV101_Text_HP, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_HP
 msgbox AscensionV101_Text_Attack, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_Attack
 msgbox AscensionV101_Text_Defense, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_Defense
 msgbox AscensionV101_Text_Speed, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_Speed
 msgbox AscensionV101_Text_SpAtk, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_SpAtk
 msgbox AscensionV101_Text_SpDef, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_EventScript_SpDef
 goto AscensionV101_EventScript_TrainingEnd
AscensionV101_EventScript_HP::
 setvar VAR_0x8005, 0
 goto AscensionV101_EventScript_Train
AscensionV101_EventScript_Attack::
 setvar VAR_0x8005, 1
 goto AscensionV101_EventScript_Train
AscensionV101_EventScript_Defense::
 setvar VAR_0x8005, 2
 goto AscensionV101_EventScript_Train
AscensionV101_EventScript_Speed::
 setvar VAR_0x8005, 3
 goto AscensionV101_EventScript_Train
AscensionV101_EventScript_SpAtk::
 setvar VAR_0x8005, 4
 goto AscensionV101_EventScript_Train
AscensionV101_EventScript_SpDef::
 setvar VAR_0x8005, 5
AscensionV101_EventScript_Train::
 special Ascension_TrainChosenStat
 goto_if_eq VAR_RESULT, 0, AscensionV101_EventScript_Unavailable
 goto_if_eq VAR_RESULT, 2, AscensionV101_EventScript_Capped
 msgbox AscensionV101_Text_Trained, MSGBOX_DEFAULT
 goto AscensionV101_EventScript_TrainingEnd
AscensionV101_EventScript_Capped::
 msgbox AscensionV101_Text_Capped, MSGBOX_DEFAULT
 goto AscensionV101_EventScript_TrainingEnd
AscensionV101_EventScript_Unavailable::
 msgbox AscensionV101_Text_Unavailable, MSGBOX_DEFAULT
 goto AscensionV101_EventScript_TrainingEnd
AscensionV101_EventScript_PracticeOffer::
 msgbox AscensionCity_Text_PracticeOffer, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionV101_EventScript_TrainingEnd
 call AscensionCity_EventScript_PracticeBattle
AscensionV101_EventScript_TrainingEnd::
 release
 end

"""
s=s[:a]+new+s[b:]
for label,value in (
("StartEV","Choose which STAT to train?\nOr practice an Arena fight."),
("Choose","Pick one POKEMON to train.\nEach drill adds 16 EVs."),
("HP","Train HP endurance?"),
("Attack","Train physical ATTACK?"),
("Defense","Train physical DEFENSE?"),
("Speed","Train SPEED and agility?"),
("SpAtk","Train SPECIAL ATTACK?"),
("SpDef","Train SPECIAL DEFENSE?"),
("Trained","Training complete! Your\nPOKEMON is stronger."),
("Capped","EV limit reached for this\nPOKEMON or chosen stat."),
("Unavailable","Choose a valid POKEMON.\nNo training was applied."),
):
    s+=f'AscensionV101_Text_{label}:\n .string "'+value.replace("\n",r"\n")+'$"\n'
city.write_text(s)

move=maps/"AscensionMoveStudio/scripts.inc";s=move.read_text()
old_start=s.index("AscensionMoveStudio_EventScript_Host::\n")
old_stop=s.index("AscensionMoveStudio_Text_Intro:",old_start)
new="""AscensionMoveStudio_EventScript_Host::
 lock
 faceplayer
 msgbox AscensionV101_Move_Text_Start, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionMoveStudio_EventScript_End
 special ChoosePartyMon
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, AscensionMoveStudio_EventScript_End
 msgbox AscensionV101_Move_Text_Restore, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_Move_EventScript_Restore
 msgbox AscensionV101_Move_Text_Guard, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_Move_EventScript_Guard
 msgbox AscensionV101_Move_Text_Evade, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_Move_EventScript_Evade
 msgbox AscensionV101_Move_Text_Ranged, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV101_Move_EventScript_Ranged
 goto AscensionMoveStudio_EventScript_End
AscensionV101_Move_EventScript_Restore::
 special Ascension_ResetArenaMoves
 goto_if_eq VAR_RESULT, 0, AscensionMoveStudio_EventScript_Unsupported
 goto AscensionV101_Move_EventScript_Done
AscensionV101_Move_EventScript_Guard::
 setvar VAR_0x8005, 1
 goto AscensionV101_Move_EventScript_Set
AscensionV101_Move_EventScript_Evade::
 setvar VAR_0x8005, 2
 goto AscensionV101_Move_EventScript_Set
AscensionV101_Move_EventScript_Ranged::
 setvar VAR_0x8005, 3
AscensionV101_Move_EventScript_Set::
 special Ascension_TrainChosenArenaMove
 goto_if_eq VAR_RESULT, 0, AscensionMoveStudio_EventScript_Unsupported
AscensionV101_Move_EventScript_Done::
 msgbox AscensionV101_Move_Text_Done, MSGBOX_DEFAULT
 goto AscensionMoveStudio_EventScript_End
AscensionMoveStudio_EventScript_Unsupported::
 msgbox AscensionMoveStudio_Text_Unsupported, MSGBOX_DEFAULT
AscensionMoveStudio_EventScript_End::
 release
 end
"""
s=s[:old_start]+new+s[old_stop:]
for label,contents in (
 ("Start","Choose an ARENA MOVE drill?\nSelect your POKEMON."),
 ("Restore","Restore its four original\nArena moves?"),
 ("Guard","GUARD drill: set slot 4\nto PROTECT?"),
 ("Evade","DODGE drill: set slot 3\nto DOUBLE TEAM?"),
 ("Ranged","RANGED drill: set slot 2\nto SWIFT?"),
 ("Done","Move training saved!\nCheck your four move slots."),
):
    s+=f'AscensionV101_Move_Text_{label}:\n .string "'+contents.replace("\n",r"\n")+'$"\n'
move.write_text(s)
print("V10.1 SERVICES: real user-selected HP/Atk/Def/Speed/SpAtk/SpDef +16 EV capped at 252/510; Move Studio offers restore or PROTECT/DOUBLE TEAM/SWIFT real-time drills; optional safe practice retained.")
