from pathlib import Path
from typing import Union

import mlflow
import numpy as np
import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader
from torch.utils.data import Dataset as torch_dataset

from giskard.core.core import SupportedModelTypes
from giskard.core.model import Model
from giskard.path_utils import get_size


class TorchMinimalDataset(torch_dataset):
    def __init__(self, df: pd.DataFrame, torch_dtype=torch.float32):
        self.entries = df
        self.torch_dtype = torch_dtype

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        return torch.tensor(self.entries.iloc[idx].to_numpy(), dtype=self.torch_dtype)


class PyTorchModel(Model):
    loader_module = 'giskard.models.pytorch'
    loader_class = 'PyTorchModel'

    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 torch_dtype=torch.float32,
                 device='cpu',
                 name: str = None,
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        super().__init__(clf,
                         model_type,
                         name,
                         data_preprocessing_function,
                         model_postprocessing_function,
                         feature_names,
                         classification_threshold,
                         classification_labels)

        self.device = device
        self.torch_dtype = torch_dtype

    @classmethod
    def read_model_from_local_dir(cls, local_path):
        return mlflow.pytorch.load_model(local_path)

    def save_to_local_dir(self, local_path):

        info = self._new_mlflow_model_meta()
        mlflow.pytorch.save_model(self.clf,
                                  path=local_path,
                                  mlflow_model=info)
        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
            yaml.dump(
                {
                    "language_version": info.flavors['python_function']['python_version'],
                    "loader_module": self.meta.loader_module,
                    "loader_class": self.meta.loader_class,
                    "language": "PYTHON",
                    "model_type": self.meta.model_type.name.upper(),
                    "threshold": self.meta.classification_threshold,
                    "feature_names": self.meta.feature_names,
                    "classification_labels": self.meta.classification_labels,
                    "id": info.model_uuid,
                    "name": self.meta.name,
                    "size": get_size(local_path),
                }, f, default_flow_style=False)

        return info

    def _raw_predict(self, data):
        self.clf.to(self.device)
        self.clf.eval()

        # Use isinstance to check if o is an instance of X or any subclass of X
        # Use is to check if the type of o is exactly X, excluding subclasses of X
        if isinstance(data, pd.DataFrame):
            data = TorchMinimalDataset(data, self.torch_dtype)
        elif not isinstance(data, torch_dataset) and not isinstance(data, DataLoader):
            raise Exception(f"The output of data_preprocessing_function is of type={type(data)}.\n \
                            Make sure that your data_preprocessing_function outputs one of the following: \n \
                            - pandas.DataFrame \n \
                            - torch.Dataset \n \
                            - torch.DataLoader")

        predictions = []
        with torch.no_grad():
            for entry in data:
                try:  # for the case of 1 input
                    predictions.append(self.clf(entry).detach().numpy())
                except:  # for the case of 2 inputs or more, like (input1, offset) or (input1, input2)
                    predictions.append(self.clf(*entry).detach().numpy())

        predictions = np.squeeze(np.array(predictions))

        if self.model_postprocessing_function:
            predictions = self.model_postprocessing_function(predictions)

        return predictions.squeeze()
