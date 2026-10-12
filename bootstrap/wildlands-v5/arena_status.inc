// WildLands Beta V6.2: short real-time status effects in the world, for all
// four battlers (leads and partners).
//   PAR 3s full stun          FRZ 5s stun, a Fire hit thaws
//   SLP 4s stun, a hit wakes  PSN 30s, 1/20 max HP every 5s
//   TOX 60s, 1/16 every 5s    BRN 40s, 1/16 every 5s (+ native attack drop)
// Poison and burn block rest regen. One status at a time, 5s immunity after
// it ends, legendaries suffer half durations. Supplies cure everything.
// The native Gen III residual clock (TickBurn) is off in the world.
struct WlStatus { u16 timer, tick, lastHp, immune; u8 code, pad; };
static EWRAM_DATA struct WlStatus sWlStatus[4] = {0};
// TEST HOOK ONLY: 1..5 inflicts PAR/SLP/BRN/PSN/FRZ on the player lead once, 6 clears.
EWRAM_DATA u8 gWildlandsStatusTest = 0;
EWRAM_DATA u8 gWildlandsStatusNow = 0;   // player lead's status code (diagnostic)

static u8 WlStatusCode(u32 s)
{
    return (s & STATUS1_PARALYSIS) ? 1 : (s & STATUS1_SLEEP) ? 2 : (s & STATUS1_BURN) ? 3
         : (s & STATUS1_PSN_ANY) ? 4 : (s & STATUS1_FREEZE) ? 5 : 0;
}

// Seconds left on battler b's status (HUD countdown); 0 when none.
static u8 WlStatusSeconds(u8 b)
{
    if (b >= 4 || !sWlStatus[b].code || !sWlStatus[b].timer)
        return 0;
    return (sWlStatus[b].timer + 59) / 60;
}

static u16 WlStatusDuration(u8 b, u8 code, bool8 toxic)
{
    u16 t = code == 1 ? 180 : code == 2 ? 240 : code == 5 ? 300
          : code == 3 ? 2400 : toxic ? 3600 : 1800;
    if (b == 1 && DirectorSoloActive())
        t /= 2;   // legendaries shake it off faster
    return t;
}

static void WlStatusClear(u8 b)
{
    u32 none = 0;
    gBattleMons[b].status1 = 0;
    SetMonData(SquadPartyMon(b), MON_DATA_STATUS, &none);
    if (b < 2)
        sArena.bodies[b].burnClock = 0;
    sArena.hudDirty = TRUE;
}

