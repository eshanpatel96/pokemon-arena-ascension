// WildLands Beta: breakable cover in the world.
// The arena's own props (rocks, logs, bushes, crystals, pods) live at a few
// hundred generated sites over the island. A small pool of the arena's prop
// slots streams to the sites around the camera, so every arena system that
// already knows props (collision, shots, line of sight, breaking, debris,
// Psychic lifting rocks, pod chains) works out in the world unchanged.
// Damage persists per site for the whole match.
#include "wildlands_props.inc"
#define WL_PROP_SLOTS 7

bool8 ArenaTerrain_WorldSlot(u8 i, s16 x, s16 y, u8 set, u8 art, u8 kind, u8 hp, u8 maxHp);
void ArenaTerrain_WorldRelease(u8 i);

// [0] sites [1] active slots [2] activations [3] releases [4] sites broken [5] slot failures
EWRAM_DATA u16 gWildlandsPropTelemetry[6] = {0};
static EWRAM_DATA u8 *sPropHp = NULL;            // per site: hp left, 0 = broken
static EWRAM_DATA u16 sPropSlotSite[WL_PROP_SLOTS] = {0};   // site + 1, 0 = free
static const u8 sPropKind[7] = {ARENA_PROP_ROCK, ARENA_PROP_ROCK, ARENA_PROP_ROCK, ARENA_PROP_WOOD,
                                ARENA_PROP_BUSH, ARENA_PROP_CRYSTAL, ARENA_PROP_POD};
static const u8 sPropStrength[7] = {3, 2, 2, 1, 1, 2, 1};

// Ruin columns (set 4) are sturdy: they take several hits.
static u8 PropStrength(const struct WlPropSite *site)
{
    return (site->set == 4 && site->art <= 2) ? 4 : sPropStrength[site->art];
}

static void PropsFree(void)
{
    if (sPropHp)
        Free(sPropHp);
    sPropHp = NULL;
}

static void PropsInit(void)
{
    u32 i;
    for (i = 0; i < WL_PROP_SLOTS; i++)
        sPropSlotSite[i] = 0;
    if (!WildlandsWorld_Active())
        return;
    // The classic arena's fixed props are not in the world: retire them so
    // nothing (Psychic, toss chains) reaches for an invisible rock.
    for (i = 0; i < ARENA_OBSTACLES; i++)
    {
        gArenaProps[i].broken = 1;
        gArenaProps[i].hp = 0;
        ArenaNav_SetObstacle(i, 0);
    }
#if WL_PROP_SITES
    if (!sWildlandsEncounterLive || !sPropHp)
    {
        PropsFree();
        sPropHp = Alloc(WL_PROP_SITES);
        if (sPropHp)
            for (i = 0; i < WL_PROP_SITES; i++)
                sPropHp[i] = PropStrength(&sWlPropSites[i]);
        memset(gWildlandsPropTelemetry, 0, sizeof(gWildlandsPropTelemetry));
    }
    gWildlandsPropTelemetry[0] = WL_PROP_SITES;
#endif
}

static void PropsSim(void)
{
#if WL_PROP_SITES
    s32 cx, cy, best = 0x7FFFFFFF;
    u32 i, k, slot, pick = WL_PROP_SITES, active = 0;
    if (!WildlandsWorld_Active() || !sPropHp || (sArena.frame & 7))
        return;
    cx = sArenaXLCameraX + 120;
    cy = sArenaXLCameraY + 80;
    for (i = 0; i < WL_PROP_SLOTS; i++)
    {
        u16 s = sPropSlotSite[i];
        const struct ArenaProp *p = &gArenaProps[i];
        if (!s)
            continue;
        if (gArenaPsychicRocks[i].state || p->reserved || p->fuse)
        { active++; continue; }   // mid-throw or about to blow: keep it
        if (!p->broken && p->hp < sPropHp[s - 1])
            sPropHp[s - 1] = p->hp;
        if (p->broken && sPropHp[s - 1])
        { sPropHp[s - 1] = 0; gWildlandsPropTelemetry[4]++; }
        if (Abs(sWlPropSites[s - 1].x - cx) > 200 || Abs(sWlPropSites[s - 1].y - cy) > 150)
        {
            ArenaTerrain_WorldRelease(i);
            sPropSlotSite[i] = 0;
            gWildlandsPropTelemetry[3]++;
        }
        else
            active++;
    }
    gWildlandsPropTelemetry[1] = active;
    for (slot = 0; slot < WL_PROP_SLOTS && sPropSlotSite[slot]; slot++)
        ;
    if (slot == WL_PROP_SLOTS)
        return;
    // One activation per pass: the nearest site in view (plus margin) that
    // is not already on a slot.
    for (k = 0; k < WL_PROP_SITES; k++)
    {
        s32 dx = sWlPropSites[k].x - cx, dy = sWlPropSites[k].y - cy, d;
        if (Abs(dx) > 168 || Abs(dy) > 120)
            continue;
        for (i = 0; i < WL_PROP_SLOTS; i++)
            if (sPropSlotSite[i] == k + 1)
                break;
        if (i < WL_PROP_SLOTS)
            continue;
        d = dx * dx + dy * dy;
        if (d < best) { best = d; pick = k; }
    }
    if (pick == WL_PROP_SITES)
        return;
    {
        const struct WlPropSite *site = &sWlPropSites[pick];
        u8 hp = sPropHp[pick];
        if (!ArenaTerrain_WorldSlot(slot, site->x, site->y, site->set, site->art, sPropKind[site->art],
                                    hp ? hp : 1, PropStrength(site)))
        {
            // Out of sprites: storm rain is cosmetic, cover is gameplay.
            gWildlandsPropTelemetry[5]++;
            ZoneFreeRain();
            return;
        }
        if (!hp)
        {
            // Already smashed: rubble only, nothing solid.
            gArenaProps[slot].broken = 1;
            gArenaProps[slot].hp = 0;
            ArenaNav_SetObstacle(slot, 0);
        }
        sPropSlotSite[slot] = pick + 1;
        gWildlandsPropTelemetry[2]++;
    }
#endif
}
