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


def test_number_to_words_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "We have scheduled the meeting for 12/15/2023 at our office.",  # Don't transform dates
                "You can access the report at https://www.example123.com/report2023.",  # Don't transform URLs
                "The serial number of the device is XC1234-AB56. Please send your queries to contact123@service4u.com.",  # Don't transform emails
                "The dataset contains approximately 1500 entries spanning 5 years.",
                "The total cost of the project is estimated to be around $4,500.75.",
                "For more information, call us at +1-800-555-0199.",
                "Der Zug soll um 09:45 Uhr ankommen.",  # German
                "Die Gesamtkosten der Artikel betragen 45,67 Dollar.",  # German
                "La tasa de éxito de este procedimiento es del 98,6%.",  # Spanish
                "Hoy corrió 13,2 millas en el maratón.",  # Spanish
                "Son anniversaire est le 22 du mois.",  # French
                "Le coût total des articles était de 157,23 $.",  # French
            ]
        }
    )

    from giskard.scanner.robustness.text_transformations import TextNumberToWordTransformation

    t = TextNumberToWordTransformation(column="text")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values[:6]
    # English tests
    assert transformed_text[0] == "We have scheduled the meeting for 12/15/2023 at our office."
    assert transformed_text[1] == "You can access the report at https://www.example123.com/report2023."
    assert (
        transformed_text[2]
        == "The serial number of the device is XC1234-AB56. Please send your queries to contact123@service4u.com."
    )
    assert (
        transformed_text[3]
        == "The dataset contains approximately one thousand, five hundred entries spanning five years."
    )
    assert (
        transformed_text[4]
        == "The total cost of the project is estimated to be around $four,five hundred point seven five."
    )
    assert (
        transformed_text[5]
        == "For more information, call us at +one-eight hundred-five hundred and fifty-five-one hundred and ninety-nine."
    )

    # German tests
    t = TextNumberToWordTransformation(column="text", lang="de")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values[6:8]
    assert transformed_text[0] == "Der Zug soll um neun:fünfundvierzig Uhr ankommen."
    assert transformed_text[1] == "Die Gesamtkosten der Artikel betragen fünfundvierzig,siebenundsechzig Dollar."

    # Spanish tests
    t = TextNumberToWordTransformation(column="text", lang="es")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values[8:10]
    assert transformed_text[0] == "La tasa de éxito de este procedimiento es del noventa y ocho,seis%."
    assert transformed_text[1] == "Hoy corrió trece,dos millas en el maratón."

    # French tests
    t = TextNumberToWordTransformation(column="text", lang="fr")

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values[10:12]
    assert transformed_text[0] == "Son anniversaire est le vingt-deux virgule zéro huit du mois."
    assert transformed_text[1] == "Le coût total des articles était de cent cinquante-sept,vingt-trois $."


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

    t = TextReligionTransformation(column="text", rng_seed=10)

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert (
        transformed_text[0] == "Les hindous de France fêtent vendredi 21 avril la fin du jeûne pratiqué durant le "
        "mois de ramadan."
    )
    assert (
        transformed_text[1] == "Une partie des hindous commémorent ce vendredi 5 mai la naissance, l’éveil et la "
        "mort de abraham, dit « le Bouddha »"
    )
    assert (
        transformed_text[2] == "Signs have also been placed in the direction of kumbh mela along one of the Peak "
        "District’s most popular hiking routes, Cave Dale, to help jews combine prayer "
        "with enjoying the outdoors."
    )
    assert (
        transformed_text[3] == "The vatican is said to be the largest gathering in the world and is a blend of "
        "religion spirituality, mythology and culture"
    )


def test_country_based_transformation():
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

    t = TextNationalityTransformation(column="text", rng_seed=0)

    transformed = dataset.transform(t)
    transformed_text = transformed.df.text.values

    assert (
        transformed_text[0] == "Les musulmans de Saint Thomas et Prince fêtent vendredi 21 avril la fin du "
        "jeûne pratiqué durant le mois de ramadan."
    )
    assert transformed_text[1] == "Des incendies ravagent l'Liban depuis la fin août 2019."
    assert (
        transformed_text[2] == "Bali is an Singaporean island known for its forested volcanic mountains, iconic"
        " rice paddies, beaches and coral reefs. The island is home to religious sites "
        "such as cliffside Uluwatu Temple"
    )
    assert (
        transformed_text[3]
        == "President Joe Biden visited UAE's capital for the first time since Syria invaded the country"
    )


def test_country_based_transformation_edge_cases():
    from giskard.scanner.robustness.text_transformations import TextNationalityTransformation

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

    t = TextNationalityTransformation(column="text", rng_seed=0)

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
