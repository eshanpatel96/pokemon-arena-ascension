#!/usr/bin/env python3
"""V9 active development pass: save-safe recruits, earned rewards, consistent
boss identities, deliberate economy and genuinely different native arena stages.

This runs after the original V9 alpha bootstrap. It is a source milestone,
NOT certification that the full town/tower art or real-time gameplay passed QA.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
maps = root / "data/maps"

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)

def update(path, before, after, label):
    s = path.read_text()
    path.write_text(once(s, before, after, label))

def change_line(path, label, message):
    s = path.read_text()
    pat = re.compile(r"("+re.escape(label)+r":\n\s*\.string \")[^\"]+(\"\n)")
    replacement = message.replace("\n", r"\n")
    s, count = pat.subn(lambda m: m.group(1)+replacement+"$"+m.group(2), s)
    if count != 1:
        raise RuntimeError(f"V9 dialogue {label}: expected 1, found {count}")
    path.write_text(s)

# Every successfully granted catalog entry is independently checkpointed in
# a NATIVE SAVED VAR. A full PC after some grants can no longer duplicate the
# first successfully handed-out Pokémon on retry. 0..80 is the next index.
vars_file = root / "include/constants/vars.h"
saved_var_h = vars_file.read_text()
# The original overlay already occupies some of Emerald's tail-end save
# variables. Never assume the last one (0x40FC) remained available: choose an
# ACTUALLY UNUSED reserved native variable from the current, fully patched
# engine. Start from 0x40F7 to avoid historical Ascension rank/floor flags.
for candidate in range(0x40F7, 0x40FD):
    unused = f"#define VAR_UNUSED_0x{candidate:04X}"
    if saved_var_h.count(unused) == 1:
        saved_var_h = saved_var_h.replace(
            unused,
            f"#define VAR_ASCENSION_STARTER_NEXT_INDEX               0x{candidate:04X} // next PC grant\\n//{unused}",
            1)
        vars_file.write_text(saved_var_h)
        break
else:
    raise RuntimeError("No unallocated native save var for starter progress")

career = root / "src/ascension_career.c"
s = career.read_text()
s = once(s,
    "    for(i=0;i<ARRAY_COUNT(sAscensionStarterPool);i++)",
    "    for(i=VarGet(VAR_ASCENSION_STARTER_NEXT_INDEX);i<ARRAY_COUNT(sAscensionStarterPool);i++)",
    "resume starter grant from native saved index")
s = once(s,
    "        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)\n            return; // storage full; don't mark success",
    "        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)\n            return; // no index advance: next attempt retries this grant\n"
    "        VarSet(VAR_ASCENSION_STARTER_NEXT_INDEX,i+1);",
    "save next catalog index after each success")

# The alpha made legendary/partner entries (slots 0/1) claimable BEFORE boss
# victory because only floor-gated slots 2..5 were conditionally filtered.
# Current-rank boss rewards and the remaining two are NOW locked until rank
# advances on successful leader defeat; earlier completed ranks are claimable.
begin = s.index("            if(rank==completed && !(")
end = s.index("            if(FlagGet(flag))continue;", begin)
s = s[:begin] + """            if(rank==completed)
            {
                // A tower in progress never grants its boss ace or end prizes.
                if(part<2 || part>=6)continue;
                if(part<4 && floor<1)continue;
                if(part>=4 && floor<2)continue;
            }
