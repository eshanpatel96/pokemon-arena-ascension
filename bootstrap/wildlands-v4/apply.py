#!/usr/bin/env python3
from pathlib import Path
import json,sys
root=Path(sys.argv[1])

def patch(path,old,new,count=1):
    p=root/path
    s=p.read_text()
    if s.count(old)!=count:
        raise SystemExit(f"{path}: expected {count} anchor(s), got {s.count(old)}: {old[:100]!r}")
    p.write_text(s.replace(old,new,count))

# ---------------------------------------------------------------------------
# 1) Arena XL -> actual first Wildlands BR-scale coordinate space.
# ---------------------------------------------------------------------------
p=root/'include/arena_navigation.h'
s=p.read_text()
s=s.replace('#define ARENA_MAX_X 16352','#define ARENA_MAX_X 4064')
s=s.replace('#define ARENA_MAX_Y 12256','#define ARENA_MAX_Y 3040')
p.write_text(s)

p=root/'src/arena_navigation.c'
s=p.read_text()
old='''const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] =
{
    {8180, 6128, 8205, 6145},
    {8132, 6098, 8153, 6115},
    {8241, 6158, 8262, 6176},
    {8096, 6149, 8114, 6165},
    {8100, 6115, 8117, 6128},
    {8273, 6105, 8285, 6121},
    {8274, 6139, 8290, 6153}
};'''
new='''const struct ArenaRect gArenaObstacles[ARENA_OBSTACLES] =
{
    {2024, 1520, 2049, 1537},
    {1976, 1490, 1997, 1507},
    {2085, 1550, 2106, 1568},
    {1940, 1541, 1958, 1557},
    {1944, 1507, 1961, 1520},
    {2117, 1497, 2129, 1513},
    {2118, 1531, 2134, 1545}
};'''
if old not in s: raise SystemExit('XL obstacle anchor drift')
p.write_text(s.replace(old,new,1))

# ---------------------------------------------------------------------------
# 2) Wildlands title screen: direct Mode-4 bitmap, no Ascension branding.
# ---------------------------------------------------------------------------
p=root/'src/title_screen.c'
s=p.read_text()
old='''static const u32 sAscensionTitleTiles[] = INCBIN_U32("graphics/title_screen/ascension_v11/tiles.bin.lz");
static const u32 sAscensionTitleMap[] = INCBIN_U32("graphics/title_screen/ascension_v11/map.bin.lz");
static const u16 sAscensionTitlePalette[] = INCBIN_U16("graphics/title_screen/ascension_v11/palette.gbapal");'''
new='''static const u8 sWildlandsTitleBitmap[] = INCBIN_U8("graphics/title_screen/wildlands_v4/title.raw");
static const u16 sWildlandsTitlePalette[] = INCBIN_U16("graphics/title_screen/wildlands_v4/title.gbapal");'''
if old not in s: raise SystemExit('title asset anchor drift')
s=s.replace(old,new,1)
old='''    LZ77UnCompVram(sAscensionTitleTiles, (void *)BG_CHAR_ADDR(0));
    LZ77UnCompVram(sAscensionTitleMap, (void *)BG_SCREEN_ADDR(31));
    LoadPalette(sAscensionTitlePalette, 0, sizeof(sAscensionTitlePalette));
    SetGpuReg(REG_OFFSET_BG0CNT, BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(31) | BGCNT_256COLOR | BGCNT_TXT256x256);'''
new='''    DmaCopy16(3, sWildlandsTitleBitmap, (void *)VRAM, 240 * 160);
    LoadPalette(sWildlandsTitlePalette, 0, sizeof(sWildlandsTitlePalette));
    SetGpuReg(REG_OFFSET_BG2PA, 0x100);
    SetGpuReg(REG_OFFSET_BG2PB, 0);
    SetGpuReg(REG_OFFSET_BG2PC, 0);
    SetGpuReg(REG_OFFSET_BG2PD, 0x100);
    SetGpuReg(REG_OFFSET_BG2X_L, 0);
    SetGpuReg(REG_OFFSET_BG2X_H, 0);
    SetGpuReg(REG_OFFSET_BG2Y_L, 0);
    SetGpuReg(REG_OFFSET_BG2Y_H, 0);'''
