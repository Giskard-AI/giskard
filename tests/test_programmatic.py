import pytest

from giskard import scan, test
from giskard.core.suite import Suite, SuiteInput
from giskard.core.test_result import TestMessageLevel
from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel
from giskard.registry.slicing_function import SlicingFunction, slicing_function
from giskard.testing.tests.performance import test_auc, test_diff_f1, test_f1


def _assert_html_generation_does_no_fail(test_suite_result):
    try:
        test_suite_result._repr_html_()
    except:  # noqa
        assert False, "An error arose when trying to generate html for test_suite_result"


@test()
def _test_a_greater_b(a: int, b: int):
    return a > b


class CustomClass:
    def __init__(self, val: int):
        self.val = val


@test()
def _test_with_custom_types(a: CustomClass, b: CustomClass):
    return a.val > b.val


def test_a_greater_b_fail():
    test_suite_result = Suite().add_test(_test_a_greater_b(1, 2)).run()

    assert not test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_a_greater_b_pass():
    test_suite_result = Suite().add_test(_test_a_greater_b(2, 1)).run()

    assert test_suite_result.passed
    _assert_html_generation_does_no_fail(test_suite_result)


def test_missing_arg():
    with pytest.warns(match="Missing 1 required parameters: {'b': <class 'int'>}"):
        result = Suite().add_test(_test_a_greater_b(a=2)).run()

        assert not result.passed

        assert len(result.results) == 1
        _, test_result, _ = result.results[0]
        assert "1 validation error" in test_result.messages[0].text


def test_missing_args():
    with pytest.warns(match="Missing 2 required parameters: {'a': <class 'int'>, 'b': <class 'int'>}"):
        result = Suite().add_test(_test_a_greater_b()).run()

        assert not result.passed

        assert len(result.results) == 1
        _, test_result, _ = result.results[0]
        assert test_result.is_error
        assert "2 validation errors" in test_result.messages[0].text


def test_missing_arg_one_global():
    with pytest.warns(match="Missing 1 required parameters: {'b': <class 'int'>}"):
        result = Suite().add_test(_test_a_greater_b()).run(a=2)

        assert not result.passed

        assert len(result.results) == 1
        _, test_result, _ = result.results[0]
        assert test_result.is_error
        assert "1 validation error" in test_result.messages[0].text, test_result.messages[0].text


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


def test_with_custom_types():
    result = _test_with_custom_types(CustomClass(2), CustomClass(3)).execute()
    assert not result

    result = _test_with_custom_types(b=CustomClass(2), a=CustomClass(3)).execute()
    assert result


def test_upgrade_test_with_migration():
    @test(name="Named test")
    def my_named_test(is_pass: bool):
        return is_pass

    suite = Suite().add_test(my_named_test(True), "True").add_test(my_named_test(False), "False")

    assert len(suite.tests) == 2
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test.meta.uuid
    assert suite.tests[0].provided_inputs == {"is_pass": True}
    assert suite.tests[1].test_id == "False"
    assert suite.tests[1].giskard_test.meta.uuid == my_named_test.meta.uuid
    assert suite.tests[1].provided_inputs == {"is_pass": False}

    @test(name="Named test")
    def my_named_test_v2(passed: bool):
        return passed

    suite.upgrade_test(my_named_test_v2, lambda params: {"passed": params["is_pass"]})

    assert len(suite.tests) == 2
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test_v2.meta.uuid
    assert suite.tests[0].provided_inputs == {"passed": True}
    assert suite.tests[1].test_id == "False"
    assert suite.tests[1].giskard_test.meta.uuid == my_named_test_v2.meta.uuid
    assert suite.tests[1].provided_inputs == {"passed": False}


def test_upgrade_test_without():
    @test(name="Named test")
    def my_named_test(is_pass: bool):
        return is_pass

    suite = Suite().add_test(my_named_test(True), "True")

    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test.meta.uuid
    assert suite.tests[0].provided_inputs == {"is_pass": True}

    @test(name="Named test")
    def my_named_test_v2(passed: bool):
        return passed

    suite.upgrade_test(my_named_test_v2)

    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test_v2.meta.uuid
    assert suite.tests[0].provided_inputs == {"is_pass": True}


def test_upgrade_test_not_matching():
    @test(name="Named test")
    def my_named_test(is_pass: bool):
        return is_pass

    suite = Suite().add_test(my_named_test(True), "True")

    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test.meta.uuid
    assert suite.tests[0].provided_inputs == {"is_pass": True}

    @test(name="Named test V2")
    def my_named_test_v2(passed: bool):
        return passed

    suite.upgrade_test(my_named_test_v2)

    assert len(suite.tests) == 1
    assert suite.tests[0].test_id == "True"
    assert suite.tests[0].giskard_test.meta.uuid == my_named_test.meta.uuid
    assert suite.tests[0].provided_inputs == {"is_pass": True}
