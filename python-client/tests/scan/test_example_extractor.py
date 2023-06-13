from unittest.mock import MagicMock
from giskard.scanner.common.examples import ExampleExtractor
from giskard.scanner.issues import Issue


def _make_issue_mock(model, dataset):
    issue = MagicMock(Issue)
    issue.model = model
    issue.dataset = dataset
    issue.features = ["Subject", "Content"]
    issue.slicing_fn = None
    issue.transformation_fn = None
    return issue


def test_example_extractor_returns_n_examples(enron_model, enron_data):
    issue = _make_issue_mock(enron_model, enron_data)
    extractor = ExampleExtractor(issue)
    df = extractor.get_examples_dataframe(n=10)

    assert len(df) == 10

    df = extractor.get_examples_dataframe(n=1)

    assert len(df) == 1


def test_example_extractor_selects_features(enron_model, enron_data):
    issue = _make_issue_mock(enron_model, enron_data)
    extractor = ExampleExtractor(issue)
    df = extractor.get_examples_dataframe()

    assert "Subject" in df.columns
    assert "Content" in df.columns
    assert "Year" not in df.columns


def test_example_extractor_returns_prediction(enron_model, enron_data):
    issue = _make_issue_mock(enron_model, enron_data)
    extractor = ExampleExtractor(issue)

    df = extractor.get_examples_dataframe(with_prediction=0)

    assert "Predicted `Target`" not in df.columns

    df = extractor.get_examples_dataframe(with_prediction=1)

    assert "Predicted `Target`" in df.columns
    assert "p = " in df["Predicted `Target`"].iloc[0]

    df = extractor.get_examples_dataframe(with_prediction=3)

    assert "Predicted `Target`" in df.columns
    assert (
        df["Predicted `Target`"].iloc[0] == "REGULATION (p = 0.48)\nINTERNAL (p = 0.20)\nCALIFORNIA CRISIS (p = 0.12)"
    )
