import pytest

from giskard import test, scan
from giskard.core.suite import Suite, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
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


def test_save_suite(german_credit_data: Dataset, german_credit_model: BaseModel):
    # with MockedClient() as (client, mr):
    #     Suite().add_test(test_auc(threshold=0.2, dataset=german_credit_data)).add_test(
    #         test_f1(threshold=0.2, dataset=german_credit_data)
    #     ).upload(client, "test_project_key")
    scan(german_credit_model, german_credit_data)


@pytest.mark.skip(reason="For active testing")
def test_save_suite_real_debug(german_credit_data: Dataset, german_credit_model: BaseModel):
    from giskard.testing import test_metamorphic_invariance, test_auc, test_diff_accuracy
    from giskard import transformation_function, slicing_function
    import pandas as pd

    @transformation_function
    def transform(df: pd.Series) -> pd.Series:
        df['age'] = df['age'] + 10
        return df

    @slicing_function(row_level=False, name='DF Head')
    def slice(df: pd.DataFrame) -> pd.DataFrame:
        return df.head()

    from giskard.client.giskard_client import GiskardClient
    client = GiskardClient("http://localhost:9000", "API_KEY")
    client.create_project("test_debug", "test_debug", "test_debug")

    german_credit_data.upload(client, 'test_debug')
    german_credit_data_actual = german_credit_data.copy()
    german_credit_data_actual.df = german_credit_data.df.head(100)
    german_credit_data_actual.upload(client, 'test_debug')

    german_credit_data_reference = german_credit_data.copy()
    german_credit_data_reference.df = german_credit_data.df.tail(100)
    german_credit_data_reference.upload(client, 'test_debug')

    german_credit_model.upload(client, 'test_debug')
    invariance = test_metamorphic_invariance(model=german_credit_model, threshold=0.2,
                                             dataset=german_credit_data,
                                             transformation_function=transform)

    auc = test_auc(model=german_credit_model, threshold=0.2, dataset=german_credit_data, slicing_function=slice)

    diff_accuracy = test_diff_accuracy(model=german_credit_model, threshold=0.2,
                                       actual_dataset=german_credit_data_actual,
                                       reference_dataset=german_credit_data_reference)

    Suite(name="Test Suite 1") \
        .add_test(auc) \
        .add_test(diff_accuracy) \
        .add_test(invariance) \
        .upload(client, 'test_debug')
