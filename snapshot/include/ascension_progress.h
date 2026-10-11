#ifndef GUARD_ASCENSION_PROGRESS_H
#define GUARD_ASCENSION_PROGRESS_H
#define ASCENSION_TOWER_COUNT 8
#define ASCENSION_SUMMIT_INDEX 8
#define ASCENSION_FLOORS_PER_TOWER 9 // bound, not a uniform progression
// Normal ranks 0..7: Bronze/Gale/Grass/Ghost/Fire/Water/Thunder/Astral.
// Rank 8 is a provisional five-stage Summit; V10 replaces its opponents
// with the full Elite Four / Champion tournament.
static inline unsigned Ascension_FloorCount(unsigned rank)
{
    static const unsigned char counts[9] = {4,5,5,6,6,7,8,9,5};
    return rank < 9 ? counts[rank] : 0;
}
#define ASCENSION_COMPLETE 9
// rank 0..7: towers, rank 8: Champion Summit, rank 9: all clear.
static inline unsigned Ascension_NextRank(unsigned rank,unsigned floor)
{return rank<ASCENSION_COMPLETE && floor+1 >= Ascension_FloorCount(rank) ? rank+1 : rank;}
static inline unsigned Ascension_NextFloor(unsigned rank,unsigned floor)
{return floor+1 >= Ascension_FloorCount(rank) ? 0 : floor+1;}
static inline unsigned Ascension_CanEnter(unsigned rank,unsigned floor)
{return rank<ASCENSION_COMPLETE && floor<Ascension_FloorCount(rank);}
void Ascension_V111StartRosterTask(void);
#endif
