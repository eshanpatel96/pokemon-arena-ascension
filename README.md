# Pokémon Arena: Ascension

A fan-made GBA development project that **extends Emerald Arena's original real-time combat**, rather than replacing it with a new minigame.

## Design commitments
- Native Emerald overworld and authentic Emerald Arena Pokémon graphics, animations, and battle environments.
- Onboarding/tutorial → Ascension City → eight battle towers → Champion Summit.
- Team management, arena-only switching, progression/saves, and eventually Mega Evolution.
- No experimental replacement combat renderer or injected arcade title screen.

## Source and build status
- This private repository is a **development/bootstrap workspace**.
- The current Actions bootstrap builds **upstream Emerald Arena baseline**, not yet the Ascension V6.1 city/tower modifications.
- The complete Ascension V6.1 modified source currently exists in the locally delivered `Pokemon-Arena-Ascension-V6.1-Tutorial-City-Source.zip`; its changes are not yet committed here.
- Do not call a ROM Delta-ready until a full GBA compilation succeeds and the game is tested in mGBA/Delta.
- Do **not** commit original Pokémon Emerald ROM files, save data, or generated ROMs.

## Upstream
- Pokémon Emerald decompilation: https://github.com/pret/pokeemerald
- Emerald Arena real-time engine: https://github.com/GBurgardt/pokemon-emerald-arena

## CI approach
The [bootstrap workflow](.github/workflows/engine-bootstrap.yml) checks out pinned Emerald source, applies the public Arena engine overlay, installs development tools, and attempts to compile the **original Arena baseline**. Its purpose is to get a functioning CI toolchain before integrating the Ascension V6.1 source changes.

This is a noncommercial fan project. Pokémon and related characters are owned by their respective rights holders.
