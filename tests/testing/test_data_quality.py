import pandas as pd
from giskard.testing.tests import data_quality
from giskard import Dataset, test

def setup_data():
    """
    Setup data for testing
    """
    data = {
        'column1': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        'column2': ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd', 'e', None]
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    return dataset

@test
def test_uniqueness_test(setup_data):
    """
    Test for the uniqueness_test function in the data_quality module.

    This test checks that the uniqueness_test function correctly calculates the 
    uniqueness ratio for a given column and correctly determines whether the 
    uniqueness ratio is above a specified threshold.

    Args:
        setup_data (Dataset): The dataset to test.

    Returns:
        None
    """
    # Call the function with test inputs
    result = data_quality.uniqueness_test(setup_data, 'column1', 0.8).execute()
    # Assert that the result is as expected
    assert result.passed is True

    result = data_quality.uniqueness_test(setup_data, 'column2', 0.8).execute()
    assert result.passed is False

@test
def test_completeness_test(setup_data):
    """
        Test for the completeness_test function in the data_quality module.

    This test checks that the completeness_test function correctly calculates the 
    completeness ratio for a given column and correctly determines whether the 
    completeness ratio is above a specified threshold.

    Args:
        setup_data (Dataset): The dataset to test.

    Returns:
        None
    """
    # Call the function with test inputs
    result = data_quality.completeness_test(setup_data, 'column1').execute()
    # Assert that the result is as expected
    assert result.passed is True

    result = data_quality.completeness_test(setup_data, 'column2').execute()
    assert result.passed is False
