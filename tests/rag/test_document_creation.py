import pytest

from giskard.rag.knowledge_base import Document


def test_single_feature_document_creation():
    doc = Document({"feature": "This a test value for a feature"}, idx=1)

    assert doc.content == "This a test value for a feature"
    assert doc.metadata == {"feature": "This a test value for a feature"}
    assert doc.id == 1


def test_multiple_features_document_creation():
    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        },
        idx=1,
    )
    assert (
        doc.content
        == "feat1: This a test value for a feature 1\nfeat2: This a test value for a feature 2\nfeat3: This a test value for a feature 3"
    )
    assert doc.metadata == {
        "feat1": "This a test value for a feature 1",
        "feat2": "This a test value for a feature 2",
        "feat3": "This a test value for a feature 3",
    }

    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        },
        features=["feat1"],
        idx=2,
    )
    assert doc.content == "This a test value for a feature 1"

    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        },
        features=["feat1", "feat2"],
        idx=3,
    )
    assert doc.content == "feat1: This a test value for a feature 1\nfeat2: This a test value for a feature 2"

    with pytest.raises(KeyError):
        doc = Document(
            {
                "feat1": "This a test value for a feature 1",
                "feat2": "This a test value for a feature 2",
                "feat3": "This a test value for a feature 3",
            },
            features=["feat4"],
            idx=4,
        )
