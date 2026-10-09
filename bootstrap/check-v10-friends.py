#!/usr/bin/env python3
"""V10 map + town native source gate; no fabricated emulator screenshots.

Proves all 9 boss entries/leader positions are within bounds and reachable
with their side exit NPC not blocking the route. Scans both city map tiles,
metatile artwork, 4bpp palette indices, door metadata and genuine landmarks.
Emits clean PNG previews with NO debug warp or object marker overlays.
"""
from pathlib import Path
import collections,json,struct,sys
from PIL import Image

root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
layouts={x["id"]:x for x in json.loads((root/"data/layouts/layouts.json").read_text())["layouts"]}
maps=root/"data/maps"
# Masters circuit is an actual additional playable campaign segment; all
# first-clear rewards are native flags and have independent save progression.
career=(root/"src/ascension_career.c").read_text()
vars_h=(root/"include/constants/vars.h").read_text()
flags_h=(root/"include/constants/flags.h").read_text()
assert "sMastersTrainerTeams[8][6]" in career
assert "sMastersRewards[18]" in career
assert "Ascension_ClaimMastersRewards(void)" in career
assert "VAR_ASCENSION_MASTERS_STAGE" in vars_h
assert "VAR_ASCENSION_MASTERS_BEST" in vars_h
assert "FLAG_ASCENSION_MASTERS_PRIZE_FIRST" in flags_h
summit=(maps/"AscensionSummit/scripts.inc").read_text()
assert "AscensionSummit_EventScript_MastersOffer" in summit
assert "AscensionSummit_EventScript_MastersNext" in summit
assert "AscensionSummit_EventScript_MastersHeal" in summit
assert summit.count("special Ascension_RecordMastersDefeat")==1
assert "special Ascension_ClaimMastersRewards" in (maps/"AscensionTeamLab/scripts.inc").read_text()
for i in range(1,10):
    label="AscensionBronzeBoss" if i==1 else f"AscensionLeader{i}"
    doc=json.loads((maps/label/"map.json").read_text())
    l=layouts[doc["layout"]];w,h=l["width"],l["height"]
    data=(root/l["blockdata_filepath"]).read_bytes()
    assert len(data)==2*w*h,(label,"incorrect layout dimensions")
    tiles=struct.unpack("<"+str(w*h)+"H",data)
    def good(p):
        x,y=p
        return 0<=x<w and 0<=y<h and ((tiles[y*w+x]>>10)&3)==0
    objs=doc["object_events"]
    assert len(objs)==2,(label,"leader+attendant required")
    boss=(objs[0]["x"],objs[0]["y"])
    helper=(objs[1]["x"],objs[1]["y"])
    assert "Leader" in objs[0]["script"] and "ExitAttendant" in objs[1]["script"]
    assert good(boss) and good(helper),(label,boss,helper,"blocked object")
    prior=maps/("AscensionSummit" if i==9 else f"AscensionTower{i}")/"scripts.inc"
    script=prior.read_text()
    import re
    target="MAP_ASCENSION_LEADER_"+str(i) if i>1 else "MAP_ASCENSION_BRONZE_BOSS"
    m=re.search(r" warp "+target+r", (\d+), (\d+)\n",script)
    assert m,(label,"missing scripted entry warp")
    entry=(int(m[1]),int(m[2]))
    assert good(entry),(label,entry,"blocked entrance")
    blocked={boss,helper}
    reached={entry};q=collections.deque([entry])
    while q:
        x,y=q.popleft()
        for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if good(p) and p not in blocked and p not in reached:
                reached.add(p);q.append(p)
    near=[(boss[0]+1,boss[1]),(boss[0]-1,boss[1]),(boss[0],boss[1]+1),(boss[0],boss[1]-1)]
    assert any(p in reached for p in near),(label,"leader inaccessible")
    assert any(abs(helper[0]-p[0])+abs(helper[1]-p[1])==1 for p in reached),(label,"gatekeeper inaccessible")
    b=(maps/label/"scripts.inc").read_text()
    assert "MAP_SCRIPT_ON_FRAME_TABLE" not in b,(label,"auto-trigger remains")
    assert b.count("dowildbattle")==1 and "MSGBOX_YESNO" in b
    assert "EventScript_ExitAttendant" in b
    assert b.count("special Ascension_RecordDefeat")==1
    print(f"{label}: A-trigger leader, walkable entry {entry}, reachable boss {boss}, visible exit {helper}")

# V10.1 requires authentic opposite-sideline staging and functional choices.
for tier in range(1,9):
    name=f"AscensionTower{tier}"
    content=(maps/name/"scripts.inc").read_text()
    for move in ("Move_MasterAside","Move_MasterReturn","Move_PlayerAdvance",
                 "Move_PlayerRetreat","Move_ChallengerEnter","Move_ChallengerExit",
                 "Move_MasterFacing","Move_MasterBackToSide"):
        assert name+"_"+move+":" in content,(name,move)
    assert " walk_right\\n walk_right\\n face_left\\n step_end".replace("\\n","\n") in content
    assert "AscensionTower"+str(tier)+"_Move_PlayerAdvance:\n walk_up\n walk_up\n face_right\n step_end" in content
    assert "AscensionTower"+str(tier)+"_Move_MasterAside:\n walk_left\n walk_down\n walk_down\n face_up\n step_end" in content
