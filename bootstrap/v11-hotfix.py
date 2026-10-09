#!/usr/bin/env python3
"""V11 native integration corrections; no save format or reward flag changes."""
from pathlib import Path
import sys
r = Path(sys.argv[1])
p = r / 'src/overworld.c'
s = p.read_text()
old = '            ClearSavedMapView();'
assert s.count(old) == 1, 'Expected single V11 saved-view migration call'
s = s.replace(old, '            CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));', 1)
p.write_text(s)
print('V11 saved-view migration uses the native CpuFill16 operation without calling a private static function.')
