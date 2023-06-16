import numpy as np
import pandas as pd
import pytest

from giskard import slicing_function, Dataset, SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import transformation_function


@slicing_function(name="slice with parenthesis")
def filter_with_parenthesis(x: pd.Series) -> bool:
    return x.credit_amount > 1000


@slicing_function(name="slice cell level", cell_level=True)
def filter_cell_level(amount: int) -> bool:
    return amount > 1000


@slicing_function
def filter_without_parenthesis(x: pd.Series) -> bool:
    return x.credit_amount > 2000


@transformation_function(name="transform with parenthesis")
def transform_with_parenthesis(x: pd.Series) -> pd.Series:
    x.credit_amount = -1
    return x


@transformation_function
def transform_without_parenthesis(x: pd.Series) -> pd.Series:
    x.credit_amount = -2
    return x


@transformation_function
def transform_divide_by_five(x: pd.Series) -> pd.Series:
    x.credit_amount /= 5
    return x


@transformation_function(cell_level=True)
def column_level_divide(nb: float, amount: int) -> float:
    return nb / amount


def test_slicing(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    assert isinstance(filter_with_parenthesis, SlicingFunction), f"{type(filter_with_parenthesis)}"
    ds = german_credit_data.slice(filter_with_parenthesis)
    assert len(ds.df) == 884
    ds = ds.slice(filter_without_parenthesis)
    assert len(ds.df) == 568


def test_slicing_using_lambda(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    ds = german_credit_data.slice(lambda x: x.credit_amount > 1000)
    assert len(ds.df) == 884
    ds = ds.slice(lambda x: x.credit_amount > 2000)
    assert len(ds.df) == 568


def test_slicing_cell_level(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    assert isinstance(filter_with_parenthesis, SlicingFunction), f"{type(filter_with_parenthesis)}"
    ds = german_credit_data.slice(filter_cell_level, column_name="credit_amount")
    assert len(ds.df) == 884
    ds = ds.slice(lambda amount: amount > 2000, cell_level=True, column_name="credit_amount")
    assert len(ds.df) == 568


def test_chain(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    german_credit_data.add_slicing_function(filter_without_parenthesis)
    german_credit_data.add_transformation_function(transform_divide_by_five)
    german_credit_data.add_slicing_function(filter_with_parenthesis)
    assert len(german_credit_data.df) == 1000
    ds = german_credit_data.process()
    assert len(ds.df) == 188


def test_transform_cell_level(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000

    ds = (
        german_credit_data.slice(filter_without_parenthesis)
        .transform(column_level_divide(amount=5), column_name="credit_amount")
        .slice(filter_with_parenthesis)
    )

    assert len(german_credit_data.df) == 1000
    assert len(ds.df) == 188


def test_transform_cell_level_parameterized(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000

    ds = (
        german_credit_data.slice(filter_without_parenthesis)
        .transform(column_level_divide(column_name="credit_amount", amount=5))
        .slice(filter_with_parenthesis)
    )

    assert len(german_credit_data.df) == 1000
    assert len(ds.df) == 188


def test_transform_cell_level_lambda(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000

    ds = (
        german_credit_data.slice(filter_without_parenthesis)
        .transform(lambda i: i / 5, cell_level=True, column_name="credit_amount")
        .slice(filter_with_parenthesis)
    )

    assert len(german_credit_data.df) == 1000
    assert len(ds.df) == 188


def test_transformation(german_credit_data: Dataset):
    ds = german_credit_data.transform(transform_without_parenthesis)
    assert np.all(ds.df.credit_amount == -2)
    ds = german_credit_data.transform(transform_with_parenthesis)
    assert np.all(ds.df.credit_amount == -1)
    assert len(german_credit_data.df) == 1000
    assert len(german_credit_data.df.credit_amount.unique()) > 1


def test_transformation_without_annotation(german_credit_data: Dataset):
    def transform_without_annotation(x: pd.Series) -> pd.Series:
        x.credit_amount = -2
        return x

    ds = german_credit_data.transform(transform_without_annotation)
    assert np.all(ds.df.credit_amount == -2)
    assert len(german_credit_data.df) == 1000
    assert len(german_credit_data.df.credit_amount.unique()) > 1


def test_missing_arg_slicing_function():
    with pytest.raises(
        TypeError, match="Required arg 0 of slice_fn to be <class 'pandas.core.series.Series'>, but none was defined"
    ):

        @slicing_function
        def slice_fn():
            return True


def test_wrong_type_slicing_function():
    with pytest.raises(
        TypeError,
        match="Required arg 0 of slice_fn to be <class 'pandas.core.series.Series'>, but <class 'int'> was defined",
    ):

        @slicing_function
        def slice_fn(row: int):
            return row > 0

        slice_fn("str")


def test_chain_with_parameters(german_credit_data: Dataset):
    @slicing_function(name="row greater than")
    def filter_greater_than(x: pd.Series, row: str, threshold: int) -> bool:
        return x[row] > threshold

    @transformation_function
    def transform_divide_by(x: pd.Series, row: str, divider: int) -> pd.Series:
        x[row] /= divider
        return x

    assert len(german_credit_data.df) == 1000
    german_credit_data.add_slicing_function(filter_greater_than("credit_amount", 2000))
    german_credit_data.add_transformation_function(transform_divide_by("credit_amount", 5))
    german_credit_data.add_slicing_function(filter_greater_than("credit_amount", 1000))
    assert len(german_credit_data.df) == 1000
    ds = german_credit_data.process()
    assert len(ds.df) == 188


def test_transformation_without_type():
    @transformation_function(row_level=True)
    def add_positive_sentence(row):
        row = row.copy()
        row.text += " I love this!"
        return row

    df = pd.DataFrame([{"text": "testing."}])
    dataset = Dataset(df, cat_columns=[])
    transformed_dataset = dataset.transform(add_positive_sentence)

    assert transformed_dataset.df.iloc[0].text == "testing. I love this!"
