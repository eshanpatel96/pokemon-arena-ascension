#!/usr/bin/env python3
"""WildLands Beta: the Lab COACH (V6 C2) and the arena-move sweep.

The deployment assistant becomes a COACH with one menu:
  PICK DUO  - opens the native Pokemon Storage (two-Pokemon cap stays)
  MOVES     - the move editor (legal + arena-supported moves only)
  CONTROLS  - the controls card
  DEPLOY    - starts a match
No bag, TMs or START menu are needed to set up a match.

Every Pokemon the player owns is swept to arena-supported (animated) moves:
all PC boxes and the party at NEW GAME, the party again whenever the duo
changes through the coach, and the duo once more at every deploy.
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


# ---- sweep helpers (C, in ascension_career.c next to the loadout) --------
p = root / 'src/ascension_career.c'
t = p.read_text()
if 'Wildlands_ArenaLoadout' not in t:
    raise SystemExit('coach: Wildlands_ArenaLoadout missing (run squad_apply first)')
p.write_text(t + r'''
// Beta: party (and optionally every PC box) to arena-supported moves only.
static void Wildlands_SweepParty(void)
{
    u32 k;
    for (k = 0; k < PARTY_SIZE; k++)
        if (GetMonData(&gPlayerParty[k], MON_DATA_SPECIES) && !GetMonData(&gPlayerParty[k], MON_DATA_IS_EGG))
            Wildlands_ArenaLoadout(&gPlayerParty[k]);
}
void Wildlands_SweepAllMoves(void)
{
    struct Pokemon mon;
    u32 box, pos;
    Wildlands_SweepParty();
    for (box = 0; box < TOTAL_BOXES_COUNT; box++)
        for (pos = 0; pos < IN_BOX_COUNT; pos++)
        {
            struct BoxPokemon *bm = GetBoxedMonPtr(box, pos);
            if (!GetBoxMonData(bm, MON_DATA_SPECIES) || GetBoxMonData(bm, MON_DATA_IS_EGG))
                continue;
            BoxMonToMon(bm, &mon);
            Wildlands_ArenaLoadout(&mon);
            SetBoxMonAt(box, pos, &mon.box);
        }
}
// Script special: after the coach's PICK DUO the new duo is swept.
void Wildlands_SweepMoves(void)
{
    Wildlands_SweepParty();
}
''')

p = root / 'data/specials.inc'
s = p.read_text()
anchor = '\tdef_special Wildlands_BufferStats'
if anchor not in s:
    raise SystemExit('coach: specials anchor drift')
p.write_text(s.replace(anchor, anchor + '\n\tdef_special Wildlands_SweepMoves', 1))

# ---- NEW GAME: sweep every PC box and the starting duo ------------------
A = 'src/realtime_arena.c'
patch(A, 'void Wildlands_ArenaLoadout(struct Pokemon *mon);\n',
      'void Wildlands_ArenaLoadout(struct Pokemon *mon);\nvoid Wildlands_SweepAllMoves(void);\n')
patch(A, '    AddBagItem(ITEM_X_SPEED,10);\n#endif\n    return TRUE;\n}',
      '    AddBagItem(ITEM_X_SPEED,10);\n    Wildlands_SweepAllMoves();   // Beta: every owned Pokemon starts arena-ready\n#endif\n    return TRUE;\n}')
# Roaming legendaries (dogs, birds, Regis) are earned in a match, not
# handed out: they leave the PC roster.
patch(A, '        if(species==SPECIES_CHARIZARD || species==SPECIES_BLASTOISE) continue;\n',
      '        if(species==SPECIES_CHARIZARD || species==SPECIES_BLASTOISE) continue;\n'
      '        if(species==SPECIES_RAIKOU || species==SPECIES_ENTEI || species==SPECIES_SUICUNE\n'
      '           || species==SPECIES_ARTICUNO || species==SPECIES_ZAPDOS || species==SPECIES_MOLTRES\n'
      '           || species==SPECIES_REGIROCK || species==SPECIES_REGICE || species==SPECIES_REGISTEEL) continue;\n')
# Deploy from the coach also sweeps the duo.
patch(A, '    VarSet(VAR_ASCENSION_FLOOR, sWildlandsPracticeGround);\n',
      '    {\n        u32 k;\n        for (k = 0; k < 2; k++)\n            Wildlands_ArenaLoadout(&gPlayerParty[k]);\n    }\n'
      '    VarSet(VAR_ASCENSION_FLOOR, sWildlandsPracticeGround);\n')

# ---- coach menu: reuse an unused multichoice slot -----------------------
M = 'src/data/script_menu.h'
patch(M, 'static const struct MenuAction MultichoiceList_UnusedSSTidal1[] =\n{\n    {gText_SouthernIsland},\n    {gText_BirthIsland},\n    {gText_Exit},\n};',
      'static const u8 sText_WlCoachDuo[] = _("PICK DUO");\n'
      'static const u8 sText_WlCoachMoves[] = _("MOVES");\n'
      'static const u8 sText_WlCoachControls[] = _("CONTROLS");\n'
      'static const u8 sText_WlCoachDeploy[] = _("DEPLOY");\n'
      'static const struct MenuAction MultichoiceList_UnusedSSTidal1[] =\n{\n'
      '    {sText_WlCoachDuo},\n    {sText_WlCoachMoves},\n    {sText_WlCoachControls},\n'
      '    {sText_WlCoachDeploy},\n    {gText_Exit},\n};')

# ---- scripts ------------------------------------------------------------
sc = root / 'data/maps/AscensionTeamLab/scripts.inc'
s = sc.read_text()
if 'WildlandsLab_EventScript_EditorChooseMon::' not in s:
    raise SystemExit('coach: move editor script missing (run move_editor_apply first)')
old_prof = (' .string "Use the PC to form a TWO-POKEMON\\n"\n'
            ' .string "squad, then report to deployment.$"\n')
if old_prof in s:
    s = s.replace(old_prof, ' .string "Talk to the COACH to pick your\\n"\n'
                            ' .string "duo, set moves and deploy.$"\n', 1)
# The build's beta version is on the Lab sign (professor), so testers can
# confirm which ROM they are running.
import os
_ver = os.environ.get('WL_VERSION', 'DEV')
if ' .string "WILDLANDS RESEARCH LAB\\p"' in s:
    s = s.replace(' .string "WILDLANDS RESEARCH LAB\\p"', ' .string "WILDLANDS BETA V' + _ver + '\\p"', 1)
else:
    raise SystemExit('coach: professor title anchor drift')
s = s.replace(' .string "TWO POKEMON. Use the PC first.$"',
              ' .string "TWO POKEMON. Choose PICK DUO.$"')
s += r'''
WildlandsLab_EventScript_Coach::
 lock
 faceplayer
 msgbox WildlandsLab_Text_CoachHello, MSGBOX_DEFAULT
WildlandsLab_EventScript_CoachMenu::
 message WildlandsLab_Text_CoachAsk
 waitmessage
 multichoice 0, 0, MULTI_UNUSED_SSTIDAL_1, FALSE
 switch VAR_RESULT
 case 0, WildlandsLab_EventScript_CoachDuo
 case 1, WildlandsLab_EventScript_CoachMoves
 case 2, WildlandsLab_EventScript_CoachControls
 case 3, WildlandsLab_EventScript_CoachDeploy
 goto WildlandsLab_EventScript_CoachBye

WildlandsLab_EventScript_CoachDuo::
 msgbox WildlandsLab_Text_CoachDuo, MSGBOX_DEFAULT
 special ShowPokemonStorageSystemPC
 waitstate
 special Wildlands_SweepMoves
 goto WildlandsLab_EventScript_CoachMenu

WildlandsLab_EventScript_CoachMoves::
 msgbox WildlandsLab_Text_EditorWhich, MSGBOX_DEFAULT
 special ChooseMonForMoveRelearner
 waitstate
 goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, WildlandsLab_EventScript_CoachMenu
 special IsSelectedMonEgg
 goto_if_eq VAR_RESULT, TRUE, WildlandsLab_EventScript_CoachMenu
 goto_if_eq VAR_0x8005, 0, WildlandsLab_EventScript_CoachMovesNone
 msgbox WildlandsLab_Text_EditorPick, MSGBOX_DEFAULT
 special TeachMoveRelearnerMove
 waitstate
 goto WildlandsLab_EventScript_CoachMoves
WildlandsLab_EventScript_CoachMovesNone::
 msgbox WildlandsLab_Text_EditorNone, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_CoachMoves

WildlandsLab_EventScript_CoachControls::
 msgbox WildlandsLab_Text_Controls, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_CoachMenu

WildlandsLab_EventScript_CoachDeploy::
 special Wildlands_QueuePractice
 goto_if_eq VAR_RESULT, 0, WildlandsLab_EventScript_CoachNeedTwo
 msgbox WildlandsLab_Text_Deploy, MSGBOX_DEFAULT
 release
 end
WildlandsLab_EventScript_CoachNeedTwo::
 msgbox WildlandsLab_Text_NeedTwo, MSGBOX_DEFAULT
 goto WildlandsLab_EventScript_CoachMenu

WildlandsLab_EventScript_CoachBye::
 msgbox WildlandsLab_Text_CoachBye, MSGBOX_DEFAULT
 release
 end

WildlandsLab_Text_CoachHello:
 .string "COACH: I'll get your duo ready.\n"
 .string "All my moves work in the ARENA.$"

WildlandsLab_Text_CoachAsk:
 .string "What do you need?$"

WildlandsLab_Text_CoachDuo:
 .string "Keep exactly TWO POKEMON in your\n"
 .string "party. The rest wait in the boxes.$"

WildlandsLab_Text_CoachBye:
 .string "Come back when you're ready.$"

WildlandsLab_Text_Controls:
 .string "D-PAD: move    A: attack\n"
 .string "B + D-PAD: dodge\p"
 .string "L / R: change move\n"
 .string "L + R: throw a POKE BALL\p"
 .string "SELECT: swap lead and partner\n"
 .string "START: pause, TEAM, LOG, MAP\p"
 .string "Stand still out of combat to\n"
 .string "heal. Stay inside the circle!$"
'''
sc.write_text(s)

# ---- the deployment assistant becomes the COACH -------------------------
mp = root / 'data/maps/AscensionTeamLab/map.json'
j = json.loads(mp.read_text())
objs = j.get('object_events', [])
print('lab object_events before coach:')
for o in objs:
    print('  ', o.get('graphics_id'), o.get('x'), o.get('y'), o.get('script'))
coach = [o for o in objs if o.get('script') == 'AscensionTeamLab_EventScript_Assistant']
if not coach:
    raise SystemExit('coach: deployment assistant not found in the lab')
for o in coach:
    o['script'] = 'WildlandsLab_EventScript_Coach'
    o['graphics_id'] = 'OBJ_EVENT_GFX_BLACK_BELT'
mp.write_text(json.dumps(j, indent=2) + '\n')
print('Lab COACH installed (PICK DUO / MOVES / CONTROLS / DEPLOY); all owned Pokemon swept to arena moves')
