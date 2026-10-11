#!/usr/bin/env python3
"""Wildlands V5 lab move editor (Gate G).

A MOVE EDITOR in the lab opens Emerald's native Move Relearner UI for either
squad member. In Wildlands its list contains every LEGAL move for the species
(level-up at any level, TM/HM compatibility, move tutors) that the realtime
Arena actually implements (ArenaMoves_Get != NULL), minus moves already known.
No TM/HM items, Heart Scales or HMs are involved; the native forget-a-move
screen replaces a chosen slot, and the party's moves are what the Arena uses.
Moves the Arena cannot perform never appear, so nothing listed can crash or
do nothing; the editor's dialogue says so explicitly.
"""
from pathlib import Path
import json, sys

root = Path(sys.argv[1])


def patch(path, old, new, count=1):
    p = root / path
    s = p.read_text()
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new))


P = 'src/pokemon.c'
patch(P, '#include "constants/abilities.h"\n',
      '#include "constants/abilities.h"\n#include "arena_moves.h"\n#include "constants/party_menu.h"\n')

helper = r'''
// ---- Wildlands move editor list (native Move Relearner UI) -------------
#define WILDLANDS_EDITOR_MAX 48
bool8 Wildlands_CanLearnTutor(u16 species, u8 tutor);

static bool8 WildlandsEditor_Add(u16 *moves, u8 *n, u16 move, const u16 *known)
{
    u32 i;
    if (!move || move >= MOVES_COUNT || *n >= WILDLANDS_EDITOR_MAX || !ArenaMoves_Get(move))
        return FALSE;
    for (i = 0; i < MAX_MON_MOVES; i++)
        if (known[i] == move)
            return FALSE;
    for (i = 0; i < *n; i++)
        if (moves[i] == move)
            return FALSE;
    moves[(*n)++] = move;
    return TRUE;
}

static u8 Wildlands_EditorMoves(struct Pokemon *mon, u16 *moves)
{
    u16 known[MAX_MON_MOVES];
    u16 species = GetMonData(mon, MON_DATA_SPECIES, 0);
    u8 n = 0;
    u32 i;
    for (i = 0; i < MAX_MON_MOVES; i++)
        known[i] = GetMonData(mon, MON_DATA_MOVE1 + i, 0);
    // Level-up moves at ANY level: every squad member deploys at match level.
    for (i = 0; i < MAX_LEVEL_UP_MOVES && gLevelUpLearnsets[species][i] != LEVEL_UP_END; i++)
        WildlandsEditor_Add(moves, &n, gLevelUpLearnsets[species][i] & LEVEL_UP_MOVE_ID, known);
    for (i = 0; i < NUM_TECHNICAL_MACHINES + NUM_HIDDEN_MACHINES; i++)
        if (CanMonLearnTMHM(mon, i))
            WildlandsEditor_Add(moves, &n, ItemIdToBattleMoveId(ITEM_TM01 + i), known);
    for (i = 0; i < TUTOR_MOVE_COUNT; i++)
        if (Wildlands_CanLearnTutor(species, i))
            WildlandsEditor_Add(moves, &n, gTutorMoves[i], known);
    return n;
}
'''
patch(P, 'u8 GetMoveRelearnerMoves(struct Pokemon *mon, u16 *moves)\n{',
      helper + '\nu8 GetMoveRelearnerMoves(struct Pokemon *mon, u16 *moves)\n{\n'
      '    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1)\n'
      '        return Wildlands_EditorMoves(mon, moves);\n'
      '    {')
# close the extra block opened above at the end of the original function body
s = (root / P).read_text()
start = s.index('        return Wildlands_EditorMoves(mon, moves);\n    {')
end = s.index('\n    return numMoves;\n}', start)
s = s[:end] + '\n    return numMoves;\n    }\n}' + s[end + len('\n    return numMoves;\n}'):]
(root / P).write_text(s)

patch(P, 'u8 GetNumberOfRelearnableMoves(struct Pokemon *mon)\n{',
      'u8 GetNumberOfRelearnableMoves(struct Pokemon *mon)\n{\n'
      '    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1\n'
      '        && GetMonData(mon, MON_DATA_SPECIES_OR_EGG, 0) != SPECIES_EGG)\n'
      '    {\n'
      '        u16 buffer[WILDLANDS_EDITOR_MAX];\n'
      '        return Wildlands_EditorMoves(mon, buffer);\n'
      '    }\n'
      '    {')
s = (root / P).read_text()
start = s.index('        return Wildlands_EditorMoves(mon, buffer);\n    }\n    {')
end = s.index('\n    return numMoves;\n}', start)
s = s[:end] + '\n    return numMoves;\n    }\n}' + s[end + len('\n    return numMoves;\n}'):]
(root / P).write_text(s)

# Tutor compatibility is static in party_menu.c; expose a read-only wrapper.
pm = root / 'src/party_menu.c'
pm.write_text(pm.read_text() + '\nbool8 Wildlands_CanLearnTutor(u16 species, u8 tutor)\n{\n    return CanLearnTutorMove(species, tutor);\n}\n')

# Lab: the second rules sign becomes the MOVE EDITOR terminal.
sc = root / 'data/maps/AscensionTeamLab/scripts.inc'
sc.write_text(sc.read_text() + r'''
WildlandsLab_EventScript_MoveEditor::
 lockall
 msgbox WildlandsLab_Text_EditorIntro, MSGBOX_DEFAULT
WildlandsLab_EventScript_EditorChooseMon::
 msgbox WildlandsLab_Text_EditorWhich, MSGBOX_DEFAULT
 special ChooseMonForMoveRelearner
 waitstate
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, WildlandsLab_EventScript_EditorDone
 special IsSelectedMonEgg
 goto_if_eq VAR_RESULT, TRUE, WildlandsLab_EventScript_EditorChooseMon
 goto_if_eq VAR_0x8005, 0, WildlandsLab_EventScript_EditorNone
 msgbox WildlandsLab_Text_EditorPick, MSGBOX_DEFAULT
 special TeachMoveRelearnerMove
 waitstate
 goto WildlandsLab_EventScript_EditorChooseMon
WildlandsLab_EventScript_EditorNone::
 msgbox WildlandsLab_Text_EditorNone, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_EditorChooseMon
WildlandsLab_EventScript_EditorDone::
 releaseall
 end

WildlandsLab_Text_EditorIntro:
 .string "MOVE EDITOR: every legal move your\n"
 .string "POKEMON can use in the ARENA is\l"
 .string "listed. No TMs or HMs needed.\p"
 .string "Moves the ARENA can't perform yet\n"
 .string "are not offered.$"

WildlandsLab_Text_EditorWhich:
 .string "Edit which squad member's moves?$"

WildlandsLab_Text_EditorPick:
 .string "Pick a move, then the slot it\n"
 .string "replaces.$"

WildlandsLab_Text_EditorNone:
 .string "It already knows every ARENA-ready\n"
 .string "move it can learn.$"
''')
mp = root / 'data/maps/AscensionTeamLab/map.json'
j = json.loads(mp.read_text())
rules = [bg for bg in j['bg_events'] if bg.get('script') == 'WildlandsLab_EventScript_Rules']
if not rules:
    raise SystemExit('lab rules sign not found; V4 lab layout drift')
rules[-1]['script'] = 'WildlandsLab_EventScript_MoveEditor'
mp.write_text(json.dumps(j, indent=2) + '\n')
print('Wildlands move editor installed: native relearner UI, legal + Arena-supported moves only, no items')
