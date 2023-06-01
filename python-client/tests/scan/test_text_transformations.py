import pandas as pd
from giskard import Dataset


def _dataset_from_dict(data):
    return Dataset(pd.DataFrame(data), target=None)


def test_gender_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "We just got this and my daughter loves it. She has played it several times.",
                "It did not work.",
                "“They pushed the feature just 1 minute before the user test”",
                "He hates doing user tests!",
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextGenderTransformation

    t = TextGenderTransformation(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.str.lower().values
    assert transformed_text[0] == "We just got this and my son loves it. He has played it several times.".lower()
    assert transformed_text[1] == "It did not work.".lower()
    assert transformed_text[2] == "“They pushed the feature just 1 minute before the user test”".lower()
    assert transformed_text[3] == "She hates doing user tests!".lower()


def test_uppercase_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "My lowercase text.",
                "My lowercase TEXT with greek letters α, β, γ",
                "Another text with → unicode ← characters 😀",
                "“And… punctuation! all should be fine — I hope!?”",
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextUppercase

    t = TextUppercase(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert transformed_text[0] == "MY LOWERCASE TEXT."
    assert transformed_text[1] == "MY LOWERCASE TEXT WITH GREEK LETTERS Α, Β, Γ"
    assert transformed_text[2] == "ANOTHER TEXT WITH → UNICODE ← CHARACTERS 😀"
    assert transformed_text[3] == "“AND… PUNCTUATION! ALL SHOULD BE FINE — I HOPE!?”"


def test_lowercase_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "My UPPERCASE text.",
                "My UPPERCASE TEXT with greek letters α, β, γ, Γ",
                "Another TEXT with → UNICODE ← characters 😀",
                "“And… PUNCTUATION! all SHOULD be fine — I HOPE!?”",
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextLowercase

    t = TextLowercase(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert transformed_text[0] == "my uppercase text."
    assert transformed_text[1] == "my uppercase text with greek letters α, β, γ, γ"
    assert transformed_text[2] == "another text with → unicode ← characters 😀"
    assert transformed_text[3] == "“and… punctuation! all should be fine — i hope!?”"


def test_punctuation_strip_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "My UPPERCASE text.",
                "My UPPERCASE TEXT with greek letters α, β, γ, Γ",
                "Another @TEXT with → $UNICODE$ ← characters 😀",
                "“And… PUNCTUATION! all SHOULD be fine — I HOPE!?”",
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextPunctuationRemovalTransformation

    t = TextPunctuationRemovalTransformation(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert transformed_text[0] == "My UPPERCASE text"
    assert transformed_text[1] == "My UPPERCASE TEXT with greek letters α β γ Γ"
    assert transformed_text[2] == "Another TEXT with → $UNICODE$ ← characters 😀"
    assert transformed_text[3] == "And PUNCTUATION all SHOULD be fine  I HOPE"
