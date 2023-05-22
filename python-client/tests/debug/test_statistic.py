from giskard.ml_worker.testing.tests.statistic import test_right_label, test_output_in_range, test_disparate_impact
from giskard.ml_worker.testing.registry.slicing_function import slicing_function

import pytest
import pandas as pd


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_statistic(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    dataset.df = dataset.df.head(20)

    classification_label = "Default"
    _predictions = model.predict(dataset)

    # test_right_label
    predictions = _predictions.prediction
    benchmark_failed_idx = list(dataset.df.loc[predictions != classification_label].index.values)
    result = test_right_label(model, dataset, classification_label=classification_label, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    # test_output_in_range
    predictions = _predictions.all_predictions[classification_label]
    benchmark_failed_idx = list(dataset.df.loc[(predictions > 0.7) | (predictions < 0.3)].index.values)
    result = test_output_in_range(model, dataset, classification_label=classification_label, debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx

    # test_disparate_impact
    @slicing_function(row_level=False)
    def protected_slice(df: pd.DataFrame):
        return df.head(10)

    @slicing_function(row_level=False)
    def unprotected_slice(df: pd.DataFrame):
        return df.tail(10)

    protected_ds = dataset.slice(protected_slice)
    unprotected_ds = dataset.slice(unprotected_slice)

    _protected_predictions = model.predict(protected_ds).prediction
    _unprotected_predictions = model.predict(unprotected_ds).prediction

    failed_protected = list(_protected_predictions != protected_ds.df[dataset.target])
    failed_unprotected = list(_unprotected_predictions != unprotected_ds.df[dataset.target])
    failed_idx_protected = [i for i, x in enumerate(failed_protected) if x]
    failed_idx_unprotected = [i for i, x in enumerate(failed_unprotected) if x]
    benchmark_failed_idx = failed_idx_protected + failed_idx_unprotected

    result = test_disparate_impact(model, dataset,
                                   protected_slicing_function=protected_slice,
                                   unprotected_slicing_function=unprotected_slice,
                                   max_threshold=1,
                                   positive_outcome="Not default", debug=True).execute()
    assert list(result.output_df.df.index.values) == benchmark_failed_idx
