import itertools
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from num2words import num2words

from ...core.core import DatasetProcessFunctionMeta
from ...datasets import Dataset
from ...functions.transformation import gruber
from ...registry.registry import get_object_uuid
from ...registry.transformation_function import TransformationFunction


class TextTransformation(TransformationFunction):
    name: str

    def __init__(self, column, needs_dataset=False):
        super().__init__(None, row_level=False, cell_level=False, needs_dataset=needs_dataset)
        self.column = column
        self.meta = DatasetProcessFunctionMeta(type="TRANSFORMATION")
        self.meta.uuid = get_object_uuid(self)
        self.meta.code = self.name
        self.meta.name = self.name
        self.meta.display_name = self.name
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = self.meta.default_doc("Automatically generated transformation function")

    def __str__(self):
        return self.name

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.apply(self.make_perturbation)
        return data

    def make_perturbation(self, text: str) -> str:
        raise NotImplementedError()


class TextUppercase(TextTransformation):
    name = "Transform to uppercase"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.upper()
        return data


class TextLowercase(TextTransformation):
    name = "Transform to lowercase"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.lower()
        return data


class TextTitleCase(TextTransformation):
    name = "Transform to title case"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.title()
        return data


class TextTypoTransformation(TextTransformation):
    name = "Add typos"

    def __init__(self, column, rate=0.05, min_length=10, rng_seed=1729):
        super().__init__(column)
        from .entity_swap import typos

        self.rate = rate
        self.min_length = min_length
        self._key_typos = typos
        self.rng = np.random.default_rng(seed=rng_seed)

    def make_perturbation(self, x):
        # Skip if the text is too short
        if len(x) < self.min_length:
            return x

        # We consider four types of typos:
        # - Insertion
        # - Deletion
        # - Replacement
        # - Transposition

        # Empirical probabilities for each category
        category_prob = [0.2, 0.2, 0.5, 0.1]

        # How many typos we generate and in which positions
        num_typos = self.rng.poisson(self.rate * len(re.sub(r"\s+", "", x)))

        # Are they insertion, deletion, replacement, or transposition?
        pos_cat = self.rng.choice(4, size=num_typos, p=category_prob, replace=True)

        for cat in pos_cat:
            # get a random position
            i = self.rng.integers(0, len(x))

            if cat == 0:  # insertion
                t = self._random_key_typo(x[i])
                x = x[:i] + t + x[i:]
            elif cat == 1:  # deletion
                if x[i].isspace():  # don’t delete spaces
                    i = min(i + 1, len(x) - 1)
                x = x[:i] + x[i + 1 :]
            elif cat == 2:  # replacement
                x = x[:i] + self._random_key_typo(x[i]) + x[i + 1 :]
            else:  # transposition
                if i < len(x) - 1:
                    x = x[:i] + x[i + 1] + x[i] + x[i + 2 :]
        return x

    def _random_key_typo(self, char):
        if char.lower() in self._key_typos:
            typo = self.rng.choice(self._key_typos[char.lower()])
            return typo if char.islower() else typo.upper()
        return char


class TextFromOCRTypoTransformation(TextTransformation):
    name = "Add typos from OCR"

    def __init__(self, column, rate=0.05, min_length=10, rng_seed=1729):
        super().__init__(column)
        from .entity_swap import ocr_typos

        self.rate = rate
        self.min_length = min_length
        self._ocr_typos = ocr_typos
        self.rng = np.random.default_rng(seed=rng_seed)

    def make_perturbation(self, x):
        # Check if the input is None
        if x is None:
            return None
        # Skip if the text is too short
        if len(x) < self.min_length:
            return x

        # OCR typos consist only of replacements and deletions
        category_prob = [0.8, 0.2]  # Probability [replacement, deletion]

        # How many typos to introduce
        num_typos = self.rng.poisson(self.rate * len(re.sub(r"\s+", "", x)))

        # Are they replacement or deletion?
        pos_cat = self.rng.choice(2, size=num_typos, p=category_prob, replace=True)

        for cat in pos_cat:
            # Get a random position avoiding spaces for deletion
            i = self.rng.integers(0, len(x))
            if cat == 0:  # Replacement
                if x[i].lower() in self._ocr_typos:
                    x = x[:i] + self._random_ocr_typo(x[i]) + x[i + 1 :]
            elif cat == 1:  # Deletion
                if not x[i].isspace():  # Don’t delete spaces
                    x = x[:i] + x[i + 1 :]
        return x

    def _random_ocr_typo(self, char):
        if char.lower() in self._ocr_typos:
            typo = self.rng.choice(self._ocr_typos[char.lower()])
            return typo if char.islower() else typo.upper()
        return char


