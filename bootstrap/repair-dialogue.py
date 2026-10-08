#!/usr/bin/env python3
"""Repair Ascension V6.1 native Emerald dialogue encoding and make intro optional."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
city = root / "data/maps/AscensionCity/scripts.inc"
hall = root / "data/maps/AscensionTowerHall/scripts.inc"

# The Emerald text converter only transforms lines that BEGIN with .string.
# Earlier Ascension scripts used "Label: .string ..." and GNU as output
# literal ASCII bytes, so the game rendered nonsense and missed 0xFF EOS.
for file in (city, hall):
    src = file.read_text()
    src, count = re.subn(
        r"(?m)^([A-Za-z_][A-Za-z0-9_]*):[ \t]+(\.string[ \t]+)",
        r"\1:\n\t\2", src
    )
    if count < 8:
        raise SystemExit(f"{file}: expected at least 8 malformed strings, found {count}")
    if re.search(r"(?m)^[A-Za-z_][A-Za-z0-9_]*:[ \t]+\.string", src):
        raise SystemExit(f"{file}: unconverted string found")
    file.write_text(src)
    print(f"{file.name}: repaired {count} text labels")

src = city.read_text()
trigger = " map_script MAP_SCRIPT_ON_FRAME_TABLE, AscensionCity_OnFrame\n"
if src.count(trigger) != 1:
    raise SystemExit("Unexpected city auto-dialogue trigger")
src = src.replace(trigger, "")
old = """AscensionCity_EventScript_Welcome::
 msgbox AscensionCity_Text_Welcome, MSGBOX_NPC
 end"""
new = """AscensionCity_EventScript_Welcome::
 lock
 faceplayer
 setvar VAR_ASCENSION_TUTORIAL, 1
 msgbox AscensionCity_Text_Welcome, MSGBOX_DEFAULT
 msgbox AscensionCity_Text_Intro3, MSGBOX_DEFAULT
 msgbox AscensionCity_Text_PracticeOffer, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionCity_EventScript_WelcomeDone
 call AscensionCity_EventScript_PracticeBattle
AscensionCity_EventScript_WelcomeDone::
 release
 end"""
if src.count(old) != 1:
    raise SystemExit("Unexpected welcome guide NPC script")
city.write_text(src.replace(old, new))
print("City introduction no longer forces dialogue; talk to the guide for optional practice.")

# Built-in verification to prevent shipping another bad introduction.
for file in (city, hall):
    src = file.read_text()
    if any(".string" in line and not line.lstrip().startswith(".string") for line in src.splitlines()):
        raise SystemExit(f"{file}: text converter will miss dialogue")
assert "map_script MAP_SCRIPT_ON_FRAME_TABLE, AscensionCity_OnFrame" not in city.read_text()
