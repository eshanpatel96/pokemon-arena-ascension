#!/usr/bin/env python3
from pathlib import Path
import struct,sys
root=Path(sys.argv[1])
p=root/'.arena-dev/art/forest.bin'
b=p.read_bytes()
if len(b)==2048:
    print('Arena XL tilemap already 32x32')
    raise SystemExit
if len(b)!=30*20*2:
    raise SystemExit(f'unexpected Arena tilemap size: {len(b)}')
src=struct.unpack('<600H',b)
out=[]
for y in range(32):
    for x in range(32):
        out.append(src[(y%20)*30+(x%30)])
p.write_bytes(struct.pack('<1024H',*out))
print('Expanded Arena stage tilemap from 30x20 to repeating 32x32 hardware map')
