from typing import List

import itertools
import random
from collections.abc import Iterator
from functools import lru_cache

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


def fix_seed(seed=1337):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


@lru_cache(None)
def warn_once(logger, msg: str):
    logger.warning(msg)