if old not in s: raise SystemExit('title load anchor drift')
s=s.replace(old,new,1)
old='''    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_0 | DISPCNT_BG0_ON);'''
new='''    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_4 | DISPCNT_BG2_ON);'''
if old not in s: raise SystemExit('title display anchor drift')
s=s.replace(old,new,1)
p.write_text(s)

# ---------------------------------------------------------------------------
# 3) Static in-game Wildlands Field Map terminal screen.
# ---------------------------------------------------------------------------
p=root/'src/field_specials.c'
s=p.read_text()
if '#include "gpu_regs.h"' not in s:
    s=s.replace('#include "graphics.h"\n','#include "graphics.h"\n#include "gpu_regs.h"\n',1)
anchor='#define TAG_ITEM_ICON 5500\n'
insert='''#define TAG_ITEM_ICON 5500

static const u8 sWildlandsWorldMapBitmap[] = INCBIN_U8("graphics/title_screen/wildlands_v4/world_map.raw");
static const u16 sWildlandsWorldMapPalette[] = INCBIN_U16("graphics/title_screen/wildlands_v4/world_map.gbapal");

static void CB2_WildlandsWorldMap(void)
{
    if (JOY_NEW(A_BUTTON | B_BUTTON | START_BUTTON))
    {
        PlaySE(SE_SELECT);
        SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_FORCED_BLANK);
        SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
    }
}

void Wildlands_ShowWorldMap(void)
{
    u16 offset;
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_FORCED_BLANK);
    DmaFill16(3, 0, (void *)VRAM, VRAM_SIZE);
    DmaFill32(3, 0, (void *)OAM, OAM_SIZE);
    DmaFill16(3, 0, (void *)PLTT, PLTT_SIZE);
    for (offset = REG_OFFSET_BG0HOFS; offset <= REG_OFFSET_BG3VOFS; offset += 2)
        SetGpuReg(offset, 0);
    DmaCopy16(3, sWildlandsWorldMapBitmap, (void *)VRAM, 240 * 160);
    LoadPalette(sWildlandsWorldMapPalette, 0, sizeof(sWildlandsWorldMapPalette));
    SetGpuReg(REG_OFFSET_BG2PA, 0x100);
    SetGpuReg(REG_OFFSET_BG2PB, 0);
    SetGpuReg(REG_OFFSET_BG2PC, 0);
    SetGpuReg(REG_OFFSET_BG2PD, 0x100);
    SetGpuReg(REG_OFFSET_BG2X_L, 0);
    SetGpuReg(REG_OFFSET_BG2X_H, 0);
    SetGpuReg(REG_OFFSET_BG2Y_L, 0);
    SetGpuReg(REG_OFFSET_BG2Y_H, 0);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_4 | DISPCNT_BG2_ON);
    SetMainCallback2(CB2_WildlandsWorldMap);
}
'''
if anchor not in s: raise SystemExit('field special anchor drift')
s=s.replace(anchor,insert,1)
p.write_text(s)

p=root/'data/specials.inc'
s=p.read_text()
anchor='''	def_special Ascension_V11EnsureSafeEntry'''
if anchor not in s: raise SystemExit('special table anchor drift')
s=s.replace(anchor,anchor+'\n\tdef_special Wildlands_ShowWorldMap, waitstate=1\n\tdef_special Wildlands_QueuePractice\n\tdef_special Wildlands_BufferStats',1)
p.write_text(s)

