import pandas as pd
from giskard.ml_worker.testing.registry.transformation_function import transformation_function
import string
import random


def upper_case(text):
    return text.upper()

def lower_case(text):
    return text.lower()

def swap_entities(text):
    # Split the text into tokens (words and punctuation marks)
    tokens = text.split(' ')

    # If there are at least two entities, swap two of them
    if len(tokens) > 1:
        entity1, entity2 = random.sample(tokens, 2)
        text = text.replace(entity1, entity2, 1)
        text = text.replace(entity2, entity1, 1)

    return text

def add_punctuation(text):
    punctuation_marks = ['.', '!', '?']
    random_punctuation = random.choice(punctuation_marks)
    return text + random_punctuation


def strip_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))


def add_typos(text):
    # Define a dictionary of common typos
    typos = {
        'a': ['s', 'z', 'q', 'w', 'x'],
        'b': ['v', 'n', 'g', 'h'],
        'c': ['x', 'v', 'f', 'd'],
        'd': ['s', 'e', 'r', 'f', 'c', 'x'],
        'e': ['w', 's', 'd', 'r'],
        'f': ['d', 'r', 't', 'g', 'v', 'c'],
        'g': ['f', 't', 'y', 'h', 'b', 'v'],
        'h': ['g', 'y', 'u', 'j', 'n', 'b'],
        'i': ['u', 'j', 'k', 'o'],
        'j': ['h', 'u', 'i', 'k', 'm', 'n'],
        'k': ['j', 'i', 'o', 'l', 'm'],
        'l': ['k', 'o', 'p'],
        'm': ['n', 'j', 'k'],
        'n': ['b', 'h', 'j', 'm'],
        'o': ['i', 'k', 'l', 'p'],
        'p': ['o', 'l'],
        'q': ['a', 'w'],
        'r': ['e', 'd', 'f', 't'],
        's': ['a', 'w', 'd', 'x', 'z'],
        't': ['r', 'f', 'g', 'y'],
        'u': ['y', 'h', 'j', 'i'],
        'v': ['c', 'f', 'g', 'b'],
        'w': ['q', 'a', 's', 'e'],
        'x': ['z', 's', 'd', 'c'],
        'y': ['t', 'g', 'h', 'u'],
        'z': ['a', 's', 'x']
    }

    # Split the text into words
    words = text.split(" ")

    # Introduce typos into some of the words
    for i in range(len(words)):
        if random.random() < 1:  # 10% chance of introducing a typo
            word = words[i]
            if len(word) > 1:
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in typos:
                    replacement = random.choice(typos[c])
                    words[i] = word[:j] + replacement + word[j + 1:]

    # Join the words back into a string
    text = ' '.join(words)

    return text

class TransformationGenerator:
    def __init__(self, model, dataset):
        self.model = model
        self.dataset = dataset
        self.column_types = dataset.column_types

    def generate_std_transformation(self, feature):
        mad = self.dataset.df[feature].mad()
        @transformation_function()
        def func(x: pd.Series) -> pd.Series:
            if self.column_types[feature] == "numeric":
                x[feature] += 3*mad
                return x
            return x

        return func

    def text_transformation(self, feature):
        @transformation_function()
        def func(x: pd.Series) -> pd.Series:
            if self.column_types[feature] == 'text':
                x[feature] = swap_entities(x[feature])
                x[feature] = add_punctuation(x[feature])
                x[feature] = add_typos(x[feature])
                x[feature] = upper_case(x[feature])
                return x

        return func
