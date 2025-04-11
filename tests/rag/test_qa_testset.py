from giskard.datasets.base import Dataset
from giskard.rag import QATestset, QuestionSample


def make_testset_samples():
    return [
        QuestionSample(
            id="1",
            question="Which milk is used to make Camembert?",
            reference_answer="Cow's milk is used to make Camembert.",
            reference_context="Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
            conversation_history=[],
            metadata={
                "question_type": "simple",
                "color": "blue",
                "topic": "Cheese_1",
                "seed_document_id": "1",
            },
        ),
        QuestionSample(
            id="2",
            question="Where is Scarmorza from?",
            reference_answer="Scarmorza is from Southern Italy.",
            reference_context="Scamorza is a Southern Italian cow's milk cheese.",
            conversation_history=[],
            metadata={
                "question_type": "simple",
                "color": "red",
                "topic": "Cheese_1",
                "seed_document_id": "2",
            },
        ),
        QuestionSample(
            id="3",
            question="Where is Scarmorza from?",
            reference_answer="Scarmorza is from Southern Italy.",
            reference_context="Scamorza is a Southern Italian cow's milk cheese.",
            conversation_history=[],
            metadata={
                "question_type": "simple",
                "color": "blue",
                "topic": "Cheese_1",
                "seed_document_id": "2",
            },
        ),
        QuestionSample(
            id="4",
            question="Where is Scarmorza from?",
            reference_answer="Scarmorza is from Southern Italy.",
            reference_context="Scamorza is a Southern Italian cow's milk cheese.",
            conversation_history=[],
            metadata={
                "question_type": "complex",
                "color": "red",
                "topic": "Cheese_1",
                "seed_document_id": "2",
            },
        ),
        QuestionSample(
            id="5",
            question="Where is Scarmorza from?",
            reference_answer="Scarmorza is from Southern Italy.",
            reference_context="Scamorza is a Southern Italian cow's milk cheese.",
            conversation_history=[],
            metadata={
                "question_type": "distracting element",
                "color": "blue",
                "distracting_context": "This is a distracting context",
                "topic": "Cheese_2",
                "seed_document_id": "2",
            },
        ),
        QuestionSample(
            id="6",
            question="Where is it from?",
            reference_answer="Scarmorza is from Southern Italy.",
            reference_context="Scamorza is a Southern Italian cow's milk cheese.",
            conversation_history=[{"role": "user", "content": "Scamorza"}],
            metadata={
                "question_type": "conversational",
                "color": "blue",
                "distracting_context": "This is a distracting context",
                "topic": "Cheese_2",
                "seed_document_id": "2",
            },
        ),
    ]


def make_swedish_testset_samples():
    return [
        QuestionSample(
            id="1",
            question="Vilken mjölk används för att göra Camembert?",
            reference_answer="Komjölk används för att göra Camembert.",
            reference_context="Camembert är en fuktig, mjuk, krämig, ytmognad ost av komjölk.",
            conversation_history=[],
            metadata={
                "question_type": "enkel",
                "color": "blå",
                "topic": "Ost_1",
                "seed_document_id": "1",
            },
        ),
        QuestionSample(
            id="2",
            question="Varifrån kommer Scamorza?",
            reference_answer="Scamorza kommer från södra Italien.",
            reference_context="Scamorza är en ost av komjölk från södra Italien.",
            conversation_history=[],
            metadata={
                "question_type": "enkel",
                "color": "röd",
                "topic": "Ost_1",
                "seed_document_id": "2",
            },
        ),
    ]


def test_qa_testset_creation():
    question_samples = make_testset_samples()
    testset = QATestset(question_samples)

    assert testset._dataframe["metadata"].iloc[2] == {
        "question_type": "simple",
        "color": "blue",
        "topic": "Cheese_1",
        "seed_document_id": "2",
    }


def test_testset_to_pandas_conversion():
    testset = QATestset(make_testset_samples())

    df = testset.to_pandas()

    assert len(df) == 6

    df = testset.to_pandas(filters={"question_type": ["simple"]})
    assert len(df) == 3
    assert all(testset._dataframe["metadata"][idx]["question_type"] == "simple" for idx in df.index)

    df = testset.to_pandas(filters={"question_type": ["distracting element"]})
    assert len(df) == 1
    assert testset._dataframe["metadata"][df.index[0]]["question_type"] == "distracting element"
    assert testset._dataframe["metadata"][df.index[0]]["distracting_context"] == "This is a distracting context"