# ---------------------------------------------------------------------------
# 4) Lab is now the Wildlands home screen.
# ---------------------------------------------------------------------------
scripts=root/'data/maps/AscensionTeamLab/scripts.inc'
scripts.write_text(r'''AscensionTeamLab_MapScripts::
 .byte 0

AscensionTeamLab_EventScript_Professor::
 lock
 faceplayer
 special Wildlands_BufferStats
 msgbox WildlandsLab_Text_Professor, MSGBOX_DEFAULT
 release
 end

AscensionTeamLab_EventScript_Assistant::
 lock
 faceplayer
 msgbox WildlandsLab_Text_Queue, MSGBOX_YESNO
 goto_if_eq VAR_RESULT, NO, WildlandsLab_EventScript_Done
 special Wildlands_QueuePractice
 goto_if_eq VAR_RESULT, 0, WildlandsLab_EventScript_NeedTwo
 msgbox WildlandsLab_Text_Deploy, MSGBOX_DEFAULT
 release
 end

WildlandsLab_EventScript_NeedTwo::
 msgbox WildlandsLab_Text_NeedTwo, MSGBOX_DEFAULT
WildlandsLab_EventScript_Done::
 release
 end

WildlandsLab_EventScript_Map::
 lock
 msgbox WildlandsLab_Text_Map, MSGBOX_DEFAULT
 special Wildlands_ShowWorldMap
 release
 end

WildlandsLab_EventScript_Rules::
 lock
 msgbox WildlandsLab_Text_Rules, MSGBOX_DEFAULT
 release
 end

WildlandsLab_Text_Professor:
 .string "WILDLANDS RESEARCH LAB\p"
 .string "MATCHES {STR_VAR_1}  WINS {STR_VAR_2}\n"
 .string "ELIMINATIONS {STR_VAR_3}\p"
 .string "Use the PC to form a TWO-POKEMON\n"
 .string "squad, then report to deployment.$"

WildlandsLab_Text_Queue:
 .string "Queue a WILDLANDS practice run?\n"
 .string "The training biome changes each run.$"

WildlandsLab_Text_Deploy:
 .string "Squad confirmed. Deploying...$"

WildlandsLab_Text_NeedTwo:
 .string "A WILDLANDS squad needs exactly\n"
 .string "TWO POKEMON. Use the PC first.$"

WildlandsLab_Text_Map:
 .string "FIELD MAP: five legendary lairs are\n"
 .string "marked from the start. A/B closes.$"

WildlandsLab_Text_Rules:
 .string "TM CASE: Arena-supported TMs are\n"
 .string "reusable. No HMs are required.\p"
 .string "Traversal is a species trait. EV\n"
 .string "grinding is disabled for Wildlands.$"
''')

mp=root/'data/maps/AscensionTeamLab/map.json'
j=json.loads(mp.read_text())
j['name']='WildlandsResearchLab'
j['show_map_name']=False
j['warp_events']=[]
for i,bg in enumerate(j['bg_events']):
    if i in (2,3): bg['script']='WildlandsLab_EventScript_Map'
    elif i in (4,5): bg['script']='WildlandsLab_EventScript_Rules'
    else: bg['script']='EventScript_PC'
mp.write_text(json.dumps(j,indent=2)+'\n')

# ---------------------------------------------------------------------------
# 5) PC party cap = 2 in Wildlands. Native PC icons/summary remain intact.
# ---------------------------------------------------------------------------
p=root/'src/pokemon_storage_system.c'
s=p.read_text()
if '#include "constants/vars.h"' not in s:
    s=s.replace('#include "constants/rgb.h"\n','#include "constants/rgb.h"\n#include "constants/vars.h"\n',1)
s=s.replace('''if (task->tInput == OPTION_WITHDRAW && CountPartyMons() == PARTY_SIZE)''',
'''if (task->tInput == OPTION_WITHDRAW
                && CountPartyMons() >= (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 ? 2 : PARTY_SIZE))''',1)
s=s.replace('''if (CalculatePlayerPartyCount() == PARTY_SIZE)
        {
            PrintMessage(MSG_PARTY_FULL);''',
'''if (CalculatePlayerPartyCount() >= (VarGet(VAR_ASCENSION_CAREER_ACTIVE) == 1 ? 2 : PARTY_SIZE))
        {
            PrintMessage(MSG_PARTY_FULL);''',1)
p.write_text(s)

# Reusable TMs inside Wildlands; HMs are never stocked.
p=root/'src/party_menu.c'
s=p.read_text()
if '#include "constants/vars.h"' not in s:
    s=s.replace('#include "constants/party_menu.h"\n','#include "constants/party_menu.h"\n#include "constants/vars.h"\n',1)
old='''        if (item < ITEM_HM01)
            RemoveBagItem(item, 1);'''
new='''        if (item < ITEM_HM01 && VarGet(VAR_ASCENSION_CAREER_ACTIVE) != 1)
            RemoveBagItem(item, 1);'''
if old not in s: raise SystemExit('TM removal anchor drift')
s=s.replace(old,new,1)
p.write_text(s)

