#!/usr/bin/env python3
"""V10.2 native Emerald wardrobe: five persistent visual choices using existing
overworld Brendan/May and Rival variants. No new animated sprite assets.

Original Name Rater remains in the same Style House. These are honest native
character sprite presets, not invented hair/skin/body-part editor controls.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]);maps=root/"data/maps"
vars_h=root/"include/constants/vars.h"
specials=root/"data/specials.inc"
career=root/"src/ascension_career.c"
avatar=root/"src/field_player_avatar.c"
style=maps/"AscensionStyleHouse/scripts.inc"
def once(s,a,b,where):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"{where} expected 1 anchor, got {n} {a[:65]!r}")
    return s.replace(a,b,1)
s=vars_h.read_text()
s=once(s,"#define VAR_UNUSED_0x40DC",
  "#define VAR_ASCENSION_WARDROBE                       0x40DC // 0..4 native player look\n//#define VAR_UNUSED_0x40DC",
  "persistent outfit state")
vars_h.write_text(s)

p=avatar.read_text()
p=once(p,'#include "constants/moves.h"','#include "constants/moves.h"\n#include "constants/vars.h"',"avatar var include")
p=once(p,
'''u8 GetPlayerAvatarGraphicsIdByStateIdAndGender(u8 state, u8 gender)
{
    return sPlayerAvatarGfxIds[state][gender];
}''',
'''u8 GetPlayerAvatarGraphicsIdByStateIdAndGender(u8 state, u8 gender)
{
    if (state == PLAYER_AVATAR_STATE_NORMAL
        && VarGet(VAR_ASCENSION_CAREER_ACTIVE))
    {
        switch(VarGet(VAR_ASCENSION_WARDROBE))
        {
        case 1:return OBJ_EVENT_GFX_BRENDAN_NORMAL;
        case 2:return OBJ_EVENT_GFX_MAY_NORMAL;
        case 3:return OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL;
        case 4:return OBJ_EVENT_GFX_RIVAL_MAY_NORMAL;
        }
    }
    return sPlayerAvatarGfxIds[state][gender];
}''',"avatar graphics on every map reload")
p=once(p,'''u8 GetPlayerAvatarGraphicsIdByCurrentState(void)
{
    u8 i;
    u8 flags = gPlayerAvatar.flags;
''',
'''u8 GetPlayerAvatarGraphicsIdByCurrentState(void)
{
    u8 i;
    u8 flags = gPlayerAvatar.flags;
    if ((flags & PLAYER_AVATAR_FLAG_ON_FOOT)
        && VarGet(VAR_ASCENSION_CAREER_ACTIVE))
        return GetPlayerAvatarGraphicsIdByStateId(PLAYER_AVATAR_STATE_NORMAL);
''',"current avatar appearance on foot")
avatar.write_text(p)
c=career.read_text()
c+="""

// Persistent GBA-native wardrobe, original player and rival sprite sheets.
void Ascension_ChooseWardrobeOutfit(void)
{
    u8 choice=gSpecialVar_0x8005;
    if(choice>4) {gSpecialVar_Result=0;return;}
    VarSet(VAR_ASCENSION_WARDROBE,choice);
    ObjectEventSetGraphicsId(&gObjectEvents[gPlayerAvatar.objectEventId],
        GetPlayerAvatarGraphicsIdByStateId(PLAYER_AVATAR_STATE_NORMAL));
    gSpecialVar_Result=1;
}
"""
# ascension_career.c already includes event object sprites and field header?
for include in ('#include "field_player_avatar.h"','#include "event_object_movement.h"'):
    if include not in c:
        c=once(c,'#include "constants/event_objects.h"','#include "constants/event_objects.h"\n'+include,include)
career.write_text(c)
sp=specials.read_text()
sp=once(sp,"\tdef_special Ascension_StudioOff",
        "\tdef_special Ascension_StudioOff\n\tdef_special Ascension_ChooseWardrobeOutfit",
        "register outfit special")
specials.write_text(sp)

f=style.read_text()
f=once(f,"AscensionStyleHouse_EventScript_Host::\n",
'''AscensionStyleHouse_EventScript_Host::
 lock
 faceplayer
 msgbox AscensionV102_Wardrobe_Text_Intro, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, AscensionStyleHouse_EventScript_NameRater
 msgbox AscensionV102_Wardrobe_Text_Original, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV102_Wardrobe_EventScript_Original
 msgbox AscensionV102_Wardrobe_Text_Brendan, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV102_Wardrobe_EventScript_Brendan
 msgbox AscensionV102_Wardrobe_Text_May, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV102_Wardrobe_EventScript_May
 msgbox AscensionV102_Wardrobe_Text_RivalBrendan, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV102_Wardrobe_EventScript_RivalBrendan
 msgbox AscensionV102_Wardrobe_Text_RivalMay, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, YES, AscensionV102_Wardrobe_EventScript_RivalMay
 goto AscensionStyleHouse_EventScript_End
AscensionV102_Wardrobe_EventScript_Original::
 setvar VAR_0x8005, 0
 goto AscensionV102_Wardrobe_EventScript_Equip
AscensionV102_Wardrobe_EventScript_Brendan::
 setvar VAR_0x8005, 1
 goto AscensionV102_Wardrobe_EventScript_Equip
AscensionV102_Wardrobe_EventScript_May::
 setvar VAR_0x8005, 2
 goto AscensionV102_Wardrobe_EventScript_Equip
AscensionV102_Wardrobe_EventScript_RivalBrendan::
 setvar VAR_0x8005, 3
 goto AscensionV102_Wardrobe_EventScript_Equip
AscensionV102_Wardrobe_EventScript_RivalMay::
 setvar VAR_0x8005, 4
AscensionV102_Wardrobe_EventScript_Equip::
 special Ascension_ChooseWardrobeOutfit
 msgbox AscensionV102_Wardrobe_Text_Done, MSGBOX_DEFAULT
 goto AscensionStyleHouse_EventScript_End
AscensionStyleHouse_EventScript_NameRater::
''',"retain Name Rater plus real wardrobe")
f+="""
AscensionV102_Wardrobe_Text_Intro:
 .string "Try a new trainer LOOK?\\nOr change POKEMON NAMES?$"
AscensionV102_Wardrobe_Text_Original:
 .string "Use your original trainer\\nappearance again?$"
AscensionV102_Wardrobe_Text_Brendan:
 .string "Wear classic BRENDAN's\\nEmerald outfit?$"
AscensionV102_Wardrobe_Text_May:
 .string "Wear classic MAY's\\nEmerald outfit?$"
AscensionV102_Wardrobe_Text_RivalBrendan:
 .string "Wear BRENDAN's rival\\nuniform and cap?$"
AscensionV102_Wardrobe_Text_RivalMay:
 .string "Wear MAY's rival\\nuniform and cap?$"
AscensionV102_Wardrobe_Text_Done:
 .string "Outfit applied! It saves\\nwith your ARENA career.$"
"""
style.write_text(f)
print("V10.2 WARDROBE: 5 actual original Emerald player/rival visual choices persisted in saved native var, with live graphics and retained Name Rater.")
