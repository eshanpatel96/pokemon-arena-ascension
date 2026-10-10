# Arena XL Stress Prototype

Goal: prove how large the native realtime Arena can become while keeping the exact Arena player controller, dodge, move timing, animation and hitboxes.

## Phase 1 target

World size: 4096 x 3072 pixels.

That is about:
- 17 GBA screens wide
- 19 GBA screens tall
- ~329 screen-sized viewports of space

This is intentionally much larger than the current 216 x 111 playable arena.

## Architecture

- Keep native ArenaBody Q8 positions and TickPlayer/Move/Dash code.
- Add world camera coordinates.
- Convert sprite presentation from screen coordinates to world coordinates plus camera offset.
- Scroll BG1 with the camera.
- Repeat the current stage tilemap for the first stress test. Unique Emerald terrain comes after camera/physics acceptance.
- Move the seven original destructible props near world center so obstacle navigation remains exercised.
- Keep combat, AI, projectiles and hit resolution in world coordinates.
- Disable storm/flood assumptions during the first XL stress test because the original water-height asset is only 240 x 160.

## Scale ceiling

The existing ArenaBody uses s32 Q8 coordinates, so body position itself is not the limiting factor. The current navigation API uses signed 16-bit pixel coordinates and some 32-bit segment math. A single unchunked Arena can reasonably be stress-tested into the several-thousand-pixel range.

First gates:
1. 4096 x 3072
2. 8192 x 6144 if Phase 1 is stable

For the final Wildlands map, chunk-local collision/navigation removes even that practical single-coordinate-space ceiling. Only nearby chunks need full Arena simulation.

## Acceptance

- Movement feel must be byte-for-byte the existing Arena TickPlayer/Move/Dash path.
- Camera follows without jitter.
- Player can cross at least 1000 world pixels in one direction.
- AI still approaches/attacks.
- Projectiles and hitboxes remain aligned while camera is displaced.
- Obstacles still block movement and can be destroyed.
- No missed-frame regression versus the normal Arena beyond a small tolerance.
- Delta-compatible 32 MB ROM.
