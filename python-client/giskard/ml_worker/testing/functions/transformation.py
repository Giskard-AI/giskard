import random
import string

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
}


@transformation_function(name="Keyboard typo")
def keyboard_typo_transformation(x: pd.Series, column_name: str, rate: float = 0.1) -> pd.Series:
    # Split the text into words
    words = x[column_name].split(" ")

    # Introduce typos into some of the words
    for i in range(len(words)):
        if random.random() < rate:
            word = words[i]
            if len(word) > 1:
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in nearbykeys:
                    replacement = random.choice(nearbykeys[c])
                    words[i] = word[:j] + replacement + word[j + 1:]

    # Join the words back into a string
    x[column_name] = ' '.join(words)
    return x


@transformation_function(name="To uppercase")
def uppercase_transformation(x: pd.Series, column_name: str) -> pd.Series:
    x[column_name] = x[column_name].upper()
    return x


@transformation_function(name="To lowercase")
def lowercase_transformation(x: pd.Series, column_name: str) -> pd.Series:
    x[column_name] = x[column_name].lower()
    return x


@transformation_function(name="Strip punctuation")
def strip_punctuation(x: pd.Series, column_name: str):
    x[column_name] = x[column_name].translate(str.maketrans('', '', string.punctuation))
    return x
