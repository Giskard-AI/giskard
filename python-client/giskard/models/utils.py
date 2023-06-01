import itertools
from collections.abc import Iterator


def check_if_data_is_iterable(data, break_it=False):
    try:
        for entry in data: # noqa
            return True
    except TypeError as te:
        if break_it:
            raise ValueError(f"{data} is not iterable.") from te
        else:
            return True


def is_tuple(entry):
    # to_unpack = True, for the case of 2 inputs or more, like (input1, offset) or (input1, input2)
    # to_unpack = False, for the case of 1 input
    return True if isinstance(entry, tuple) else False


def is_data_unpackable(data):
    check_if_data_is_iterable(data, break_it=True)
    for entry in data:
        return is_tuple(entry)


def map_to_tuples(data: Iterator):
    item = next(data)
    data = itertools.chain([item], data)

    if isinstance(item, tuple):  # nothing to do
        return data

    return map(lambda x: (x,), data)
