import numpy as np
import pandas as pd

from giskard import Dataset
from giskard.models.base.wrapper import WrapperModel


def test_wrapper_model_handles_batching():
    class CustomModel(WrapperModel):
        expected_batch_size = []

        def model_predict(self, data):
            assert len(data) in self.expected_batch_size
            return [0] * len(data)

        @classmethod
        def load_model(cls):
            pass

        def save_model(self, path):
            pass

    dataset = Dataset(pd.DataFrame({"A": np.ones(101)}))

    model = CustomModel(None, model_type="regression")
    model.expected_batch_size = [101]

    model.predict(dataset)

    model = CustomModel(None, model_type="regression", batch_size=1)
    model.expected_batch_size = [1]

    model.predict(dataset)

    model = CustomModel(None, model_type="regression", batch_size=20)
    model.expected_batch_size = [20, 1]

    model.predict(dataset)