class TextPunctuationRemovalTransformation(TextTransformation):
    name = "Punctuation Removal"

    _punctuation = "¡!¿?⸘‽“”‘’‛‟.,‚„'\"′″´˝`…:;­–‑—§¶†‡/-‒‼︎⁇⁈⁉︎❛❜❝❞"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._trans_table = str.maketrans("", "", self._punctuation)
        self._regex = re.compile(rf"\b[{re.escape(self._punctuation)}]+\b")

    def make_perturbation(self, text):
        # Split URLs so that they are not affected by the transformation
        pieces = gruber.split(text)

        # Non-URLs are even-numbered entries
        for i in range(0, len(pieces), 2):
            # Replace punctuation at boundaries with a space, so that we don't
            # accidentally join words together. Then strip the rest.
            pieces[i] = self._regex.sub(" ", pieces[i]).translate(self._trans_table)

        return "".join(pieces)


class TextAccentRemovalTransformation(TextTransformation):
    name = "Accent Removal"

    def __init__(self, column, rate=1.0, rng_seed=1729):
        super().__init__(column)
        self.rate = rate
        self.rng = np.random.default_rng(seed=rng_seed)

    def make_perturbation(self, text):
        return "".join(
            char
            for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn" or self.rng.random() > self.rate
        )


class TextLanguageBasedTransformation(TextTransformation):
    def __init__(self, column, rng_seed=1729):
        super().__init__(column, needs_dataset=True)
        self._lang_dictionary = dict()
        self._load_dictionaries()
        self.rng = np.random.default_rng(seed=rng_seed)

    def _load_dictionaries(self):
        raise NotImplementedError()

    def execute(self, dataset: Dataset) -> pd.DataFrame:
        feature_data = dataset.df.loc[:, (self.column,)].dropna().astype(str)
        meta_dataframe = dataset.column_meta[self.column, "text"].add_suffix("__gsk__meta")
        feature_data = feature_data.join(meta_dataframe)
        dataset.df.loc[feature_data.index, self.column] = feature_data.apply(self.make_perturbation, axis=1)
        return dataset.df

    def make_perturbation(self, row):
        raise NotImplementedError()

    def _switch(self, word, language):
        raise NotImplementedError()

    def _select_dict(self, language):
        try:
            return self._lang_dictionary[language]
        except KeyError:
            return None


class TextGenderTransformation(TextLanguageBasedTransformation):
    name = "Switch Gender"

    def _load_dictionaries(self):
        from .entity_swap import gender_switch_en, gender_switch_fr

        self._lang_dictionary = {"en": gender_switch_en, "fr": gender_switch_fr}

    def make_perturbation(self, row):
        text = row[self.column]
        language = row["language__gsk__meta"]

        if language not in self._lang_dictionary:
            return text

        replacements = [self._switch(token, language) for token in text.split()]
        replacements = [r for r in replacements if r is not None]

        new_text = text
        for original_word, switched_word in replacements:
            new_text = re.sub(rf"\b{re.escape(original_word)}\b", switched_word, new_text)

        return new_text

    def _switch(self, word, language):
        try:
            return (word, self._lang_dictionary[language][word.lower()])
        except KeyError:
            return None


class TextNumberToWordTransformation(TextLanguageBasedTransformation):
    name = "Transform numbers to words"

    def _load_dictionaries(self):
        # Regex to match numbers in text
        self._regex = re.compile(r"(?<!\d/)(?<!\d\.)\b\d+(?:\.\d+)?\b(?!(?:\.\d+)?@|\d?/?\d)")

    def make_perturbation(self, row):
        # Replace numbers with words
        value = row[self.column]
        if pd.isna(value):
            return value
        lang = row["language__gsk__meta"] if not pd.isna(row["language__gsk__meta"]) else "en"

        if lang == "fa" or lang == "id":
            # In num2words, the convertor of "fa" and "id" are buggy,
            # see https://github.com/savoirfairelinux/num2words/issues/476
            # Give up doing this now, wait for merging https://github.com/savoirfairelinux/num2words/pull/524
            return value

        try:
            return self._regex.sub(lambda x: num2words(x.group(), lang=lang), value)
        except NotImplementedError:
            # Fallback to english in case of unimplemented
            return self._regex.sub(lambda x: num2words(x.group(), lang="en"), value)


