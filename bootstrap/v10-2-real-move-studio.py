#!/usr/bin/env python3
"""V10.2 species-legal 4-slot Move Studio via native Emerald move-relearner UI.

Only moves with actual Emerald Arena realtime profiles may be chosen. A JSON
coverage report lists legal Emerald moves still missing engine functionality.
"""
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]);maps=root/"data/maps"
career=root/"src/ascension_career.c"
relearner=root/"src/move_relearner.c"
specials=root/"data/specials.inc"
studio=maps/"AscensionMoveStudio/scripts.inc"
roster=json.loads((root/"tools/arena/roster.json").read_text())
d=root/"src/data/pokemon"
learn=(d/"level_up_learnsets.h").read_text()
tm=(d/"tmhm_learnsets.h").read_text()
tutor=(d/"tutor_learnsets.h").read_text()
egg=(d/"egg_moves.h").read_text()
profiles=(root/"src/arena_moves.c").read_text()
supported={m.group(1) for m in re.finditer(r"\{\s*MOVE_([A-Z0-9_]+)\s*,",profiles)}
supported.discard("STRUGGLE")
def once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{label}: expected one anchor, found {n}: {a[:80]!r}")
    return s.replace(a,b,1)
def region(s,pattern):
    m=re.search(pattern,s,re.S)
    return m.group(1) if m else None
entries=[]
all_used=[]
coverage={}
for item in roster:
    species=item["species"]
    proper="".join(p.title() for p in species.split("_"))
    lv=region(learn,r"s"+proper+r"LevelUpLearnset\[\]\s*=\s*\{(.*?)\n\};")
    tmlearn=region(tm,r"\[SPECIES_"+species+r"\]\s*=\s*\{\s*\.learnset\s*=\s*\{(.*?)\}\s*\}")
    tutorlearn=region(tutor,r"\[SPECIES_"+species+r"\]\s*=\s*\((.*?)\),")
    assert lv is not None and tmlearn is not None and tutorlearn is not None,("Missing learnset",species)
    egglearn=region(egg,r"egg_moves\("+species+r"\s*,(.*?)\),")
    moves=sorted(set(re.findall(r"MOVE_([A-Z0-9_]+)",lv)
                    +re.findall(r"\.([A-Z0-9_]+)\s*=\s*TRUE",tmlearn)
                    +re.findall(r"TUTOR\(MOVE_([A-Z0-9_]+)\)",tutorlearn)
                    +re.findall(r"MOVE_([A-Z0-9_]+)",egglearn or "")))
    native=[m for m in moves if m in supported]
    unsupported=[m for m in moves if m not in supported]
    assert len(native)<=46,(species,len(native))
    entries.append((species,len(all_used),len(native)))
    all_used.extend(native)
    coverage[species]={"legal_moves":len(moves),"native_usable":len(native),
                       "not_yet_supported":unsupported}
assert len(entries)==len(roster)==187
assert len(all_used)<32767
inc=root/"src/ascension_studio_legal.inc"
inc.write_text("""// GENERATED from pinned native Emerald + original Arena source.
struct AscensionStudioEntry {u16 species;u16 start;u8 count;};
static const u16 sAscensionStudioMoveBank[] = {
"""+",".join("MOVE_"+m for m in all_used)+"""};
static const struct AscensionStudioEntry sAscensionStudioIndex[] = {
"""+",\n".join(" {SPECIES_%s,%d,%d}" % t for t in entries)+"""
};
""")
report={"roster":len(roster),"existing_Arena_move_profiles":len(supported),
        "legal_species_move_pairs":sum(c["legal_moves"] for c in coverage.values()),
        "usable_species_move_pairs":sum(c["native_usable"] for c in coverage.values()),
        "missing_species_move_pairs":sum(len(c["not_yet_supported"]) for c in coverage.values()),
        "species":coverage,
        "limitations":"Level-up at any level, TM/HM, tutor and direct egg lists; inheritance from breeding family not fully expanded. Unsupported native Arena moves excluded until their actions work."}
(root/"v10-2-move-coverage.json").write_text(json.dumps(report,indent=2)+"\n")

