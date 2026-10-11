// Matheus Lynar's playtesting: clear pause navigation and non-blocking EXP.
static const u8 sQualityBag[] = _("BAG");
static const u8 sQualityParty[] = _("POKEMON");
static const u8 sQualityBagHelp[] = _("USE ITEMS FROM YOUR BAG");
static const u8 sQualityPartyHelp[] = _("CHOOSE YOUR NEXT POKEMON");
static const u8 sQualityConfirm[] = _("A: OPEN   B: BACK TO BATTLE");
static const u8 sQualityTabs[] = _("L/R: MOVES  BAG  POKEMON");
static const u8 sQualityExp[] = _(" EXP");
static EWRAM_DATA u32 sFieldExp[PARTY_SIZE]={};
static EWRAM_DATA u8 sFieldLevel[PARTY_SIZE]={};
static EWRAM_DATA u8 sFieldCaughtName[POKEMON_NAME_LENGTH+1]={};
static EWRAM_DATA u8 sFieldCaught=0;
static const u8 sQualityLevelUp[] = _("LEVEL UP! LVL ");
static const u8 sQualityCaughtParty[] = _("CAUGHT / PARTY");
static const u8 sQualityCaughtPC[] = _("CAUGHT / PC");
EWRAM_DATA u32 gArenaQualityTelemetry[4]={}; // queued XP, shown XP, toasts, caught
#define EXP_TAG 0xA7C0
static const struct OamData sExpOam={.shape=SPRITE_SHAPE(64x32),.size=SPRITE_SIZE(64x32),.priority=0};
static void ExpSpriteTick(struct Sprite *sprite)
{
    if(gMain.callback2!=CB2_Overworld || ArePlayerFieldControlsLocked()
        || ScriptContext_IsEnabled() || !sprite->data[0]--)
    {
        u8 side=sprite->data[1];
        DestroySprite(sprite);
        FreeSpriteTilesByTag(EXP_TAG+side);
        if(side==1)FreeSpritePaletteByTag(EXP_TAG);
    }
}
static const struct SpriteTemplate sExpTemplate={.tileTag=EXP_TAG,.paletteTag=EXP_TAG,
    .oam=&sExpOam,.anims=gDummySpriteAnimTable,.images=NULL,
    .affineAnims=gDummySpriteAffineAnimTable,.callback=ExpSpriteTick};
void RealtimeArena_QueueExp(u8 party,u32 amount)
{
    if(party>=PARTY_SIZE || !amount)return;
    sFieldExp[party]+=amount;
    gArenaQualityTelemetry[0]+=amount;
}
void RealtimeArena_QueueLevel(u8 party,u8 level)
{if(party<PARTY_SIZE)sFieldLevel[party]=level;}
static void QueueCaught(struct Pokemon *mon,u8 destination)
{
    GetMonData(mon,MON_DATA_NICKNAME,sFieldCaughtName);
    sFieldCaughtName[POKEMON_NAME_LENGTH]=EOS;
    sFieldCaught=destination==MON_GIVEN_TO_PARTY?1:2;
}
static void ExpPixel(u32 *tiles,u32 x,u32 y,u8 color)
{
    u32 i=(x/64)*256+((y/8)*8+(x%64)/8)*8+y%8;
    u32 shift=(x&7)*4;
    tiles[i]=(tiles[i]&~(15u<<shift))|((u32)color<<shift);
}
static void ExpText(u32 *tiles,u32 x,u32 y,const u8 *text)
{
    while(*text!=EOS && x<122)
    {
        u8 c=*text++;u32 bits=0,row,col;
        if(c>=CHAR_0&&c<=CHAR_9)bits=sHudTinyGlyphs[c-CHAR_0];
        else if(c>=CHAR_A&&c<=CHAR_Z)bits=sHudTinyGlyphs[10+c-CHAR_A];
        else if(c==CHAR_PLUS)bits=0x05D0;
        for(row=0;row<5;row++)for(col=0;col<3;col++)
            if(bits&(1<<(14-row*3-col)))ExpPixel(tiles,x+col,y+row,2);
        x+=4;
    }
}
static void ArenaExpFieldTick(void)
{
    u32 i,x,y;u32 *tiles;u8 text[40],*end,ids[2];
    static const u16 palette[16]={0,RGB(3,7,10),RGB(29,31,29),RGB(8,29,23)};
    struct SpritePalette pal={palette,EXP_TAG};
    if(gPaletteFade.active || ArePlayerFieldControlsLocked() || ScriptContext_IsEnabled()
        || GetSpriteTileStartByTag(EXP_TAG)!=0xFFFF)return;
    for(i=0;i<PARTY_SIZE;i++)if(sFieldExp[i]||sFieldLevel[i])break;
    if(i==PARTY_SIZE && !sFieldCaught)return;
    tiles=AllocZeroed(2048);
    if(!tiles)return;
    for(y=1;y<28;y++)for(x=1;x<127;x++)ExpPixel(tiles,x,y,1);
    for(x=3;x<125;x++)ExpPixel(tiles,x,27,3);
    if(i<PARTY_SIZE)
    {
        GetMonData(&gPlayerParty[i],MON_DATA_NICKNAME,text);text[10]=EOS;
        ExpText(tiles,6,4,text);
        text[0]=CHAR_PLUS;end=ConvertIntToDecimalStringN(text+1,sFieldExp[i],STR_CONV_MODE_LEFT_ALIGN,6);
        StringCopy(end,sQualityExp);ExpText(tiles,6,11,text);
        if(sFieldLevel[i])
        {
            ConvertIntToDecimalStringN(StringCopy(text,sQualityLevelUp),sFieldLevel[i],STR_CONV_MODE_LEFT_ALIGN,3);
            ExpText(tiles,6,19,text);
        }
    }
    else
    {
        ExpText(tiles,6,4,sFieldCaughtName);
        ExpText(tiles,6,13,sFieldCaught==1?sQualityCaughtParty:sQualityCaughtPC);
    }
    if(LoadSpritePalette(&pal)==0xFF){Free(tiles);return;}
    for(x=0;x<2;x++)
    {
        struct SpriteSheet sheet={tiles+x*256,1024,EXP_TAG+x};
        struct SpriteTemplate t=sExpTemplate;t.tileTag+=x;
        if(LoadSpriteSheet(&sheet)==0xFFFF)break;
        ids[x]=CreateSprite(&t,144+x*64,20,0);
        if(ids[x]==MAX_SPRITES){FreeSpriteTilesByTag(EXP_TAG+x);break;}
        gSprites[ids[x]].data[0]=180;gSprites[ids[x]].data[1]=x;
    }
    Free(tiles);
    if(x!=2)
    {
        if(x){DestroySprite(&gSprites[ids[0]]);FreeSpriteTilesByTag(EXP_TAG);}
        FreeSpritePaletteByTag(EXP_TAG);return;
    }
    if(i<PARTY_SIZE)
    {
        if(sFieldLevel[i])PlayFanfare(MUS_LEVEL_UP);
        gArenaQualityTelemetry[1]+=sFieldExp[i];
        sFieldExp[i]=0;sFieldLevel[i]=0;
    }
    else sFieldCaught=0;
    gArenaQualityTelemetry[2]++;
}
