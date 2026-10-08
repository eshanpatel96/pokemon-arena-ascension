#!/usr/bin/env python3
"""V9 native Emerald exterior facades for the eight-tower world.

Retile only existing town metatiles and use already loaded Emerald palettes:
Phantom amethyst chapel, Verdant green academy, Tidal blue seaside citadel,
Thunder bronze/electric reactor. Bronze, Gale, Inferno, Astral already have
distinct native stone, dome, pyramid and observatory silhouettes.

No new GBA art sheet or renderer. Preserve all native collision, elevations,
door tiles and event positions. Still requires real-world visual QA in Delta.
"""
from pathlib import Path
import json,struct,sys
root=Path(sys.argv[1]);maps=root/'data/maps'
plans=[
 ('AscensionCity','west',56,72,[
   ('Phantom',4,6,18,19,2,6),
   ('Verdant',6,16,33,37,9,8)]),
 ('AscensionCityEast','east',72,72,[
   ('Tidal',40,50,50,55,12,5),
   ('Thunder',35,45,24,29,5,12)])
]
for area,side,width,height,places in plans:
    mapf=maps/area/'map.json'
    events=json.loads(mapf.read_text())
    warps={(x['x'],x['y']) for x in events['warp_events']}
    path=root/f'data/layouts/{area}/map.bin'
    before=path.read_bytes();assert len(before)==width*height*2
    words=list(struct.unpack('<'+str(width*height)+'H',before))
    secondary=root/f'data/tilesets/secondary/battle_frontier_outside_{side}'
    primary=root/'data/tilesets/primary/general'
    primet=(primary/'metatiles.bin').read_bytes()
    primeattrs=(primary/'metatile_attributes.bin').read_bytes()
    secmt=bytearray((secondary/'metatiles.bin').read_bytes())
    secattrs=bytearray((secondary/'metatile_attributes.bin').read_bytes())
    assert len(secmt)%16==0 and len(secattrs)==len(secmt)//8
    used={word&1023 for word in words}
    free=sorted((i for i in range(512,512+len(secmt)//16) if i not in used),reverse=True)
    for title,x0,x1,y0,y1,oldpal,newpal in places:
        transform={}
        changed=0
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if (x,y) in warps:continue
                i=y*width+x;mid=words[i]&1023
                bank=primet if mid<512 else secmt
                offset=mid if mid<512 else mid-512
                tiles=struct.unpack_from('<8H',bank,16*offset)
                if sum(t>>12==oldpal for t in tiles)<2:continue
                if mid not in transform:
                    assert free, f'{area}: no native metatiles for {title}'
                    target=free.pop(0)
                    newtiles=[(t&0xfff)|(newpal<<12) if (t>>12)==oldpal else t for t in tiles]
                    struct.pack_into('<8H',secmt,16*(target-512),*newtiles)
                    attrs=primeattrs if mid<512 else secattrs
                    j=mid if mid<512 else mid-512
                    secattrs[2*(target-512):2*(target-512)+2]=attrs[2*j:2*j+2]
                    transform[mid]=target
                words[i]=(words[i]&~1023)|transform[mid]
                changed+=1
        assert changed>=5,(area,title,changed)
        print(f'{title}: {changed} native building cells re-paletted using {len(transform)} original metatiles')
    assert all(((words[y*width+x]>>10)&3)==((struct.unpack_from('<H',before,2*(y*width+x))[0]>>10)&3) for y in range(height) for x in range(width)),area+' collision mutated'
    for w in events['warp_events']:
        i=w['y']*width+w['x']
        assert words[i]==struct.unpack_from('<H',before,2*i)[0],(area,w)
    assert len(events['object_events'])<=16
    path.write_bytes(struct.pack('<'+str(width*height)+'H',*words))
    (secondary/'metatiles.bin').write_bytes(secmt)
    (secondary/'metatile_attributes.bin').write_bytes(secattrs)
    print(f'{area}: original doors and collision preserved; {len(free)} secondary metatiles free')
print('V9 source exterior pass: four dramatically distinct native tower palette treatments, original other four building silhouettes retained; visuals still need emulator QA.')
