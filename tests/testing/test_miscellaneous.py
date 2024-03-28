import numpy as np
import pandas as pd

from giskard import Dataset, Model
from giskard.testing.tests import miscellaneous


def test_monotonicity():
    """
    Test for the monotonicity function in the miscellaneous module.

    This test checks that the model is monotonic with respect to a given column.

    Returns:
        None
    """
    # Setup data for testing
    data = {
        "col1": np.arange(0, 1, 0.01),
        "col2": np.arange(0, 1, 0.01),
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    model_increasing = Model(lambda df: df["col1"], model_type="regression", feature_names=["col1", "col2"])

    # Call the function with test inputs
    result = miscellaneous.test_monotonicity(model_increasing, dataset, "col1").execute()

    # Assert that the result is as expected
    assert result.passed, "Test failed: the model should be monotonic"

    # Call the function with test inputs
    result = miscellaneous.test_monotonicity(model_increasing, dataset, "col1", increasing=False).execute()

    # Assert that the result is as expected
    assert not result.passed, "Test failed: the model should not be monotonic"
