import pytest
import numpy as np

from giskard import slicing_function
from giskard.models.precooked import PrecookedModel


@slicing_function(row_level=False)
def random_slice(df):
    return df.sample(100)


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_precooked_model(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    precooked_model = PrecookedModel.from_model(model, dataset)

    assert np.all(precooked_model.predict(dataset).raw == model.predict(dataset).raw)

    data_slice = dataset.slice(random_slice)
    assert np.all(precooked_model.predict(data_slice).raw == model.predict(data_slice).raw)
