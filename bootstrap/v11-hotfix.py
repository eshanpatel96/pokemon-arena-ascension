#!/usr/bin/env python3
"""V11 native integration corrections; no save format or reward flag changes."""
from pathlib import Path
import sys
r=Path(sys.argv[1])
p=r/'src/overworld.c'
s=p.read_text()
old='            ClearSavedMapView();'
assert s.count(old)==1, 'Expected single V11 saved-view migration call'
s=s.replace(old,'            CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));',1)
p.write_text(s)
print('V11 saved-view migration uses the native CpuFill16 operation without calling a private static function.')

# Native saved-map cache checks must count u16 elements, not bytes. Without
# this correction a cleared view reads into the party and looks nonempty.
p=r/'src/fieldmap.c';s=p.read_text()
old='for (i = 0; i < sizeof(gSaveBlock1Ptr->mapView); i++)'
assert s.count(old)==1
s=s.replace(old,'for (i = 0; i < ARRAY_COUNT(gSaveBlock1Ptr->mapView); i++)',1)
p.write_text(s)

# Rebuild actors/camera through the existing native Continue-warp path when
# a room layout changed. Restoring saved city/old-Gym actor coordinates into
# new geometry is not safe even after clearing the tile cache.
p=r/'src/overworld.c';s=p.read_text()
needle='            CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));\n            LoadObjEventTemplatesFromHeader();'
assert s.count(needle)==1
s=s.replace(needle,needle+'''
            gSaveBlock1Ptr->continueGameWarp = gSaveBlock1Ptr->location;
            gSaveBlock1Ptr->continueGameWarp.warpId = WARP_ID_NONE;
            gSaveBlock1Ptr->continueGameWarp.x = 9;
            gSaveBlock1Ptr->continueGameWarp.y = 18;
            SetContinueGameWarpStatus();''',1)
p.write_text(s)

# BIOS LZ77UnCompVram cannot use distance-1 backreferences. Re-encode the
# approved pixels with minimum distance 2, exactly like native gbagfx's
# default. No pixel or palette redesign, and no added EWRAM scratch buffer.
from collections import defaultdict,deque

def decode_lz(data):
    assert data[0]==16
    size=int.from_bytes(data[1:4],'little');out=bytearray();at=4
    while len(out)<size:
        flags=data[at];at+=1
        for bit in range(8):
            if len(out)>=size:break
            if flags & (128>>bit):
                a,b=data[at:at+2];at+=2
                n=(a>>4)+3;distance=((a&15)<<8)+b+1
                assert 0<distance<=len(out)
                for _ in range(n):
                    if len(out)<size:out.append(out[-distance])
            else:out.append(data[at]);at+=1
    return bytes(out)

def encode_vram(data):
    out=bytearray([16])+len(data).to_bytes(3,'little');pos=0;hist=defaultdict(deque)
    while pos<len(data):
        flag_at=len(out);out.append(0);flags=0
        for bit in range(8):
            if pos>=len(data):break
            q=hist[data[pos:pos+3]]
            while q and pos-q[0]>4096:q.popleft()
            best=0;where=0
            for start in reversed(q):
                if pos-start<2:continue
                n=3
                while n<18 and pos+n<len(data) and data[start+n]==data[pos+n]:n+=1
                if n>best:best=n;where=start
                if best==18:break
            used=1
            if best>=3:
                flags|=128>>bit;d=pos-where-1
                out.extend((((best-3)<<4)|(d>>8),d&255));used=best
            else:out.append(data[pos])
            for k in range(used):hist[data[pos+k:pos+k+3]].append(pos+k)
            pos+=used
        out[flag_at]=flags
    while len(out)%4:out.append(0)
    return bytes(out)

for name in ('tiles.bin.lz','map.bin.lz'):
    p=r/'graphics/title_screen/ascension_v11'/name
    old=p.read_bytes();raw=decode_lz(old);new=encode_vram(raw)
    assert decode_lz(new)==raw
    p.write_bytes(new)
    print(f'VRAM-safe unchanged title {name}: {len(old)} -> {len(new)} bytes')

# Host test runner portability and native-data interpretation, not game code.
p=r.parent/'bootstrap/v11-smoke.c'
if p.exists():
    s=p.read_text()
    if not s.startswith('#define _GNU_SOURCE'):
        s='#define _GNU_SOURCE\n'+s
    s=s.replace('==3 && nsym<90000',"==3 && addr>=0x02000000 && addr<0x0a000000 && type!='a' && type!='A' && nsym<90000")
    s=s.replace('uint32_t sb=rd32(symbol("gSaveBlock1Ptr")),money=rd32(sb+0x490);','uint32_t sb=rd32(symbol("gSaveBlock1Ptr")),money=rd32(sb+0x490)^rd32(rd32(symbol("gSaveBlock2Ptr"))+0xac);')
    s=s.replace('check("encrypted money unchanged after reload",rd32(sb+0x490)==money);','check("decrypted native money unchanged after reload",(rd32(sb+0x490)^rd32(rd32(symbol("gSaveBlock2Ptr"))+0xac))==money);')
    p.write_text(s)
print('V11 native cache bounds, actor-safe Continue migration, VRAM-safe title and host smoke corrections applied.')