# ---------------------------------------------------------------------------
# 6) Arena runtime: 105 roster, queue, five practice grounds, smaller ordinary
# sprites, boss legends larger, and a highlighted AI partner movement prototype.
# ---------------------------------------------------------------------------
p=root/'src/realtime_arena.c'
s=p.read_text()
s=s.replace('#define ARENA_XL_WORLD_W 16384','#define ARENA_XL_WORLD_W 4096',1)
s=s.replace('#define ARENA_XL_WORLD_H 12288','#define ARENA_XL_WORLD_H 3072',1)

# Do not auto-launch directly after NEW GAME; enter the Lab.
old='''void RealtimeArena_DemoFieldCallback(void)
{
    FieldCB_WarpExitFadeFromBlack();
    sArenaXLAutoLaunch=TRUE;
}'''
new='''void RealtimeArena_DemoFieldCallback(void)
{
    FieldCB_WarpExitFadeFromBlack();
}'''
if old not in s: raise SystemExit('V4 demo callback anchor drift')
s=s.replace(old,new,1)

# Wildlands launch roster and exact two-mon initial squad.
start=s.index('''#if !ARENA_LAB
    static const struct {u16 species;u8 level;} team[] = {''')
end=s.index('''#endif
    if (!sDemoRequested) return FALSE;''',start)
species=[
'VENUSAUR','CHARIZARD','BLASTOISE','BUTTERFREE','BEEDRILL','PIDGEOT','ARBOK','RAICHU','SANDSLASH','NIDOQUEEN','NIDOKING','CLEFABLE','NINETALES','VILEPLUME','VENOMOTH','DUGTRIO','PERSIAN','GOLDUCK','ARCANINE','POLIWRATH','ALAKAZAM','MACHAMP','VICTREEBEL','TENTACRUEL','GOLEM','RAPIDASH','SLOWBRO','DEWGONG','CLOYSTER','GENGAR','KINGLER','EXEGGUTOR','MAROWAK','SEAKING','STARMIE','JYNX','GYARADOS','LAPRAS','FLAREON','ARTICUNO','ZAPDOS','DRAGONITE','RHYDON','ELECTABUZZ',
'CROBAT','BELLOSSOM','AZUMARILL','SCIZOR','SKARMORY','KINGDRA','RAIKOU','ENTEI','SUICUNE',
'SCEPTILE','BLAZIKEN','SWAMPERT','MIGHTYENA','LINOONE','BEAUTIFLY','DUSTOX','LUDICOLO','SHIFTRY','SWELLOW','PELIPPER','GARDEVOIR','BRELOOM','SLAKING','NINJASK','SHEDINJA','EXPLOUD','HARIYAMA','DELCATTY','SABLEYE','AGGRON','MEDICHAM','MANECTRIC','PLUSLE','MINUN','SWALOT','SHARPEDO','WAILORD','CAMERUPT','TORKOAL','FLYGON','CACTURNE','ALTARIA','SOLROCK','WHISCASH','CRAWDAUNT','CLAYDOL','CRADILY','ARMALDO','MILOTIC','KECLEON','BANETTE','ABSOL','GLALIE','WALREIN','SALAMENCE','METAGROSS','REGIROCK','REGICE','REGISTEEL','DUSCLOPS','ROSELIA']
assert len(species)==105 and len(set(species))==105
arr=', '.join('SPECIES_'+x for x in species)
block=f'''#if !ARENA_LAB
    static const u16 sWildlandsRoster[] = {{{arr}}};
    static const struct {{u16 species;u8 level;}} team[] = {{
        {{SPECIES_CHARIZARD,60}}, {{SPECIES_BLASTOISE,60}}
    }};
    static const u16 sDemoMoves[2][MAX_MON_MOVES] =
    {{
        {{MOVE_FLAMETHROWER, MOVE_WING_ATTACK, MOVE_SLASH, MOVE_PROTECT}},
        {{MOVE_WATER_GUN, MOVE_HYDRO_PUMP, MOVE_BITE, MOVE_PROTECT}}
    }};
'''
s=s[:start]+block+s[end:]

s=s.replace('''    SetWarpDestination(MAP_GROUP(MAP_ASCENSION_CITY), MAP_NUM(MAP_ASCENSION_CITY),
                       WARP_ID_NONE, 26, 40);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ASCENSION_CITY);''',
'''    SetWarpDestination(MAP_GROUP(MAP_ASCENSION_TEAM_LAB), MAP_NUM(MAP_ASCENSION_TEAM_LAB),
                       WARP_ID_NONE, 6, 10);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ASCENSION_CITY);''',1)

