#!/usr/bin/env python3
"""V9 starter catalog: Professor Birch can register 80 genuinely animated mons
into the native Pokemon PC exactly once, with varied valid Arena action slots.

User chooses 'yes' at the lab; never seeds while entering a map or every save.
Full native Pokedex/187 recruitment remains an iterative feature.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);maps=root/"data/maps"
groups={
"grass": "BULBASAUR IVYSAUR VENUSAUR VICTREEBEL BELLOSSOM LOTAD LOMBRE LUDICOLO SEEDOT NUZLEAF SHIFTRY SHROOMISH BRELOOM",
"fire": "CHARMANDER CHARMELEON CHARIZARD NINETALES ARCANINE RAPIDASH FLAREON SLUGMA",
"water": "SQUIRTLE WARTORTLE BLASTOISE GOLDUCK POLIWRATH TENTACOOL TENTACRUEL GOLDEEN SEAKING STARYU LAPRAS MARILL AZUMARILL BARBOACH WHISCASH",
"psychic": "ABRA KADABRA",
"fighting": "PRIMEAPE MACHOP MACHOKE MAKUHITA HARIYAMA MEDITITE MEDICHAM",
"ground": "SANDSHREW DUGTRIO MAROWAK",
"poison": "ARBOK KOFFING GULPIN SWALOT",
"bug": "BUTTERFREE BEEDRILL VENOMOTH WURMPLE SILCOON BEAUTIFLY CASCOON DUSTOX",
"flying": "ZUBAT GOLBAT SCYTHER",
"normal": "CLEFABLE PERSIAN EEVEE POOCHYENA MIGHTYENA ZIGZAGOON LINOONE SLAKOTH VIGOROTH WHISMUR LOUDRED EXPLOUD NOSEPASS SKITTY DELCATTY MAGIKARP",
"electric": "MAGNEMITE",
}
styles=[
 ("MOVE_ABSORB","MOVE_GIGA_DRAIN","MOVE_PROTECT","MOVE_GROWTH"),
 ("MOVE_EMBER","MOVE_FLAMETHROWER","MOVE_PROTECT","MOVE_QUICK_ATTACK"),
 ("MOVE_WATER_GUN","MOVE_SURF","MOVE_PROTECT","MOVE_BITE"),
 ("MOVE_PSYCHIC","MOVE_SWIFT","MOVE_REFLECT","MOVE_PROTECT"),
 ("MOVE_MACH_PUNCH","MOVE_SLAM","MOVE_CROSS_CHOP","MOVE_PROTECT"),
 ("MOVE_MUD_SHOT","MOVE_DIG","MOVE_SLAM","MOVE_PROTECT"),
 ("MOVE_ACID","MOVE_BITE","MOVE_GROWL","MOVE_PROTECT"),
 ("MOVE_LEECH_LIFE","MOVE_AERIAL_ACE","MOVE_SCRATCH","MOVE_PROTECT"),
 ("MOVE_WING_ATTACK","MOVE_GUST","MOVE_QUICK_ATTACK","MOVE_PROTECT"),
 ("MOVE_TACKLE","MOVE_QUICK_ATTACK","MOVE_SLASH","MOVE_PROTECT"),
 ("MOVE_THUNDER_SHOCK","MOVE_SHOCK_WAVE","MOVE_QUICK_ATTACK","MOVE_PROTECT"),
]
specs=[]
for idx,names in enumerate(groups.values()):
 for name in names.split():specs.append((name,idx))
roster=json.loads((root/"tools/arena/roster.json").read_text())
animated={x["species"] for x in roster}
assert len(specs)==80,len(specs)
assert len(set(name for name,idx in specs))==80
assert all(name in animated for name,idx in specs)
original=(root/"src/arena_moves.c").read_text()
for style in styles:
 for move in style:
  if "{"+move+"," not in original:raise RuntimeError("native move unsupported: "+move)

flags=root/"include/constants/flags.h"
h=flags.read_text()
assert h.count("#define FLAG_UNUSED_0x021")==1
h=h.replace("#define FLAG_UNUSED_0x021","#define FLAG_ASCENSION_STARTER_ROSTER_CLAIMED")
flags.write_text(h)

career=root/"src/ascension_career.c"
c=career.read_text()
c=c.replace('#include "money.h"','#include "money.h"\n#include "constants/flags.h"',1)
items=",\n".join("    {SPECIES_"+name+", "+str(index)+"}" for name,index in specs)
moves=",\n".join("    {"+", ".join(move for move in style)+"}" for style in styles)
c+="""

