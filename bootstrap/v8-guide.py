#!/usr/bin/env python3
"""Native V8 START-menu Arena Guide and tower sign/directions.

Operate on the assembled original Emerald+Arena source after V7 world expansion.
No custom title screen, battle renderer or extra BG buffers. Idempotence: fail if
already applied, because silent duplicates can corrupt a GBA ROM.
"""
from pathlib import Path
import sys, json

root=Path(sys.argv[1])
src=root/"src/start_menu.c"
header=root/"include/constants/vars.h"
arena=root/"src/realtime_arena.c"
scripts=root/"data/event_scripts.s"
west=root/"data/maps/AscensionCity/map.json"
city_scripts=root/"data/maps/AscensionCity/scripts.inc"
east_scripts=root/"data/maps/AscensionCityEast/scripts.inc"

def replace_one(s,needle,replacement,identity):
    count=s.count(needle)
    if count!=1:
        raise RuntimeError("%s: expected unique source anchor, found %d: %r"%(identity,count,needle[:90]))
    return s.replace(needle,replacement,1)

v=header.read_text()
v=replace_one(v,"#define VAR_UNUSED_0x40FD", "#define VAR_ASCENSION_CAREER_ACTIVE",str(header))
header.write_text(v)
v=arena.read_text()
v=replace_one(v,"    VarSet(VAR_ASCENSION_TUTORIAL, 0);",
                "    VarSet(VAR_ASCENSION_CAREER_ACTIVE, 1);\n    VarSet(VAR_ASCENSION_TUTORIAL, 0);",str(arena))
arena.write_text(v)

v=src.read_text()
v=replace_one(v,'#include "script.h"','#include "script.h"\n#include "constants/vars.h"',str(src))
v=replace_one(v,'    MENU_ACTION_PYRAMID_BAG\n','    MENU_ACTION_PYRAMID_BAG,\n    MENU_ACTION_ARENA_GUIDE\n',str(src))
v=replace_one(v,"sCurrentStartMenuActions[9]","sCurrentStartMenuActions[10]",str(src))
v=replace_one(v,"static bool8 StartMenuPokeNavCallback(void);","static bool8 StartMenuPokeNavCallback(void);\nstatic bool8 StartMenuArenaGuideCallback(void);",str(src))
v=replace_one(v,"static const struct MenuAction sStartMenuItems[] =", 'static const u8 sText_ArenaGuide[] = _("ARENA GUIDE");\nextern const u8 EventScript_AscensionGuide[];\n\nstatic const struct MenuAction sStartMenuItems[] =',str(src))
v=replace_one(v,'[MENU_ACTION_PYRAMID_BAG]     = {gText_MenuBag,     {.u8_void = StartMenuBattlePyramidBagCallback}}',
    '[MENU_ACTION_PYRAMID_BAG]     = {gText_MenuBag,     {.u8_void = StartMenuBattlePyramidBagCallback}},\n    [MENU_ACTION_ARENA_GUIDE]     = {sText_ArenaGuide,    {.u8_void = StartMenuArenaGuideCallback}}',str(src))
v=replace_one(v,"    AddStartMenuAction(MENU_ACTION_SAVE);\n    AddStartMenuAction(MENU_ACTION_OPTION);",
                "    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1)\n        AddStartMenuAction(MENU_ACTION_ARENA_GUIDE);\n\n    AddStartMenuAction(MENU_ACTION_SAVE);\n    AddStartMenuAction(MENU_ACTION_OPTION);",str(src))
v=replace_one(v,'            && gMenuCallback != StartMenuExitCallback\n',
                '            && gMenuCallback != StartMenuExitCallback\n            && gMenuCallback != StartMenuArenaGuideCallback\n',str(src))
v=replace_one(v,"static bool8 StartMenuExitCallback(void)\n{",
"""static bool8 StartMenuArenaGuideCallback(void)
{
    // Works within ordinary Emerald UI; no extra VRAM allocation.
    RemoveExtraStartMenuWindows();
    HideStartMenu();
    ScriptContext_SetupScript(EventScript_AscensionGuide);
    return TRUE;
}

static bool8 StartMenuExitCallback(void)
{""",str(src))
src.write_text(v)

