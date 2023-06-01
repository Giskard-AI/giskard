import itertools
from collections.abc import Iterator
from typing import List
import numpy as np


def map_to_tuples(data: Iterator):
    item = next(data)
    data = itertools.chain([item], data)

    if isinstance(item, tuple):  # nothing to do
        return data

    return map(lambda x: (x,), data)


def np_types_to_native(some_list: List):
    if some_list is not None:
        return [np_type_to_native(i) for i in some_list]
    return some_list


def np_type_to_native(i):
    return i.item() if isinstance(i, np.generic) else i
