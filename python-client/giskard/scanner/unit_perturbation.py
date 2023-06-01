import pandas as pd
from giskard.ml_worker.testing.registry.transformation_function import transformation_function
import random
import spacy


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


class TextTransformer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.text = None

    def load(self, text):
        self.text = text

    def execute_protocol(self):
        self._replace_by_mask()  # replace proper noun, gender,ethnicity,location by a mask
        return self.text
    def tokenize(self):
        return self.nlp(self.text)
    def _replace_by_mask(self):
        doc = self.tokenize()
        new_text = []
        for token in doc:
            if token.ent_type_ == "GPE":
                new_text.append("[LOCATION]")
            elif token.ent_type_ == "NORP":
                new_text.append("[ETHNICITY]")
            elif token.tag_ == "PRP" or token.tag_ == "PRP$":  # PRP$
                new_text.append("[GENDER]")
            elif token.tag_ == "PROPN":
                new_text.append("[PROPER NOUN]")
            else:
                # Tranformation suite
                text_transformed = str(token.text)
                text_transformed = self.add_typos(text_transformed)
                text_transformed = self.char_perturbation(text_transformed)
                text_transformed = self.title_case(text_transformed)
                text_transformed = self.word_perturbation(text_transformed)
                new_text.append(str(text_transformed))
        return " ".join(new_text)

    def char_perturbation(self, text):
        # Get the token's text and apply a perturbation with probability 0.1
        if random.random() < 0.1:
            # Choose a perturbation type randomly
            perturbation_type = random.choice(['insert', 'delete', 'replace'])
            # Apply the perturbation
            if perturbation_type == 'insert':
                idx = random.randint(0, len(text))
                new_char = chr(random.randint(33, 126))
                text = text[:idx] + new_char + text[idx:]
                return text
            elif perturbation_type == 'delete':
                idx = random.randint(0, len(text) - 1)
                text = text[:idx] + text[idx + 1:]
                return text
            elif perturbation_type == 'replace':
                idx = random.randint(0, len(text) - 1)
                new_char = chr(random.randint(33, 126))
                text = text[:idx] + new_char + text[idx + 1:]
                return text
        return text

    def word_perturbation(self, text):
        if random.random() < 0.05:  # 5% of the words
            # Choose a text augmentation operation randomly
            op = random.choice(['delete', 'replace'])  # ['delete', 'add', 'swap'], 'swap'

            # Delete the word
            if op == 'delete':
                if len(text) > 1:
                    return ""

            # Replace the word by another random word
            elif op == 'replace':
                # Choose a random word from the vocabulary
                new_word = str(random.choice(list(self.nlp.vocab.strings)))
                return new_word

    def upper_case(self, text):
        return text.upper()

    def lower_case(self, text):
        return text.lower()

    def title_case(self, text):
        return text.title()

    def add_typos(self, text):
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
        if random.random() < 0.2:  # 10% chance of introducing a typo
            if len(text) > 1:
                j = random.randint(0, len(text) - 1)
                c = text[j]
                if c in typos:
                    replacement = random.choice(typos[c])
                    text_modified = text[:j] + replacement + text[j + 1:]
                    return text_modified

        return text
