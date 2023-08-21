import random
import re

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
                "He hates doing user tests! for his company",
                "Il déteste faire les tests en langue française",
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
    assert transformed_text[3] == "She hates doing user tests! for her company".lower()
    assert transformed_text[4] == "Elle déteste faire les tests en langue français".lower()


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
                "This.., is my site.. http://www.example.com/, and ., it .,.,. http://stackoverflow.com rules!..",
                "comma,separated,list",
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextPunctuationRemovalTransformation

    t = TextPunctuationRemovalTransformation(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert transformed_text[0] == "My UPPERCASE text"
    assert transformed_text[1] == "My UPPERCASE TEXT with greek letters α β γ Γ"
    assert transformed_text[2] == "Another @TEXT with → $UNICODE$ ← characters 😀"
    assert transformed_text[3] == "And PUNCTUATION all SHOULD be fine  I HOPE"
    assert transformed_text[4] == "This is my site http://www.example.com/ and  it  http://stackoverflow.com rules"
    assert transformed_text[5] == "comma separated list"


def test_religion_based_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "Les musulmans de France fêtent vendredi 21 avril la fin du jeûne pratiqué durant le mois de ramadan.",
                "Une partie des bouddhistes commémorent ce vendredi 5 mai la naissance, l’éveil et la mort de "
                "Siddhartha gautama, dit « le Bouddha »",
                "Signs have also been placed in the direction of Mecca along one of the Peak District’s most popular "
                "hiking routes, Cave Dale, to help Muslims combine prayer with enjoying the outdoors.",
                "The Kumbh Mela is said to be the largest gathering in the world and is a blend of religion "
                "spirituality, mythology and culture",
            ]
        }
    )
    from giskard.scanner.robustness.text_transformations import TextReligionTransformation

    t = TextReligionTransformation(column="text")

    random.seed(0)
    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert (
        transformed_text[0] == "Les hindous de France fêtent vendredi 21 avril la fin du jeûne pratiqué durant le "
        "mois de ramadan."
    )
    assert (
        transformed_text[1] == "Une partie des chrétiens commémorent ce vendredi 5 mai la naissance, l’éveil et la "
        "mort de muhammad, dit « le Bouddha »"
    )
    assert (
        transformed_text[2] == "Signs have also been placed in the direction of kumbh mela along one of the Peak "
        "District’s most popular hiking routes, Cave Dale, to help christians combine prayer "
        "with enjoying the outdoors."
    )
    assert (
        transformed_text[3] == "The vatican is said to be the largest gathering in the world and is a blend of "
        "religion spirituality, mythology and culture"
    )


def test_country_based_transformation():
    import random

    random.seed(10)
    dataset = _dataset_from_dict(
        {
            "text": [
                "Les musulmans de France fêtent vendredi 21 avril la fin du jeûne pratiqué durant le mois de ramadan.",
                "Des incendies ravagent l'Australie depuis la fin août 2019.",
                "Bali is an Indonesian island known for its forested volcanic mountains, iconic rice paddies, "
                "beaches and coral reefs. The island is home to religious sites such as cliffside Uluwatu Temple",
                "President Joe Biden visited Ukraine's capital for the first time since Russia invaded the country",
            ]
        }
    )
    from giskard.scanner.robustness.text_transformations import TextNationalityTransformation

    t = TextNationalityTransformation(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert (
        transformed_text[0] == "Les musulmans de Eswatini fêtent vendredi 21 avril la fin du "
        "jeûne pratiqué durant le mois de ramadan."
    )
    assert transformed_text[1] == "Des incendies ravagent l'Congo depuis la fin août 2019."
    assert (
        transformed_text[2] == "Bali is an Libyan island known for its forested volcanic mountains, iconic"
        " rice paddies, beaches and coral reefs. The island is home to religious sites "
        "such as cliffside Uluwatu Temple"
    )
    assert (
        transformed_text[3]
        == "President Joe Biden visited U.S.'s capital for the first time since Nigeria invaded the country"
    )


def test_country_based_transformation_edge_cases():
    from giskard.scanner.robustness.text_transformations import TextNationalityTransformation

    random.seed(0)
    df = pd.DataFrame(
        {
            "text": [
                "Countries like Italy, that are followed by punctuation",
                "Germany is at the beginning of the sentence",
                "And at the end is Sweden",
                "France",
            ],
            "language__gsk__meta": "en",
        }
    )

    t = TextNationalityTransformation(column="text")

    t1 = t.make_perturbation(df.iloc[0])
    t2 = t.make_perturbation(df.iloc[1])
    t3 = t.make_perturbation(df.iloc[2])
    t4 = t.make_perturbation(df.iloc[3])

    assert re.match(r"Countries like (.+), that are followed by punctuation", t1).group(1) != "Italy"
    assert re.match(r"(.+) is at the beginning of the sentence", t2).group(1) != "Germany"
    assert re.match(r"And at the end is (.+)", t3).group(1) != "Sweden"
    assert "France" not in t4


def test_country_based_transformation_escapes_special_chars():
    from giskard.scanner.robustness.text_transformations import TextNationalityTransformation

    df = pd.DataFrame(
        {
            "text": [
                "Things like UXSX should not be touched",
                "Same for U0KX!",
                "But U.S. should be replaced",
                "And also U.K., that must be replaced",
            ],
            "language__gsk__meta": "en",
        }
    )

    t = TextNationalityTransformation(column="text")

    assert t.make_perturbation(df.iloc[0]) == "Things like UXSX should not be touched"
    assert t.make_perturbation(df.iloc[1]) == "Same for U0KX!"
    assert t.make_perturbation(df.iloc[2]) != "But U.S. should be replaced"
    assert t.make_perturbation(df.iloc[3]) != "And also U.K., that must be replaced"


def test_typo_transformation():
    from giskard.scanner.robustness.text_transformations import TextTypoTransformation

    t = TextTypoTransformation(column="text", rng_seed=1)
    p = t.make_perturbation("If one doesn't know his mistakes, he won't want to correct them.")

    assert p == "If one doesn't know his misakes, he won't want to corrcet them."
