import pandas as pd

from giskard.slicing.slice import ContainsWord, Query, QueryBasedSliceFunction, GreaterThan, LowerThan, EqualTo


def test_simple_comparison_query():
    df = pd.DataFrame({"feature 1": [2, 4, 10, 2, 8], "feature with special chars'\"£££££": ["a", "b", "c", "d", "e"]})

    q = QueryBasedSliceFunction(Query([LowerThan("feature 1", 5)]))

    res = q.execute(df)
    assert res.columns.tolist() == ["feature 1", "feature with special chars'\"£££££"]
    assert len(res) == 3
    assert res["feature 1"].tolist() == [2, 4, 2]
    assert res["feature with special chars'\"£££££"].tolist() == ["a", "b", "d"]

    q = QueryBasedSliceFunction(Query([GreaterThan("feature 1", 8, True)]))

    res = q.execute(df)
    assert len(res) == 2
    assert res["feature 1"].tolist() == [10, 8]


def test_equality_comparison_query():
    df = pd.DataFrame(
        {"feature 1": [2, 4, 10, 2, 8], "feature with special @chars`'\"£££££": ["a", "b@'\"£££££", "c", "d", "e"]}
    )

    q = QueryBasedSliceFunction(Query([EqualTo("feature with special @chars`'\"£££££", "b@'\"£££££")]))

    res = q.execute(df)
    assert len(res) == 1


def _make_text_df(texts):
    return pd.DataFrame({"feature": texts})


def test_contains_word_clause():
    expected = {
        "this is a test": True,
        "test this": True,
        "in the test middle": True,
        "testing the feature": False,
        "Test, now with punctuation": True,
        "UPPERCASE TEST!": True,
        "Test-this": True,
        "And test!": True,
        "Not containing anything": False,
    }
    df = _make_text_df(expected.keys())
    clause = ContainsWord("feature", "tEst")

    assert clause.mask(df).tolist() == list(expected.values())