s=career.read_text()
s+="""

// Original Emerald four-move learner UI bridge; no fake scripted move drills.
#include "ascension_studio_legal.inc"
EWRAM_DATA u8 gAscensionStudioMode=0;
void Ascension_StudioOn(void) {gAscensionStudioMode=TRUE;}
void Ascension_StudioOff(void) {gAscensionStudioMode=FALSE;}
u8 Ascension_GetStudioMoves(struct Pokemon *mon,u16 *output)
{
    u16 species,i,j,known[4];
    u8 count=0;
    if(!mon||GetMonData(mon,MON_DATA_IS_EGG))return 0;
    species=GetMonData(mon,MON_DATA_SPECIES);
    for(j=0;j<4;j++) known[j]=GetMonData(mon,MON_DATA_MOVE1+j);
    for(i=0;i<ARRAY_COUNT(sAscensionStudioIndex);i++)
    {
        const struct AscensionStudioEntry *entry=&sAscensionStudioIndex[i];
        if(entry->species!=species)continue;
        for(j=0;j<entry->count;j++)
        {
            u16 move=sAscensionStudioMoveBank[entry->start+j];
            u8 k;
            for(k=0;k<4;k++)if(known[k]==move)break;
            if(k==4)output[count++]=move;
        }
        return count;
    }
    return 0;
}
"""
career.write_text(s)
r=relearner.read_text()
r=once(r,"#define MAX_RELEARNER_MOVES max(MAX_LEVEL_UP_MOVES, 25)",
    "// 47 choices plus Cancel fit the native realtime-legal catalog.\n#define MAX_RELEARNER_MOVES 48\nextern u8 gAscensionStudioMode;\nextern u8 Ascension_GetStudioMoves(struct Pokemon *mon,u16 *moves);",
    "native move list capacity")
r=once(r,
  "sMoveRelearnerStruct->numMenuChoices = GetMoveRelearnerMoves(&gPlayerParty[sMoveRelearnerStruct->partyMon], sMoveRelearnerStruct->movesToLearn);",
  "sMoveRelearnerStruct->numMenuChoices = gAscensionStudioMode ? Ascension_GetStudioMoves(&gPlayerParty[sMoveRelearnerStruct->partyMon], sMoveRelearnerStruct->movesToLearn) : GetMoveRelearnerMoves(&gPlayerParty[sMoveRelearnerStruct->partyMon], sMoveRelearnerStruct->movesToLearn);",
  "connect native scrolling move/slot editor")
relearner.write_text(r)
ss=specials.read_text()
ss=once(ss,"\tdef_special Ascension_TrainChosenArenaMove",
   "\tdef_special Ascension_TrainChosenArenaMove\n\tdef_special Ascension_StudioOn\n\tdef_special Ascension_StudioOff",
   "native Move Studio mode selectors")
specials.write_text(ss)
# Native ChoosePartyMon gets party index in VAR_0x8004. The full Emerald
# move-relearner UI handles the four replacement slots, confirm and cancel.
s="""AscensionMoveStudio_MapScripts::
 .byte 0
AscensionMoveStudio_EventScript_Host::
 lock
 faceplayer
 msgbox AscensionV102_Move_Text_Welcome, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionV102_Move_EventScript_End
 msgbox AscensionV102_Move_Text_Pick, MSGBOX_DEFAULT
 special ChoosePartyMon
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, AscensionV102_Move_EventScript_End
 special Ascension_StudioOn
 msgbox AscensionV102_Move_Text_ChooseMove, MSGBOX_DEFAULT
 special TeachMoveRelearnerMove
 special Ascension_StudioOff
 msgbox AscensionV102_Move_Text_Return, MSGBOX_DEFAULT
AscensionV102_Move_EventScript_End::
 special Ascension_StudioOff
 release
 end
AscensionV102_Move_Text_Welcome:
 .string "MOVE STUDIO: choose real\\nlearnable POKEMON moves?$"
AscensionV102_Move_Text_Pick:
 .string "Choose a PARTY POKEMON.\\nReal-time moves only.$"
AscensionV102_Move_Text_ChooseMove:
 .string "Choose a MOVE, then one\\nof the FOUR slots to swap.$"
AscensionV102_Move_Text_Return:
 .string "Studio saved! Come back\\nfor another move change.$"
"""
studio.write_text(s)
assert "Ascension_GetStudioMoves" in career.read_text()
print("V10.2 STUDIO: native Emerald move list/preview + four-slot swap. %d of %d legal species-move pairs currently real-time supported; coverage report generated." % (report["usable_species_move_pairs"],report["legal_species_move_pairs"]))
