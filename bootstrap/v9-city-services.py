#!/usr/bin/env python3
"""V9 city-service repair, preserving original Emerald native screens.

Make the old placeholder Style House a real party Name Rater and the Move
Studio a functional 4-move Arena-baseline repair desk. Full tactical loadout
editor, EV/nature/Wardrobe and their UI remain explicit unfinished V9 tasks.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
maps=root/"data/maps"
career=root/"src/ascension_career.c"
specials=root/"data/specials.inc"

def swap_once(old,new,s,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: expected 1 anchor, got {n}")
    return s.replace(old,new,1)

def string(label,value):
    return label+":\n\t.string \""+value.replace("\n",r"\n")+"$\"\n"

# The old Style House text was a non-functional "more options soon" notice.
# The native Name Rater route uses real party selection, OT checks, and
# Emerald's original naming screen callback (not custom save editing).
style=maps/"AscensionStyleHouse/scripts.inc"
s=style.read_text()
assert "AscensionStyleHouse_EventScript_Host::" in s
assert "more options soon" in s
s="""AscensionStyleHouse_MapScripts::
 .byte 0
AscensionStyleHouse_EventScript_Host::
 lock
 faceplayer
 msgbox AscensionStyleHouse_Text_Welcome, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionStyleHouse_EventScript_End
 msgbox AscensionStyleHouse_Text_Choose, MSGBOX_DEFAULT
 special ChoosePartyMon
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, AscensionStyleHouse_EventScript_End
 specialvar VAR_RESULT, ScriptGetPartyMonSpecies
 goto_if_eq VAR_RESULT, SPECIES_EGG, AscensionStyleHouse_EventScript_Egg
 special IsMonOTIDNotPlayers
 goto_if_eq VAR_RESULT, TRUE, AscensionStyleHouse_EventScript_NotOwned
 specialvar VAR_RESULT, MonOTNameNotPlayer
 goto_if_eq VAR_RESULT, TRUE, AscensionStyleHouse_EventScript_NotOwned
 msgbox AscensionStyleHouse_Text_Rename, MSGBOX_DEFAULT
 call Common_EventScript_NameReceivedPartyMon
 msgbox AscensionStyleHouse_Text_Done, MSGBOX_DEFAULT
 goto AscensionStyleHouse_EventScript_End
AscensionStyleHouse_EventScript_Egg::
 msgbox AscensionStyleHouse_Text_Egg, MSGBOX_DEFAULT
 goto AscensionStyleHouse_EventScript_End
AscensionStyleHouse_EventScript_NotOwned::
 msgbox AscensionStyleHouse_Text_NotOwned, MSGBOX_DEFAULT
AscensionStyleHouse_EventScript_End::
 release
 end
"""
for k,line in (
 ("Welcome","NAME STUDIO! Change a\nPOKEMON nickname for FREE?"),
 ("Choose","Select a POKEMON from\nyour party to rename."),
 ("Rename","Your name, your team!\nChoose a new nickname."),
 ("Done","All done! Your new name\nhas been saved."),
 ("Egg","An EGG cannot be renamed."),
 ("NotOwned","Only your own POKEMON\ncan be renamed here."),
):
    s+=string("AscensionStyleHouse_Text_"+k,line)
style.write_text(s)

# The first Move Studio service is a genuine emergency move profile repair:
# when item/TM/evolution/PP changes give a known recruit incompatible moves,
# restore the four original, identified, supported Arena baseline profiles.
# Full 187-species/custom loadout editing is NOT claimed by this facility.
s=career.read_text()
s+="""

// Restore known native real-time moves for starter/tower-reward recruits.
// Other species are never silently assigned an invalid shared profile.
void Ascension_ResetArenaMoves(void)
{
    u16 species,i,slot;
    const u16 *profile=NULL;
    gSpecialVar_Result=0;
    if(gSpecialVar_0x8004>=PARTY_SIZE)return;
    if(GetMonData(&gPlayerParty[gSpecialVar_0x8004],MON_DATA_IS_EGG))return;
    species=GetMonData(&gPlayerParty[gSpecialVar_0x8004],MON_DATA_SPECIES);
    for(i=0;i<ARRAY_COUNT(sAscensionStarterPool);i++)
        if(sAscensionStarterPool[i].species==species)
        {
            profile=sAscensionStarterMoves[sAscensionStarterPool[i].style];
            break;
        }
    if(profile==NULL)
        for(i=0;i<ASCENSION_TOWER_COUNT*8;i++)
            if(sTowerPrizes[i/8][i%8]==species)
            {
                profile=sTowerRewardMoveProfiles[i/8];
                break;
            }
    if(profile==NULL)return;
    for(slot=0;slot<MAX_MON_MOVES;slot++)
        SetMonMoveSlot(&gPlayerParty[gSpecialVar_0x8004],profile[slot],slot);
    gSpecialVar_Result=1;
}
"""
career.write_text(s)

s=specials.read_text()
s=swap_once("\tdef_special Ascension_ClaimTowerRewards",
            "\tdef_special Ascension_ClaimTowerRewards\n\tdef_special Ascension_ResetArenaMoves",
            s,"register real Move Studio special")
specials.write_text(s)

studio=maps/"AscensionMoveStudio/scripts.inc"
original=studio.read_text()
assert "AscensionMoveStudio_EventScript_Host::" in original
assert "MOVE STUDIO" in original
s="""AscensionMoveStudio_MapScripts::
 .byte 0
AscensionMoveStudio_EventScript_Host::
 lock
 faceplayer
 msgbox AscensionMoveStudio_Text_Intro, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionMoveStudio_EventScript_End
 msgbox AscensionMoveStudio_Text_Select, MSGBOX_DEFAULT
 special ChoosePartyMon
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, AscensionMoveStudio_EventScript_End
 special Ascension_ResetArenaMoves
 goto_if_eq VAR_RESULT, 0, AscensionMoveStudio_EventScript_Unsupported
 msgbox AscensionMoveStudio_Text_Ready, MSGBOX_DEFAULT
 goto AscensionMoveStudio_EventScript_End
AscensionMoveStudio_EventScript_Unsupported::
 msgbox AscensionMoveStudio_Text_Unsupported, MSGBOX_DEFAULT
AscensionMoveStudio_EventScript_End::
 release
 end
"""
for k,line in (
 ("Intro","MOVE STUDIO: restore\nfour native Arena moves?"),
 ("Select","Select a registered\nstarter or tower recruit."),
 ("Ready","Four Arena moves restored!\nCheck PP before battling."),
 ("Unsupported","No approved profile yet.\nThis POKEMON is unchanged."),
):
    s+=string("AscensionMoveStudio_Text_"+k,line)
studio.write_text(s)
assert "SetMonMoveSlot(&gPlayerParty[gSpecialVar_0x8004],profile[slot],slot)" in career.read_text()
print("V9 central services: original native party nickname UI in Style House and functional 4-move profile restoration for 80+64 registered recruits in Move Studio (custom move editor still outstanding).")
