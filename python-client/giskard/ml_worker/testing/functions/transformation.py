from random import randint

import pandas as pd

from giskard.ml_worker.testing.registry.transformation_function import transformation_function

nearbykeys = {
    'a': ['q', 'w', 's', 'x', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 's', 'd', 'r'],
    'f': ['d', 'r', 't', 'g', 'v', 'c'],
    'g': ['f', 't', 'y', 'h', 'b', 'v'],
    'h': ['g', 'y', 'u', 'j', 'n', 'b'],
    'i': ['u', 'j', 'k', 'o'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],
    'm': ['n', 'j', 'k', 'l'],
    'n': ['b', 'h', 'j', 'm'],
    'o': ['i', 'k', 'l', 'p'],
    'p': ['o', 'l'],
    'q': ['w', 'a', 's'],
    'r': ['e', 'd', 'f', 't'],
    's': ['w', 'e', 'd', 'x', 'z', 'a'],
    't': ['r', 'f', 'g', 'y'],
    'u': ['y', 'h', 'j', 'i'],
    'v': ['c', 'f', 'g', 'v', 'b'],
    'w': ['q', 'a', 's', 'e'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'g', 'h', 'u'],
    'z': ['a', 's', 'x'],
    ' ': ['c', 'v', 'b', 'n', 'm']
}


@transformation_function(name="Keyboard typo")
def keyboard_typo_transformation(x: pd.Series, column_name: str, rate: float = 0.01) -> pd.Series:
    text = list(x[column_name])
    typos = int(len(text) * rate)
    for i in range(typos):
        pos = randint(0, len(text) - 1)
        if text[pos] in nearbykeys:
            keys = nearbykeys[text[pos]]
            text[pos] = keys[randint(0, len(keys) - 1)]

    x[column_name] = "".join(text)
    return x
