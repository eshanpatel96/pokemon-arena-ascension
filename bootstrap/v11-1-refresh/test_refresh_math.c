#include <stdint.h>
#include <stdio.h>
#include <assert.h>
typedef int32_t s32; typedef uint16_t u16; typedef uint8_t bool8;
#include "ascension_refresh_math.inc"
int main(void) {
    unsigned assertions=0;
    for(s32 damage=0;damage<=65535;damage++) {
        assert(AscensionRefresh_DamageValue(damage,0,0,0,0,0,0)==damage);assertions++;
        assert(AscensionRefresh_DamageValue(damage,1,0,0,0,0,0)==(damage+1)/2);assertions++;
        assert(AscensionRefresh_DamageValue(damage,1,1,1,1,0,0)==(damage+1)/2);assertions++;
        assert(AscensionRefresh_DamageValue(damage,1,1,1,0,1,0)==(damage+1)/2);assertions++;
        assert(AscensionRefresh_DamageValue(damage,1,1,1,0,0,1)==damage);assertions++;
        s32 wet=AscensionRefresh_DamageValue(damage,1,1,1,0,0,0);
        assert(wet==(damage*120/100+1)/2 && wet<=damage);assertions++;
    }
    assert(AscensionRefresh_DamageValue(0,1,1,1,0,0,0)==0);assertions++;
    for(u16 speed=1;speed<=2048;speed++) {
        assert(AscensionRefresh_SpeedValue(speed,1,1,1,1)==speed*115/100);assertions++;
        assert(AscensionRefresh_SpeedValue(speed,1,1,1,0)==speed*3/4);assertions++;
        assert(AscensionRefresh_SpeedValue(speed,1,0,1,1)==speed);assertions++;
        assert(AscensionRefresh_SpeedValue(speed,1,1,0,1)==speed);assertions++;
    }
    printf("PASS %u integer-policy assertions. Not a fight-duration or hazard playtest.\n",assertions);
}