def test_testset_to_dataset_conversion():
    testset = QATestset(make_testset_samples())

    dataset = testset.to_dataset()

    assert dataset.name == "QA Testset"
    assert dataset._target is False
    assert isinstance(dataset, Dataset)

    testset = QATestset(make_testset_samples())

    dataset = testset.to_dataset(filters={"question_type": ["simple"]})
    assert len(dataset) == 3


def test_qa_testset_saving_loading(tmp_path):
    testset = QATestset(make_testset_samples())
    path = tmp_path / "testset.jsonl"
    testset.save(path)
    loaded_testset = QATestset.load(path)

    assert len(testset._dataframe) == len(loaded_testset._dataframe)
    assert all(
        [
            original == loaded
            for original, loaded in zip(testset._dataframe["metadata"], loaded_testset._dataframe["metadata"])
        ]
    )


def test_qa_testset_push_to_hf_hub(mocker):
    testset = QATestset(make_swedish_testset_samples())  # Use the swedish dataset for speed

    mock_push_to_hf_hub = mocker.patch("datasets.Dataset.push_to_hub")
    mock_dataset_card_push = mocker.patch("huggingface_hub.DatasetCard.push_to_hub")

    testset.push_to_hf_hub(repo_id="test-repo", token="fake-token", private=True, some_arg="value")

    mock_push_to_hf_hub.assert_called_once_with(
        "test-repo",
        token="fake-token",
        private=True,
        some_arg="value",
    )
    mock_dataset_card_push.assert_called_once_with(repo_id="test-repo", token="fake-token", repo_type="dataset")


def test_qa_testset_load_from_hf_hub(mocker):
    mock_load_dataset = mocker.patch("giskard.rag.testset.load_dataset")
    mock_load_dataset.return_value = [
        {
            "id": "1",
            "question": "Which milk is used to make Camembert?",
            "reference_answer": "Cow's milk is used to make Camembert.",
            "reference_context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
            "conversation_history": [],
            "metadata": {
                "question_type": "simple",
                "color": "blue",
                "topic": "Cheese_1",
                "seed_document_id": "1",
            },
        },
        {
            "id": "2",
            "question": "Where is Scarmorza from?",
            "reference_answer": "Scarmorza is from Southern Italy.",
            "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            "conversation_history": [],
            "metadata": {
                "question_type": "simple",
                "color": "red",
                "topic": "Cheese_1",
                "seed_document_id": "2",
            },
        },
    ]

    testset = QATestset.load_from_hf_hub(repo_id="test-repo", token="fake-token")

    assert len(testset.samples) == 2
    assert testset.samples[0].question == "Which milk is used to make Camembert?"
    assert testset.samples[0].metadata == {
        "question_type": "simple",
        "color": "blue",
        "topic": "Cheese_1",
        "seed_document_id": "1",
    }
    assert testset.samples[1].question == "Where is Scarmorza from?"
    assert testset.samples[1].metadata == {
        "question_type": "simple",
        "color": "red",
        "topic": "Cheese_1",
        "seed_document_id": "2",
    }
    mock_load_dataset.assert_called_once_with("test-repo", token="fake-token", split="train")


def test_qa_testset_saving_loading_swedish(tmp_path):
    testset = QATestset(make_swedish_testset_samples())
    path = tmp_path / "testset.jsonl"
    testset.save(path)
    loaded_testset = QATestset.load(path)

    assert all(
        [
            original == loaded
            for original, loaded in zip(testset._dataframe["metadata"], loaded_testset._dataframe["metadata"])
        ]
    )


def test_metadata_value_retrieval():
    testset = QATestset(make_testset_samples())

    assert testset.get_metadata_values("question_type") == [
        "complex",
        "conversational",
        "distracting element",
        "simple",
    ]
    assert testset.get_metadata_values("color") == ["blue", "red"]
    assert testset.get_metadata_values("distracting_context") == ["This is a distracting context"]


def test_testset_samples_property():
    testset = QATestset(make_testset_samples())

    assert len(testset.samples) == 6
    assert testset.samples[0].question == "Which milk is used to make Camembert?"
    assert testset.samples[0].conversation_history == []
    assert testset.samples[0].id == "1"
    assert testset.samples[0].metadata == {
        "question_type": "simple",
        "color": "blue",
        "topic": "Cheese_1",
        "seed_document_id": "1",
    }
    assert testset.samples[-1].question == "Where is it from?"
    assert testset.samples[-1].conversation_history == [{"role": "user", "content": "Scamorza"}]
    assert testset.samples[-1].id == "6"
    assert testset.samples[-1].metadata == {
        "question_type": "conversational",
        "color": "blue",
        "distracting_context": "This is a distracting context",
        "topic": "Cheese_2",
        "seed_document_id": "2",
    }
