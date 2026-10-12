#define WL_BIOME_COUNT 1
extern const struct Tileset gTileset_General;
extern const struct Tileset gTileset_Fortree;
static const struct Tileset *const sWlOutdoorPairs[1][2] = {{&gTileset_General,&gTileset_Fortree}};
#define WL_BIOME_BLOCK 8
#define WL_BIOME_GW 5
#define WL_BIOME_GH 6
static const u8 sWlBiomeBlocks[WL_BIOME_GW * WL_BIOME_GH] = {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1};
static const u8 sWlBiomeCells[] = INCBIN_U8("data/wildlands_world/biome.bin");
#define WL_BIOME_START 0
#define WL_LANDMARK_COUNT 1
static const s16 sWlLandmarks[1][2] = {{2248,1880}};
