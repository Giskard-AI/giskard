from giskard.rag.vector_store import Document


def test_single_feature_document_creation():
    doc = Document({"feature": "This a test value for a feature"})

    assert doc.page_content == "This a test value for a feature"
    assert doc.metadata == {"feature": "This a test value for a feature"}


def test_multiple_features_document_creation():
    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        }
    )
    assert (
        doc.page_content
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
    )
    assert doc.page_content == "This a test value for a feature 1"

    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        },
        features=["feat1", "feat2"],
    )
    assert doc.page_content == "feat1: This a test value for a feature 1\nfeat2: This a test value for a feature 2"

    doc = Document(
        {
            "feat1": "This a test value for a feature 1",
            "feat2": "This a test value for a feature 2",
            "feat3": "This a test value for a feature 3",
        },
        features=["feat4"],
    )
    assert (
        doc.page_content
        == "feat1: This a test value for a feature 1\nfeat2: This a test value for a feature 2\nfeat3: This a test value for a feature 3"
    )