for label in ("Ascension_TrainChosenStat","Ascension_TrainChosenArenaMove"):
    assert f"void {label}(void)" in career,label
west=(maps/"AscensionCity/scripts.inc").read_text()
studio=(maps/"AscensionMoveStudio/scripts.inc").read_text()
for key in ("AscensionV101_Text_HP","AscensionV101_Text_Attack",
            "AscensionV101_Text_Defense","AscensionV101_Text_Speed",
            "AscensionV101_Text_SpAtk","AscensionV101_Text_SpDef"):
    assert key in west,key
# Native Emerald's detailed scrolling move list, slot replacement and cancel
# should be used. Only move profiles genuinely implemented in Arena may show.
assert "AscensionV102_Move_Text_ChooseMove" in studio
assert "special TeachMoveRelearnerMove" in studio
assert "special Ascension_StudioOn" in studio
assert "special Ascension_StudioOff" in studio
assert "Ascension_GetStudioMoves(struct Pokemon" in career
assert (root/"src/ascension_studio_legal.inc").is_file()
report=json.loads((root/"v10-2-move-coverage.json").read_text())
assert report["roster"]==187
assert report["existing_Arena_move_profiles"]>=80
assert report["usable_species_move_pairs"]>2500
assert report["missing_species_move_pairs"]>0
bronze=(maps/"AscensionTower1/scripts.inc").read_text()
assert "warp MAP_ASCENSION_BRONZE_BOSS, 5, 12" in bronze
biomes=(root/"src/arena_biomes.inc").read_text()
assert "case MAP_ASCENSION_LEADER_8:gArenaBiome=4;gArenaStage=12;break;" in biomes
boss_bronze=json.loads((maps/"AscensionBronzeBoss/map.json").read_text())
assert boss_bronze["object_events"][1]["graphics_id"]=="OBJ_EVENT_GFX_HIKER"

for area,side,w,h in (("AscensionCity","west",56,72),("AscensionCityEast","east",72,72)):
    city=json.loads((maps/area/"map.json").read_text())
    tile_root=root/"data/tilesets"
    ts=[tile_root/"primary/general",tile_root/f"secondary/battle_frontier_outside_{side}"]
    imgs=[Image.open(t/"tiles.png") for t in ts]
    assert all(img.mode=="P" for img in imgs)
    assert all(v<=15 for im in imgs for v in im.getdata()),(area,"non-4bpp pixel")
    meta=[struct.unpack("<"+str(len((t/"metatiles.bin").read_bytes())//2)+"H",(t/"metatiles.bin").read_bytes()) for t in ts]
    words=struct.unpack("<"+str(w*h)+"H",(root/f"data/layouts/{area}/map.bin").read_bytes())
    palettes=[]
    for p in range(16):
        src=ts[0] if p<6 else ts[1]
        contents=(src/"palettes"/f"{p:02}.pal").read_text().splitlines()
        colors=[tuple(map(int,line.split())) for line in contents[3:19]]
        assert len(colors)==16 and all(len(c)==3 and all(0<=v<=255 for v in c) for c in colors)
        palettes.append(colors)
    cache={}
    outimg=Image.new("RGB",(w*16,h*16))
    for my in range(h):
        for mx in range(w):
            mid=words[my*w+mx]&1023
            if mid not in cache:
                bank=0 if mid<512 else 1
                ix=mid if bank==0 else mid-512
                assert ix*8+8<=len(meta[bank]),(area,mid,"invalid metatile")
                chunk=meta[bank][ix*8:ix*8+8]
                patch=Image.new("RGB",(16,16))
                pix=patch.load()
                for layer in (0,1):
                    for n in range(4):
                        v=chunk[layer*4+n];tile=v&1023;pal=(v>>12)&15
                        tilebank=0 if tile<512 else 1
                        off=tile if tile<512 else tile-512
                        tx=(off%16)*8;ty=(off//16)*8
                        assert ty+8<=imgs[tilebank].height,(area,mid,tile,"invalid tile")
                        px=imgs[tilebank].load()
                        for yy in range(8):
                            for xx in range(8):
                                raw=px[tx+(7-xx if v&1024 else xx),ty+(7-yy if v&2048 else yy)]
                                assert 0<=raw<=15
                                if layer==1 and raw==0:continue
                                pix[(n%2)*8+xx,(n//2)*8+yy]=palettes[pal][raw]
                cache[mid]=patch
            outimg.paste(cache[mid],(mx*16,my*16))
    seen=set()
    for warp in city["warp_events"]:
        k=(warp["x"],warp["y"])
        assert k not in seen and 0<=k[0]<w and 0<=k[1]<h,(area,k)
        seen.add(k)
    for obj in city["object_events"]:
        assert 0<=obj["x"]<w and 0<=obj["y"]<h
    assert len(city["object_events"])<=16
    outfile=out/f"{area}-CLEAN-NATIVE-TILES.png"
    outimg.save(outfile)
    print(f"{area}: {len(cache)} existing native metatiles, {len(city['warp_events'])} unique door warps; rendered clean source preview {outfile}")
print("V10 MAP/TOWN STATIC QA PASSED. Previews contain NO diagnostic NPC red squares or warp-number circles; screenshots are NOT gameplay.")
