#include "global.h"
#include "title_screen.h"
#include "main.h"
#include "main_menu.h"
#include "intro.h"
#include "sprite.h"
#include "task.h"
#include "palette.h"
#include "gpu_regs.h"
#include "scanline_effect.h"
#include "decompress.h"
#include "sound.h"
#include "m4a.h"
#include "clear_save_data_menu.h"
#include "reset_rtc_screen.h"
#include "event_data.h"
#include "constants/rgb.h"
#include "constants/songs.h"

// Preserve the native intro's external blend table; no second game renderer.
const u16 gTitleScreenAlphaBlend[64] = {
 0x0010,0x0110,0x0210,0x0310,0x0410,0x0510,0x0610,0x0710,
 0x0810,0x0910,0x0A10,0x0B10,0x0C10,0x0D10,0x0E10,0x0F10,
 0x100F,0x100E,0x100D,0x100C,0x100B,0x100A,0x1009,0x1008,
 0x1007,0x1006,0x1005,0x1004,0x1003,0x1002,0x1001,0x1000,
 0x1000,0x1001,0x1002,0x1003,0x1004,0x1005,0x1006,0x1007,
 0x1008,0x1009,0x100A,0x100B,0x100C,0x100D,0x100E,0x100F,
 0x0F10,0x0E10,0x0D10,0x0C10,0x0B10,0x0A10,0x0910,0x0810,
 0x0710,0x0610,0x0510,0x0410,0x0310,0x0210,0x0110,0x0010
};
static const u32 sV11Tiles[] = INCBIN_U32("graphics/ascension_v11/title.tiles.lz");
static const u32 sV11Map[] = INCBIN_U32("graphics/ascension_v11/title.map.lz");
static const u16 sV11Palette[] = INCBIN_U16("graphics/ascension_v11/title.gbapal");
static void VBlankTitle(void) { LoadOam(); ProcessSpriteCopyRequests(); TransferPlttBuffer(); }
static void GoToMenu(void)
{
    if (!UpdatePaletteFade()) SetMainCallback2(CB2_InitMainMenu);
}
static void RunTitle(void)
{
    if (UpdatePaletteFade()) return;
    if (JOY_NEW(A_BUTTON | START_BUTTON))
    {
        FadeOutBGM(4);
        BeginNormalPaletteFade(PALETTES_ALL,0,0,16,RGB_BLACK);
        SetMainCallback2(GoToMenu);
    }
    else if (JOY_HELD(B_BUTTON | SELECT_BUTTON | DPAD_UP) == (B_BUTTON | SELECT_BUTTON | DPAD_UP))
        SetMainCallback2(CB2_InitClearSaveDataScreen);
    else if (JOY_HELD(B_BUTTON | SELECT_BUTTON | DPAD_LEFT) == (B_BUTTON | SELECT_BUTTON | DPAD_LEFT) && CanResetRTC())
        SetMainCallback2(CB2_InitResetRtcScreen);
}
void CB2_InitTitleScreen(void)
{
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT,0);
    SetGpuReg(REG_OFFSET_BLDCNT,0);
    SetGpuReg(REG_OFFSET_BLDALPHA,0);
    SetGpuReg(REG_OFFSET_BLDY,0);
    DmaFill16(3,0,(void *)VRAM,VRAM_SIZE);
    DmaFill32(3,0,(void *)OAM,OAM_SIZE);
    ResetPaletteFade(); ResetTasks(); ResetSpriteData(); FreeAllSpritePalettes();
    ScanlineEffect_Stop();
    LZ77UnCompVram(sV11Tiles,(void *)BG_CHAR_ADDR(0));
    LZ77UnCompVram(sV11Map,(void *)BG_SCREEN_ADDR(31));
    LoadPalette(sV11Palette,0,512);
    SetGpuReg(REG_OFFSET_BG0HOFS,0);SetGpuReg(REG_OFFSET_BG0VOFS,0);
    SetGpuReg(REG_OFFSET_BG0CNT,BGCNT_CHARBASE(0)|BGCNT_SCREENBASE(31)|BGCNT_256COLOR|BGCNT_TXT256x256);
    SetGpuReg(REG_OFFSET_WIN0H,0);SetGpuReg(REG_OFFSET_WIN0V,0);
    SetGpuReg(REG_OFFSET_WIN1H,0);SetGpuReg(REG_OFFSET_WIN1V,0);
    BeginNormalPaletteFade(PALETTES_ALL,0,16,0,RGB_BLACK);
    SetVBlankCallback(VBlankTitle);
    EnableInterrupts(INTR_FLAG_VBLANK);
    SetGpuReg(REG_OFFSET_DISPCNT,DISPCNT_MODE_0|DISPCNT_BG0_ON);
    PlayBGM(MUS_TITLE);
    SetMainCallback2(RunTitle);
}
