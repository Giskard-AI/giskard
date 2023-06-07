import numpy as np
import pandas as pd
import pytest
import torch
import torch.nn as nn

from giskard import Dataset
from giskard.core.model_validation import validate_model
from giskard.models.pytorch import PyTorchModel


class ManualLinearRegression(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)


def test_error():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = ManualLinearRegression().to(device)

    df = pd.DataFrame({"x": np.array([1]), "y": np.array([2])})

    def preproc_func(df):
        return df.values.tolist()

    my_model = PyTorchModel(
        name="my_linear_model",
        model=model,
        feature_names=["x"],
        model_type="regression",
        data_preprocessing_function=preproc_func,
    )

    my_test_dataset = Dataset(df.head(), name="test dataset", target="y")

    with pytest.raises(Exception) as e:
        validate_model(my_model, validate_ds=my_test_dataset)
        assert e.match(
            f"The output of data_preprocessing_function is of type={type(df.values.tolist())}.\n \
                            Make sure that your data_preprocessing_function outputs one of the following: \n \
                            - pandas.DataFrame \n \
                            - torch.Dataset \n \
                            - torch.DataLoader"
        )
