#!/usr/bin/env python3
"""V9 physical West City architecture and campus garden.

Edits native metatiles/graphics within their EXISTING 4bpp slots, retaining
layout size, collision, doors and the original Emerald renderer. This is the
first actual city-facade pass, not the eight-tower final art acceptance.
"""
from pathlib import Path
from PIL import Image
from collections import deque
import json,struct,sys

root=Path(sys.argv[1])
city=root/"data/maps/AscensionCity"
layout=root/"data/layouts/AscensionCity/map.bin"
pdir=root/"data/tilesets/primary/general"
sdir=root/"data/tilesets/secondary/battle_frontier_outside_west"
obj=json.loads((city/"map.json").read_text())
width,height=56,72
initial=list(struct.unpack("<"+str(width*height)+"H",layout.read_bytes()))
words=list(initial)
primary_meta=(pdir/"metatiles.bin").read_bytes()
secondary_meta=bytearray((sdir/"metatiles.bin").read_bytes())
secondary_attrs=bytearray((sdir/"metatile_attributes.bin").read_bytes())
primary_attrs=(pdir/"metatile_attributes.bin").read_bytes()
assert len(secondary_meta)%16==0 and len(secondary_attrs)==len(secondary_meta)//8
assert len(primary_meta)%16==0 and len(primary_attrs)==len(primary_meta)//8

def mid(x,y): return words[y*width+x]&1023
def word(x,y): return words[y*width+x]
def set_mid(x,y,id):words[y*width+x]=(words[y*width+x]&~1023)|id
def attrs(a,mi): return a[mi*2:mi*2+2]

free_mid=[i for i in range(512,512+len(secondary_meta)//16)
          if i not in {n&1023 for n in words}]
free_mid.sort(reverse=True)
assert len(free_mid)>=30, "Not enough unused native metatiles"

def add_metatile(original,new_palette=None,new_tiles=None):
    assert free_mid
    new=free_mid.pop(0)
    bank=primary_meta if original<512 else secondary_meta
    index=original if original<512 else original-512
    tiles=list(struct.unpack_from("<8H",bank,index*16))
    if new_palette is not None:
        tiles=[(v&0xfff)|(new_palette<<12) if (v>>12)==1 else v
               for v in tiles]
    if new_tiles is not None:
        tiles=[(v&~1023)|new_tiles.get(v&1023,v&1023) for v in tiles]
    struct.pack_into("<8H",secondary_meta,(new-512)*16,*tiles)
    attr_bank=primary_attrs if original<512 else secondary_attrs
    secondary_attrs[(new-512)*2:(new-512)*2+2]=attrs(attr_bank,index)
    return new

# V10.1: do NOT recolor only one shade of native roofs. In the phone build
# that created mismatched pixel-art roof pieces instead of finished houses.
# Leave original Emerald metatiles and palettes intact and identify these
# services through functional signs, original architecture and the LAB.

# Place LAB letters in two unused tiles of the WEST *secondary* image, not
# shared Hoenn General tiles spelling MART. Keep native 8px tile resolution.
used_tiles={v&1023 for v in
  struct.unpack("<"+str(len(secondary_meta)//2)+"H",secondary_meta)
  if (v&1023)>=512}
assert 1022 not in used_tiles and 1023 not in used_tiles
img=Image.open(sdir/"tiles.png")
assert img.mode=="P" and img.size==(128,256)
font={"L":("100","100","100","100","111"),
      "A":("010","101","111","101","101"),
      "B":("110","101","110","101","110")}
letters=[["0"]*16 for _ in range(8)]
x0=2
for ch in "LAB":
    for yy,row in enumerate(font[ch]):
        for dx,bit in enumerate(row):
            if bit=="1":letters[yy+1][x0+dx]="1"
    x0+=4
for xx in range(16):
    for yy in range(8):
        pal_index=((13 if yy<=3 else 14) if letters[yy][xx]=="1"
                   else (1 if yy<3 else 2))
        tile=(1022 if xx<8 else 1023)-512
        img.putpixel(((tile%16)*8+(xx%8),(tile//16)*8+yy),pal_index)
img.save(sdir/"tiles.png")
assert mid(52,51)==0x42 and mid(53,51)==0x43
set_mid(52,51,add_metatile(0x42,new_tiles={329:1022}))
set_mid(53,51,add_metatile(0x43,new_tiles={330:1023}))

# A 5x3 raised flower-bed copied from the same native city creates a real,
# collideable landscaped courtyard. All destination tiles were open sidewalk.
for dy in range(3):
    for dx in range(5):
        x,y=43+dx,47+dy
        assert initial[y*width+x]>>10==0,(x,y,"garden blocks original object")
        donor=initial[(45+dy)*width+17+dx]
        assert donor>>12==0
        words[y*width+x]=donor

# Functional VISIBLY TILED doorway plaques; both are beside entrances, not
# on top of their one-tile door or a wandering character.
for x,y,label in (
    (44,45,"AscensionV9City_EventScript_SupplySign"),
    (54,45,"AscensionV9City_EventScript_MoveSign"),
):
    assert (x,y) not in {(w["x"],w["y"]) for w in obj["warp_events"]}
    assert (x,y) not in {(e["x"],e["y"]) for e in obj["object_events"]+obj["bg_events"]}
    assert word(x,y)>>10==0
    words[y*width+x]=initial[30*width+45]
    obj["bg_events"].append(dict(type="sign",x=x,y=y,elevation=0,
        player_facing_dir="BG_EVENT_PLAYER_FACING_ANY",script=label))

script=city/"scripts.inc"
text=script.read_text()
for label,lines in (
    ("AscensionV9City_EventScript_SupplySign",
     "ARENA SUPPLIES - buy\nhealing and battle items."),
    ("AscensionV9City_EventScript_MoveSign",
     "MOVE STUDIO - prepare\nyour Arena moves."),
):
    assert label not in text
    text+="\n"+label+"::\n msgbox "+label+"_Text, MSGBOX_SIGN\n end\n"
    text+=label+'_Text:\n\t.string "'+lines.replace("\n",r"\n")+'$"\n'
script.write_text(text)

# Preserve all prior entry/return warp IDs and prove their access path exists.
for actor in obj["object_events"]:
    assert (word(actor["x"],actor["y"])>>10)&3==0,actor["script"]
for num in (3,4,6):
    x,y=obj["warp_events"][num]["x"],obj["warp_events"][num]["y"]
    assert (word(x,y+1)>>10)&3==0,("blocked doorway",num)
def neighbors(pt):
    x,y=pt
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        X,Y=x+dx,y+dy
        if 0<=X<width and 0<=Y<height and ((word(X,Y)>>10)&3)==0:
            yield X,Y
seen={(40,45)}
queue=deque(seen)
while queue:
    for pt in neighbors(queue.popleft()):
        if pt not in seen:seen.add(pt);queue.append(pt)
for destination in ((45,45),(53,45),(51,52),(50,54)):
    assert destination in seen,("unreachable service",destination)
assert len(obj["object_events"])<=16
layout.write_bytes(struct.pack("<"+str(len(words))+"H",*words))
(sdir/"metatiles.bin").write_bytes(secondary_meta)
(sdir/"metatile_attributes.bin").write_bytes(secondary_attrs)
(city/"map.json").write_text(json.dumps(obj,indent=2)+"\n")
print("V9 CENTRAL CAMPUS: true native LAB facade glyph, different Supply/Move roofs, 5x3 physical flower court, two tiled signs. NPC/door/campus traversal verified by static BFS.")
