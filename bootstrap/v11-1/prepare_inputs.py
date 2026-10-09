#!/usr/bin/env python3
"""Recover exact baseline build inputs; never synthesize missing native payloads."""
from pathlib import Path
import hashlib,json,sys
r=Path(sys.argv[1]);rom=Path(sys.argv[2]).read_bytes()
assert hashlib.sha256(rom).hexdigest()=='93e6a36e7f3b85dc6c6328b4f479bb264ef9ecfbb8ab08b053ca786531a36770'
# Symbol bounds from that exact baseline ELF. These are embedded native programs,
# not the main ROM, inadvertently excluded by the old source archive's *.gba rule.
rows=[('mb_berry_fix',0xaa954c,0xaad140,'f3d87e14688faf0190b33e071607887c7783462b45f92f1cb7135eec56260740'),('mb_ereader',0xaa646c,0xaa954c,'e50d06841b3485282bf772f1cfe2988da2bb476eb26ff5337b467af8a60bdf07'),('mb_colosseum',0xaad140,0xad5140,'d133d340ce7507932bcb3a83f9ee1dd9905072763d493b66db20e1bde4304572')]
proof=[]
for name,start,end,digest in rows:
 b=rom[start:end];assert hashlib.sha256(b).hexdigest()==digest
 p=r/'data'/(name+'.gba')
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
 proof.append({'file':str(p.relative_to(r)),'bytes':len(b),'sha256':digest})
p=r/'data/maps/AscensionTeamLab/scripts.inc';s=p.read_text()
a=' checkflag FLAG_ASCENSION_STARTER_ROSTER_CLAIMED\n goto_if_set AscensionV111_RosterReady'
b=' goto_if_set FLAG_ASCENSION_STARTER_ROSTER_CLAIMED, AscensionV111_RosterReady'
assert s.count(a)==1 or s.count(b)==1
p.write_text(s.replace(a,b,1))
(r/'v11-1-preserved-build-inputs.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Verified and restored three byte-identical embedded native programs; native flag macro corrected.')
