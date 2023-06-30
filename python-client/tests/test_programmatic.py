import pytest

from giskard import test, scan
from giskard.core.suite import Suite, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction, slicing_function
from giskard.ml_worker.testing.test_result import TestMessageLevel
from giskard.models.base import BaseModel
from giskard.testing.tests.performance import test_auc, test_f1, test_diff_f1


@test()
def _test_a_greater_b(a: int, b: int):
    return a > b


def test_a_greater_b_fail():
    passed, _ = Suite().add_test(_test_a_greater_b(1, 2)).run()
    assert not passed


def test_a_greater_b_pass():
    passed, _ = Suite().add_test(_test_a_greater_b(2, 1)).run()
    assert passed


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
    passed, _ = Suite().add_test(_test_a_greater_b()).run(a=2, b=1)
    assert passed


def test_argument_overriden():
    passed, _ = Suite().add_test(_test_a_greater_b(a=1, b=2)).run(a=3)
    assert passed


def test_multiple(german_credit_data: Dataset, german_credit_model: BaseModel):
    assert (
        Suite()
        .add_test(test_auc(threshold=0.2))
        .add_test(test_f1(threshold=0.2))
        .run(dataset=german_credit_data, model=german_credit_model)[0]
    )


def test_all_inputs_exposed_and_shared(german_credit_data, german_credit_model):
    assert (
        Suite()
        .add_test(test_auc())
        .add_test(test_f1())
        .add_test(_test_a_greater_b())
        .run(dataset=german_credit_data, model=german_credit_model, threshold=0.2, a=2, b=1)[0]
    )


def test_shared_input(german_credit_model: BaseModel, german_credit_data: Dataset):
    last_half = german_credit_data.slice(SlicingFunction(lambda df: df.tail(len(df) // 2), row_level=False))

    shared_input = SuiteInput("dataset", Dataset)

    assert (
        Suite()
        .add_test(test_auc(dataset=shared_input, threshold=0.2))
        .add_test(test_f1(dataset=shared_input, threshold=0.2))
        .add_test(test_diff_f1(threshold=0.2, actual_dataset=shared_input))
        .run(model=german_credit_model, dataset=german_credit_data, reference_dataset=last_half)[0]
    )


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

    assert result[0]
    assert len(result[1]) == 3


def test_giskard_test_class(german_credit_data: Dataset, german_credit_model: BaseModel):
    shared_input = SuiteInput("dataset", Dataset)

    assert (
        Suite()
        .add_test(test_auc(dataset=shared_input, threshold=0.2))
        .run(model=german_credit_model, dataset=german_credit_data)[0]
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

    assert result[0] is False
    assert result[1][0][1].passed is False
    assert result[1][0][1].is_error is True
    assert result[1][0][1].messages[0].type is TestMessageLevel.ERROR
    assert "The sliced dataset in test_f1 is empty." in result[1][0][1].messages[0].text
    assert result[1][1][1].passed is True
    assert result[1][1][1].is_error is False


def test_save_suite(german_credit_data: Dataset, german_credit_model: BaseModel):
    # with MockedClient() as (client, mr):
    #     Suite().add_test(test_auc(threshold=0.2, dataset=german_credit_data)).add_test(
    #         test_f1(threshold=0.2, dataset=german_credit_data)
    #     ).upload(client, "test_project_key")
    scan(german_credit_model, german_credit_data)


# def test_save_suite_real(german_credit_data: Dataset, german_credit_model: BaseModel):
#     from giskard.client.giskard_client import GiskardClient
#     client = GiskardClient("http://localhost:9000",
#                            "")
#
#     german_credit_data.upload(client, 'test')
#     german_credit_model.upload(client, 'test')
#
#     Suite(name="Test Suite 1") \
#         .add_test(test_auc, threshold=0.2, dataset=german_credit_data) \
#         .add_test(test_f1, threshold=0.2, dataset=german_credit_data) \
#         .save(client, 'credit')