old='''    // A native NEW GAME preset, never an imported save or a fixture mailbox.
    // RequestDemo already refuses when any existing save is present.
    FlagSet(FLAG_ARENA_PRACTICE);
    gPlayerPartyCount = ARRAY_COUNT(team);
    for (i = 0; i < ARRAY_COUNT(team); i++)
    {
        CreateMon(&gPlayerParty[i], team[i].species, team[i].level,
                  20, TRUE, i * 2, OT_ID_PLAYER_ID, 0);
        for (j = 0; j < MAX_MON_MOVES; j++)
            SetMonMoveSlot(&gPlayerParty[i], sDemoMoves[i][j], j);
    }
    for (i = 0; i < ARRAY_COUNT(box); i++)
        CreateBoxMonAt(0, i, box[i].species, box[i].level,
                       20, TRUE, i * 2, OT_ID_PLAYER_ID, 0);'''
new='''    // Wildlands uses the native PC as the immersive team picker. Two are in
    // the party; every other curated species is waiting in Boxes.
    u32 storageSlot = 0;
    FlagSet(FLAG_ARENA_PRACTICE);
    gPlayerPartyCount = ARRAY_COUNT(team);
    for (i = 0; i < ARRAY_COUNT(team); i++)
    {
        CreateMon(&gPlayerParty[i], team[i].species, team[i].level,
                  20, TRUE, i * 2, OT_ID_PLAYER_ID, 0);
        for (j = 0; j < MAX_MON_MOVES; j++)
            SetMonMoveSlot(&gPlayerParty[i], sDemoMoves[i][j], j);
    }
    for (i = 0; i < ARRAY_COUNT(sWildlandsRoster); i++)
    {
        u16 species=sWildlandsRoster[i];
        if(species==SPECIES_CHARIZARD || species==SPECIES_BLASTOISE) continue;
        CreateBoxMonAt(storageSlot / IN_BOX_COUNT, storageSlot % IN_BOX_COUNT,
                       species, 60, 20, TRUE, storageSlot * 2, OT_ID_PLAYER_ID, 0);
        storageSlot++;
    }
    // Every Arena-supported TM is present exactly once and is reusable.
    // HMs are deliberately absent: traversal belongs to the species.
    for(i=ITEM_TM01;i<ITEM_HM01;i++)
        if(ArenaMoves_Get(ItemIdToBattleMoveId(i))) AddBagItem(i,1);
    AddBagItem(ITEM_POTION,20);
    AddBagItem(ITEM_SUPER_POTION,10);
    AddBagItem(ITEM_X_ATTACK,10);
    AddBagItem(ITEM_X_DEFEND,10);
    AddBagItem(ITEM_X_SPEED,10);'''
if old not in s: raise SystemExit('demo roster body anchor drift')
s=s.replace(old,new,1)

# Stats + lab queue.
anchor='''void RealtimeArena_DemoFieldCallback(void)
{
    FieldCB_WarpExitFadeFromBlack();
}'''
insert=anchor+'''

static EWRAM_DATA u8 sWildlandsPracticeGround = 0;

void Wildlands_QueuePractice(void)
{
    if (CalculatePlayerPartyCount() != 2)
    {
        gSpecialVar_Result = 0;
        return;
    }
    VarSet(VAR_ASCENSION_FLOOR, sWildlandsPracticeGround);
    sWildlandsPracticeGround = (sWildlandsPracticeGround + 1) % 5;
    FlagSet(FLAG_ARENA_PRACTICE);
    sArenaXLAutoLaunch = TRUE;
    gSpecialVar_Result = 1;
}

void Wildlands_BufferStats(void)
{
    ConvertIntToDecimalStringN(gStringVar1, VarGet(VAR_ASCENSION_RANK), STR_CONV_MODE_LEFT_ALIGN, 4);
    ConvertIntToDecimalStringN(gStringVar2, VarGet(VAR_ASCENSION_CHAMPION_WINS), STR_CONV_MODE_LEFT_ALIGN, 4);
    ConvertIntToDecimalStringN(gStringVar3, VarGet(VAR_ASCENSION_MASTERS_BEST), STR_CONV_MODE_LEFT_ALIGN, 4);
}
'''
if s.count(anchor)!=1: raise SystemExit('demo callback insert drift')
s=s.replace(anchor,insert,1)

