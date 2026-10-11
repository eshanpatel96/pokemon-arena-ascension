#include "global.h"
#include "title_screen.h"
#include "main.h"
#include "main_menu.h"
#include "palette.h"
#include "gpu_regs.h"
#include "sprite.h"
#include "task.h"
#include "scanline_effect.h"
#include "decompress.h"
#include "sound.h"
#include "m4a.h"
#include "clear_save_data_menu.h"
#include "reset_rtc_screen.h"
#include "event_data.h"
#include "berry_fix_program.h"
#include "constants/songs.h"
#include "constants/rgb.h"
static const u8 sWildlandsTitleBitmap[] = INCBIN_U8("graphics/title_screen/wildlands_v4/title.raw");
static const u16 sWildlandsTitlePalette[] = INCBIN_U16("graphics/title_screen/wildlands_v4/title.gbapal");
const u16 gTitleScreenAlphaBlend[64] =
{
    BLDALPHA_BLEND(16, 0),
    BLDALPHA_BLEND(16, 1),
    BLDALPHA_BLEND(16, 2),
    BLDALPHA_BLEND(16, 3),
    BLDALPHA_BLEND(16, 4),
    BLDALPHA_BLEND(16, 5),
    BLDALPHA_BLEND(16, 6),
    BLDALPHA_BLEND(16, 7),
    BLDALPHA_BLEND(16, 8),
    BLDALPHA_BLEND(16, 9),
    BLDALPHA_BLEND(16, 10),
    BLDALPHA_BLEND(16, 11),
    BLDALPHA_BLEND(16, 12),
    BLDALPHA_BLEND(16, 13),
    BLDALPHA_BLEND(16, 14),
    BLDALPHA_BLEND(16, 15),
    BLDALPHA_BLEND(15, 16),
    BLDALPHA_BLEND(14, 16),
    BLDALPHA_BLEND(13, 16),
    BLDALPHA_BLEND(12, 16),
    BLDALPHA_BLEND(11, 16),
    BLDALPHA_BLEND(10, 16),
    BLDALPHA_BLEND(9, 16),
    BLDALPHA_BLEND(8, 16),
    BLDALPHA_BLEND(7, 16),
    BLDALPHA_BLEND(6, 16),
    BLDALPHA_BLEND(5, 16),
    BLDALPHA_BLEND(4, 16),
    BLDALPHA_BLEND(3, 16),
    BLDALPHA_BLEND(2, 16),
    BLDALPHA_BLEND(1, 16),
    BLDALPHA_BLEND(0, 16),
    [32 ... 63] = BLDALPHA_BLEND(0, 16)
};


static void VBlank_AscensionTitle(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}
static void Main_AscensionTitle(void)
{
    RunTasks();
    UpdatePaletteFade();
}
static void Task_AscensionTitle(u8 taskId)
{
    if (gPaletteFade.active) return;
    if (gTasks[taskId].data[0])
    {
        u8 action = gTasks[taskId].data[0];
        DestroyTask(taskId);
        SetVBlankCallback(NULL);
        if (action == 2) SetMainCallback2(CB2_InitClearSaveDataScreen);
        else if (action == 3) SetMainCallback2(CB2_InitResetRtcScreen);
        else if (action == 4) SetMainCallback2(CB2_InitBerryFixProgram);
        else SetMainCallback2(CB2_InitMainMenu);
        return;
    }
    if ((JOY_HELD(B_BUTTON | SELECT_BUTTON | DPAD_UP)) == (B_BUTTON | SELECT_BUTTON | DPAD_UP))
        gTasks[taskId].data[0] = 2;
    else if ((JOY_HELD(B_BUTTON | SELECT_BUTTON | DPAD_LEFT)) == (B_BUTTON | SELECT_BUTTON | DPAD_LEFT) && CanResetRTC())
        gTasks[taskId].data[0] = 3;
    else if ((JOY_HELD(B_BUTTON | SELECT_BUTTON)) == (B_BUTTON | SELECT_BUTTON))
        gTasks[taskId].data[0] = 4;
    else if (JOY_NEW(A_BUTTON | START_BUTTON))
        gTasks[taskId].data[0] = 1;
    if (gTasks[taskId].data[0])
    {
        FadeOutBGM(4);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
    }
}
void CB2_InitTitleScreen(void)
{
    u16 offset;
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_FORCED_BLANK);
    ScanlineEffect_Stop();
    ResetTasks();
    ResetSpriteData();
    FreeAllSpritePalettes();
    ResetPaletteFade();
    DmaFill16(3, 0, (void *)VRAM, VRAM_SIZE);
    DmaFill32(3, 0, (void *)OAM, OAM_SIZE);
    DmaFill16(3, 0, (void *)PLTT, PLTT_SIZE);
    for (offset = REG_OFFSET_BG0HOFS; offset <= REG_OFFSET_BG3VOFS; offset += 2)
        SetGpuReg(offset, 0);
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    SetGpuReg(REG_OFFSET_MOSAIC, 0);
    SetGpuReg(REG_OFFSET_WIN0H, 0);
    SetGpuReg(REG_OFFSET_WIN0V, 0);
    SetGpuReg(REG_OFFSET_WIN1H, 0);
    SetGpuReg(REG_OFFSET_WIN1V, 0);
    SetGpuReg(REG_OFFSET_WININ, 0);
    SetGpuReg(REG_OFFSET_WINOUT, 0);
    DmaCopy16(3, sWildlandsTitleBitmap, (void *)VRAM, 240 * 160);
    LoadPalette(sWildlandsTitlePalette, 0, sizeof(sWildlandsTitlePalette));
    SetGpuReg(REG_OFFSET_BG2PA, 0x100);
    SetGpuReg(REG_OFFSET_BG2PB, 0);
    SetGpuReg(REG_OFFSET_BG2PC, 0);
    SetGpuReg(REG_OFFSET_BG2PD, 0x100);
    SetGpuReg(REG_OFFSET_BG2X_L, 0);
    SetGpuReg(REG_OFFSET_BG2X_H, 0);
    SetGpuReg(REG_OFFSET_BG2Y_L, 0);
    SetGpuReg(REG_OFFSET_BG2Y_H, 0);
    BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
    CreateTask(Task_AscensionTitle, 0);
    BuildOamBuffer();
    EnableInterrupts(INTR_FLAG_VBLANK);
    SetVBlankCallback(VBlank_AscensionTitle);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_4 | DISPCNT_BG2_ON);
    m4aSongNumStart(MUS_TITLE);
    SetMainCallback2(Main_AscensionTitle);
}
