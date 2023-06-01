import pytest

from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
from giskard.ml_worker.core.suite import Suite, SuiteInput
from giskard.ml_worker.testing.tests.performance import test_auc, test_f1, test_diff_f1, AucTest
from tests.utils import MockedClient


def _test_dataset_size(ds: Dataset, threshold):
    print("Running test_dataset_size")
    return len(ds.df) > threshold


def _test_a_greater_b(a: int, b: int):
    return a > b


def test_a_greater_b_fail():
    passed, _ = Suite().add_test(_test_a_greater_b, a=1, b=2).run()
    assert not passed


def test_a_greater_b_pass():
    passed, _ = Suite().add_test(_test_a_greater_b, a=2, b=1).run()
    assert passed


def test_missing_arg():
    with pytest.raises(Exception, match="Missing 1 required parameters: {'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b, a=2).run()


def test_missing_args():
    with pytest.raises(Exception, match="Missing 2 required parameters: {'a': <class 'int'>, 'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b).run()


def test_missing_arg_one_global():
    with pytest.raises(Exception, match="Missing 1 required parameters: {'b': <class 'int'>}"):
        Suite().add_test(_test_a_greater_b).run(a=2)


def test_all_global():
    passed, _ = Suite().add_test(_test_a_greater_b).run(a=2, b=1)
    assert passed


def test_multiple(german_credit_data: Dataset, german_credit_model: BaseModel):
    assert (
        Suite()
        .add_test(test_auc, threshold=0.2)
        .add_test(test_f1, threshold=0.2)
        .run(actual_slice=german_credit_data, model=german_credit_model)[0]
    )


def test_all_inputs_exposed_and_shared(german_credit_data, german_credit_model):
    assert (
        Suite()
        .add_test(test_auc)
        .add_test(test_f1)
        .add_test(_test_a_greater_b)
        .run(actual_slice=german_credit_data, model=german_credit_model, threshold=0.2, a=2, b=1)[0]
    )


def test_shared_input(german_credit_data: Dataset, german_credit_model: BaseModel):
    first_half = german_credit_data.slice(lambda df: df.head(len(df) // 2))
    last_half = german_credit_data.slice(lambda df: df.tail(len(df) // 2))

    shared_input = SuiteInput("dataset", Dataset)

    assert (
        Suite()
        .add_test(test_auc, actual_slice=shared_input, threshold=0.2)
        .add_test(test_f1, actual_slice=shared_input, threshold=0.2)
        .add_test(test_diff_f1, threshold=0.2)
        .run(model=german_credit_model, dataset=german_credit_data, actual_slice=first_half, reference_slice=last_half)[
            0
        ]
    )


def test_multiple_execution_of_same_test(german_credit_data: Dataset, german_credit_model: BaseModel):
    first_half = german_credit_data.slice(lambda df: df.head(len(df) // 2))
    last_half = german_credit_data.slice(lambda df: df.tail(len(df) // 2))

    shared_input = SuiteInput("dataset", Dataset)

    result = Suite() \
        .add_test(test_auc, actual_slice=shared_input, threshold=0.2) \
        .add_test(test_auc, actual_slice=shared_input, threshold=0.25) \
        .add_test(test_auc, actual_slice=shared_input, threshold=0.3) \
        .run(model=german_credit_model, dataset=german_credit_data, actual_slice=first_half, reference_slice=last_half)

    assert result[0]
    assert len(result[1].items()) == 3


def test_giskard_test_class(german_credit_data: Dataset, german_credit_model: BaseModel):
    shared_input = SuiteInput("dataset", Dataset)

    assert (
        Suite()
        .add_test(AucTest(actual_slice=shared_input, threshold=0.2))
        .run(model=german_credit_model, dataset=german_credit_data)[0]
    )


def test_save_suite(german_credit_data: Dataset, german_credit_model: BaseModel):
    with MockedClient() as (client, mr):
        Suite().add_test(test_auc, threshold=0.2, actual_slice=german_credit_data).add_test(
            test_f1, threshold=0.2, actual_slice=german_credit_data
        ).save(client, "test_project_key")

# def test_save_suite_real(german_credit_data: Dataset, german_credit_model: BaseModel):
#    client = GiskardClient("http://localhost:9000", "")
#
#    Suite(name="Test Suite 1") \
#        .add_test(test_auc, threshold=0.2, actual_slice=german_credit_data) \
#        .add_test(test_f1, threshold=0.2, actual_slice=german_credit_data) \
#        .save(client, 'credit')