# Scale hierarchy: ordinary ~90%, selectable legends slightly larger, boss-only
# legends substantially larger in encounter form.
old='''static u16 MonVisualScale(u8 side)
{
    switch (gBattleMons[side].species)
    {
    case SPECIES_EEVEE:
    case SPECIES_PIKACHU:
    case SPECIES_TREECKO:
    case SPECIES_SQUIRTLE:
    case SPECIES_BULBASAUR:
    case SPECIES_POOCHYENA: return 232;
    case SPECIES_DRAGONITE:
    case SPECIES_RAYQUAZA:
    case SPECIES_SNORLAX:
    case SPECIES_BLASTOISE:
    case SPECIES_CHARIZARD: return 244;
    default: return 240;
    }
}'''
new='''static u16 MonVisualScale(u8 side)
{
    switch (gBattleMons[side].species)
    {
    case SPECIES_MEWTWO:
    case SPECIES_LUGIA:
    case SPECIES_HO_OH:
    case SPECIES_KYOGRE:
    case SPECIES_RAYQUAZA: return 304;
    case SPECIES_ARTICUNO:
    case SPECIES_ZAPDOS:
    case SPECIES_RAIKOU:
    case SPECIES_ENTEI:
    case SPECIES_SUICUNE:
    case SPECIES_REGIROCK:
    case SPECIES_REGICE:
    case SPECIES_REGISTEEL: return 248;
    case SPECIES_DRAGONITE:
    case SPECIES_SNORLAX:
    case SPECIES_BLASTOISE:
    case SPECIES_CHARIZARD:
    case SPECIES_SALAMENCE:
    case SPECIES_METAGROSS: return 236;
    default: return 230;
    }
}'''
if old not in s: raise SystemExit('visual scale anchor drift')
s=s.replace(old,new,1)

