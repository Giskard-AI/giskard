import pandas as pd

from giskard.datasets import Dataset


def test_dataset_language_exhaustive_text_column_extraction():
    df = pd.DataFrame(
        {
            "col1": [
                "How does deforestation contribute to climate change according to IPCC reports?",
                "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique?",
                "¿Cuál es el papel de los gases de efecto invernadero en el calentamiento global?",
            ],
            "col2": [
                "Proč zpráva IPCC naznačuje, že lidské aktivity nejsou hlavní příčinou klimatických změn?",
                "CAT1",
                "CAT2",
            ],
            "col3": [0, 1, 2],
        }
    )

    dataset = Dataset(df, column_types={"col1": "text", "col2": "category"}, target="col3")
    languages = dataset.extract_languages()
    languages.sort()
    assert languages == ["en", "es", "fr"]

    dataset = Dataset(df, column_types={"col1": "text", "col2": "text"}, target="col3")
    languages = dataset.extract_languages()
    languages.sort()
    assert languages == ["cs", "en", "es", "fr"]


def test_dataset_language_when_empty():
    df = pd.DataFrame(
        {
            "col1": [
                "How does deforestation contribute to climate change according to IPCC reports?",
                "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique?",
                "¿Cuál es el papel de los gases de efecto invernadero en el calentamiento global?",
            ],
            "col2": ["CAT0", "CAT1", "CAT2"],
            "col3": [0, 1, 2],
            "col4": [3, 4, 5],
        }
    )

    dataset = Dataset(df, column_types={"col1": "category", "col2": "text", "col3": "text"}, target="col4")
    languages = dataset.extract_languages()
    languages.sort()
    assert languages == []

    df = pd.DataFrame(
        {
            "col1": [
                "How does deforestation contribute to climate change according to IPCC reports?",
                "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique?",
                "¿Cuál es el papel de los gases de efecto invernadero en el calentamiento global?",
            ],
            "col2": [None, "CAT1", "CAT2"],
            "col3": ["Bonjour", None, None],
            "col4": [3, 4, 5],
        }
    )

    dataset = Dataset(df, column_types={"col1": "category", "col2": "text", "col3": "text"}, target="col4")
    languages = dataset.extract_languages()
    languages.sort()
    assert languages == []


def test_dataset_language_column_filtering():
    df = pd.DataFrame(
        {
            "col1": [
                "How does deforestation contribute to climate change according to IPCC reports?",
                "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique?",
                "¿Cuál es el papel de los gases de efecto invernadero en el calentamiento global?",
            ],
            "col2": [
                "Proč zpráva IPCC naznačuje, že lidské aktivity nejsou hlavní příčinou klimatických změn?",
                "CAT1",
                "CAT2",
            ],
            "col3": [0, 1, 2],
            "col4": [3, 4, 5],
        }
    )

    dataset = Dataset(df, column_types={"col1": "text", "col2": "text", "col3": "numeric"}, target="col4")
    languages = dataset.extract_languages(columns=["col2"])
    languages.sort()
    assert languages == ["cs"]

    dataset = Dataset(df, column_types={"col1": "text", "col2": "text", "col3": "numeric"}, target="col4")
    languages = dataset.extract_languages(columns=["col1", "col2"])
    languages.sort()
    assert languages == ["cs", "en", "es", "fr"]

    dataset = Dataset(df, column_types={"col1": "text", "col2": "text", "col3": "numeric"}, target="col4")
    languages = dataset.extract_languages(columns=["col3"])
    languages.sort()
    assert languages == []

    dataset = Dataset(df, column_types={"col1": "text", "col2": "text", "col3": "numeric"}, target="col4")
    languages = dataset.extract_languages(columns=["col4"])
    languages.sort()
    assert languages == []
