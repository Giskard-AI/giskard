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


def numpy_encoder(some_list: List):
    if some_list is not None:
        if isinstance(some_list[0], np.integer):
            return [int(i) for i in some_list]
        if isinstance(some_list[0], np.floating):
            return [float(i) for i in some_list]
    return some_list
