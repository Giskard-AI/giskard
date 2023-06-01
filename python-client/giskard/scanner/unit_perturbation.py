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
        self.replace()  # replace proper noun, gender,ethnicity,location by a mask
        # self.char_perturbation()  # 10% of the words for each sentence
        # self.word_perturbation()  # 10% of the words for each sentence
        self.title_case()
        self.upper_case()
        self.lower_case()
        # @TODO: Change the functions so it doesn't take to much time to run
        return self.text

    def replace(self):
        self.text = self._replace_by_mask(["GPE", "NORP", "PRP", "PROPN"])

    def _replace_by_mask(self, tag_list):
        doc = self.nlp(self.text)
        new_text = []
        for token in doc:
            if token.ent_type_ == "GPE" and "GPE" in tag_list:
                new_text.append("[LOCATION]")
            elif token.ent_type_ == "NORP" and "NORP" in tag_list:
                new_text.append("[ETHNICITY]")
            elif (token.tag_ == "PRP" or token.tag_ == "PRP$") and "PRP" in tag_list:  # PRP$
                new_text.append("[GENDER]")
            elif token.tag_ == "PROPN" and "PROPN" in tag_list:
                new_text.append("[PROPER NOUN]")
            else:
                new_text.append(str(token.text))
        return " ".join(new_text)

    def char_perturbation(self):
        """
        Perform a character-level perturbation attack on the input text by adding or deleting random characters, and
        perform a typo attack on the input text.
        """
        # Split the text into tokens
        tokens = self.text.split()

        # Loop over the tokens in the document
        for i in range(len(tokens)):
            # Get the token's text and apply a perturbation with probability 0.1
            if random.random() < 0.1:
                # Choose a perturbation type randomly
                perturbation_type = random.choice(['insert', 'delete', 'replace'])

                # Apply the perturbation
                if perturbation_type == 'insert':
                    idx = random.randint(0, len(tokens[i]))
                    new_char = chr(random.randint(33, 126))
                    tokens[i] = tokens[i][:idx] + new_char + tokens[i][idx:]
                elif perturbation_type == 'delete':
                    idx = random.randint(0, len(tokens[i]) - 1)
                    tokens[i] = tokens[i][:idx] + tokens[i][idx + 1:]
                elif perturbation_type == 'replace':
                    idx = random.randint(0, len(tokens[i]) - 1)
                    new_char = chr(random.randint(33, 126))
                    tokens[i] = tokens[i][:idx] + new_char + tokens[i][idx + 1:]

        # Return the modified text as a string
        self.text = ' '.join(tokens)

    def word_perturbation(self):
        """
        Perform random text augmentation by deleting a word, adding a random word, or swapping two words in the input text.
        """
        # Tokenize the input text into words
        words = self.text.split()

        for i in range(len(words)):
            if random.random() < 0.1:
                # Choose a text augmentation operation randomly
                op = random.choice(['delete', 'add', 'swap'])  # ['delete', 'add', 'swap']

                # Delete a random word from the text
                if op == 'delete':
                    if len(words) > 1:
                        # Choose a random word in the document (excluding the first word)
                        word_idx = random.randint(1, len(words) - 1)
                        # Delete the selected word
                        words.pop(word_idx)

                # Add a random word to the text
                elif op == 'add':
                    # Choose a random word from the vocabulary
                    new_word = str(random.choice(list(self.nlp.vocab.strings)))
                    word_idx = random.randint(0, len(words))
                    words.insert(word_idx, new_word)

                # Swap two random words in the text
                elif op == 'swap':
                    if len(words) > 1:
                        # Choose two random words in the document (excluding the first word)
                        word_idx_1 = random.randint(1, len(words) - 1)
                        word_idx_2 = random.randint(1, len(words) - 1)
                        # Swap the selected words
                        words[word_idx_1], words[word_idx_2] = words[word_idx_2], words[word_idx_1]

        # Return the modified text as a string
        self.text = ' '.join(words)

    def upper_case(self):
        self.text = self.text.upper()

    def lower_case(self):
        self.text = self.text.lower()

    def title_case(self):
        self.text = self.text.title()

    def add_typos(self):
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
        words = self.text.split(" ")

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

        self.text = text

# text = "She her the brown fox jumps over the lazy dog in Sydney, was christian"
# text_perturbation_generator = TextTransformer()
# print(text_perturbation_generator.replace_gender(text))
# print(text_perturbation_generator.replace_loc(text))
# print(text_perturbation_generator.replace_ethnicity(text))
# print(text_perturbation_generator.lower_case(text))
# print(text_perturbation_generator.upper_case(text))
# print(text_perturbation_generator.title_case(text))
# print(text_perturbation_generator.word_perturbation(text))
# print(text_perturbation_generator.char_perturbation(text))
# print( [method for method in dir(text_perturbation_generator)
#                                 if callable(getattr(text_perturbation_generator, method))
#                                 and not method.startswith("__")
#         and not method.startswith("_")])
