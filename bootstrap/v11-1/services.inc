/* V11.1: native roster preparation, species-legal enemy slots, reversible EVs.
 * Included after existing starter pools and legal move index. No save layout changes.
 */
#include "pokemon_storage_system.h"
#include "task.h"
#include "script.h"
#include "field_screen_effect.h"

static const struct AscensionStudioEntry *V111LegalEntry(u16 species)
{
    u16 i;
    for(i=0;i<ARRAY_COUNT(sAscensionStudioIndex);i++)
        if(sAscensionStudioIndex[i].species==species)return &sAscensionStudioIndex[i];
    return NULL;
}
static bool8 V111LegalMove(const struct AscensionStudioEntry *e,u16 move)
{
    u16 i;
    if(!move)return FALSE;
    for(i=0;i<e->count;i++)if(sAscensionStudioMoveBank[e->start+i]==move)return TRUE;
    return FALSE;
}
static void V111Loadout(struct Pokemon *mon,const u16 *preferred)
{
    u16 species=GetMonData(mon,MON_DATA_SPECIES),chosen[4]={0},i,j,n=0;
    const struct AscensionStudioEntry *e=V111LegalEntry(species);
    if(!e||GetMonData(mon,MON_DATA_IS_EGG))return;
    for(i=0;i<4;i++)
    {
        u16 move=preferred?preferred[i]:GetMonData(mon,MON_DATA_MOVE1+i);
        if(!V111LegalMove(e,move))continue;
        for(j=0;j<n;j++)if(chosen[j]==move)break;
        if(j==n)chosen[n++]=move;
    }
    while(n<4)
    {
        s16 best=-32767;
        u16 pick=MOVE_NONE;
        for(i=0;i<e->count;i++)
        {
            u16 move=sAscensionStudioMoveBank[e->start+i];
            u8 type=gBattleMoves[move].type;
            s16 score=gBattleMoves[move].power;
            for(j=0;j<n;j++)if(chosen[j]==move)break;
            if(j<n)continue;
            if(score>120)score=120;
            if(score)
            {
                if(type==gSpeciesInfo[species].types[0]||type==gSpeciesInfo[species].types[1])score+=35;
                for(j=0;j<n;j++)if(gBattleMoves[chosen[j]].power&&gBattleMoves[chosen[j]].type==type)break;
                if(j==n)score+=25;
            }
            else if(move==MOVE_PROTECT)score=25;
            if(score>best){best=score;pick=move;}
        }
        if(!pick)break;
        chosen[n++]=pick;
    }
    for(i=0;i<4;i++)SetMonMoveSlot(mon,chosen[i],i);
}
static void Ascension_V111LegalizeEnemyParty(void)
{
    u8 i;
    for(i=0;i<PARTY_SIZE;i++)
        if(GetMonData(&gEnemyParty[i],MON_DATA_SPECIES))V111Loadout(&gEnemyParty[i],NULL);
}
static bool8 V111Owned(u16 species)
{
    u16 box,slot;
    for(slot=0;slot<PARTY_SIZE;slot++)
        if(GetMonData(&gPlayerParty[slot],MON_DATA_SPECIES)==species)return TRUE;
    for(box=0;box<TOTAL_BOXES_COUNT;box++)
        for(slot=0;slot<IN_BOX_COUNT;slot++)
            if(GetBoxMonDataAt(box,slot,MON_DATA_SPECIES)==species)return TRUE;
    return FALSE;
}
static bool8 V111StarterStep(void)
{
    struct Pokemon mon;
    u16 index=VarGet(VAR_ASCENSION_STARTER_NEXT_INDEX);
    const struct AscensionStarterSpecies *entry;
    if(FlagGet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED))return TRUE;
    if(index>=ARRAY_COUNT(sAscensionStarterPool))
    {
        FlagSet(FLAG_ASCENSION_STARTER_ROSTER_CLAIMED);
        return TRUE;
    }
    entry=&sAscensionStarterPool[index];
    if(!V111Owned(entry->species))
    {
        CreateMon(&mon,entry->species,60,USE_RANDOM_IVS,FALSE,0,OT_ID_PLAYER_ID,0);
        V111Loadout(&mon,sAscensionStarterMoves[entry->style]);
        if(GiveMonToPlayer(&mon)==MON_CANT_GIVE)
        {
            gSpecialVar_Result=0;
            return TRUE; /* Keep the retry index and unclaimed rights. */
        }
    }
    VarSet(VAR_ASCENSION_STARTER_NEXT_INDEX,index+1);
    return FALSE;
}
static void Task_V111Roster(u8 id)
{
    u8 i;
    for(i=0;i<2;i++)if(V111StarterStep())
    {
        bool8 fromScript=gTasks[id].data[0];
        DestroyTask(id);
        if(fromScript)ScriptContext_Enable();
        else FieldCB_WarpExitFadeFromBlack();
        return;
    }
}
void Ascension_V111StartRosterTask(void)
{
    u8 task;
    gSpecialVar_Result=1;
    LockPlayerFieldControls();
    task=CreateTask(Task_V111Roster,0);
    if(task==NUM_TASKS)FieldCB_WarpExitFadeFromBlack();
}
void Ascension_V111SyncRoster(void)
{
    u8 task;
    gSpecialVar_Result=1;
    task=CreateTask(Task_V111Roster,0);
    if(task<NUM_TASKS)gTasks[task].data[0]=1;
    else {gSpecialVar_Result=0;ScriptContext_Enable();}
}
void Ascension_V111ResetEVs(void)
{
    u8 i,zero=0;
    struct Pokemon *mon;
    gSpecialVar_Result=0;
    if(gSpecialVar_0x8004>=PARTY_SIZE)return;
    mon=&gPlayerParty[gSpecialVar_0x8004];
    if(!GetMonData(mon,MON_DATA_SPECIES)||GetMonData(mon,MON_DATA_IS_EGG))return;
    for(i=0;i<6;i++)SetMonData(mon,MON_DATA_HP_EV+i,&zero);
    CalculateMonStats(mon);
    gSpecialVar_Result=1;
}