class TextReligionTransformation(TextLanguageBasedTransformation):
    name = "Switch Religion"

    def _load_dictionaries(self):
        from .entity_swap import religion_dict_en, religion_dict_fr

        self._lang_dictionary = {"en": religion_dict_en, "fr": religion_dict_fr}

    def make_perturbation(self, row):
        # Get text
        text = row[self.column]

        # Get language and corresponding dictionary
        language = row["language__gsk__meta"]
        religion_dict = self._select_dict(language)

        # Check if we support this language
        if religion_dict is None:
            return text

        # Mask entities and prepare replacements
        replacements = []
        for n_list, term_list in enumerate(religion_dict):
            for n_term, term in enumerate(term_list):
                mask_value = f"__GSK__ENT__RELIGION__{n_list}__{n_term}__"
                text, num_rep = re.subn(rf"\b{re.escape(term)}(s?)\b", rf"{mask_value}\1", text, flags=re.IGNORECASE)
                if num_rep > 0:
                    i = (n_term + 1 + self.rng.choice(len(term_list) - 1)) % len(term_list)
                    replacement = term_list[i]
                    replacements.append((mask_value, replacement))

        # Replace masks
        for mask, replacement in replacements:
            text = text.replace(mask, replacement)

        return text


class TextNationalityTransformation(TextLanguageBasedTransformation):
    name = "Switch countries from high- to low-income and vice versa"

    def _load_dictionaries(self):
        with Path(__file__).parent.joinpath("nationalities.json").open("r") as f:
            nationalities_dict = json.load(f)
        self._lang_dictionary = {"en": nationalities_dict["en"], "fr": nationalities_dict["fr"]}

    def make_perturbation(self, row):
        text = row[self.column]
        language = row["language__gsk__meta"]
        nationalities_word_dict = self._select_dict(language)

        if nationalities_word_dict is None:
            return text

        ent_types = list(itertools.product(["country", "nationality"], ["high-income", "low-income"]))

        # Mask entities and prepare replacements
        replacements = []
        for entity_type, income_type in ent_types:
            for n, entity_word in enumerate(nationalities_word_dict[entity_type][income_type]):
                mask_value = f"__GSK__ENT__{entity_type}__{income_type}__{n}__"
                text, num_rep = re.subn(
                    rf"(\W|^){re.escape(entity_word)}(\W|$)",
                    rf"\g<1>{mask_value}\g<2>",
                    text,
                    flags=re.IGNORECASE,
                )
                if num_rep > 0:
                    r_income_type = "low-income" if income_type == "high-income" else "high-income"
                    replacement = self.rng.choice(nationalities_word_dict[entity_type][r_income_type])
                    replacements.append((mask_value, replacement))

        # Replace masks
        for mask, replacement in replacements:
            text = text.replace(mask, replacement)

        return text


class TextFromSpeechTypoTransformation(TextLanguageBasedTransformation):
    name = "Add text from speech typos"

    def __init__(self, column, rng_seed=1729, min_length=10):
        super().__init__(column, rng_seed=rng_seed)

        self.min_length = min_length

    def _load_dictionaries(self):
        from .entity_swap import speech_typos

        self._word_typos = speech_typos

    def make_perturbation(self, row):
        text = row[self.column]
        language = row["language__gsk__meta"]

        # Skip if the text is too short
        if len(text) < self.min_length:
            return text
        # Skip if language isn't supported
        if language != "en":
            return text

        # We are considering homophones
        # Split the input text by spaces to get the words
        words = text.split()
        transformed_words = []

        # Iterate over each word in the input text
        for word in words:
            # Normalize the word to handle cases
            normalized_word = word.lower()

            # Check if the current word is present in _word_typos dictionary
            if normalized_word in self._word_typos:
                # Choose a random typo for the current word
                typo_options = self._word_typos[normalized_word]
                chosen_typo = self.rng.choice(typo_options)

                # Retain original word case
                if word.istitle():
                    chosen_typo = chosen_typo.capitalize()
                elif word.isupper():
                    chosen_typo = chosen_typo.upper()
                else:
                    # Keep typo as it is in the typo dictionary
                    pass

                # Append the typo to the transformed words list
                transformed_words.append(chosen_typo)
            else:
                # The word is not in the dictionary, keep it as is
                transformed_words.append(word)

        # Reconstruct the transformed text from the words
        transformed_text = " ".join(transformed_words)
        return transformed_text
