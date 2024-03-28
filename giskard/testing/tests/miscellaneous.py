import numpy as np

from giskard import Dataset, TestResult, test
from giskard.models.base import BaseModel
from giskard.testing.tests.debug_slicing_functions import row_failing_monotonicity_slicing_fn


@test(name="Monotonicity", tags=["monotonicity"])
def test_monotonicity(
    model: BaseModel,
    dataset: Dataset,
    column_name: str,
    increasing: bool = True,
    random_state: int = 123456,
    num_samples: int = 100,
    num_grid: int = 50,
    classif_index_label: int = 0,
    debug: bool = True,
):
    """Test if the model is monotonic for a given column name by selecting random samples from
    the dataset and augmenting them with different values for the specified column

    Parameters
    ----------
    model : BaseModel
        Model used to compute the test
    dataset : Dataset
        Actual dataset used to compute the test
    column_name : str
        Column name against which monotonicity is to be tested
    increasing : bool
        Whether to test for increasing or decreasing monotonicity
    random_state : int
        Random state for sampling
    num_samples : int
        Number of samples from which generate the grid and test
    num_grid : int
        Number of points in the grid of values for the colum
    classif_index_label : int
        If classification, which index to consider for the test
    debug : bool
        If True and the test fails,
        a dataset will be provided containing all the incorrectly predicted rows. (Default value = False)

    Returns
    -------
    TestResult
        The test result.
    """
    # Get min and max values
    min_col = dataset.df[column_name].min()
    max_col = dataset.df[column_name].max()

    # Create grid of values between min and max
    values_col = np.linspace(min_col, max_col, num_grid)

    # Generate data from existing rows by modifying the value of the column of interest
    augmented_df = []
    sample_rows = dataset.df.sample(n=num_samples, random_state=random_state).copy()
    for value in values_col:
        sample_rows_copy = sample_rows.copy()
        sample_rows_copy.loc[:, column_name] = value.astype(dataset.df.dtypes[column_name])
        augmented_df.append(sample_rows_copy)

    # Predictions
    predictions = []
    for current_df in augmented_df:
        predictions.append(model.predict_df(current_df[model.feature_names]))
    predictions = np.array(predictions)

    # If classification, select the right index in the last dimension
    if predictions.ndim == 3:
        predictions = predictions[:, :, classif_index_label]

    # Check for monotonicity
    if increasing:
        passed = np.diff(predictions, axis=0) >= 0
    else:
        passed = np.diff(predictions, axis=0) <= 0

    # --- debug ---
    output_ds = list()
    if not passed.all():
        output_ds.append(
            dataset.slice(row_failing_monotonicity_slicing_fn(index_failure=sample_rows.index[~passed.all(axis=0)]))
        )
    # ---

    return TestResult(passed=passed.all(), output_ds=output_ds)
