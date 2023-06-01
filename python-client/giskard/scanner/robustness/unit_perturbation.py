import pandas as pd
from giskard.ml_worker.testing.registry.transformation_function import transformation_function
import random
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
from giskard.scanner.robustness.entity_swap import masculine_to_feminine, feminine_to_masculine, minority_groups, \
    religion_dict, typos
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
import string

@transformation_function(row_level=False)
def text_uppercase(x: pd.DataFrame, column: str) -> pd.Series:  # Or Series in input ?
    y = x.copy()
    y[column] = y[column].str.upper()
    return y


@transformation_function(row_level=False)
def text_lowercase(x: pd.DataFrame, column: str) -> pd.Series:
    y = x.copy()
    y[column] = y[column].str.lower()
    return y


@transformation_function(row_level=False)
def text_titlecase(x: pd.DataFrame, column: str) -> pd.Series:
    y = x.copy()
    y[column] = y[column].str.title()
    return y


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
    def perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._remove_punc(token))
        return " ".join(new_text)

    def _remove_punc(self,text):
        return text.translate(str.maketrans('', '', string.punctuation))


class TransformationGenerator:
    def __init__(self, model, dataset):
        self.model = model
        self.dataset = dataset
        self.column_types = dataset.column_types
        self.text_perturbation_generator = TextTransformer()

    def generate_std_transformation(self, feature):
        mad = self.dataset.df[feature].mad()

        @transformation_function()
        def func(x: pd.Series) -> pd.Series:
            if self.column_types[feature] == "numeric":
                x[feature] += 3 * mad
                return x
            return x

        return func

    def text_transformation(self, feature):
        @transformation_function()
        def func(x: pd.Series) -> pd.Series:
            if self.column_types[feature] == 'text':
                self.text_perturbation_generator.load(x[feature])
                x[feature] = self.text_perturbation_generator.execute_protocol()
                return x

        return func

#
#
# # def tokenize(self):
# #     return self.nlp(self.text)
# def _switch_gender(token):
#     if token in masculine_to_feminine.keys():
#         switch_to = masculine_to_feminine[token]
#         return switch_to
#     elif token in feminine_to_masculine.keys():
#         switch_to = feminine_to_masculine[token]
#         return switch_to
#     else:
#         return token
#
# def _switch_minority(token):
#     if token in minority_groups:
#         switch_to = random.choice(minority_groups.remove(token))
#         return switch_to
#     else:
#         return token
#
# def _switch_religion(token):
#     token_low = token.lower()
#     for word_list in religion_dict.values():
#         if token_low in word_list:
#             word_list.remove(token_low)
#             switch_to_random_word = random.choice(word_list)
#             return switch_to_random_word
#     return token
