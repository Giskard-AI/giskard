import pandas as pd
import pytest

from giskard.datasets.base import Dataset
from giskard.rag import QATestset


def make_testset_df():
    return pd.DataFrame(
        [
            {
                "id": "1",
                "question": "Which milk is used to make Camembert?",
                "reference_answer": "Cow's milk is used to make Camembert.",
                "reference_context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
            },
            {
                "id": "2",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            },
            {
                "id": "3",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            },
            {
                "id": "4",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            },
            {
                "id": "5",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            },
        ]
    ).set_index("id")


def make_metadata():
    return {
        "1": {"difficulty": 1, "color": "blue"},
        "2": {"difficulty": 1, "color": "red"},
        "3": {"difficulty": 1, "color": "blue"},
        "4": {"difficulty": 2, "color": "red"},
        "5": {"difficulty": 3, "color": "blue", "distracting_context": "This is a distracting context"},
    }


def test_qa_testset_creation():
    df = make_testset_df()
    testset = QATestset(df)

    assert testset._dataframe.equals(df)

    metadata = make_metadata()
    testset = QATestset(df, metadata)
    assert testset._metadata == metadata

    with pytest.raises(ValueError, match="At least one metadata id is not in the dataframe index."):
        testset = QATestset(df.drop("3"), metadata)

    with pytest.raises(ValueError, match="At least one dataframe id is not in the metadata."):
        del metadata["1"]
        testset = QATestset(df, metadata)


def test_testset_to_pandas_conversion():
    testset = QATestset(make_testset_df(), make_metadata())

    df = testset.to_pandas()

    assert len(df) == 5

    df = testset.to_pandas(filters={"difficulty": [1]})
    assert len(df) == 3
    assert all(testset._metadata[idx]["difficulty"] == 1 for idx in df.index)

    df = testset.to_pandas(filters={"difficulty": [3]})
    assert len(df) == 1
    assert testset._metadata[df.index[0]]["difficulty"] == 3
    assert testset._metadata[df.index[0]]["distracting_context"] == "This is a distracting context"


def test_testset_to_dataset_conversion():
    testset = QATestset(make_testset_df())

    dataset = testset.to_dataset()

    assert dataset.name == "QA Testset"
    assert dataset._target is False
    assert isinstance(dataset, Dataset)

    testset = QATestset(make_testset_df(), make_metadata())

    dataset = testset.to_dataset(filters={"difficulty": [1]})
    assert len(dataset) == 3


def test_qa_testset_saving_loading(tmp_path):
    testset = QATestset(make_testset_df(), make_metadata())
    path = tmp_path / "testset.jsonl"
    testset.save(path)
    loaded_testset = QATestset.load(path)

    assert len(testset._dataframe) == len(loaded_testset._dataframe)
    assert testset._metadata == loaded_testset._metadata


def test_metadata_value_retrieval():
    testset = QATestset(make_testset_df(), make_metadata())

    assert testset.get_metadata_values("difficulty") == [1, 2, 3]
    assert testset.get_metadata_values("color") == ["blue", "red"]
    assert testset.get_metadata_values("distracting_context") == ["This is a distracting context"]
