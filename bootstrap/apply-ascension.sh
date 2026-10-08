#!/usr/bin/env bash
set -euo pipefail
source_root="${1:?Usage: bash bootstrap/apply-ascension.sh SOURCE_ROOT STAGING_ROOT}"
staging="${2:?Usage: bash bootstrap/apply-ascension.sh SOURCE_ROOT STAGING_ROOT}"
mkdir -p "$staging"

# Reconstruct and verify Ascension source changes before touching the GBA engine.
cat bootstrap/overlay.part{1,2,3}.b64 | base64 -d > "$staging/ascension-v6.1-overlay.tar.xz"
printf '%s  %s\n' '585218a612582eab442b99a1d22dd839378649aa5fc6708a59377d617bc39983' "$staging/ascension-v6.1-overlay.tar.xz" | sha256sum -c -
tar -xJf "$staging/ascension-v6.1-overlay.tar.xz" -C "$staging"

cp -a "$staging/include/." "$source_root/include/"
cp -a "$staging/src/." "$source_root/src/"
cp -a "$staging/data/." "$source_root/data/"
# Patch other game files from the verified overlay.
# Clean upstream realtime_arena.c differs from our prior local V4 source:
# apply its modifications separately using a checked transformation.
awk '/^--- a\/src\/realtime_arena.c/{skip=1;next} /^--- a\//{skip=0} !skip' "$staging/changes.patch" > "$staging/other.patch"
(cd "$source_root" && patch --forward -p1 < "$staging/other.patch")
python3 bootstrap/patch-realtime.py "$source_root/src/realtime_arena.c"
# Original Arena release defines this battle script in assembly but omits
# its C extern. Keep the evolution-learning behavior, not a workaround.
grep -q '^BattleScript_ArenaEvolutionLearn::' "$source_root/data/battle_scripts_1.s"
if ! grep -q 'extern const u8 BattleScript_ArenaEvolutionLearn\[\]' "$source_root/src/arena_evolution.inc"; then
  sed -i '1i extern const u8 BattleScript_ArenaEvolutionLearn[];' "$source_root/src/arena_evolution.inc"
fi

# The city layout duplicates the native Battle Frontier tiles: no new low-res art.
mkdir -p "$source_root/data/layouts/AscensionCity"
cp "$source_root/data/layouts/BattleFrontier_OutsideWest/map.bin" "$source_root/data/layouts/AscensionCity/map.bin"
cp "$source_root/data/layouts/BattleFrontier_OutsideWest/border.bin" "$source_root/data/layouts/AscensionCity/border.bin"

python3 bootstrap/repair-dialogue.py "$source_root"
python3 bootstrap/expand-world.py "$source_root"
python3 bootstrap/v8-city-gates.py "$source_root"
python3 bootstrap/v8-guide.py "$source_root"
python3 bootstrap/v8-bronze-teams.py "$source_root"
python3 bootstrap/v8-one-door-lab.py "$source_root"
python3 bootstrap/v8-2-tournament.py "$source_root"
python3 bootstrap/v8-2-city-life.py "$source_root"
python3 bootstrap/v8-2-rematches.py "$source_root"
python3 bootstrap/v9-core.py "$source_root"

echo 'Ascension V6.2 original-engine source and encoded dialogue applied.'
