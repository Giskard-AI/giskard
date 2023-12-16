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

@test
def test_range_test():
    data = {
        'column1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'column2': [1, 2, 3, 4, 5, 100, 7, 8, 9, 10],
        'column3': [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10],
        'column4': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Test with column1, expected to pass
    result = data_quality.range_test(dataset, 'column1', 1, 10)
    assert result.passed is True

    # Test with column2, expected to fail
    result = data_quality.range_test(dataset, 'column2', 1, 10)
    assert result.passed is False

    # Test with column3, expected to fail
    result = data_quality.range_test(dataset, 'column3', 1, 10)
    assert result.passed is False

    # Test with column4, expected to pass
    result = data_quality.range_test(dataset, 'column4', 0, 0)
    assert result.passed is True

@test
def test_validity_test():
    """
    Test for the validity_test function in the data_quality module.

    This test checks that the validity_test function correctly determines whether all values in a 
    given column are in a specified set of valid values.

    Returns:
        None
    """
    # Setup data for testing
    data = {
        'column1': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        'column2': ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd', 'e', 'z']
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Call the function with test inputs
    result = data_quality.validity_test(dataset,
                                        'column1',
                                        valid_values=['a', 'b', 'c',
                                                    'd', 'e', 'f',
                                                    'g', 'h', 'i', 'j'])
    # Assert that the result is as expected
    assert result.passed is True

    result = data_quality.validity_test(dataset,
                                        'column2',
                                        valid_values=['a', 'b', 'c', 'd', 'e'])
    assert result.passed is False

@test
def test_correlation_test():
    """
    Test for the correlation_test function in the data_quality module.

    This test checks that the correlation_test function correctly determines whether two columns 
    in a given dataset have a correlation that is above a specified threshold.

    Returns:
        None
    """
    # Setup data for testing
    data = {
        'Survived': [0, 1, 1, 1, 0],
        'Pclass': [3, 1, 3, 1, 3],
        'Age': [22, 38, 26, 35, 35],
        'Fare': [7.25, 71.2833, 7.925, 53.1, 8.05]
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Call the function with test inputs
    result = data_quality.correlation_test(dataset, 'Survived', 'Pclass', False, 0.5).execute()
    # Assert that the result is as expected
    assert result.passed is True, "Test failed: Survived and Pclass should not have correlation above 0.5"

    result = data_quality.correlation_test(dataset, 'Survived', 'Age', False, 0.5).execute()
    assert result.passed is True, "Test failed: Survived and Age should not have correlation above 0.5"

    result = data_quality.correlation_test(dataset, 'Survived', 'Fare', True, 0.5).execute()
    assert result.passed is True, "Test failed: Survived and Fare should have correlation above 0.5"
   