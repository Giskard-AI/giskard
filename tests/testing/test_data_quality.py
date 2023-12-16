import numpy as np
import pandas as pd
from giskard.testing.tests import data_quality
from giskard import Dataset

def test_uniqueness_test():
    """
    Test for the uniqueness_test function in the data_quality module.

    This test checks that the uniqueness_test function correctly calculates the 
    uniqueness ratio for a given column and correctly determines whether the 
    uniqueness ratio is above a specified threshold.

    Args:
        None

    Returns:
        None
    """
    data = {
        'column1': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        'column2': ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd', 'e', None]
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    # Call the function with test inputs
    result = data_quality.uniqueness_test(dataset, 'column1', 0.8)
    # Assert that the result is as expected
    assert result.passed is True

    result = data_quality.uniqueness_test(dataset, 'column2', 0.8)
    assert result.passed is False

def test_completeness_test():
    """
    Test for the completeness_test function in the data_quality module.

    This test checks that the completeness_test function correctly identifies incomplete data.

    Returns:
        None
    """
    # Setup data for testing
    data = {
        'age': [20, 25, 23, 40, 67, 55, 44, None, 47, 60],  # One missing value
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Call the function with test inputs
    result = data_quality.completeness_test(dataset, 'age', 0.9)
    # Assert that the result is as expected
    assert result.passed is True, "Test failed: there should be enough complete data"

    # Test case where there is not enough complete data
    data['age'] = [20, 25, 23, None, None, None, None, None, None, None]  # Many missing values
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    result = data_quality.completeness_test(dataset, 'age', 0.9)
    assert result.passed is False, "Test failed: there should not be enough complete data"

def test_range_test():
    """
    Test for the range_test function in the data_quality module. 

    This test checks that the range_test function correctly determines
    whether all values are within a range.

    Returns:
        None
    """
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
    result = data_quality.correlation_test(dataset, 'Survived', 'Pclass', False, 0.5)
    assert result.passed is True, "Test failed: Survived and Pclass should not have correlation above 0.5"

    result = data_quality.correlation_test(dataset, 'Survived', 'Age', False, 0.5)
    assert result.passed is True,"Test failed: Survivedand Age should not have correlation above 0.5"

    result = data_quality.correlation_test(dataset, 'Survived', 'Fare', True, 0.5)
    assert result.passed is True, "Test failed: Survived and Fare should have correlation above 0.5"
  
def test_outlier_test():
    """
    Test for the outlier_test function in the data_quality module.

    This test checks that the outlier_test function correctly identifies outliers in a given column.

    Returns:
        None
    """
    # Setup data for testing
    np.random.seed(0)
    data = {
        'column1': np.random.normal(0, 1, 1000),  # Normal distribution, should not have outliers
        'column2': np.concatenate([np.random.normal(0, 1, 990),
                                   np.array([10, 10, 10, 10, 10, 10, 10, 10, 10, 10])])
                                     # Normal distribution with some extreme values, should have outliers
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Call the function with test inputs
    result = data_quality.outlier(dataset, 'column1', eps=3, min_samples=2)
    # Assert that the result is as expected
    assert result.passed is True, "Test failed: column1 should not have outliers"

def test_ensure_all_exists():
    """
    Test for the ensure_all_exists function in the data_quality module.

    This test checks that the ensure_all_exists function
    correctly determines whether all values in a 
    given column are present in a column of another dataset.

    Returns:
        None
    """
    # Setup data for testing
    np.random.seed(0)
    data1 = {
        'column1': np.random.choice(['a', 'b', 'c', 'd', 'e'], 1000)
    }
    data2 = {
        'column2': np.random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'], 1000)
    }
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)
    dataset1 = Dataset(df1)
    dataset2 = Dataset(df2)

    # Call the function with test inputs
    result = data_quality.ensure_all_exists(dataset2, 'column2', dataset1, 'column1', threshold=0.0)
    # Assert that the result is as expected
    assert result.passed is False, "Test failed: All values in column2 are present in column1"

    result = data_quality.ensure_all_exists(dataset1, 'column1', dataset2, 'column2', threshold=0.5)
    assert result.passed is True, "Test failed: more than 50% of values in column1 should be present in column2"

    result = data_quality.ensure_all_exists(dataset1, 'column1', dataset2, 'column2', threshold=1.0)
    assert result.passed is True, "Test failed: all values in column1 should be present in column2"

def test_label_consistency_test():
    """
    Test for the label_consistency_test function in the data_quality module.

    This test checks that the label_consistency_test function correctly checks the consistency
    of the datatype across each label throughout the dataset.

    Args:
        setup_data (Dataset): The dataset to test.

    Returns:
        None
    """
    data = {
        'column1': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        'column2': ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd', 'e', 'f'],
        'column3': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    # Call the function with test inputs
    result = data_quality.label_consistency_test(dataset, 'column3')
    # Assert that the result is as expected
    assert result.passed is True

    result = data_quality.label_consistency_test(dataset, 'column1')
    assert result.passed is False

def test_mislabel():
    """
    Test for the mislabel function in the data_quality module.

    This test checks that the mislabel function correctly identifies mislabelled data.

    Returns:
        None
    """
    # Setup data for testing
    data = {
        'age': [20, 25, 23, 40, 67, 55, 44, 17, 47, 60],
        'group': ["<30", "<30", "<30", ">=30", ">=30", ">=30", ">=30", ">=30", ">=30", ">=30"],
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Call the function with test inputs
    result = data_quality.mislabel(dataset, 'group', reference_columns=['age'])
    # Assert that the result is as expected
    assert result.passed is False, "Test failed: there should be mislabelled data"
