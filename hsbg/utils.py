"""Utility functions."""
from typing import Iterable, List

from hsbg.models import Minion


def filter_minions(minions: Iterable[Minion], clone: bool = False, **kwargs: dict) -> List[Minion]:
    """Find all the minions in the given iterable matching the given keyword arguments.
    Each keyword argument should be an attribute of the Minion class.

    Args:
        minions: An iterable of minions to filter.
        clone: Whether to clone the minions.
        **kwargs: Keyword arguments corresponding to minion attributes to match.
    """
    matches = []
    for minion in minions:
        if any(getattr(minion, key) != value for key, value in kwargs.items()):
            continue

        if clone:
            matches.append(minion.clone())
        else:
            matches.append(minion)

    return matches
