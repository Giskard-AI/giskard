import pandas as pd
from giskard import wrap_dataset


def _dataset_from_dict(data):
    return wrap_dataset(pd.DataFrame(data), target=None)


def test_gender_transformation():
    dataset = _dataset_from_dict(
        {
            "text": [
                "We just got this and my daughter loves it. She has played it several times.",
                "It did not work",
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