# Partner movement actor. It intentionally does not deal damage in V4 Alpha:
# this build is for judging follow/guard/regroup behavior before the 4-body
# combat refactor.
anchor='''static u16 MonMassSpeedFactor(u8 side)
{'''
partner=r'''#define WILDLANDS_PARTNER_TAG (MON_TAG + 4)
struct WildlandsPartnerActor
{
    s32 x,y;
    u32 animClock;
    const struct ArenaSpriteSet *art;
    u16 species;
    u8 sprite,shadow,marker,facing,moving,drawnFrame,drawnDirection,active,mode;
};
static EWRAM_DATA struct WildlandsPartnerActor sWildlandsPartner = {};
EWRAM_DATA u32 gWildlandsPartnerTelemetry[8] = {};

static void WildlandsPartner_Init(void)
{
    struct WildlandsPartnerActor *p=&sWildlandsPartner;
    struct SpriteTemplate t=sMonTemplate;
    struct SpriteSheet sheet;
    struct SpritePalette pal;
    struct Sprite *spr;
    memset(p,0,sizeof(*p));
    memset(gWildlandsPartnerTelemetry,0,sizeof(gWildlandsPartnerTelemetry));
    if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)!=1 || gPlayerPartyCount<2)return;
    p->species=GetMonData(&gPlayerParty[1],MON_DATA_SPECIES);
    p->art=ArenaSprites_Get(p->species);
    if(!p->art)return;
    ArenaSprites_Decode(&p->art->animations[ARENA_ANIM_IDLE],FACE_DOWN,0,gDecompressionBuffer);
    sheet.data=gDecompressionBuffer;sheet.size=2048;sheet.tag=WILDLANDS_PARTNER_TAG;
    LoadSpriteSheet(&sheet);
    pal.data=p->art->palette;pal.tag=WILDLANDS_PARTNER_TAG;
    LoadSpritePalette(&pal);
    t.tileTag=WILDLANDS_PARTNER_TAG;t.paletteTag=WILDLANDS_PARTNER_TAG;
    p->x=sArena.bodies[0].x-36*Q;p->y=sArena.bodies[0].y+28*Q;p->facing=FACE_DOWN;
    p->sprite=CreateSprite(&t,p->x/Q,p->y/Q,1);
    p->shadow=CreateSprite(&sShadowTemplate,p->x/Q,p->y/Q+8,9);
    p->marker=CreateSprite(&sShotTemplate,p->x/Q,p->y/Q-27,0);
    spr=&gSprites[p->sprite];
    spr->oam.affineAnimPaused=TRUE;spr->oam.affineAnimBeginning=FALSE;
    SetOamMatrix(spr->oam.matrixNum,256*256/230,0,0,256*256/230);
    gSprites[p->marker].oam.paletteNum=IndexOfSpritePaletteTag(SHOT_TAG);
    p->drawnFrame=p->drawnDirection=255;p->active=TRUE;
    gWildlandsPartnerTelemetry[0]=1;
    gWildlandsPartnerTelemetry[1]=p->species;
}

static void WildlandsPartner_Update(void)
{
    struct WildlandsPartnerActor *p=&sWildlandsPartner;
    struct ArenaBody *lead=&sArena.bodies[0],*enemy=&sArena.bodies[1];
    s32 tx,ty,dx,dy,maxd,step=300;
    static const s8 fx[8]={0,1,1,1,0,-1,-1,-1};
    static const s8 fy[8]={1,1,0,-1,-1,-1,0,1};
    const struct ArenaSpriteAnimation *anim;
    u8 frame;
    struct Sprite *spr;
    if(!p->active)return;

    // Out of pressure: loose formation behind and to the side of the player.
    tx=lead->x-fx[lead->facing]*38*Q-fy[lead->facing]*14*Q;
    ty=lead->y-fy[lead->facing]*38*Q+fx[lead->facing]*14*Q;
    p->mode=0;
    // When an enemy is close, slide into a guard/flank position between the
    // player and threat instead of stacking directly on the lead.
    dx=enemy->x-lead->x;dy=enemy->y-lead->y;
    if(Abs(dx)<150*Q && Abs(dy)<150*Q)
    {
        u8 f=Facing(dx,dy);
        tx=lead->x+fx[f]*34*Q-fy[f]*18*Q;
        ty=lead->y+fy[f]*34*Q+fx[f]*18*Q;
        p->mode=1;
    }

    dx=tx-p->x;dy=ty-p->y;
    maxd=max(Abs(dx),Abs(dy));
    if(maxd>120*Q){step=520;p->mode=2;} // regroup/catch-up
    p->moving=maxd>2*Q;
    if(p->moving)
    {
        s32 mx=dx*step/max(1,maxd),my=dy*step/max(1,maxd);
        s32 nx=Clamp(p->x+mx,ARENA_MIN_X*Q,ARENA_MAX_X*Q);
        s32 ny=Clamp(p->y+my,ARENA_MIN_Y*Q,ARENA_MAX_Y*Q);
        p->facing=Facing(mx,my);
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,nx/Q,p->y/Q,10))p->x=nx;
        if(ArenaNav_LineClear(p->x/Q,p->y/Q,p->x/Q,ny/Q,10))p->y=ny;
    }

    spr=&gSprites[p->sprite];
    spr->x=p->x/Q;spr->y=p->y/Q;
    gSprites[p->shadow].x=spr->x;gSprites[p->shadow].y=p->y/Q+8;
    gSprites[p->marker].x=spr->x;
    gSprites[p->marker].y=p->y/Q-28+((sArena.frame>>3)&1);
    anim=&p->art->animations[p->moving?ARENA_ANIM_WALK:ARENA_ANIM_IDLE];
    frame=ArenaSprites_Frame(anim,p->animClock/Q);
    spr->y += 8-p->art->ground[(p->moving?ARENA_ANIM_WALK:ARENA_ANIM_IDLE)*8+p->facing]*230/256;
    if(frame!=p->drawnFrame || p->facing!=p->drawnDirection)
    {
        ArenaSprites_Decode(anim,p->facing,frame,gDecompressionBuffer);
        ArenaRender_Copy(gDecompressionBuffer,
            (u8*)OBJ_VRAM0+GetSpriteTileStartByTag(WILDLANDS_PARTNER_TAG)*32,2048);
        p->drawnFrame=frame;p->drawnDirection=p->facing;
    }
    if(!sArena.paused)p->animClock+=Q;
    gWildlandsPartnerTelemetry[2]=p->mode;
    gWildlandsPartnerTelemetry[3]=p->x/Q;
    gWildlandsPartnerTelemetry[4]=p->y/Q;
    gWildlandsPartnerTelemetry[5]=maxd/Q;
}

static void WildlandsPartner_Destroy(void)
{
    struct WildlandsPartnerActor *p=&sWildlandsPartner;
    if(!p->active)return;
    FreeOamMatrix(gSprites[p->sprite].oam.matrixNum);
    DestroySprite(&gSprites[p->sprite]);
    DestroySprite(&gSprites[p->shadow]);
    DestroySprite(&gSprites[p->marker]);
    FreeSpriteTilesByTag(WILDLANDS_PARTNER_TAG);
    FreeSpritePaletteByTag(WILDLANDS_PARTNER_TAG);
    p->active=FALSE;
}

static u16 MonMassSpeedFactor(u8 side)
{'''
if s.count(anchor)!=1: raise SystemExit('partner insert anchor drift')
s=s.replace(anchor,partner,1)

