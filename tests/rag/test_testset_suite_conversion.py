import pandas as pd

from giskard.rag import QATestset


def make_testset_df():
    return pd.DataFrame(
        [
            {
                "question": "Which milk is used to make Camembert?",
                "reference_answer": "Cow's milk is used to make Camembert.",
                "reference_context": "Camembert is a moist, soft, creamy, surface-ripened cow's milk cheese.",
            },
            {
                "question": "Where is Scarmorza from?",
                "reference_answer": "Scarmorza is from Southern Italy.",
                "reference_context": "Scamorza is a Southern Italian cow's milk cheese.",
            },
        ]
    )


def test_testset_suite_conversion():
    testset = QATestset(make_testset_df())
    suite = testset.to_test_suite()

    assert "dataset" in suite.default_params
    assert suite.default_params["dataset"].df.loc[0, "question"] == "Which milk is used to make Camembert?"
    assert (
        suite.default_params["dataset"].df.loc[1, "reference_context"]
        == "Scamorza is a Southern Italian cow's milk cheese."
    )

    assert len(suite.tests) == 1
    assert suite.tests[0].display_name == "TestsetCorrectnessTest"
