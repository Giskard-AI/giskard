import pandas as pd
from giskard.testing.tests import data_quality
from giskard import Dataset, test

def setup_data():
    # Setup code goes here. This could include creating a Dataset instance for testing.
    data = {
        'column1': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
        'column2': ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd', 'e', None]
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    return dataset

@test
def test_uniqueness_test(setup_data):
    # Call the function with test inputs
    result = data_quality.uniqueness_test(setup_data, 'column1', 0.8)
    # Assert that the result is as expected
    assert result.passed == True

    result = data_quality.uniqueness_test(setup_data, 'column2', 0.8)
    assert result.passed == False


