"""Utility functions."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterable, Tuple, List, Dict, Callable, Optional, Union

import colorama
from tqdm import tqdm


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
        for x in table:
            table[x][1] = tuple(table[x][1])
            table[x] = tuple(table[x])

    return table


def parallel_map(iterables: Union[list, iter], function: callable, n_jobs: Optional[int] = 16,
                 use_kwargs: Optional[bool] = False, front_num: Optional[int] = 3,
                 show_progress_bar: Optional[bool] = True, initial_value: Optional[list] = None,
                 raise_errors: Optional[bool] = False, include_errors: Optional[bool] = True,
                 extend_result: Optional[bool] = False, return_output: Optional[bool] = True,
                 add_func: Optional[callable] = None) -> Union[list, None]:
    """A parallel version of the map function with a progress bar.
    Return a list of the form [function(iterables[0]), function(iterables[1]), ...].
    Args:
        iterables: A sequence, collection, or iterator object.
        function: A function to apply to the elements of `iterables`.
        n_jobs: The number of jobs to run.
        use_kwargs: Whether to consider the elements of iterables as dictionaries of
            keyword arguments to function.
        front_num: The number of iterations to run serially before dispatching the
            parallel jobs. Useful for catching exceptions.
        show_progress_bar: Whether to show a progress bar while the jobs run.
        initial_value: The initial value of the output list.
            This should be an iterables-like object.
        raise_errors: Whether to raise errors.
        include_errors: Whether to include the errors in the output list.
        extend_result: Whether the resultant list should be extended rather than appended to.
        return_output: Whether to return a list containing the output values of the function.
            If False, this function does not return None.
        add_func: A custom function for adding the output values of the function to the result list.
            This function has two parameters, the value to add and the list to add it to, and it
            should mutate the list.
    Preconditions:
        - n_jobs >= 1
        - front_num >= 0
    """
    if isinstance(iterables, list):
        front = [function(**b) if use_kwargs else function(b) for b in iterables[:front_num]]
        iterables = iterables[front_num:]
    else:
        front = []
        for _ in range(front_num):
            a = next(iterables)
            front.append(function(**a) if use_kwargs else function(a))

    def _add_func(x: object, output: list) -> None:
        """Add a value to the output list."""
        # No reason to add if we aren't returning the output.
        if not return_output:
            return

        if add_func is not None:
            add_func(x, output)
        else:
            if extend_result:
                output.extend(x)
            else:
                output.append(x)

    output = initial_value or list()
    for x in front:
        _add_func(x, output)

    # If n_jobs == 1, then we are not parallelising, run all elements serially.
    if n_jobs == 1:
        for a in tqdm(iterables):
            x = function(**a) if use_kwargs else function(a)
            _add_func(x, output)

        return output if return_output else None

    with ThreadPoolExecutor(max_workers=n_jobs) as pool:
        futures = [
            pool.submit(function, **c) if use_kwargs else
            pool.submit(function, c) for c in iterables
        ]

        for _ in tqdm(as_completed(futures), total=len(futures), unit='it',
                      unit_scale=True, disable=not show_progress_bar):
            # Do nothing...This for loop is just here to iterate through the futures
            pass

    # Don't bother retrieving the results from the future...If we don't return anything.
    if not return_output:
        return None

    for _, future in tqdm(enumerate(futures)):
        try:
            _add_func(future.result(), output)
        except Exception as exception:
            if raise_errors:
                raise exception
            if include_errors:
                _add_func(exception, output)

    return output

def colourise_string(string: str, colour: str) -> str:
    """Return a string with a stdout colour format."""
    reset_style = colorama.Style.RESET_ALL
    return f'{colour}{string}{reset_style}'


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['concurrent.futures', 'tqdm'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E0602', 'E1136', 'R0913', 'R0914', 'W0703', 'E9969']
    })

    import python_ta.contracts
    python_ta.contracts.check_all_contracts()
