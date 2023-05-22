import pandas as pd
import pytest

from giskard.ml_worker.testing.tests.metamorphic import test_metamorphic_invariance, test_metamorphic_increasing, \
    test_metamorphic_decreasing
from giskard.ml_worker.testing.registry.transformation_function import transformation_function


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_portion(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    dataset.df = dataset.df.head(100)

    @transformation_function(row_level=False)
    def transformation_func(df: pd.DataFrame):
        df['age'] += 10
        return df

    perturbed_dataset = dataset.transform(transformation_func)

    predictions = model.predict(dataset).raw_prediction
    perturbed_predictions = model.predict(perturbed_dataset).raw_prediction

    # Invariance
    failed_predictions = predictions != perturbed_predictions
    failed_idx = [i for i, x in enumerate(failed_predictions) if x]

    result = test_metamorphic_invariance(model, dataset, transformation_func,
                                         threshold=1, debug=True).execute()
    assert list(result.output_df.df.index.values) == failed_idx

    classification_label = "Default"

    predictions = model.predict(dataset).all_predictions[classification_label].values
    perturbed_predictions = model.predict(perturbed_dataset).all_predictions[classification_label].values

    # Increasing
    failed_predictions = predictions >= perturbed_predictions
    failed_idx = [i for i, x in enumerate(failed_predictions) if x]

    result = test_metamorphic_increasing(model, dataset, transformation_func,
                                         classification_label=classification_label, threshold=1, debug=True).execute()
    assert list(result.output_df.df.index.values) == failed_idx

    # Decreasing
    failed_predictions = predictions <= perturbed_predictions
    failed_idx = [i for i, x in enumerate(failed_predictions) if x]

    result = test_metamorphic_decreasing(model, dataset, transformation_func,
                                         classification_label=classification_label, threshold=1, debug=True).execute()
    assert list(result.output_df.df.index.values) == failed_idx
