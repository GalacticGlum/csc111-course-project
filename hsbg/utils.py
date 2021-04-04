"""Utility functions."""
from __future__ import annotations
from typing import Any, Iterable, Tuple, List, Dict, Callable, Optional, Union


def filter_minions(minions: Iterable[Minion], clone: bool = False, limit: Optional[int] = None,
                   **kwargs: dict) -> List[Minion]:
    """Find all the minions in the given iterable matching the given keyword arguments.
    Each keyword argument should be an attribute of the Minion class.

    Args:
        minions: An iterable of minions to filter.
        clone: Whether to clone the minions.
        limit: The maximum length of the returned list.
        **kwargs: Keyword arguments corresponding to minion attributes to match.
    """
    matches = []
    for minion in minions:
        if limit is not None and len(matches) == limit:
            break
        if any(getattr(minion, key) != value for key, value in kwargs.items()):
            continue

        if clone:
            matches.append(minion.clone())
        else:
            matches.append(minion)

    return matches


def make_frequency_table(values: List[Any], key: Optional[Callable[[Any], Any]] = None) \
        -> Dict[Any, Union[int, Tuple[Tuple[Any], int]]]:
    """Return a dict mapping the frequency of each distinct element in the given list.

    If a key is provided, then the value of the dict is a 2-tuple containing the frequency and
    a tuple of the elements of values before the key was applied.

    Args:
        values: A list of values.
        key: A function which takes in as input an element of the list, and returns some value,
             which is then used as a key to the frequency table.

    >>> values = [1, 3, 3, 5, 4, 3]
    >>> make_frequency_table(values) == {1: 1, 3: 3, 4: 1, 5: 1}
    True
    >>> expected = {2: (1, (1,)), 6: (3, (3, 3, 3)), 8: (1, (4,)), 10: (1, (5,))}
    >>> make_frequency_table(values, key=lambda x: 2 * x) == expected
    True
    """
    table = {}
    for x in values:
        if key is not None:
            y = key(x)
            if y not in table:
                table[y] = [0, []]

            table[y][0] += 1
            table[y][1].append(x)
        else:
            if x not in table:
                table[x] = 0
            table[x] += 1

    if key is not None:
        # Convert lists to tuples
        for x in table.keys():
            table[x][1] = tuple(table[x][1])
            table[x] = tuple(table[x])

    return table

if __name__ == '__main__':
    import doctest
    doctest.testmod()
