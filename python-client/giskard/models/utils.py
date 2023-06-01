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


def numpy_encoder(l: List):
    e = l[0]
    if isinstance(e, np.integer):
        return [int(i) for i in l]
    if isinstance(e, np.floating):
        return [float(i) for i in l]
    return l
