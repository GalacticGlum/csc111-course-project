"""Implementation of various minion cards."""
from hsbg.models import Minion, MinionAbility, MinionKeyword, MinionType, TIER_RANKS

# NOTE: The event arguments don't exist yet! This is merely a sketch of how it will look.
# We still need to implement an event system!

################################################################################
# Tier 1 cards
################################################################################
ALLEY_CAT = Minion(
    'Alleycat', MinionType.BEAST, health, 1,
    keywords=MinionKeyword.BATTLE_CRY,
    on_played=lambda ctx: ctx.board.summon('Tabbycat', ctx.index, \
                                           golden: ctx.source_minion.level == 2)
)
TABBY_CAT = Minion('Tabbycat', MinionType.BEAST, 1, 1, in_pool=False)
DIRE_WOLF_ALPHA = Minion(
    'Dire Wolf Alpha', MinionType.BEAST, 2, 2,
    cost=2,
    on_played=lambda ctx: ctx.board.buff_adjacent(ctx.source_minion, attack=1, aura=True)
)