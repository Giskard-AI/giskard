import itertools
from collections.abc import Iterator


def map_to_tuples(data: Iterator):
    item = next(data)
    data = itertools.chain([item], data)

    if isinstance(item, tuple):  # nothing to do
        return data

    return map(lambda x: (x,), data)
