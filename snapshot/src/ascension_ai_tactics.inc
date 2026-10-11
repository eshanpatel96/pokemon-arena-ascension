/* Bounded career-only scoring; no input prediction or native damage mutation.
 * Called once per legal, PP-available candidate at the existing perception tick.
 * A large negative score means the original evaluator rejected an action.
 */
static s32 AscensionAi_AdjustScore(const struct ArenaMoveProfile *p,
    s32 score, s32 distance, bool8 repeat, bool8 visibleCommitment,
    bool8 lowHp, u8 style)
{
    s32 cost;
    if (score <= -900) return score;
    cost = p->recovery / 4;
    if (cost > 36) cost = 36;
    if (p->kind != ARENA_MOVE_SELF) score -= cost;
    if (repeat && p->kind != ARENA_MOVE_SELF)
        score -= score > 225 ? score / 3 : 75;
    if (p->kind == ARENA_MOVE_MELEE && distance < 47) score += 48;
    else if (p->kind == ARENA_MOVE_RUSH && distance < 80) score += 32;
    else if (p->kind == ARENA_MOVE_PROJECTILE && distance > 58) score += 26;
    else if (p->kind == ARENA_MOVE_CONE && distance < 95) score += 18;
    /* Long windups at close range are punishable. A visible committed attack
     * is an opportunity for a fast counter, not perfect future-input reading. */
    if (p->kind != ARENA_MOVE_SELF && distance < 55)
    {
        if (p->windup <= 10) score += visibleCommitment ? 42 : 18;
        else if (p->windup >= 20 && !visibleCommitment) score -= 40;
    }
    if (lowHp && p->kind == ARENA_MOVE_PROJECTILE && distance > 60) score += 20;
    switch (style)
    {
    case 0:
        if (p->kind == ARENA_MOVE_MELEE || p->kind == ARENA_MOVE_RUSH) score += 52;
        else if (p->kind == ARENA_MOVE_PROJECTILE && distance < 55) score -= 32;
        break;
    case 1:
        if (p->kind == ARENA_MOVE_PROJECTILE && distance > 45) score += 48;
        else if (p->kind == ARENA_MOVE_CONE && distance > 65) score += 20;
        break;
    case 2:
        if (p->kind == ARENA_MOVE_SELF && lowHp) score += 45;
        else if (p->kind == ARENA_MOVE_CONE && distance < 85) score += 20;
        break;
    case 3:
        if (visibleCommitment && p->windup <= 16
            && (p->kind == ARENA_MOVE_MELEE || p->kind == ARENA_MOVE_RUSH)) score += 55;
        break;
    default:
        if (p->kind == ARENA_MOVE_PROJECTILE && distance > 90) score += 15;
        if (p->kind == ARENA_MOVE_MELEE && distance < 40) score += 15;
        break;
    }
    return score;
}
