import pandas as pd

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
                "conversation_history": [],
                "metadata": {"question_type": 1, "color": "blue"},
            },
            {
                "id": "2",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [],
                "metadata": {"question_type": 1, "color": "red"},
            },
            {
                "id": "3",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [],
                "metadata": {"question_type": 1, "color": "blue"},
            },
            {
                "id": "4",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [],
                "metadata": {"question_type": 2, "color": "red"},
            },
            {
                "id": "5",
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": [],
                "metadata": {
                    "question_type": 3,
                    "color": "blue",
                    "distracting_context": "This is a distracting context",
                },
            },
            {
                "id": "6",
                "question": "Where is it from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
                "conversation_history": ["Scamorza"],
                "metadata": {
                    "question_type": 6,
                    "color": "blue",
                    "distracting_context": "This is a distracting context",
                },
            },
        ]
    ).set_index("id")


def test_qa_testset_creation():
    df = make_testset_df()
    testset = QATestset(df)

    assert testset._dataframe.equals(df)
    assert testset._dataframe["metadata"].iloc[2] == {"question_type": 1, "color": "blue"}


def test_testset_to_pandas_conversion():
    testset = QATestset(make_testset_df())

    df = testset.to_pandas()

    assert len(df) == 6

    df = testset.to_pandas(filters={"question_type": [1]})
    assert len(df) == 3
    assert all(testset._dataframe["metadata"][idx]["question_type"] == 1 for idx in df.index)

    df = testset.to_pandas(filters={"question_type": [3]})
    assert len(df) == 1
    assert testset._dataframe["metadata"][df.index[0]]["question_type"] == 3
    assert testset._dataframe["metadata"][df.index[0]]["distracting_context"] == "This is a distracting context"


def test_testset_to_dataset_conversion():
    testset = QATestset(make_testset_df())

    dataset = testset.to_dataset()

    assert dataset.name == "QA Testset"
    assert dataset._target is False
    assert isinstance(dataset, Dataset)

    testset = QATestset(make_testset_df())

    dataset = testset.to_dataset(filters={"question_type": [1]})
    assert len(dataset) == 3


def test_qa_testset_saving_loading(tmp_path):
    testset = QATestset(make_testset_df())
    path = tmp_path / "testset.jsonl"
    testset.save(path)
    loaded_testset = QATestset.load(path)

    assert len(testset._dataframe) == len(loaded_testset._dataframe)
    assert testset._dataframe["metadata"].equals(loaded_testset._dataframe["metadata"])


def test_metadata_value_retrieval():
    testset = QATestset(make_testset_df())

    assert testset.get_metadata_values("question_type") == [1, 2, 3, 6]
    assert testset.get_metadata_values("color") == ["blue", "red"]
    assert testset.get_metadata_values("distracting_context") == ["This is a distracting context"]