struct AscensionStarterSpecies {u16 species;u8 style;};
static const struct AscensionStarterSpecies sAscensionStarterPool[] =
{
"""+items+"""
};
static const u16 sAscensionStarterMoves[][MAX_MON_MOVES] =
{
"""+moves+"""
};

// Professor Birch hands out a native PC catalog exactly once. A full PC does
// not destroy an existing Pokemon or fake a successful grant.
void Ascension_RegisterStarterRoster(void)
{
    struct Pokemon mon;
    u16 i;
    u8 slot;
    gSpecialVar_Result=0;
    if(FlagGet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED))
    {
        gSpecialVar_Result=2;
        return;
    }
    for(i=0;i<ARRAY_COUNT(sAscensionStarterPool);i++)
    {
        const struct AscensionStarterSpecies *candidate=&sAscensionStarterPool[i];
        CreateMon(&mon,candidate->species,60,USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
        for(slot=0;slot<MAX_MON_MOVES;slot++)
            SetMonMoveSlot(&mon,sAscensionStarterMoves[candidate->style][slot],slot);
        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)
            return; // storage full; don't mark success
    }
    FlagSet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED);
    gSpecialVar_Result=1;
}
"""
career.write_text(c)

specials=root/"data/specials.inc";v=specials.read_text()
needle="\tdef_special Ascension_RecordDefeat"
assert v.count(needle)==1
specials.write_text(v.replace(needle,needle+"\n\tdef_special Ascension_RegisterStarterRoster"))
lab=maps/"AscensionTeamLab/scripts.inc";s=lab.read_text()
old="""AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 msgbox AscensionTeamLab_Text_OpenBoxes, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_ProfessorDone
 special ShowPokemonStorageSystemPC
AscensionTeamLab_EventScript_ProfessorDone::
 release
 end"""
new="""AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 msgbox AscensionTeamLab_Text_Professor, MSGBOX_DEFAULT
 msgbox AscensionTeamLab_Text_StarterOffer, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_ProfessorOpen
 special Ascension_RegisterStarterRoster
 goto_if_eq VAR_RESULT, 0, AscensionTeamLab_EventScript_NoStorage
 goto_if_eq VAR_RESULT, 2, AscensionTeamLab_EventScript_ProfessorOpen
 msgbox AscensionTeamLab_Text_Added, MSGBOX_DEFAULT
 goto AscensionTeamLab_EventScript_ProfessorOpen
AscensionTeamLab_EventScript_NoStorage::
 msgbox AscensionTeamLab_Text_NoStorage, MSGBOX_DEFAULT
AscensionTeamLab_EventScript_ProfessorOpen::
 msgbox AscensionTeamLab_Text_OpenBoxes, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionTeamLab_EventScript_ProfessorDone
 special ShowPokemonStorageSystemPC
AscensionTeamLab_EventScript_ProfessorDone::
 release
 end"""
assert s.count(old)==1
s=s.replace(old,new)
for k,msg in {
"StarterOffer":"Register 80 Arena POKEMON\\nin your PC boxes?",
"Added":"Your starting roster is ready!\\nOpen BOXES to form a team.",
"NoStorage":"Not enough PC space!\\nFree a few slots and retry."}.items():
 s+="\nAscensionTeamLab_Text_"+k+":\n\t.string \""+msg+"$\"\n"
lab.write_text(s)
print("V9 Lab: one-time 80 native starter species registration, 11 varied real-time move profiles, Professor-led PC management.")
