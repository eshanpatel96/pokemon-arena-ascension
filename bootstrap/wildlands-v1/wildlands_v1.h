#ifndef GUARD_WILDLANDS_V1_H
#define GUARD_WILDLANDS_V1_H

#include "global.h"

bool8 WildlandsV1_IsActive(void);
void WildlandsV1_Tick(void);
void WildlandsV1_HandleInput(u16 newKeys, u16 heldKeys);
void WildlandsV1_StartLoadout(void);
void WildlandsV1_PreOam(void);
void WildlandsV1_Reset(void);

#endif // GUARD_WILDLANDS_V1_H
