import numpy as np
import pandas as pd
import pytest

from giskard import Dataset, Model
from giskard.testing.tests import stability


def test_checks():
    """
    Test for checks in stability

    Returns:
        None
    """

    # Create data
    data = {
        "seasonality_x": np.arange(0, 1, 0.01),
        "seasonality_y": np.arange(0, 1, 0.01),
        "non_numeric": ["object" for _ in range(np.arange(0, 1, 0.01).shape[0])],
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)

    # Create models
    model_error_1 = Model(
        lambda df: df["seasonality_x"], model_type="regression", feature_names=["seasonality_x", "seasonality_y"]
    )
    model_error_2 = Model(lambda df: df["seasonality_x"], model_type="regression", feature_names=["non_numeric"])

    # Check if raises error when feature is not in model.features
    with pytest.raises(ValueError):
        stability._check_features(
            feature_names=["non_numeric"],
            feature_values=None,
            model=model_error_1,
            dataset=dataset,
        ).execute()

    # Check if raises error when feature is not numeric
    with pytest.raises(ValueError):
        stability.test_smoothness(
            feature_names=["non_numeric"],
            feature_values=None,
            model=model_error_2,
            datatset=dataset,
        ).execute()


@pytest.mark.parametrize("ord", [1, 2])
def test_smoothness(ord):
    """
    Test for smoothness function in the stability module

    Returns:
        None
    """

    # Generate model and dataset
    rng = np.random.default_rng(123456)
    data = {
        "seasonality_x": np.arange(0, 1, 0.01),
        "seasonality_y": np.arange(0, 1, 0.01),
        "non_numeric": ["object" for _ in range(np.arange(0, 1, 0.01).shape[0])],
    }
    df = pd.DataFrame(data)
    dataset = Dataset(df)
    model_smooth = Model(
        lambda df: df["seasonality_x"], model_type="regression", feature_names=["seasonality_x", "seasonality_y"]
    )
    model_rough = Model(
        lambda df: pd.Series(rng.random(size=len(df)) * 100),
        model_type="regression",
        feature_names=["seasonality_x", "seasonality_y"],
    )

    # Column values to test
    column_values = {
        "seasonality_x": np.sin(2 * np.pi * np.arange(0, 1, 0.01)),
        "seasonality_y": np.cos(2 * np.pi * np.arange(0, 1, 0.01)),
    }

    ref_function = np.sin(2 * np.pi * np.arange(0, 1, 0.01))

    # Call the function with test inputs
    result = stability.test_smoothness(
        model_smooth,
        dataset,
        feature_names=["seasonality_x", "seasonality_y"],
        feature_values=column_values,
        ord=ord,
        ref_function=ref_function,
    ).execute()

    # Assert that the result is as expected
    assert result.passed, "Test failed: the model should be considered smooth"
    if ord == 1:
        assert np.isclose(result.metric, 0, atol=1e-3), "Test failed: the metric value should be 0"
    elif ord == 2:
        assert np.isclose(result.metric, 0, atol=1e-3), "Test failed: the metric value should be 0"

    # Call the function with test inputs
    result = stability.test_smoothness(
        model_rough,
        dataset,
        feature_names=["seasonality_x", "seasonality_y"],
        feature_values=column_values,
        ord=ord,
        ref_function=ref_function,
    ).execute()

    # Assert that the result is as expected
    assert not result.passed, "Test failed: the model should not be considered smooth"
    if ord == 1:
        assert np.isclose(result.metric, 3.020, atol=1e-3), "Test failed: the metric value should be 3.020"
    elif ord == 2:
        assert np.isclose(result.metric, 9.003, atol=1e-3), "Test failed: the metric value should be 9.003"


def test_monotonicity():
    """
    Test for the monotonicity function in the stability module.

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
    result = stability.test_monotonicity(model_increasing, dataset, feature_names=["col1"]).execute()

    # Assert that the result is as expected
    assert result.passed, "Test failed: the model should be considered monotonic"
    assert result.metric == 0, "Test failed: the metric value should be 0"

    # Call the function with test inputs
    result = stability.test_monotonicity(model_increasing, dataset, feature_names=["col1"], increasing=False).execute()

    # Assert that the result is as expected
    assert not result.passed, "Test failed: the model should not be considered monotonic"
    assert result.metric == 1, "Test failed: the metric value should be 1"
