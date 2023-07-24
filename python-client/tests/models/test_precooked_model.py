import numpy as np
import pandas as pd
import pytest

from giskard import slicing_function
from giskard.models._precooked import PrecookedModel


@slicing_function(name="random", row_level=False)
def random_slice(df: pd.DataFrame) -> pd.DataFrame:
    return df.sample(100)


@pytest.mark.parametrize(
    "model,dataset",
    [("german_credit_model", "german_credit_data")],
)
def test_precooked_model(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)
    precooked_model = PrecookedModel.from_model(model, dataset)
    data_slice = dataset.slice(random_slice())
    # assert np.all(data_slice.df.columns == dataset.df.columns)
    # assert np.all(precooked_model.predict(dataset).raw == model.predict(dataset).raw)

    assert np.all(precooked_model.predict(data_slice).raw == model.predict(data_slice).raw)