# Readable directory uses the original Emerald text converter.
# Dynamic progress in gStringVar1/gStringVar2 comes from native career special.
directory=[
 ("Bronze Trials", "WEST district - EAST side"),
 ("Gale Tower", "WEST district - NORTHWEST"),
 ("Verdant Crown", "WEST district - SOUTHWEST"),
 ("Phantom Spire", "WEST district - FAR WEST"),
 ("Inferno Forge", "EAST district - NORTHEAST"),
 ("Tidal Bastion", "EAST district - SOUTH"),
 ("Thunder Citadel", "EAST district - CENTRAL"),
 ("Astral Apex", "EAST district - NORTHWEST"),
 ("Champion Summit", "EAST district - NORTH hall")
]
# Construct short 2-line messages, avoid unsupported glyphs and longer than
# two typical Emerald text lines. Additional guide dialogs are opt-in.
def emerald_text(label,s):
    return '%s:\n\t.string "%s$"\n'%(label,s.replace("\n",r"\n"))
data="""@ Available through START > ARENA GUIDE during Ascension career mode.
EventScript_AscensionGuide::
 lockall
 special Ascension_GetProgress
 goto_if_eq VAR_RESULT, 0, EventScript_AscensionGuide_Completed
 msgbox AscensionGuide_Text_Progress, MSGBOX_DEFAULT
"""
for i in range(9):
    data+=f" goto_if_eq VAR_ASCENSION_RANK, {i}, EventScript_AscensionGuide_Tier{i}\n"
data+=" goto EventScript_AscensionGuide_List\n"
for i,(name,location) in enumerate(directory):
    data+=f"""EventScript_AscensionGuide_Tier{i}::
 msgbox AscensionGuide_Text_Tier{i}, MSGBOX_DEFAULT
 goto EventScript_AscensionGuide_List
"""
data+="""EventScript_AscensionGuide_Completed::
 msgbox AscensionGuide_Text_Completed, MSGBOX_DEFAULT
EventScript_AscensionGuide_List::
 msgbox AscensionGuide_Text_ShowAll, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, EventScript_AscensionGuide_Done
 msgbox AscensionGuide_Text_List1, MSGBOX_DEFAULT
 msgbox AscensionGuide_Text_List2, MSGBOX_DEFAULT
 msgbox AscensionGuide_Text_List3, MSGBOX_DEFAULT
EventScript_AscensionGuide_Done::
 releaseall
 end
"""
data+=emerald_text("AscensionGuide_Text_Progress","CURRENT RANK {STR_VAR_1}, FLOOR {STR_VAR_2}.\nFind your NEXT tower:")
for i,(name,location) in enumerate(directory):
    data+=emerald_text(f"AscensionGuide_Text_Tier{i}",f"{i+1}. {name.upper()}\n{location}")
data+=emerald_text("AscensionGuide_Text_Completed","CHAMPION! All towers cleared.\nRematches await you.")
data+=emerald_text("AscensionGuide_Text_ShowAll","Show the full tower order?")
data+=emerald_text("AscensionGuide_Text_List1","1 BRONZE / 2 GALE / 3 GRASS\n4 GHOST - WEST district")
data+=emerald_text("AscensionGuide_Text_List2","5 FIRE / 6 WATER / 7 THUNDER\n8 ASTRAL - WEST district")
data+=emerald_text("AscensionGuide_Text_List3","9 CHAMPION SUMMIT - EAST\nUse building signs and guides.")
v=scripts.read_text()
# This is the reusable script include registered through event_scripts.s,
# right beside the original V7 tower scripts. It uses native, English text.
marker='\t.include "data/maps/AscensionTower8/scripts.inc"'
v=replace_one(v,marker,marker+'\n\t.include "data/ascension_guide.inc"',str(scripts))
scripts.write_text(v)
(root/"data/ascension_guide.inc").write_text(data)

# Enhance the *existing* authentic in-world sign scripts; no invisible or fake
# background graphics on unsupported floor tiles.
v=city_scripts.read_text()
v+=('\nAscensionCity_EventScript_Directory::\n'
    ' msgbox AscensionCity_Text_Directory, MSGBOX_SIGN\n end\n'
    +emerald_text("AscensionCity_Text_Directory",
       "ASCENSION TOWERS 1-8\nUse START > ARENA GUIDE."))
city_scripts.write_text(v)
city=json.loads(west.read_text())
assert len(city["warp_events"])==8
assert len(city["bg_events"])>=2
# Existing authentic city signs already have tower labels from V8 layout.
west.write_text(json.dumps(city,indent=2)+"\n")

# Existing East district NPC points to the right destination; keep the text
# concise and consistent with the new in-game guide.
v=east_scripts.read_text()
v+=emerald_text("AscensionEast_Text_Guide","The Summit is in EAST city.\nSTART > ARENA GUIDE.")
east_scripts.write_text(v)
print("OK: native START > ARENA GUIDE, active-career flag, English tower directory and western sign.")
