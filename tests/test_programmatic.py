import pytest

from giskard import test, scan
from giskard.core.suite import Suite, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction, slicing_function
from giskard.ml_worker.testing.test_result import TestMessageLevel
from giskard.models.base import BaseModel
from giskard.testing.tests.performance import test_auc, test_f1, test_diff_f1


def _assert_html_generation_does_no_fail(test_suite_result):
    try:
        test_suite_result._repr_html_()
    except:  # noqa
        assert False, "An error arose when trying to generate html for test_suite_result"


@test()
def _test_a_greater_b(a: int, b: int):
    return a > b


def test_a_greater_b_fail():
    test_suite_result = Suite().add_test(_test_a_greater_b(1, 2)).run()

    assert not test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_a_greater_b_pass():
    test_suite_result = Suite().add_test(_test_a_greater_b(2, 1)).run()

    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_missing_arg():
    with pytest.raises(Exception, match="Missing 1 required parameters: {'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b(a=2)).run()


def test_missing_args():
    with pytest.raises(Exception, match="Missing 2 required parameters: {'a': <class 'int'>, 'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b()).run()


def test_missing_arg_one_global():
    with pytest.raises(Exception, match="Missing 1 required parameters: {'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b()).run(a=2)


def test_all_global():
    test_suite_result = Suite().add_test(_test_a_greater_b()).run(a=2, b=1)

    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_argument_not_overriden():
    test_suite_result = Suite().add_test(_test_a_greater_b(a=1, b=2)).run(a=3)

    assert not test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_multiple(german_credit_data: Dataset, german_credit_model: BaseModel):
    test_suite_result = (
        Suite()
        .add_test(test_auc(threshold=0.2))
        .add_test(test_f1(threshold=0.2))
        .run(dataset=german_credit_data, model=german_credit_model)
    )

    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_all_inputs_exposed_and_shared(german_credit_data, german_credit_model):
    test_suite_result = (
        Suite()
        .add_test(test_auc())
        .add_test(test_f1())
        .add_test(_test_a_greater_b())
        .run(dataset=german_credit_data, model=german_credit_model, threshold=0.2, a=2, b=1)
    )

    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_shared_input(german_credit_model: BaseModel, german_credit_data: Dataset):
    last_half = german_credit_data.slice(SlicingFunction(lambda df: df.tail(len(df) // 2), row_level=False))

    shared_input = SuiteInput("dataset", Dataset)

    test_suite_result = (
        Suite()
        .add_test(test_auc(dataset=shared_input, threshold=0.2))
        .add_test(test_f1(dataset=shared_input, threshold=0.2))
        .add_test(test_diff_f1(threshold=0.2, actual_dataset=shared_input))
        .run(model=german_credit_model, dataset=german_credit_data, reference_dataset=last_half)
    )
    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_multiple_execution_of_same_test(german_credit_data: Dataset, german_credit_model: BaseModel):
    first_half = german_credit_data.slice(SlicingFunction(lambda df: df.head(len(df) // 2), row_level=False))
    last_half = german_credit_data.slice(SlicingFunction(lambda df: df.tail(len(df) // 2), row_level=False))

    shared_input = SuiteInput("dataset", Dataset)

    result = (
        Suite()
        .add_test(test_auc(dataset=shared_input, threshold=0.2))
        .add_test(test_auc(dataset=shared_input, threshold=0.25))
        .add_test(test_auc(dataset=shared_input, threshold=0.3))
        .run(
            model=german_credit_model,
            dataset=german_credit_data,
            actual_dataset=first_half,
            reference_dataset=last_half,
        )
    )

    assert result.passed
    assert len(result.results) == 3
    _assert_html_generation_does_no_fail(result)


def test_giskard_test_class(german_credit_data: Dataset, german_credit_model: BaseModel):
    shared_input = SuiteInput("dataset", Dataset)

    assert (
        Suite()
        .add_test(test_auc(dataset=shared_input, threshold=0.2))
        .run(model=german_credit_model, dataset=german_credit_data)
        .passed
    )


def test_execution_error(german_credit_data: Dataset, german_credit_model: BaseModel):
    shared_input = SuiteInput("dataset", Dataset)

    @slicing_function(row_level=False)
    def empty_slice(x):
        return x.iloc[[]]

    result = (
        Suite()
        .add_test(test_f1(dataset=shared_input, threshold=0.2, slicing_function=empty_slice))
        .add_test(test_f1(dataset=shared_input, threshold=0.2))
        .run(model=german_credit_model, dataset=german_credit_data)
    )

    assert result.passed is False
    results = result.results
    assert results[0][1].passed is False
    assert results[0][1].is_error is True
    assert results[0][1].messages[0].type is TestMessageLevel.ERROR
    assert "The sliced dataset in test_f1 is empty." in results[0][1].messages[0].text
    assert results[1][1].passed is True
    assert results[1][1].is_error is False

    _assert_html_generation_does_no_fail(result)


def test_save_suite(german_credit_data: Dataset, german_credit_model: BaseModel):
    # with MockedClient() as (client, mr):
    #     Suite().add_test(test_auc(threshold=0.2, dataset=german_credit_data)).add_test(
    #         test_f1(threshold=0.2, dataset=german_credit_data)
    #     ).upload(client, "test_project_key")
    scan(german_credit_model, german_credit_data)


def test_remove_by_id():
    suite = Suite().add_test(test_f1, "F1").add_test(test_auc, "AUC").add_test(test_diff_f1, "Diff F1")

    assert len(suite.tests) == 3
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "AUC"
    assert suite.tests[2].test_id == "Diff F1"

    suite.remove_test(1)
    assert len(suite.tests) == 2
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "Diff F1"

    suite.remove_test(-1)
    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "F1"


def test_remove_by_name():
    suite = Suite().add_test(test_f1, "F1").add_test(test_auc, "AUC").add_test(test_diff_f1, "Diff F1")

    assert len(suite.tests) == 3
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "AUC"
    assert suite.tests[2].test_id == "Diff F1"

    suite.remove_test("AUC")
    assert len(suite.tests) == 2
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "Diff F1"

    suite.remove_test("AUC")
    assert len(suite.tests) == 2

    suite.remove_test("Diff F1")
    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "F1"


def test_remove_by_reference():
    suite = Suite().add_test(test_f1, "F1").add_test(test_auc, "AUC").add_test(test_diff_f1, "Diff F1")

    assert len(suite.tests) == 3
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "AUC"
    assert suite.tests[2].test_id == "Diff F1"

    suite.remove_test(test_auc)
    assert len(suite.tests) == 2
    assert suite.tests[0].test_id == "F1"
    assert suite.tests[1].test_id == "Diff F1"

    suite.remove_test(test_auc)
    assert len(suite.tests) == 2

    suite.remove_test(test_diff_f1)
    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "F1"


def test_update_params():
    suite = Suite().add_test(_test_a_greater_b(1, 2))

    assert not suite.run().passed

    suite.update_test_params(0, a=3)

    assert suite.run().passed


@pytest.mark.skip(reason="For active testing")
def test_save_suite_real_debug(german_credit_data: Dataset, german_credit_model: BaseModel):
    from giskard.testing import test_metamorphic_invariance, test_auc, test_diff_accuracy
    from giskard import transformation_function, slicing_function
    import pandas as pd

    @transformation_function
    def transform(df: pd.Series) -> pd.Series:
        df["age"] = df["age"] + 10
        return df

    @slicing_function(row_level=False, name="DF Head")
    def slice(df: pd.DataFrame) -> pd.DataFrame:
        return df.head()

    from giskard.client.giskard_client import GiskardClient

    client = GiskardClient("http://localhost:9000", "API_KEY")
    client.create_project("test_debug", "test_debug", "test_debug")

    german_credit_data.upload(client, "test_debug")
    german_credit_data_actual = german_credit_data.copy()
    german_credit_data_actual.df = german_credit_data.df.head(100)
    german_credit_data_actual.upload(client, "test_debug")

    german_credit_data_reference = german_credit_data.copy()
    german_credit_data_reference.df = german_credit_data.df.tail(100)
    german_credit_data_reference.upload(client, "test_debug")

    german_credit_model.upload(client, "test_debug")
    invariance = test_metamorphic_invariance(
        model=german_credit_model, threshold=0.2, dataset=german_credit_data, transformation_function=transform
    )

    auc = test_auc(model=german_credit_model, threshold=0.2, dataset=german_credit_data, slicing_function=slice)

    diff_accuracy = test_diff_accuracy(
        model=german_credit_model,
        threshold=0.2,
        actual_dataset=german_credit_data_actual,
        reference_dataset=german_credit_data_reference,
    )

    Suite(name="Test Suite 1").add_test(auc).add_test(diff_accuracy).add_test(invariance).upload(client, "test_debug")