static void StatusSim(void)
{
    u32 b;
    if (!WildlandsWorld_Active())
        return;
    if (gWildlandsStatusTest)
    {
        static const u32 sTestBits[6] = {STATUS1_PARALYSIS, 3, STATUS1_BURN, STATUS1_POISON, STATUS1_FREEZE, 0};
        u32 bit = sTestBits[(gWildlandsStatusTest - 1) % 6];   // 6 clears
        sWlStatus[0].immune = 0;
        gBattleMons[0].status1 = bit;
        SetMonData(SquadPartyMon(0), MON_DATA_STATUS, &bit);
        gWildlandsStatusTest = 0;
    }
    gWildlandsStatusNow = WlStatusCode(gBattleMons[0].status1);
    for (b = 0; b < 4; b++)
    {
        struct WlStatus *s = &sWlStatus[b];
        u32 st;
        u8 code;
        bool8 toxic;
        if (!SquadAlive(b))
        {
            s->code = 0; s->timer = 0; s->immune = 0;
            continue;
        }
        st = gBattleMons[b].status1;
        code = WlStatusCode(st);
        toxic = (st & STATUS1_TOXIC_POISON) != 0;
        if (s->immune)
            s->immune--;
        if (!code)
        {
            if (s->code) { s->code = 0; s->timer = 0; s->immune = 300; }   // cured (supplies, thaw)
            s->lastHp = gBattleMons[b].hp;
            continue;
        }
        if (code != s->code)
        {
            // Onset (or a different status): refused while immune.
            if (s->immune && !s->code)
            {
                WlStatusClear(b);
                continue;
            }
            s->code = code;
            s->timer = WlStatusDuration(b, code, toxic);
            s->tick = 0;
            s->lastHp = gBattleMons[b].hp;
            gWildlandsStatusTelemetry[3]++;
            sArena.hudDirty = TRUE;
        }
        // Asleep: any damage wakes you.
        if (code == 2 && gBattleMons[b].hp < s->lastHp)
        {
            WlStatusClear(b);
            s->code = 0; s->timer = 0; s->immune = 300;
            continue;
        }
        s->lastHp = gBattleMons[b].hp;
        // Burn and poison: a pulse every 5s.
        if ((code == 3 || code == 4) && ++s->tick >= 300)
        {
            u16 hp = gBattleMons[b].hp, dmg = gBattleMons[b].maxHP / ((code == 4 && !toxic) ? 20 : 16);
            s32 x, y;
            s->tick = 0;
            if (!dmg) dmg = 1;
            if (dmg > hp) dmg = hp;
            hp -= dmg;
            gBattleMons[b].hp = hp;
            SetMonData(SquadPartyMon(b), MON_DATA_HP, &hp);
            SquadPos(b, &x, &y);
            ArenaFeedback_Impact(b & 1, x / Q, y / Q, dmg, ARENA_FEEDBACK_DAMAGE);
            if (b < 2) sArena.bodies[b].flash = 5;
            else sSquadWings[b - 2].flash = 5;
            s->lastHp = hp;
            sArena.hudDirty = TRUE;
            if (!hp)
            {
                s->code = 0; s->timer = 0;
                gWildlandsStatusTelemetry[1]++;
                SquadKO(b, (b & 1) ^ 1);
                if (sArena.resultTimer)
                    return;
                continue;
            }
        }
        if (s->timer && !--s->timer)
        {
            WlStatusClear(b);
            s->code = 0; s->immune = 300;
        }
    }
}

// Secondary status from hits that involve a partner (the native lead-vs-lead
// path keeps its own secondary rules). Type immunities apply.
static void StatusSecondary(u8 attacker, u8 target, u16 move)
{
    u32 bit = 0;
    u8 type = gBattleMoves[move].type;
    if (!WildlandsWorld_Active())
        return;
    // Fire thaws a frozen target.
    if ((gBattleMons[target].status1 & STATUS1_FREEZE) && type == TYPE_FIRE)
    {
        WlStatusClear(target);
        return;
    }
    if (gBattleMons[target].status1 || (target < 4 && sWlStatus[target].immune))
        return;
    switch (gBattleMoves[move].effect)
    {
    case EFFECT_BURN_HIT:     bit = STATUS1_BURN; break;
    case EFFECT_FREEZE_HIT:   bit = STATUS1_FREEZE; break;
    case EFFECT_PARALYZE_HIT: bit = STATUS1_PARALYSIS; break;
    case EFFECT_POISON_HIT:   bit = STATUS1_POISON; break;
    }
    if (!bit || Random() % 100 >= gBattleMoves[move].secondaryEffectChance)
        return;
    if ((bit == STATUS1_BURN && IS_BATTLER_OF_TYPE(target, TYPE_FIRE))
        || (bit == STATUS1_FREEZE && IS_BATTLER_OF_TYPE(target, TYPE_ICE))
        || (bit == STATUS1_POISON && (IS_BATTLER_OF_TYPE(target, TYPE_POISON) || IS_BATTLER_OF_TYPE(target, TYPE_STEEL))))
        return;
    gBattleMons[target].status1 = bit;
    SetMonData(SquadPartyMon(target), MON_DATA_STATUS, &bit);
    sArena.hudDirty = TRUE;
    (void)attacker;
}

// Poisoned or burned Pokemon do not regenerate while resting.
static bool8 StatusBlocksHealing(u8 b)
{
    return WildlandsWorld_Active() && (gBattleMons[b].status1 & (STATUS1_BURN | STATUS1_PSN_ANY));
}
