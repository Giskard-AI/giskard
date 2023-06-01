import numpy as np
import pandas as pd

from giskard import slicing_function, Dataset
from giskard.ml_worker.testing.registry.transformation_function import transformation_function


@slicing_function(name='slice with parenthesis')
def filter_with_parenthesis(x: pd.Series) -> bool:
    return x.credit_amount > 1000


@slicing_function
def filter_without_parenthesis(x: pd.Series) -> bool:
    return x.credit_amount > 2000


@transformation_function(name='transform with parenthesis')
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


def test_slicing(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    ds = german_credit_data.slice(filter_with_parenthesis)
    assert len(ds.df) == 884
    ds = ds.slice(filter_without_parenthesis)
    assert len(ds.df) == 568


def test_chain(german_credit_data: Dataset):
    assert len(german_credit_data.df) == 1000
    german_credit_data.add_slicing_function(filter_without_parenthesis)
    german_credit_data.add_transformation_function(transform_divide_by_five)
    german_credit_data.add_slicing_function(filter_with_parenthesis)
    assert len(german_credit_data.df) == 1000
    ds = german_credit_data.process()
    assert len(ds.df) == 188


def test_transformation(german_credit_data: Dataset):
    ds = german_credit_data.transform(transform_without_parenthesis)
    assert np.all(ds.df.credit_amount == -2)
    ds = german_credit_data.transform(transform_with_parenthesis)
    assert np.all(ds.df.credit_amount == -1)
    assert len(german_credit_data.df) == 1000
    assert len(german_credit_data.df.credit_amount.unique()) > 1