""" + s[end:]

# Keep the latest approved defeat cap, not the alpha/obsolete roadmap values.
s = once(s, "    if(penalty>1200)penalty=1200;",
            "    if(penalty>1000)penalty=1000;", "loss fine cap")
s = once(s,
    " AddMoney(&gSaveBlock1Ptr->money, 650 + rank*160 + floor*125);",
    " AddMoney(&gSaveBlock1Ptr->money,\n"
    "          floor==2 ? (1500 + rank*200) : (350 + rank*55 + floor*125));",
    "early normal/boss payout tuning")

# On leader maps, the distinct overworld EXPERT_F and PSYCHIC_M characters
# must also match the native battle trainer photo and name. Both matching
# photo classes have original Emerald trainer identities.
s = once(s,
    "             TRAINER_NORMAN_1,TRAINER_FLANNERY_1,TRAINER_JUAN_1,",
    "             TRAINER_EDWARD,TRAINER_FLANNERY_1,TRAINER_JUAN_1,",
    "Phantom leader native trainer photo")
s = once(s,
    "             TRAINER_ROXANNE_1,TRAINER_WINONA_1,TRAINER_JUAN_1,",
    "             TRAINER_ROXANNE_1,TRAINER_WINONA_1,TRAINER_MOLLIE,",
    "Verdant leader native trainer photo")
career.write_text(s)

# Stage 0..16 belong to the ORIGINAL Emerald Arena renderer. Previously all
# tower trial stages matched their boss stage, defeating the purpose of two
# different combat backdrops. These select native contrasting terrain only,
# with no claim that unique hazard sprites exist for all eight venues.
biome = root / "src/arena_biomes.inc"
s = biome.read_text()
trial_stages = [
    (1,4,8,2,2),    # Bronze: rocky landscape --> dramatic stone gym coliseum
    (2,4,13,4,7),   # Gale: open-air --> high-tower skyline
    (3,0,5,0,0),    # Verdant: deep forest --> native green sanctuary
    (4,4,14,4,4),  # Phantom: interior --> psychic/crypt chamber
    (5,2,16,4,11), # Inferno: native heated gym --> volcanic boss panorama
    (6,1,1,1,1),   # Tidal: water trial --> flood-lit gym
    (7,4,10,4,4),  # Thunder: basic training ring --> electric gym
    (8,4,15,4,7),  # Astral: open sky --> psychic observatory
]
boss_stages = [8,13,5,14,16,15,10,14]
for tier,old_biome,old_stage,new_biome,new_stage in trial_stages:
    s = once(s,
         f"case MAP_ASCENSION_TOWER_{tier}: gArenaBiome={old_biome};gArenaStage={old_stage};break;",
         f"case MAP_ASCENSION_TOWER_{tier}: gArenaBiome={new_biome};gArenaStage={new_stage};break;",
         f"trial environment stage {tier}") if (old_biome,old_stage)!=(new_biome,new_stage) else s
for tier in range(2,9):
    old_stages = {2:13,3:5,4:14,5:16,6:1,7:10,8:15}
    stage = boss_stages[tier-1]
    if stage != old_stages[tier]:
        s = once(s,
           f"case MAP_ASCENSION_LEADER_{tier}:gArenaBiome={4 if tier in (2,4,7,8) else 0 if tier==3 else 2 if tier==5 else 1};gArenaStage={old_stages[tier]};break;",
           f"case MAP_ASCENSION_LEADER_{tier}:gArenaBiome={4 if stage>=8 and stage<16 else 2 if stage==16 else 1 if stage==1 else 0};gArenaStage={stage};break;",
           f"leader environment stage {tier}")
biome.write_text(s)

# Tidal/Thunder final rounds automatically engage the already native
# rain, shallow-flood and electrical-conduction effect. This is a real Arena
# weather mechanic, using existing art, rendering and counterplay. Start only
# if the shared storm is inactive so a trainer-party send-out does not
# unconditionally reset the environment mid-round.
arena = root / "src/realtime_arena.c"
s = arena.read_text()
anchor = "    ElementsInit();\n    StormSprites();"
s = once(s, anchor, anchor + """
    if (VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1
        && !StormActive()
        && ((gSaveBlock1Ptr->location.mapNum |
             (gSaveBlock1Ptr->location.mapGroup<<8))==MAP_ASCENSION_LEADER_6
            || (gSaveBlock1Ptr->location.mapNum |
                (gSaveBlock1Ptr->location.mapGroup<<8))==MAP_ASCENSION_LEADER_7))
        StormStart(); // supported native flood/conductivity, not a fake overlay
""", "native boss environmental storm entry")
arena.write_text(s)

# The boss rooms already have appropriate native Emerald overworld assets.
# Give each leader explicit stakes and accurate next-tower/recruit information.
tower_messages = [
    ("AscensionBronzeBoss", "REGIROCK + AGGRON earned!\nClaim them at the LAB.", "GALE TOWER opens next."),
    ("AscensionLeader2", "LUGIA + DRAGONITE earned!\nNext: VERDANT CROWN.", "VERDANT CROWN opens next."),
    ("AscensionLeader3", "SUICUNE + SCEPTILE earned!\nNext: PHANTOM SPIRE.", "PHANTOM SPIRE opens next."),
    ("AscensionLeader4", "MEWTWO + GENGAR earned!\nNext: INFERNO FORGE.", "INFERNO FORGE opens next."),
    ("AscensionLeader5", "ENTEI + BLAZIKEN earned!\nNext: TIDAL BASTION.", "TIDAL BASTION opens next."),
    ("AscensionLeader6", "KYOGRE + SWAMPERT earned!\nNext: THUNDER CITADEL.", "THUNDER CITADEL opens next."),
    ("AscensionLeader7", "ZAPDOS + METAGROSS earned!\nNext: ASTRAL APEX.", "ASTRAL APEX opens next."),
    ("AscensionLeader8", "RAYQUAZA + SALAMENCE!\nAll 8 towers are clear.", "Champion circuit is V10."),
]
for name, earned, next_tower in tower_messages:
    file = maps / name / "scripts.inc"
    change_line(file, name+"_Text_Win", earned)
    # The new title clarifies that a different battlefield is deliberate.
    if name == "AscensionBronzeBoss":
        change_line(file, name+"_Text_Intro",
                    "BRONZE MASTER'S COLOSSEUM!\nFace REGIROCK last.")
    else:
        stage_title = {
            "AscensionLeader2":"SKY STORM ARENA",
            "AscensionLeader3":"ANCIENT TREE SANCTUARY",
            "AscensionLeader4":"THE SPECTRAL CRYPT",
            "AscensionLeader5":"THE MOLTEN FURNACE",
            "AscensionLeader6":"FLOODED AMPHITHEATER",
            "AscensionLeader7":"LIGHTNING REACTOR",
            "AscensionLeader8":"CELESTIAL OBSERVATORY",
        }[name]
        change_line(file, name+"_Text_Welcome", stage_title+"!\nThe leader awaits.")
        change_line(file, name+"_Text_Lost",
                    "Recover your team in town.\nThe leader will be ready.")

# Inspect earned text; it is NOT a promise that the prizes are in the player's
# party. Claim them through Birch. The main lock/flag fix above is authoritative.
assert "if(part<2 || part>=6)continue;" in career.read_text()
assert "VAR_ASCENSION_STARTER_NEXT_INDEX" in vars_file.read_text()
assert "StormStart(); // supported native" in arena.read_text()
assert all((maps/name/"scripts.inc").is_file() for name,_,_ in tower_messages)
print("V9 safety/atmosphere: resume-safe starter PC grants; boss rewards correctly gated; latest money cap; proper leader identities, native battle stage contrast and two native storm bosses.")
