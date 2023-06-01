import string
import random
import pandas as pd
import re

from .entity_swap import typos
from ...ml_worker.testing.registry.transformation_function import TransformationFunction
from ...ml_worker.testing.registry.transformation_function import transformation_function
from giskard.scanner.robustness.entity_swap import gender_switch_en


@transformation_function(row_level=False)
def text_uppercase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.upper()
    return df


text_uppercase.name = "Transform to uppercase"


@transformation_function(row_level=False)
def text_lowercase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.lower()
    return df


text_lowercase.name = "Transform to lowercase"


@transformation_function(row_level=False)
def text_titlecase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.title()
    return df


text_titlecase.name = "Transform to title case"


class TextTransformation(TransformationFunction):
    row_level = False

    def __init__(self, column):
        self.column = column

    def execute(self, data: pd.DataFrame):
        data = data.copy()
        data[self.column] = data[self.column].apply(self.make_perturbation)
        return data

    def make_perturbation(self, text: str) -> str:
        raise NotImplementedError()


class TextTypoTransformation(TextTransformation):
    name = "Add typos"

    def make_perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._add_typos(token))
        return " ".join(new_text)

    def _add_typos(self, word):
        # Get the token's word and apply a perturbation with probability 0.1
        if random.random() < 0.2 and len(word) > 1:
            # Choose a perturbation type randomly
            perturbation_type = random.choice(['insert', 'delete', 'replace'])
            # Apply the perturbation
            if perturbation_type == 'insert':
                idx = random.randint(0, len(word))
                new_char = chr(random.randint(33, 126))
                word = word[:idx] + new_char + word[idx:]
                return word
            elif perturbation_type == 'delete':
                idx = random.randint(0, len(word) - 1)
                word = word[:idx] + word[idx + 1:]
                return word
            elif perturbation_type == 'replace':
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in typos:
                    replacement = random.choice(typos[c])
                    text_modified = word[:j] + replacement + word[j + 1:]
                    return text_modified
        return word


class TextPunctuationRemovalTransformation(TextTransformation):
    name = "Punctuation Removal"

    def make_perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._remove_punc(token))
        return " ".join(new_text)

    def _remove_punc(self, text):
        return text.translate(str.maketrans('', '', string.punctuation))


class TextGenderTransformation(TextTransformation):
    name = "Switch gender"

    def make_perturbation(self, x):
        split_text = x.split()
        new_words = []
        for token in split_text:
            new_word = self._switch(token)
            if new_word != token:
                new_words.append(new_word)

        new_text = x
        for original_word,switched_word in new_words:
            new_text = re.sub(fr"\b{original_word}\b", switched_word, new_text)
        return new_text

    def _switch(self, word):
        if word.lower() in gender_switch_en:
            return [word, gender_switch_en[word.lower()]]
        else:
            return word
