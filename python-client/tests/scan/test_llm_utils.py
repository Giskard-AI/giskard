from giskard.scanner.llm.utils import load_default_dataset


def test_default_dataset_loader():
    dataset = load_default_dataset()

    assert dataset.columns.tolist() == ["type", "question", "best_answer"]
    assert dataset.column_types["type"] == "category"
    assert dataset.column_types["question"] == "text"
    assert dataset.column_types["best_answer"] == "text"
    assert len(dataset.df) > 100
