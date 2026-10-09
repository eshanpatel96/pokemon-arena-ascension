#!/usr/bin/env python3
"""Run after upstream Arena asset generation. No new RAM or decoding path."""
from pathlib import Path
import re, sys, hashlib, json
r=Path(sys.argv[1]);p=r/'graphics/arena/oswarlin/stages.inc';s=p.read_text()
f=(r/'graphics/arena/oswarlin/flood.8bpp').read_bytes()
rows=re.findall(r'static const u32 sStage(\d+)Tiles\[\]=INCBIN_U32\("([^"]+)"\);',s)
assert len(rows)==17, 'Expected pinned original 17-stage catalog'
proof=[]
for n,path in rows:
 i=int(n);raw=(r/path).read_bytes();offset=i*76800
 assert len(raw)==38400 and f[offset:offset+len(raw)]==raw,('Stage is not byte-identical',i)
 proof.append({'stage':i,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'flood_offset':offset})
s=re.sub(r'static const u32 sStage\d+Tiles\[\]=INCBIN_U32\("[^"]+"\);\n','',s)
s='extern const u32 gArenaStageFlood[];\n'+s
for i in range(17):s=s.replace('sStage'+str(i)+'Tiles','(gArenaStageFlood + '+str(i*19200)+')')
p.write_text(s)
report={'identical_raw_bytes_removed':17*38400,'runtime_change':'Direct ROM pointer aliases only; no decompression or new RAM','stages':proof}
(r/'v11-1-art-dedup-proof.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified byte-identical dry scenery removed:',17*38400,'bytes. Final linked headroom must be measured separately.')
