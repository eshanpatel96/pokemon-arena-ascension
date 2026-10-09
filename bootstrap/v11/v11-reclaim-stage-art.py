#!/usr/bin/env python3
"""After original arena art packing, alias identical dry scenery already in flood.
No decompression, new RAM, physics change, or loss of pixel data. Fail closed.
"""
from pathlib import Path
import re,sys,hashlib,json
r=Path(sys.argv[1]);p=r/'graphics/arena/oswarlin/stages.inc';s=p.read_text();f=(r/'graphics/arena/oswarlin/flood.8bpp').read_bytes()
rows=re.findall(r'static const u32 sStage(\d+)Tiles\[\]=INCBIN_U32\("([^\"]+)"\);',s)
assert len(rows)==17,('expected original stage catalog',len(rows))
proof=[]
for sn,path in rows:
 i=int(sn);raw=(r/path).read_bytes();off=i*76800
 assert len(raw)==38400 and f[off:off+38400]==raw,('dry art mismatch',i)
 proof.append(dict(stage=i,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),flood_offset=off))
s=re.sub(r'static const u32 sStage\d+Tiles\[\]=INCBIN_U32\("[^\"]+"\);\n','',s)
s='extern const u32 gArenaStageFlood[];\n'+s
for i in range(17):s=s.replace(f'sStage{i}Tiles',f'(gArenaStageFlood + {i*19200})')
p.write_text(s)
(r/'v11-art-dedup-proof.json').write_text(json.dumps({'identical_raw_bytes_no_longer_duplicated':17*38400,'stages':proof,'runtime_changes':'none; direct ROM pointer aliases only'},indent=2))
print('V11 byte-identical scenery deduplication:',17*38400,'ROM bytes removed; no EWRAM or IWRAM allocation.')
