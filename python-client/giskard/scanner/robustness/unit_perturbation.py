import string
import random
import pandas as pd

from ...scanner.robustness.entity_swap import typos
from ...ml_worker.testing.registry.transformation_function import TransformationFunction
from ...ml_worker.testing.registry.transformation_function import transformation_function


@transformation_function(row_level=False)
def text_uppercase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.upper()
    return df


@transformation_function(row_level=False)
def text_lowercase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.lower()
    return df


@transformation_function(row_level=False)
def text_titlecase(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.title()
    return df


class TextTransformation(TransformationFunction):
    def execute(self, data: pd.Series):
        series_to_perturb = data.copy()
        series_perturbed = series_to_perturb.apply(self.perturbation)
        return series_perturbed

    def perturbation(self, x):
        return x


class TextTypoTransformation(TextTransformation):
    name = "Typo"

    def perturbation(self, x):
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
                word = word[:idx] + word[idx + 1 :]
                return word
            elif perturbation_type == 'replace':
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in typos:
                    replacement = random.choice(typos[c])
                    text_modified = word[:j] + replacement + word[j + 1 :]
                    return text_modified
        return word


class TextPunctuationRemovalTransformation(TextTransformation):
    name = "Punctuation Removal"

    def perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._remove_punc(token))
        return " ".join(new_text)

    def _remove_punc(self, text):
        return text.translate(str.maketrans('', '', string.punctuation))
