from giskard.rag import QATestset
from tests.rag.test_qa_testset import make_testset_df


def test_testset_suite_conversion():
    testset = QATestset(make_testset_df())
    suite = testset.to_test_suite()

    assert "dataset" in suite.default_params
    assert suite.default_params["dataset"].df.iloc[0]["question"] == "Which milk is used to make Camembert?"
    assert (
        suite.default_params["dataset"].df.iloc[1]["reference_context"]
        == "Scamorza is a Southern Italian cow's milk cheese."
    )

    assert len(suite.tests) == 1
    assert suite.tests[0].display_name == "TestsetCorrectnessTest"


def test_testset_suite_conversion_with_metadata():
    testset = QATestset(make_testset_df())
    suite = testset.to_test_suite(slicing_metadata=["question_type"])

    assert len(suite.tests) == 3
    assert suite.tests[0].display_name == "TestsetCorrectnessTest_question_type_1"

    assert len(suite.tests[0].provided_inputs["dataset"].df) == 3
    assert len(suite.tests[1].provided_inputs["dataset"].df) == 1
    assert len(suite.tests[2].provided_inputs["dataset"].df) == 1

    suite = testset.to_test_suite(slicing_metadata=["question_type", "color"])
    assert len(suite.tests) == 5

    assert suite.tests[3].display_name == "TestsetCorrectnessTest_color_blue"
    assert len(suite.tests[3].provided_inputs["dataset"].df) == 3
    assert suite.tests[4].display_name == "TestsetCorrectnessTest_color_red"
    assert len(suite.tests[4].provided_inputs["dataset"].df) == 2