# Initialize after two native battlers.
anchor='''    sArena.cueSprite = CreateSprite(&sShotTemplate, 120, 32, 0);'''
if s.count(anchor)!=1: raise SystemExit('partner init anchor drift')
s=s.replace(anchor,'''    WildlandsPartner_Init();
    sArena.cueSprite = CreateSprite(&sShotTemplate, 120, 32, 0);''',1)

# Update as the last frame decode so gDecompressionBuffer remains stable for
# the queued VBlank copy.
anchor='''    MonVisualScaleApply();
    CoverDraw();'''
if s.count(anchor)!=1: raise SystemExit('partner update anchor drift')
s=s.replace(anchor,'''    MonVisualScaleApply();
    WildlandsPartner_Update();
    CoverDraw();''',1)

# Clean up in both faint and menu-exit paths.
s=s.replace('''        gSprites[sArena.aimSprite].invisible=TRUE;
        gSprites[sArena.cueSprite].invisible=TRUE;''',
'''        gSprites[sArena.aimSprite].invisible=TRUE;
        gSprites[sArena.cueSprite].invisible=TRUE;
        WildlandsPartner_Destroy();''',1)
s=s.replace('''    SetVBlankCallback(NULL);
    ArenaFeedback_Destroy();''',
'''    SetVBlankCallback(NULL);
    ArenaFeedback_Destroy();
    WildlandsPartner_Destroy();''',1)

# Simple persistent practice counters on successful enemy KO.
anchor='''    if(fainted)
    {
        sArena.active=FALSE;'''
new='''    if(fainted)
    {
        if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && FlagGet(FLAG_ARENA_PRACTICE)
           && gBattleMons[1].hp==0)
        {
            VarSet(VAR_ASCENSION_RANK,min(9999,VarGet(VAR_ASCENSION_RANK)+1));
            VarSet(VAR_ASCENSION_CHAMPION_WINS,min(9999,VarGet(VAR_ASCENSION_CHAMPION_WINS)+1));
            VarSet(VAR_ASCENSION_MASTERS_BEST,min(9999,VarGet(VAR_ASCENSION_MASTERS_BEST)+1));
        }
        sArena.active=FALSE;'''
if s.count(anchor)!=1: raise SystemExit('stats anchor drift')
s=s.replace(anchor,new,1)

p.write_text(s)

# Five practice-ground looks, corresponding to the five fixed legendary lairs.
p=root/'src/arena_biomes.inc'
s=p.read_text()
anchor='''    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;
    LoadPalette(sStagePalettes[gArenaStage],0,512);'''
new='''    if(VarGet(VAR_ASCENSION_CAREER_ACTIVE)==1 && FlagGet(FLAG_ARENA_PRACTICE))
    {
        static const u8 sWildlandsGrounds[5]={13,10,14,15,16};
        gArenaStage=sWildlandsGrounds[VarGet(VAR_ASCENSION_FLOOR)%5];
        gArenaBiome=(gArenaStage==15)?1:(gArenaStage==16?2:4);
    }
    if(gArenaStage>=8&&gArenaStage<16)gArenaBiome=4;
    LoadPalette(sStagePalettes[gArenaStage],0,512);'''
if s.count(anchor)!=1: raise SystemExit('biome override anchor drift')
p.write_text(s.replace(anchor,new,1))

print('Applied Wildlands V4 Alpha: title/lab/map/105 roster/PC cap/TMs/partner/grounds')
